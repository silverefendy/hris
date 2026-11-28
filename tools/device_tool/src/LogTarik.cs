using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Windows.Forms;

namespace HrisDeviceTool
{
    public class LogRow
    {
        public string Id = "";
        public DateTime Waktu;
        public int Verify = 0;
        public int InOut = 0;
        public int WorkCode = 0;
        public int Seq = 0;
        public string Nama = "";
    }

    public static class BacaLog
    {
        // Jumlah log menurut mesin (status 6). -1 bila gagal dibaca.
        public static int Hitung(object zkObj)
        {
            dynamic zk = zkObj;
            int v = 0;
            try
            {
                bool ok = zk.GetDeviceStatus(1, 6, ref v);
                return ok ? v : -1;
            }
            catch
            {
                return -1;
            }
        }

        // Hanya membaca daftar user (ID -> nama) dari mesin yang sama.
        public static Dictionary<string, string> Nama(object zkObj)
        {
            dynamic zk = zkObj;
            Dictionary<string, string> r = new Dictionary<string, string>();
            try
            {
                bool okAll = zk.ReadAllUserID(1);
                if (!okAll) return r;
                string id = "", name = "", pwd = "";
                int priv = 0;
                bool en = false;
                int n = 0;
                while (n < 100000)
                {
                    bool ok = zk.SSR_GetAllUserInfo(1, ref id, ref name, ref pwd, ref priv, ref en);
                    if (!ok) break;
                    n++;
                    string k = id.Trim('\0').Trim();
                    if (k.Length > 0) r[k] = name.Trim('\0').Trim();
                }
            }
            catch { }
            return r;
        }

        // Hanya membaca. Mengembalikan null bila dibatalkan.
        public static List<LogRow> Baca(object zkObj, Func<bool> batal, Action<string> progres, out int tidakValid)
        {
            dynamic zk = zkObj;
            tidakValid = 0;
            List<LogRow> hasil = new List<LogRow>();
            bool ok = false;
            try { ok = zk.ReadAllGLogData(1); }
            catch { ok = zk.ReadGeneralLogData(1); }
            if (!ok) return hasil;

            string id = "";
            int vm = 0, io = 0, y = 0, mo = 0, d = 0, h = 0, mi = 0, s = 0, wc = 0;
            int n = 0;
            while (n < 2000000)
            {
                bool got = zk.SSR_GetGeneralLogData(1, ref id, ref vm, ref io, ref y, ref mo, ref d, ref h, ref mi, ref s, ref wc);
                if (!got) break;
                n++;
                if (n % 500 == 0)
                {
                    if (batal()) return null;
                    progres(n + " log terbaca");
                }
                LogRow r = new LogRow();
                r.Id = id.Trim('\0').Trim();
                r.Verify = vm;
                r.Seq = n;
                r.InOut = io;
                r.WorkCode = wc;
                try { r.Waktu = new DateTime(y, mo, d, h, mi, s); }
                catch { tidakValid++; continue; }
                if (r.Id.Length == 0) { tidakValid++; continue; }
                hasil.Add(r);
            }
            return hasil;
        }
    }

    public class LogForm : Form
    {
        Store st;
        Func<MesinItem, object> opener;
        MesinPicker cmbMesin;
        DateTimePicker dtSejak;
        TextBox txtCari;
        Button btnTarik, btnBatal, btnEkspor;
        Label lblStatus;
        CheckBox chkNama;
        ListView lv;
        List<LogRow> semua = new List<LogRow>();
        string namaMesin = "";
        int jumlahMesin = -1;
        bool batal = false;
        bool jalan = false;
        const int MaksTampil = 20000;

        public LogForm(Store store, Func<MesinItem, object> open)
        {
            st = store;
            opener = open;
            Text = "Tarik log absensi (hanya membaca, tidak menghapus apa pun di mesin)";
            ClientSize = new Size(960, 600);
            StartPosition = FormStartPosition.CenterParent;

            Controls.Add(Lbl("Mesin", 10, 14));
            cmbMesin = new MesinPicker();
            
            cmbMesin.Location = new Point(55, 10);
            cmbMesin.Width = 200;
            
            foreach (MesinItem m in st.Data.Mesin) cmbMesin.Items.Add(m);
            if (cmbMesin.Items.Count > 0) cmbMesin.SelectedIndex = 0;
            Controls.Add(cmbMesin);

            btnTarik = Tombol("Tarik dari mesin", 270, 8, 130);
            btnTarik.Click += delegate { OnTarik(); };
            btnBatal = Tombol("Batal", 410, 8, 70);
            btnBatal.Enabled = false;
            btnBatal.Click += delegate { batal = true; };
            btnEkspor = Tombol("Ekspor CSV + manifest", 490, 8, 170);
            btnEkspor.Click += delegate { OnEkspor(); };
            chkNama = new CheckBox();
            chkNama.Text = "Sertakan nama di CSV";
            chkNama.Location = new Point(675, 13);
            chkNama.AutoSize = true;
            Controls.Add(chkNama);

            Controls.Add(Lbl("Sejak tanggal", 10, 48));
            dtSejak = new DateTimePicker();
            dtSejak.Format = DateTimePickerFormat.Custom;
            dtSejak.CustomFormat = "dd-MM-yyyy";
            dtSejak.ShowCheckBox = true;
            dtSejak.Checked = true;
            dtSejak.Value = DateTime.Today.AddDays(-7);
            dtSejak.Location = new Point(95, 44);
            dtSejak.Width = 130;
            dtSejak.ValueChanged += delegate { Tampil(); };
            Controls.Add(dtSejak);

            Controls.Add(Lbl("Cari ID atau nama", 245, 48));
            txtCari = new TextBox();
            txtCari.Location = new Point(355, 44);
            txtCari.Width = 150;
            txtCari.TextChanged += delegate { Tampil(); };
            Controls.Add(txtCari);

            lblStatus = Lbl("Pilih mesin lalu klik Tarik dari mesin. Hanya membaca.", 10, 76);
            Controls.Add(lblStatus);

            lv = new ListView();
            lv.View = View.Details;
            lv.FullRowSelect = true;
            lv.GridLines = true;
            lv.Location = new Point(10, 100);
            lv.Size = new Size(940, 490);
            lv.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;
            lv.Columns.Add("No", 70);
            lv.Columns.Add("ID", 110);
            lv.Columns.Add("Nama", 200);
            lv.Columns.Add("Waktu", 170);
            lv.Columns.Add("Verifikasi", 90);
            lv.Columns.Add("Status", 80);
            lv.Columns.Add("Workcode", 90);
            Controls.Add(lv);
        }

        Label Lbl(string t, int x, int y)
        {
            Label l = new Label();
            l.Text = t;
            l.Location = new Point(x, y);
            l.AutoSize = true;
            return l;
        }

        Button Tombol(string t, int x, int y, int w)
        {
            Button b = new Button();
            b.Text = t;
            b.Location = new Point(x, y);
            b.Size = new Size(w, 28);
            Controls.Add(b);
            return b;
        }

        void Status(string s)
        {
            lblStatus.Text = s;
            Application.DoEvents();
        }

        void OnTarik()
        {
            if (jalan) return;
            MesinItem m = cmbMesin.SelectedItem as MesinItem;
            if (m == null) { MessageBox.Show("Pilih mesin dulu."); return; }
            jalan = true;
            batal = false;
            btnTarik.Enabled = false;
            btnBatal.Enabled = true;
            AuditLog.Tulis("Tarik log", "mulai, mesin " + m.Nama);
            object zk = opener(m);
            try
            {
                if (zk == null) { Status("Tidak bisa terhubung ke mesin."); return; }
                jumlahMesin = BacaLog.Hitung(zk);
                int tidakValid;
                List<LogRow> hasil = BacaLog.Baca(zk, delegate { return batal; },
                    delegate (string s) { Status("Mesin " + m.Nama + ": " + s); }, out tidakValid);
                if (hasil == null) { AuditLog.Tulis("Tarik log", "dibatalkan, mesin " + m.Nama); Status("Dibatalkan."); return; }
                hasil.Sort(delegate (LogRow a, LogRow b)
                {
                    int c = a.Waktu.CompareTo(b.Waktu);
                    return c != 0 ? c : string.Compare(a.Id, b.Id, StringComparison.Ordinal);
                });
                Status("Membaca daftar nama user...");
                Dictionary<string, string> nm = BacaLog.Nama(zk);
                foreach (LogRow x in hasil)
                {
                    string v;
                    if (nm.TryGetValue(x.Id, out v)) x.Nama = v;
                }
                semua = hasil;
                namaMesin = m.Nama;
                SimpanOtomatis(m.Nama, hasil);
                string infoDb = SimpanDb(m.Nama, hasil);
                string cek = (jumlahMesin >= 0 && jumlahMesin != hasil.Count + tidakValid)
                    ? " | PERHATIAN: jumlah menurut mesin " + jumlahMesin + ", terbaca " + (hasil.Count + tidakValid)
                    : (jumlahMesin >= 0 ? " | jumlah cocok dengan mesin (" + jumlahMesin + ")" : "");
                AuditLog.Tulis("Tarik log", "selesai, mesin " + m.Nama + ", terbaca " + hasil.Count + ", tidak valid " + tidakValid + ", jumlah di mesin " + jumlahMesin);
                Status("Selesai " + DateTime.Now.ToString("HH:mm:ss") + ". Terbaca " + hasil.Count + " log valid, " + tidakValid + " tidak valid" + cek + infoDb + ". Tidak ada yang diubah di mesin.");
                Tampil();
            }
            catch (Exception e)
            {
                AuditLog.Tulis("Tarik log", "GAGAL: " + e.Message);
                MessageBox.Show(e.Message, "Gagal menarik log", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
            finally
            {
                Dev.Disconnect(zk);
                Cursor = Cursors.Default;
                jalan = false;
                btnTarik.Enabled = true;
                btnBatal.Enabled = false;
            }
        }

        List<LogRow> Saring()
        {
            List<LogRow> r = new List<LogRow>();
            string q = txtCari.Text.Trim();
            bool pakaiTgl = dtSejak.Checked;
            DateTime sejak = dtSejak.Value.Date;
            foreach (LogRow x in semua)
            {
                if (pakaiTgl && x.Waktu < sejak) continue;
                if (q.Length > 0 && x.Id.IndexOf(q, StringComparison.OrdinalIgnoreCase) < 0 && x.Nama.IndexOf(q, StringComparison.OrdinalIgnoreCase) < 0) continue;
                r.Add(x);
            }
            return r;
        }

        void Tampil()
        {
            List<LogRow> r = Saring();
            lv.BeginUpdate();
            lv.Items.Clear();
            int n = 0;
            foreach (LogRow x in r)
            {
                if (n >= MaksTampil) break;
                n++;
                ListViewItem it = new ListViewItem(x.Seq.ToString());
                it.SubItems.Add(x.Id);
                it.SubItems.Add(x.Nama);
                it.SubItems.Add(x.Waktu.ToString("yyyy-MM-dd HH:mm:ss"));
                it.SubItems.Add(x.Verify.ToString());
                it.SubItems.Add(x.InOut.ToString());
                it.SubItems.Add(x.WorkCode.ToString());
                lv.Items.Add(it);
            }
            lv.EndUpdate();
            if (semua.Count > 0)
                Text = "Tarik log absensi - " + namaMesin + ": " + r.Count + " dari " + semua.Count + " log" + (r.Count > MaksTampil ? " (daftar menampilkan " + MaksTampil + " pertama)" : "");
        }

        static string Aman(string s)
        {
            foreach (char c in Path.GetInvalidFileNameChars()) s = s.Replace(c.ToString(), "_");
            return s.Replace(" ", "_");
        }

        static string HashFile(string path)
        {
            using (SHA256 sha = SHA256.Create())
            {
                byte[] b = sha.ComputeHash(File.ReadAllBytes(path));
                StringBuilder sb = new StringBuilder();
                foreach (byte x in b) sb.Append(x.ToString("x2"));
                return sb.ToString();
            }
        }

        void SimpanOtomatis(string mesin, List<LogRow> rows)
        {
            try
            {
                if (rows.Count == 0) return;
                string dir = Path.Combine(st.DataDir, "tarikan");
                Directory.CreateDirectory(dir);
                string baseName = "tarikan_" + Aman(mesin) + "_" + DateTime.Now.ToString("yyyyMMdd_HHmmss");
                string csv = Path.Combine(dir, baseName + ".csv");
                StringBuilder sb = new StringBuilder();
                sb.Append("device_user_id;punch_time;verify_mode;punch_status_raw;workcode\r\n");
                foreach (LogRow x in rows)
                {
                    sb.Append(x.Id).Append(';')
                      .Append(x.Waktu.ToString("yyyy-MM-dd HH:mm:ss")).Append(';')
                      .Append(x.Verify).Append(';')
                      .Append(x.InOut).Append(';')
                      .Append(x.WorkCode).Append("\r\n");
                }
                File.WriteAllText(csv, sb.ToString(), new UTF8Encoding(false));
                string hash = HashFile(csv);
                StringBuilder mf = new StringBuilder();
                mf.Append("format=hdt-log-1\r\n");
                mf.Append("otomatis=ya\r\n");
                mf.Append("mesin=" + mesin + "\r\n");
                mf.Append("diekspor=" + DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") + "\r\n");
                mf.Append("baris=" + rows.Count + "\r\n");
                mf.Append("rentang_awal=" + rows[0].Waktu.ToString("yyyy-MM-dd HH:mm:ss") + "\r\n");
                mf.Append("rentang_akhir=" + rows[rows.Count - 1].Waktu.ToString("yyyy-MM-dd HH:mm:ss") + "\r\n");
                mf.Append("jumlah_di_mesin=" + jumlahMesin + "\r\n");
                mf.Append("sha256=" + hash + "\r\n");
                File.WriteAllText(Path.Combine(dir, baseName + ".hdtman"), mf.ToString(), new UTF8Encoding(false));
                AuditLog.Tulis("Salinan otomatis", "mesin " + mesin + ", baris " + rows.Count + ", berkas " + baseName + ".csv, sha256 " + hash);
            }
            catch (Exception e)
            {
                AuditLog.Tulis("Salinan otomatis", "GAGAL: " + e.Message);
            }
        }

        // Salinan ke database lokal. CSV tetap dibuat; kegagalan di sini tidak menggagalkan tarikan.
        string SimpanDb(string mesin, List<LogRow> rows)
        {
            try
            {
                List<global::HrisDeviceTool.Data.BarisLog> daftar = new List<global::HrisDeviceTool.Data.BarisLog>();
                foreach (LogRow x in rows)
                {
                    global::HrisDeviceTool.Data.BarisLog b = new global::HrisDeviceTool.Data.BarisLog();
                    b.Id = x.Id;
                    b.Waktu = x.Waktu;
                    b.Verifikasi = x.Verify;
                    b.Status = x.InOut;
                    b.WorkCode = x.WorkCode;
                    daftar.Add(b);
                }
                using (global::System.Data.SQLite.SQLiteConnection c = global::HrisDeviceTool.Data.HdtDatabase.Buka(global::HrisDeviceTool.Data.HdtDatabase.BerkasDefault()))
                {
                    global::HrisDeviceTool.Data.HasilSimpan h = global::HrisDeviceTool.Data.LogDb.Simpan(c, mesin, daftar, "tarik", jumlahMesin, "");
                    AuditLog.Tulis("Simpan log ke database", "mesin " + mesin + ", terbaca " + h.Terbaca + ", baru " + h.Baru + ", sudah ada " + h.Dilewati);
                    return " | database: baru " + h.Baru + ", sudah ada " + h.Dilewati;
                }
            }
            catch (Exception e)
            {
                AuditLog.Tulis("Simpan log ke database", "GAGAL: " + e.Message);
                return " | database GAGAL: " + e.Message;
            }
        }

        void OnEkspor()
        {
            List<LogRow> r = Saring();
            if (r.Count == 0) { MessageBox.Show("Tidak ada baris untuk diekspor. Tarik log dulu atau longgarkan filter."); return; }
            string stamp = DateTime.Now.ToString("yyyyMMdd_HHmmss");
            string baseName = "log_" + Aman(namaMesin) + "_" + stamp;
            string csv = Path.Combine(st.DataDir, baseName + ".csv");
            StringBuilder sb = new StringBuilder();
            sb.Append("device_user_id;punch_time;verify_mode;punch_status_raw;workcode" + (chkNama.Checked ? ";nama" : "") + "\r\n");
            foreach (LogRow x in r)
            {
                sb.Append(x.Id).Append(';')
                  .Append(x.Waktu.ToString("yyyy-MM-dd HH:mm:ss")).Append(';')
                  .Append(x.Verify).Append(';')
                  .Append(x.InOut).Append(';')
                  .Append(x.WorkCode).Append(chkNama.Checked ? ";" + x.Nama.Replace(";", ",") : "").Append("\r\n");
            }
            File.WriteAllText(csv, sb.ToString(), new UTF8Encoding(false));
            string hash = HashFile(csv);
            StringBuilder mf = new StringBuilder();
            mf.Append("format=hdt-log-1\r\n");
            mf.Append("mesin=" + namaMesin + "\r\n");
            mf.Append("diekspor=" + DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") + "\r\n");
            mf.Append("baris=" + r.Count + "\r\n");
            mf.Append("kolom_nama=" + (chkNama.Checked ? "ya" : "tidak") + "\r\n");
            mf.Append("rentang_awal=" + r[0].Waktu.ToString("yyyy-MM-dd HH:mm:ss") + "\r\n");
            mf.Append("rentang_akhir=" + r[r.Count - 1].Waktu.ToString("yyyy-MM-dd HH:mm:ss") + "\r\n");
            mf.Append("jumlah_di_mesin=" + jumlahMesin + "\r\n");
            mf.Append("sha256=" + hash + "\r\n");
            string man = Path.Combine(st.DataDir, baseName + ".hdtman");
            File.WriteAllText(man, mf.ToString(), new UTF8Encoding(false));
            AuditLog.Tulis("Ekspor log", "mesin " + namaMesin + ", baris " + r.Count + ", berkas " + Path.GetFileName(csv) + ", sha256 " + hash);
            MessageBox.Show("Diekspor:\r\n" + csv + "\r\n" + man + "\r\n\r\nSHA-256: " + hash, "Ekspor");
        }
    }
}
