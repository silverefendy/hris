using System;
using System.Drawing;
using System.Windows.Forms;

namespace HrisDeviceTool
{
    public static class Dlg
    {
        // Mengembalikan teks, atau null bila dibatalkan
        public static string Prompt(string title, string text, bool secret, bool confirm)
        {
            Form f = new Form();
            f.Text = title;
            f.FormBorderStyle = FormBorderStyle.FixedDialog;
            f.StartPosition = FormStartPosition.CenterScreen;
            f.MinimizeBox = false;
            f.MaximizeBox = false;
            f.ClientSize = new Size(400, confirm ? 190 : 140);

            Label l = new Label();
            l.Text = text;
            l.Location = new Point(12, 10);
            l.Size = new Size(376, 50);
            TextBox t = new TextBox();
            t.Location = new Point(12, 66);
            t.Width = 376;
            t.UseSystemPasswordChar = secret;
            f.Controls.Add(l);
            f.Controls.Add(t);

            TextBox t2 = null;
            int by = 100;
            if (confirm)
            {
                Label l2 = new Label();
                l2.Text = "Ulangi:";
                l2.Location = new Point(12, 96);
                l2.AutoSize = true;
                t2 = new TextBox();
                t2.Location = new Point(12, 114);
                t2.Width = 376;
                t2.UseSystemPasswordChar = secret;
                f.Controls.Add(l2);
                f.Controls.Add(t2);
                by = 148;
            }

            Button ok = new Button();
            ok.Text = "OK";
            ok.DialogResult = DialogResult.OK;
            ok.Location = new Point(222, by);
            Button cancel = new Button();
            cancel.Text = "Batal";
            cancel.DialogResult = DialogResult.Cancel;
            cancel.Location = new Point(312, by);
            f.Controls.Add(ok);
            f.Controls.Add(cancel);
            f.AcceptButton = ok;
            f.CancelButton = cancel;

            while (true)
            {
                if (f.ShowDialog() != DialogResult.OK)
                {
                    f.Dispose();
                    return null;
                }
                if (confirm && t.Text != t2.Text)
                {
                    MessageBox.Show("Isian tidak sama, ulangi.", "HRIS Device Tool");
                    continue;
                }
                string r = t.Text;
                f.Dispose();
                return r;
            }
        }
    }

    public class MesinDialog : Form
    {
        Store st;
        MesinItem editing;
        TextBox txtNama, txtIp, txtPort, txtKey, txtHris;
        CheckBox chkIngat;
        public MesinItem Result;
        public string KeyResult = "";

        TextBox Field(string label, int y, int width, bool secret)
        {
            Label l = new Label();
            l.Text = label;
            l.Location = new Point(12, y);
            l.AutoSize = true;
            TextBox t = new TextBox();
            t.Location = new Point(12, y + 16);
            t.Width = width;
            t.UseSystemPasswordChar = secret;
            Controls.Add(l);
            Controls.Add(t);
            return t;
        }

        public MesinDialog(Store store, MesinItem edit, string existingKey)
        {
            st = store;
            editing = edit;
            Text = (edit == null) ? "Tambah mesin" : "Ubah mesin";
            FormBorderStyle = FormBorderStyle.FixedDialog;
            StartPosition = FormStartPosition.CenterParent;
            MinimizeBox = false;
            MaximizeBox = false;
            ClientSize = new Size(400, 296);

            txtNama = Field("Nama mesin (bebas, contoh: Produksi)", 10, 376, false);
            txtIp = Field("Alamat IP (contoh: 192.168.1.10)", 54, 376, false);
            txtPort = Field("Port (biasanya 4370)", 98, 100, false);
            txtKey = Field("Comm Key (kosongkan bila mesin tidak memakai)", 142, 376, true);
            txtHris = Field("Nama di HRIS (persis seperti Device Name di HRIS; kosong = tidak dikirim)", 186, 376, false);

            chkIngat = new CheckBox();
            chkIngat.Text = "Ingat Comm Key (terenkripsi Windows, hanya terbaca di PC ini)";
            chkIngat.Location = new Point(12, 232);
            chkIngat.AutoSize = true;
            Controls.Add(chkIngat);

            Button bTes = new Button();
            bTes.Text = "Tes koneksi";
            bTes.Location = new Point(12, 260);
            bTes.Size = new Size(110, 28);
            bTes.Click += delegate { OnTes(); };
            Button bOk = new Button();
            bOk.Text = "Simpan";
            bOk.Location = new Point(222, 260);
            bOk.Size = new Size(80, 28);
            bOk.Click += delegate { OnSimpan(); };
            Button bCancel = new Button();
            bCancel.Text = "Batal";
            bCancel.Location = new Point(312, 260);
            bCancel.Size = new Size(80, 28);
            bCancel.DialogResult = DialogResult.Cancel;
            Controls.Add(bTes);
            Controls.Add(bOk);
            Controls.Add(bCancel);
            CancelButton = bCancel;

            txtPort.Text = "4370";
            if (edit != null)
            {
                txtNama.Text = edit.Nama;
                txtIp.Text = edit.Ip;
                txtPort.Text = edit.Port.ToString();
                txtKey.Text = existingKey;
                chkIngat.Checked = edit.IngatKey;
                txtHris.Text = edit.NamaDiHris;
            }
        }

        bool ReadFields(out string nama, out string ip, out int port)
        {
            nama = txtNama.Text.Trim();
            ip = txtIp.Text.Trim();
            port = 0;
            if (nama.Length == 0) { MessageBox.Show("Nama mesin wajib diisi."); return false; }
            if (ip.Length == 0) { MessageBox.Show("Alamat IP wajib diisi."); return false; }
            if (!int.TryParse(txtPort.Text.Trim(), out port) || port < 1 || port > 65535)
            {
                MessageBox.Show("Port harus angka 1-65535.");
                return false;
            }
            return true;
        }

        void OnTes()
        {
            string nama, ip;
            int port;
            if (!ReadFields(out nama, out ip, out port)) return;
            MesinItem tmp = new MesinItem();
            tmp.Nama = nama;
            tmp.Ip = ip;
            tmp.Port = port;
            Cursor = Cursors.WaitCursor;
            object zk = null;
            try
            {
                zk = Dev.Connect(tmp, txtKey.Text);
                Cursor = Cursors.Default;
                MessageBox.Show("Koneksi OK.\r\n" + Dev.ShortInfo(zk), "Tes koneksi");
            }
            catch (Exception e)
            {
                Cursor = Cursors.Default;
                MessageBox.Show(e.Message, "Tes koneksi GAGAL", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
            finally
            {
                Dev.Disconnect(zk);
                Cursor = Cursors.Default;
            }
        }

        void OnSimpan()
        {
            string nama, ip;
            int port;
            if (!ReadFields(out nama, out ip, out port)) return;
            foreach (MesinItem m in st.Data.Mesin)
            {
                if (!object.ReferenceEquals(m, editing) &&
                    string.Equals(m.Nama, nama, StringComparison.OrdinalIgnoreCase))
                {
                    MessageBox.Show("Nama mesin sudah dipakai. Pilih nama lain.");
                    return;
                }
            }
            MesinItem r = new MesinItem();
            r.Nama = nama;
            r.Ip = ip;
            r.Port = port;
            r.IngatKey = chkIngat.Checked;
            r.NamaDiHris = txtHris.Text.Trim();
            if (editing != null)
            {
                r.NamaLama.AddRange(editing.NamaLama);
                if (!string.Equals(editing.Nama, nama, StringComparison.OrdinalIgnoreCase) && !r.NamaLama.Contains(editing.Nama))
                    r.NamaLama.Add(editing.Nama);
                r.NamaLama.RemoveAll(delegate (string s) { return string.Equals(s, nama, StringComparison.OrdinalIgnoreCase); });
            }
            r.TanpaKey = (txtKey.Text.Trim().Length == 0 || txtKey.Text.Trim() == "0");
            Result = r;
            KeyResult = txtKey.Text;
            DialogResult = DialogResult.OK;
        }
    }
}
