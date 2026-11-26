using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Windows.Forms;

namespace HrisDeviceTool
{
    // Pagar pengaman bertingkat (bukan keamanan penuh): user < supervisor < manager < direksi < administrator
    public static class Peran
    {
        public static readonly string[] Nama = new string[] { "user", "supervisor", "manager", "direksi", "administrator" };
        public static int Level = 0; // 0 = belum masuk

        public static string NamaAktif
        {
            get { return Level == 0 ? "belum masuk" : Nama[Level - 1]; }
        }

        static Dictionary<string, int> perlu = Isi();

        static Dictionary<string, int> Isi()
        {
            Dictionary<string, int> d = new Dictionary<string, int>();
            string[] u1 = { "OnInfo", "OnPindai", "OnRingkas", "OnEkspor", "OnCekUser", "OnDaftarUser", "OnBanding", "OnTarikLog", "OnKelolaSalinan", "OnDiagnostik", "OnPanduan", "OnCekSemua", "OnCekDb" };
            string[] u2 = { "OnTambahUserUji", "OnPicu", "OnSelesai", "OnBacaTemplate", "OnKirimHris" };
            string[] u3 = { "HapusPermanenSalinan", "OnCadangDb" };
            string[] u5 = { "OnTambah", "OnUbah", "OnHapus", "OnUrutAz", "OnGeser", "OnPengaturanHris" };
            foreach (string s in u1) d[s] = 1;
            foreach (string s in u2) d[s] = 2;
            foreach (string s in u3) d[s] = 3;
            foreach (string s in u5) d[s] = 5;
            return d;
        }

        // Aksi yang belum terdaftar otomatis butuh administrator
        public static bool Boleh(string aksi)
        {
            int p;
            if (!perlu.TryGetValue(aksi, out p)) p = 5;
            if (Level >= p) return true;
            AuditLog.Tulis("Ditolak", aksi + " (butuh minimal " + Nama[p - 1] + ")");
            MessageBox.Show("Aksi ini butuh peran minimal \"" + Nama[p - 1] + "\".\r\nAnda masuk sebagai \"" + NamaAktif + "\".",
                "HRIS Device Tool", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return false;
        }
    }

    public class LoginForm : Form
    {
        ComboBox cmb;
        TextBox txt;
        public int Pilihan { get { return cmb.SelectedIndex; } }
        public string Sandi { get { return txt.Text; } }

        public LoginForm(string pesan)
        {
            Text = "HRIS Device Tool - Masuk";
            FormBorderStyle = FormBorderStyle.FixedDialog;
            StartPosition = FormStartPosition.CenterScreen;
            MinimizeBox = false;
            MaximizeBox = false;
            ClientSize = new Size(340, 195);

            Label l1 = new Label();
            l1.Text = pesan;
            l1.Location = new Point(12, 10);
            l1.Size = new Size(316, 32);
            Label l2 = new Label();
            l2.Text = "Peran";
            l2.Location = new Point(12, 48);
            l2.AutoSize = true;
            cmb = new ComboBox();
            cmb.DropDownStyle = ComboBoxStyle.DropDownList;
            cmb.Location = new Point(12, 64);
            cmb.Width = 316;
            foreach (string n in Peran.Nama) cmb.Items.Add(n);
            cmb.SelectedIndex = 0;
            Label l3 = new Label();
            l3.Text = "Kata sandi";
            l3.Location = new Point(12, 98);
            l3.AutoSize = true;
            txt = new TextBox();
            txt.Location = new Point(12, 114);
            txt.Width = 316;
            txt.UseSystemPasswordChar = true;

            Button ok = new Button();
            ok.Text = "Masuk";
            ok.DialogResult = DialogResult.OK;
            ok.Location = new Point(158, 154);
            Button cancel = new Button();
            cancel.Text = "Keluar";
            cancel.DialogResult = DialogResult.Cancel;
            cancel.Location = new Point(248, 154);

            Controls.Add(l1);
            Controls.Add(l2);
            Controls.Add(cmb);
            Controls.Add(l3);
            Controls.Add(txt);
            Controls.Add(ok);
            Controls.Add(cancel);
            AcceptButton = ok;
            CancelButton = cancel;
            ActiveControl = txt;
        }
    }

    // Lima akun tetap. Kata sandi disimpan sebagai hash PBKDF2 + salt di data\pengguna.hdtusr
    public static class Akun
    {
        static readonly string[] Bawaan = new string[] { "user123", "supervisor123", "manager123", "direksi123", "administrator123" };

        static string Berkas(Store st) { return Path.Combine(st.DataDir, "pengguna.hdtusr"); }

        static string[] Buat(string pw)
        {
            byte[] salt = new byte[16];
            RandomNumberGenerator rng = RandomNumberGenerator.Create();
            rng.GetBytes(salt);
            byte[] h = new Rfc2898DeriveBytes(pw, salt, 20000).GetBytes(32);
            return new string[] { Convert.ToBase64String(salt), Convert.ToBase64String(h) };
        }

        static bool Sama(string pw, string[] rec)
        {
            byte[] salt = Convert.FromBase64String(rec[0]);
            byte[] ex = Convert.FromBase64String(rec[1]);
            byte[] h = new Rfc2898DeriveBytes(pw, salt, 20000).GetBytes(32);
            if (h.Length != ex.Length) return false;
            int diff = 0;
            for (int i = 0; i < h.Length; i++) diff |= h[i] ^ ex[i];
            return diff == 0;
        }

        static void Simpan(Store st, Dictionary<string, string[]> d)
        {
            StringBuilder sb = new StringBuilder();
            foreach (string n in Peran.Nama)
                sb.Append(n).Append(':').Append(d[n][0]).Append(':').Append(d[n][1]).Append("\r\n");
            File.WriteAllText(Berkas(st), sb.ToString(), new UTF8Encoding(false));
        }

        static Dictionary<string, string[]> Muat(Store st)
        {
            Dictionary<string, string[]> d = new Dictionary<string, string[]>();
            string f = Berkas(st);
            if (File.Exists(f))
            {
                foreach (string line in File.ReadAllLines(f))
                {
                    string[] p = line.Trim().Split(':');
                    if (p.Length == 3) d[p[0]] = new string[] { p[1], p[2] };
                }
            }
            bool ubah = false;
            for (int i = 0; i < Peran.Nama.Length; i++)
            {
                if (!d.ContainsKey(Peran.Nama[i]))
                {
                    d[Peran.Nama[i]] = Buat(Bawaan[i]);
                    ubah = true;
                }
            }
            if (ubah) Simpan(st, d);
            return d;
        }

        // true = berhasil masuk
        public static bool Masuk(Store st)
        {
            AuditLog.Dir = st.LogDir;
            Dictionary<string, string[]> d;
            try { d = Muat(st); }
            catch (Exception e)
            {
                MessageBox.Show("Berkas pengguna tidak bisa dibaca:\r\n" + e.Message, "HRIS Device Tool", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return false;
            }
            string pesan = "Pilih peran dan masukkan kata sandi.";
            while (true)
            {
                LoginForm f = new LoginForm(pesan);
                DialogResult r = f.ShowDialog();
                int idx = f.Pilihan;
                string pw = f.Sandi;
                f.Dispose();
                if (r != DialogResult.OK)
                {
                    AuditLog.Tulis("Login", "dibatalkan");
                    return false;
                }
                if (Sama(pw, d[Peran.Nama[idx]]))
                {
                    Peran.Level = idx + 1;
                    AuditLog.Tulis("Login", "berhasil sebagai " + Peran.Nama[idx]);
                    return true;
                }
                AuditLog.Tulis("Login", "GAGAL untuk peran " + Peran.Nama[idx]);
                Thread.Sleep(800);
                pesan = "Kata sandi salah. Coba lagi.";
            }
        }

        public static void Ganti(Store st)
        {
            try
            {
                Dictionary<string, string[]> d = Muat(st);
                int target = Peran.Level;
                if (Peran.Level == 5)
                {
                    string t = Dlg.Prompt("Ganti kata sandi", "Peran yang diganti (user, supervisor, manager, direksi, administrator):", false, false);
                    if (t == null) return;
                    target = Array.IndexOf(Peran.Nama, t.Trim().ToLowerInvariant()) + 1;
                    if (target == 0) { MessageBox.Show("Nama peran tidak dikenal.", "HRIS Device Tool"); return; }
                }
                string nama = Peran.Nama[target - 1];
                if (target == Peran.Level)
                {
                    string lama = Dlg.Prompt("Ganti kata sandi", "Kata sandi saat ini untuk \"" + nama + "\":", true, false);
                    if (lama == null) return;
                    if (!Sama(lama, d[nama])) { MessageBox.Show("Kata sandi saat ini salah.", "HRIS Device Tool"); return; }
                }
                string baru = Dlg.Prompt("Ganti kata sandi", "Kata sandi baru untuk \"" + nama + "\" (minimal 4 karakter):", true, true);
                if (baru == null) return;
                if (baru.Length < 4) { MessageBox.Show("Kata sandi minimal 4 karakter.", "HRIS Device Tool"); return; }
                d[nama] = Buat(baru);
                Simpan(st, d);
                AuditLog.Tulis("Ganti kata sandi", "peran " + nama + " (oleh " + Peran.NamaAktif + ")");
                MessageBox.Show("Kata sandi \"" + nama + "\" diganti.", "HRIS Device Tool");
            }
            catch (Exception e)
            {
                MessageBox.Show("Gagal mengganti kata sandi:\r\n" + e.Message, "HRIS Device Tool", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
        }
    }
}
