using System;
using System.Drawing;
using System.IO;
using System.Threading;
using System.Windows.Forms;

namespace HrisDeviceTool
{
    // Token HRIS disimpan terenkripsi Windows (DPAPI) di data\hris.hdtsec, terpisah dari mesin.hdtdata.
    public static class HrisToken
    {
        public const int Panjang = 48;
        public const string Awalan = "hris_";

        public static string Berkas(Store st) { return Path.Combine(st.DataDir, "hris.hdtsec"); }
        public static bool Ada(Store st) { return File.Exists(Berkas(st)); }

        public static bool Valid(string t)
        {
            return t != null && t.Length == Panjang && t.StartsWith(Awalan, StringComparison.Ordinal);
        }

        public static void Simpan(Store st, string token)
        {
            File.WriteAllBytes(Berkas(st), Dpapi.Lindungi(token));
        }

        public static void Hapus(Store st)
        {
            if (File.Exists(Berkas(st))) File.Delete(Berkas(st));
        }

        // null bila belum ada atau tidak bisa dibuka (PC/akun Windows lain)
        public static string Ambil(Store st)
        {
            string f = Berkas(st);
            if (!File.Exists(f)) return null;
            string plain;
            try
            {
                if (!Dpapi.TryBuka(File.ReadAllBytes(f), out plain)) return null;
            }
            catch (Exception) { return null; }
            return plain;
        }
    }

    public class HrisDialog : Form
    {
        Store st;
        TextBox txtUrl, txtToken;
        ComboBox cmbMesin;
        Button btnTes;
        Label lblStatus, lblTokenAda;

        Label Lbl(string t, int x, int y)
        {
            Label l = new Label();
            l.Text = t;
            l.Location = new Point(x, y);
            l.AutoSize = true;
            return l;
        }

        public HrisDialog(Store store)
        {
            st = store;
            Text = "Pengaturan HRIS";
            FormBorderStyle = FormBorderStyle.FixedDialog;
            StartPosition = FormStartPosition.CenterParent;
            MinimizeBox = false;
            MaximizeBox = false;
            ClientSize = new Size(460, 322);

            Controls.Add(Lbl("Alamat server HRIS (contoh: http://10.1.0.26:8001)", 12, 10));
            txtUrl = new TextBox();
            txtUrl.Location = new Point(12, 28);
            txtUrl.Width = 436;
            txtUrl.Text = st.Data.UrlHris ?? "";
            Controls.Add(txtUrl);

            lblTokenAda = Lbl(HrisToken.Ada(st)
                ? "Token: sudah tersimpan di PC ini (kosongkan kolom di bawah untuk tetap memakainya)."
                : "Token: belum ada.", 12, 62);
            Controls.Add(lblTokenAda);
            Controls.Add(Lbl("Token baru (48 karakter, diawali hris_)", 12, 84));
            txtToken = new TextBox();
            txtToken.Location = new Point(12, 102);
            txtToken.Width = 436;
            txtToken.UseSystemPasswordChar = true;
            Controls.Add(txtToken);

            Controls.Add(Lbl("Mesin untuk tes koneksi (harus punya Nama di HRIS)", 12, 136));
            cmbMesin = new ComboBox();
            cmbMesin.DropDownStyle = ComboBoxStyle.DropDownList;
            cmbMesin.Location = new Point(12, 154);
            cmbMesin.Width = 436;
            foreach (MesinItem m in st.Data.Mesin)
            {
                if ((m.NamaDiHris ?? "").Trim().Length > 0) cmbMesin.Items.Add(m);
            }
            if (cmbMesin.Items.Count > 0) cmbMesin.SelectedIndex = 0;
            Controls.Add(cmbMesin);

            btnTes = new Button();
            btnTes.Text = "Tes koneksi";
            btnTes.Location = new Point(12, 188);
            btnTes.Size = new Size(110, 28);
            btnTes.Click += delegate { OnTes(); };
            Controls.Add(btnTes);

            Button btnHapusToken = new Button();
            btnHapusToken.Text = "Hapus token";
            btnHapusToken.Location = new Point(130, 188);
            btnHapusToken.Size = new Size(110, 28);
            btnHapusToken.Click += delegate { OnHapusToken(); };
            Controls.Add(btnHapusToken);

            lblStatus = new Label();
            lblStatus.Location = new Point(12, 226);
            lblStatus.Size = new Size(436, 50);
            Controls.Add(lblStatus);

            Button btnSimpan = new Button();
            btnSimpan.Text = "Simpan";
            btnSimpan.Location = new Point(278, 284);
            btnSimpan.Size = new Size(80, 28);
            btnSimpan.Click += delegate { OnSimpan(); };
            Controls.Add(btnSimpan);

            Button btnTutup = new Button();
            btnTutup.Text = "Tutup";
            btnTutup.Location = new Point(368, 284);
            btnTutup.Size = new Size(80, 28);
            btnTutup.DialogResult = DialogResult.Cancel;
            Controls.Add(btnTutup);
            CancelButton = btnTutup;
        }

        string UrlBersih()
        {
            string u = txtUrl.Text.Trim().TrimEnd('/');
            Uri uri;
            if (!Uri.TryCreate(u, UriKind.Absolute, out uri) ||
                (uri.Scheme != Uri.UriSchemeHttp && uri.Scheme != Uri.UriSchemeHttps))
            {
                MessageBox.Show("Alamat server harus diawali http:// atau https://", "Pengaturan HRIS",
                    MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return null;
            }
            return u;
        }

        void OnTes()
        {
            string url = UrlBersih();
            if (url == null) return;
            string tok = txtToken.Text.Trim();
            if (tok.Length == 0) tok = HrisToken.Ambil(st);
            if (!HrisToken.Valid(tok))
            {
                MessageBox.Show("Token belum ada atau formatnya salah (harus 48 karakter, diawali hris_).\r\n" +
                    "Tes tidak dikirim, supaya tidak menambah hitungan blokir di server.",
                    "Pengaturan HRIS", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }
            MesinItem m = cmbMesin.SelectedItem as MesinItem;
            if (m == null)
            {
                MessageBox.Show("Pilih mesin untuk tes. Isi dulu kolom Nama di HRIS pada mesin (tombol Ubah).",
                    "Pengaturan HRIS", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }
            string nama = m.NamaDiHris.Trim();
            btnTes.Enabled = false;
            lblStatus.Text = "Menghubungi server...";
            ThreadPool.QueueUserWorkItem(delegate (object s)
            {
                string pesan;
                bool ok = false;
                try { ok = KirimHris.TesKoneksi(url, tok, nama, out pesan); }
                catch (Exception ex) { pesan = "Kesalahan: " + ex.Message; }
                if (IsHandleCreated && !IsDisposed)
                {
                    BeginInvoke(new MethodInvoker(delegate
                    {
                        btnTes.Enabled = true;
                        lblStatus.Text = (ok ? "BERHASIL. " : "GAGAL. ") + pesan;
                    }));
                }
            });
        }

        void OnSimpan()
        {
            string url = UrlBersih();
            if (url == null) return;
            string tok = txtToken.Text.Trim();
            if (tok.Length > 0 && !HrisToken.Valid(tok))
            {
                MessageBox.Show("Format token salah (harus 48 karakter, diawali hris_). Tidak disimpan.",
                    "Pengaturan HRIS", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }
            try
            {
                st.Data.UrlHris = url;
                st.SaveData();
                if (tok.Length > 0) HrisToken.Simpan(st, tok);
            }
            catch (Exception e)
            {
                MessageBox.Show("Gagal menyimpan:\r\n" + e.Message, "Pengaturan HRIS",
                    MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }
            AuditLog.Tulis("Pengaturan HRIS", "URL " + url + (tok.Length > 0 ? ", token diganti" : ""));
            txtToken.Clear();
            lblTokenAda.Text = "Token: sudah tersimpan di PC ini (kosongkan kolom di bawah untuk tetap memakainya).";
            lblStatus.Text = "Tersimpan.";
        }

        void OnHapusToken()
        {
            if (!HrisToken.Ada(st)) { MessageBox.Show("Belum ada token tersimpan."); return; }
            if (MessageBox.Show("Hapus token HRIS yang tersimpan di PC ini?", "Pengaturan HRIS",
                MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
            try
            {
                HrisToken.Hapus(st);
                AuditLog.Tulis("Pengaturan HRIS", "token dihapus");
                lblTokenAda.Text = "Token: belum ada.";
                lblStatus.Text = "Token dihapus.";
            }
            catch (Exception e)
            {
                MessageBox.Show("Gagal menghapus:\r\n" + e.Message, "Pengaturan HRIS");
            }
        }
    }
}