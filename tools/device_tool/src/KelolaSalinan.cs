using System;
using System.Collections.Generic;
using System.Drawing;
using System.Globalization;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Windows.Forms;

namespace HrisDeviceTool
{
    public class SalinanItem
    {
        public string Base = "", Dir = "", Mesin = "", Rentang = "", Hash = "";
        public string Terkirim = "";
        public int Baris;
        public long Ukuran;
        public DateTime Waktu;
        public DateTime HapusPada = DateTime.MinValue;
        public string Csv { get { return Path.Combine(Dir, Base + ".csv"); } }
        public string Man { get { return Path.Combine(Dir, Base + ".hdtman"); } }
    }

    // Logika salinan otomatis penarikan log + tempat sampah 14 hari.
    // Hanya menyentuh berkas di komputer ini, tidak pernah menyentuh mesin.
    public static class Salinan
    {
        public const int HariSimpan = 14;
        const string FormatStempel = "yyyyMMdd_HHmmss";

        public static string Aktif(Store st) { return Path.Combine(st.DataDir, "tarikan"); }
        public static string Sampah(Store st) { return Path.Combine(Aktif(st), "_sampah"); }

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

        static SalinanItem Baca(string man)
        {
            SalinanItem it = new SalinanItem();
            it.Dir = Path.GetDirectoryName(man);
            it.Base = Path.GetFileNameWithoutExtension(man);
            string sha = "", awal = "", akhir = "", diekspor = "";
            try
            {
                foreach (string line in File.ReadAllLines(man))
                {
                    int i = line.IndexOf('=');
                    if (i < 0) continue;
                    string k = line.Substring(0, i);
                    string v = line.Substring(i + 1).Trim();
                    if (k == "mesin") it.Mesin = v;
                    else if (k == "baris") int.TryParse(v, out it.Baris);
                    else if (k == "sha256") sha = v;
                    else if (k == "rentang_awal") awal = v;
                    else if (k == "rentang_akhir") akhir = v;
                    else if (k == "diekspor") diekspor = v;
                    else if (k == "terkirim") it.Terkirim = v.Replace("|", "  ");
                }
            }
            catch { }
            DateTime t;
            if (DateTime.TryParse(diekspor, out t)) it.Waktu = t;
            else it.Waktu = File.GetLastWriteTime(man);
            if (awal.Length > 0 || akhir.Length > 0)
                it.Rentang = (awal.Length >= 10 ? awal.Substring(0, 10) : awal) + " s/d " + (akhir.Length >= 10 ? akhir.Substring(0, 10) : akhir);
            long ukuran = new FileInfo(man).Length;
            if (!File.Exists(it.Csv)) it.Hash = "CSV hilang";
            else
            {
                ukuran += new FileInfo(it.Csv).Length;
                if (sha.Length == 0) it.Hash = "tanpa hash";
                else
                {
                    try { it.Hash = string.Equals(HashFile(it.Csv), sha, StringComparison.OrdinalIgnoreCase) ? "cocok" : "BERUBAH"; }
                    catch { it.Hash = "gagal dibaca"; }
                }
            }
            it.Ukuran = ukuran;
            return it;
        }

        static void Urut(List<SalinanItem> r)
        {
            r.Sort(delegate (SalinanItem a, SalinanItem b) { return b.Waktu.CompareTo(a.Waktu); });
        }

        public static List<SalinanItem> DaftarAktif(Store st)
        {
            List<SalinanItem> r = new List<SalinanItem>();
            string d = Aktif(st);
            if (!Directory.Exists(d)) return r;
            foreach (string man in Directory.GetFiles(d, "*.hdtman", SearchOption.TopDirectoryOnly))
                r.Add(Baca(man));
            Urut(r);
            return r;
        }

        public static List<SalinanItem> DaftarSampah(Store st)
        {
            List<SalinanItem> r = new List<SalinanItem>();
            string s = Sampah(st);
            if (!Directory.Exists(s)) return r;
            foreach (string sub in Directory.GetDirectories(s))
            {
                DateTime hp;
                if (!DateTime.TryParseExact(Path.GetFileName(sub), FormatStempel, CultureInfo.InvariantCulture, DateTimeStyles.None, out hp)) continue;
                foreach (string man in Directory.GetFiles(sub, "*.hdtman"))
                {
                    SalinanItem it = Baca(man);
                    it.HapusPada = hp;
                    r.Add(it);
                }
            }
            Urut(r);
            return r;
        }

        public static string Ukuran(List<SalinanItem> l)
        {
            long t = 0;
            foreach (SalinanItem x in l) t += x.Ukuran;
            return Ukuran(t);
        }

        public static string Ukuran(long b)
        {
            if (b < 1024) return b + " B";
            if (b < 1024 * 1024) return (b / 1024.0).ToString("0.0") + " KB";
            return (b / 1024.0 / 1024.0).ToString("0.0") + " MB";
        }

        static void PindahPasangan(SalinanItem it, string tujuan)
        {
            Directory.CreateDirectory(tujuan);
            if (File.Exists(it.Csv)) File.Move(it.Csv, Path.Combine(tujuan, it.Base + ".csv"));
            if (File.Exists(it.Man)) File.Move(it.Man, Path.Combine(tujuan, it.Base + ".hdtman"));
        }

        public static int KeSampah(Store st, List<SalinanItem> l)
        {
            string tujuan = Path.Combine(Sampah(st), DateTime.Now.ToString(FormatStempel));
            int n = 0;
            foreach (SalinanItem it in l)
            {
                try
                {
                    PindahPasangan(it, tujuan);
                    n++;
                    AuditLog.Tulis("Salinan ke sampah", "mesin " + it.Mesin + ", berkas " + it.Base);
                }
                catch (Exception e) { AuditLog.Tulis("Salinan ke sampah", "GAGAL " + it.Base + ": " + e.Message); }
            }
            return n;
        }

        public static int Pulihkan(Store st, List<SalinanItem> l)
        {
            string tujuan = Aktif(st);
            int n = 0;
            foreach (SalinanItem it in l)
            {
                try
                {
                    if (File.Exists(Path.Combine(tujuan, it.Base + ".hdtman")) || File.Exists(Path.Combine(tujuan, it.Base + ".csv")))
                    {
                        AuditLog.Tulis("Salinan pulihkan", "dilewati, nama sudah ada: " + it.Base);
                        continue;
                    }
                    PindahPasangan(it, tujuan);
                    n++;
                    AuditLog.Tulis("Salinan pulihkan", "mesin " + it.Mesin + ", berkas " + it.Base);
                }
                catch (Exception e) { AuditLog.Tulis("Salinan pulihkan", "GAGAL " + it.Base + ": " + e.Message); }
            }
            HapusSubfolderKosong(st);
            return n;
        }

        public static int HapusPermanen(Store st, List<SalinanItem> l)
        {
            int n = 0;
            foreach (SalinanItem it in l)
            {
                try
                {
                    if (File.Exists(it.Csv)) File.Delete(it.Csv);
                    if (File.Exists(it.Man)) File.Delete(it.Man);
                    n++;
                    AuditLog.Tulis("Salinan hapus permanen", "mesin " + it.Mesin + ", berkas " + it.Base);
                }
                catch (Exception e) { AuditLog.Tulis("Salinan hapus permanen", "GAGAL " + it.Base + ": " + e.Message); }
            }
            HapusSubfolderKosong(st);
            return n;
        }

        public static void TandaiTerkirim(SalinanItem it, string server, KirimHasil h)
        {
            string host = server.Replace("http://", "").Replace("https://", "").TrimEnd('/');
            string t = File.ReadAllText(it.Man);
            string nl = t.Contains("\r\n") ? "\r\n" : "\n";
            if (t.Length > 0 && !t.EndsWith("\n")) t += nl;
            t += "terkirim=" + DateTime.Now.ToString("yyyy-MM-dd HH:mm") + "|" + host +
                "|c=" + h.Created + "|d=" + h.Duplicate + "|e=" + h.Error + nl;
            File.WriteAllText(it.Man, t, new UTF8Encoding(false));
            AuditLog.Tulis("Salinan tandai terkirim", "mesin " + it.Mesin + ", berkas " + it.Base);
        }

        static void HapusSubfolderKosong(Store st)
        {
            try
            {
                string s = Sampah(st);
                if (!Directory.Exists(s)) return;
                foreach (string sub in Directory.GetDirectories(s))
                {
                    if (Directory.GetFileSystemEntries(sub).Length == 0) Directory.Delete(sub);
                }
            }
            catch { }
        }

        // Dipanggil saat aplikasi dibuka dan saat jendela dibuka.
        // Menghapus permanen isi sampah yang sudah lebih dari HariSimpan hari.
        public static int BersihkanOtomatis(Store st)
        {
            int n = 0;
            try
            {
                string s = Sampah(st);
                if (!Directory.Exists(s)) return 0;
                foreach (string sub in Directory.GetDirectories(s))
                {
                    DateTime hp;
                    if (!DateTime.TryParseExact(Path.GetFileName(sub), FormatStempel, CultureInfo.InvariantCulture, DateTimeStyles.None, out hp)) continue;
                    if (hp.AddDays(HariSimpan) > DateTime.Now) continue;
                    int isi = Directory.GetFiles(sub).Length;
                    Directory.Delete(sub, true);
                    n += isi;
                    AuditLog.Tulis("Salinan hapus permanen", "otomatis (lewat " + HariSimpan + " hari), folder " + Path.GetFileName(sub) + ", berkas " + isi);
                }
            }
            catch (Exception e) { AuditLog.Tulis("Salinan hapus permanen", "otomatis GAGAL: " + e.Message); }
            return n;
        }
    }

    public class KelolaSalinanForm : Form
    {
        Store st;
        RadioButton rbAktif, rbSampah;
        ListView lv;
        DateTimePicker dtBatas;
        Button btnSemua, btnLama, btnHapus, btnPulih, btnPermanen, btnKosong, btnKirim, btnPengHris;
        Label lblInfo;

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
            b.Anchor = AnchorStyles.Bottom | AnchorStyles.Left;
            return b;
        }

        public KelolaSalinanForm(Store store)
        {
            st = store;
            Text = "Kelola salinan penarikan log (hanya berkas di komputer ini)";
            ClientSize = new Size(1000, 580);
            StartPosition = FormStartPosition.CenterParent;

            rbAktif = new RadioButton();
            rbAktif.Text = "Salinan aktif";
            rbAktif.Location = new Point(10, 10);
            rbAktif.AutoSize = true;
            rbAktif.Checked = true;
            rbSampah = new RadioButton();
            rbSampah.Text = "Tempat sampah (terhapus permanen otomatis setelah " + Salinan.HariSimpan + " hari)";
            rbSampah.Location = new Point(130, 10);
            rbSampah.AutoSize = true;
            rbAktif.CheckedChanged += delegate { Muat(); };
            Controls.Add(rbAktif);
            Controls.Add(rbSampah);

            Controls.Add(Lbl("Lebih lama dari tanggal", 10, 46));
            dtBatas = new DateTimePicker();
            dtBatas.Format = DateTimePickerFormat.Custom;
            dtBatas.CustomFormat = "dd-MM-yyyy";
            dtBatas.Value = DateTime.Today.AddDays(-30);
            dtBatas.Location = new Point(150, 42);
            dtBatas.Width = 110;
            Controls.Add(dtBatas);

            Button btnCentangLama = new Button();
            btnCentangLama.Text = "Centang yang lebih lama";
            btnCentangLama.Location = new Point(270, 40);
            btnCentangLama.Size = new Size(170, 28);
            btnCentangLama.Click += delegate { CentangLama(); };
            btnLama = btnCentangLama;
            Controls.Add(btnLama);

            btnSemua = new Button();
            btnSemua.Text = "Centang semua";
            btnSemua.Location = new Point(450, 40);
            btnSemua.Size = new Size(120, 28);
            btnSemua.Click += delegate { foreach (ListViewItem li in lv.Items) li.Checked = true; };
            Controls.Add(btnSemua);

            Button btnNol = new Button();
            btnNol.Text = "Hapus centang";
            btnNol.Location = new Point(580, 40);
            btnNol.Size = new Size(110, 28);
            btnNol.Click += delegate { foreach (ListViewItem li in lv.Items) li.Checked = false; };
            Controls.Add(btnNol);

            lv = new ListView();
            lv.View = View.Details;
            lv.FullRowSelect = true;
            lv.GridLines = true;
            lv.CheckBoxes = true;
            lv.Location = new Point(10, 78);
            lv.Size = new Size(980, 430);
            lv.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;
            lv.Columns.Add("Mesin", 120);
            lv.Columns.Add("Waktu tarik", 140);
            lv.Columns.Add("Baris", 70);
            lv.Columns.Add("Rentang data", 170);
            lv.Columns.Add("Ukuran", 80);
            lv.Columns.Add("Hash", 90);
            lv.Columns.Add("Terkirim ke HRIS", 140);
            lv.Columns.Add("Terhapus permanen pada", 150);
            Controls.Add(lv);

            btnHapus = Tombol("Hapus ke sampah", 10, 518, 140);
            btnHapus.Click += delegate { OnHapus(); };
            btnPulih = Tombol("Pulihkan", 10, 518, 110);
            btnPulih.Click += delegate { OnPulih(); };
            btnPermanen = Tombol("Hapus permanen (dicentang)", 130, 518, 190);
            btnPermanen.Click += delegate { OnPermanen(); };
            btnKosong = Tombol("Kosongkan sampah", 330, 518, 150);
            btnKosong.Click += delegate { OnKosong(); };
            Controls.Add(btnHapus);
            Controls.Add(btnPulih);
            Controls.Add(btnPermanen);
            Controls.Add(btnKosong);
            btnKirim = Tombol("Kirim ke HRIS (dicentang)", 160, 518, 190);
            btnKirim.Click += delegate { OnKirim(); };
            btnPengHris = Tombol("Pengaturan HRIS", 360, 518, 140);
            btnPengHris.Click += delegate { OnPengaturanHris(); };
            Controls.Add(btnKirim);
            Controls.Add(btnPengHris);

            lblInfo = Lbl("", 10, 554);
            lblInfo.Anchor = AnchorStyles.Bottom | AnchorStyles.Left;
            Controls.Add(lblInfo);

            Salinan.BersihkanOtomatis(st);
            Muat();
        }

        void Muat()
        {
            bool sam = rbSampah.Checked;
            btnHapus.Visible = !sam;
            btnPulih.Visible = sam;
            btnPermanen.Visible = sam;
            btnKosong.Visible = sam;
            btnKirim.Visible = !sam;
            btnPengHris.Visible = !sam;
            List<SalinanItem> items = sam ? Salinan.DaftarSampah(st) : Salinan.DaftarAktif(st);
            lv.BeginUpdate();
            lv.Items.Clear();
            long total = 0;
            foreach (SalinanItem it in items)
            {
                ListViewItem li = new ListViewItem(it.Mesin);
                li.SubItems.Add(it.Waktu.ToString("yyyy-MM-dd HH:mm"));
                li.SubItems.Add(it.Baris.ToString());
                li.SubItems.Add(it.Rentang);
                li.SubItems.Add(Salinan.Ukuran(it.Ukuran));
                li.SubItems.Add(it.Hash);
                li.SubItems.Add(it.Terkirim.Length > 0 ? it.Terkirim : "belum");
                li.SubItems.Add(sam ? it.HapusPada.AddDays(Salinan.HariSimpan).ToString("yyyy-MM-dd HH:mm") : "");
                li.Tag = it;
                if (it.Hash == "BERUBAH" || it.Hash == "CSV hilang") li.ForeColor = Color.Firebrick;
                lv.Items.Add(li);
                total += it.Ukuran;
            }
            lv.EndUpdate();
            lblInfo.Text = (sam ? "Di sampah: " : "Salinan aktif: ") + items.Count + " pasang berkas, total " + Salinan.Ukuran(total) + ". Folder: " + (sam ? Salinan.Sampah(st) : Salinan.Aktif(st));
        }

        List<SalinanItem> Dipilih()
        {
            List<SalinanItem> r = new List<SalinanItem>();
            foreach (ListViewItem li in lv.CheckedItems) r.Add((SalinanItem)li.Tag);
            return r;
        }

        void CentangLama()
        {
            DateTime batas = dtBatas.Value.Date;
            foreach (ListViewItem li in lv.Items)
            {
                SalinanItem it = (SalinanItem)li.Tag;
                li.Checked = it.Waktu.Date < batas;
            }
        }

        MesinItem CariMesin(string nama)
        {
            foreach (MesinItem m in st.Data.Mesin)
            {
                if (string.Equals(m.Nama, nama, StringComparison.OrdinalIgnoreCase)) return m;
            }
            return null;
        }

        bool KonfirmasiBelumTerkirim(List<SalinanItem> p)
        {
            int belum = 0;
            foreach (SalinanItem it in p) { if (it.Terkirim.Length == 0) belum++; }
            if (belum == 0) return true;
            string tanya = belum + " dari " + p.Count + " salinan BELUM tercatat terkirim ke HRIS.\r\n\r\n" +
                "Menghapusnya bisa menghilangkan data absensi yang belum ada di HRIS. Tetap lanjut?";
            return MessageBox.Show(tanya, "Salinan belum terkirim", MessageBoxButtons.YesNo,
                MessageBoxIcon.Warning, MessageBoxDefaultButton.Button2) == DialogResult.Yes;
        }

        void OnPengaturanHris()
        {
            if (!Peran.Boleh("OnPengaturanHris")) return;
            using (HrisDialog d = new HrisDialog(st)) { d.ShowDialog(this); }
        }

        void OnKirim()
        {
            if (!Peran.Boleh("OnKirimHris")) return;
            List<SalinanItem> p = Dipilih();
            if (p.Count == 0) { MessageBox.Show("Centang salinan yang mau dikirim ke HRIS."); return; }
            string url = (st.Data.UrlHris ?? "").Trim();
            string tok = HrisToken.Ambil(st);
            if (url.Length == 0 || !HrisToken.Valid(tok))
            {
                MessageBox.Show("Alamat server atau token HRIS belum diatur.\r\nMinta administrator mengisinya lewat tombol Pengaturan HRIS.",
                    "Kirim ke HRIS", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }
            List<string> masalah = new List<string>();
            long totalBaris = 0;
            foreach (SalinanItem it in p)
            {
                MesinItem mm = CariMesin(it.Mesin);
                if (mm == null || (mm.NamaDiHris ?? "").Trim().Length == 0)
                    masalah.Add(it.Mesin + ": kolom Nama di HRIS belum diisi (atau mesin tidak ada di daftar).");
                else if (it.Hash != "cocok")
                    masalah.Add(it.Mesin + " (" + it.Base + "): hash " + it.Hash + ", tidak dikirim.");
                totalBaris += it.Baris;
            }
            if (masalah.Count > 0)
            {
                MessageBox.Show("Tidak bisa dikirim:\r\n\r\n" + string.Join("\r\n", masalah.ToArray()),
                    "Kirim ke HRIS", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }
            string tanya = "Kirim " + p.Count + " salinan (" + totalBaris.ToString("N0") + " baris) ke " + url + " ?\r\n\r\n" +
                "Kirim ulang aman: baris yang sudah ada di HRIS dihitung duplicate, bukan data ganda.";
            if (MessageBox.Show(tanya, "Kirim ke HRIS", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;

            int ke = 0, sukses = 0;
            foreach (SalinanItem it in p)
            {
                ke++;
                MesinItem mm = CariMesin(it.Mesin);
                KirimOpsi o = new KirimOpsi();
                o.UrlDasar = url;
                o.Token = tok;
                o.NamaDiHris = mm.NamaDiHris.Trim();
                try { o.BarisCsv = File.ReadAllLines(it.Csv); }
                catch (Exception ex)
                {
                    AuditLog.Tulis("Salinan kirim HRIS", "GAGAL baca " + it.Base + ": " + ex.Message);
                    MessageBox.Show("Berkas tidak bisa dibaca:\r\n" + ex.Message, "Kirim ke HRIS", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    break;
                }
                KirimHasil h = KirimProgressForm.Tampilkan(this, o, "Kirim ke HRIS: " + o.NamaDiHris + " (" + ke + " dari " + p.Count + ")");
                if (h == null) break;
                AuditLog.Tulis("Salinan kirim HRIS", "mesin " + it.Mesin + ", berkas " + it.Base + ", " + h.Ringkas() +
                    (h.Pesan.Length > 0 ? ", " + h.Pesan : ""));
                if (h.DetailError.Count > 0)
                {
                    try { KirimHris.TulisError(Path.Combine(it.Dir, it.Base + ".hdterr"), h); }
                    catch (Exception) { }
                }
                if (h.Berhenti || h.Dibatalkan) break;
                if (h.Error == 0)
                {
                    try { Salinan.TandaiTerkirim(it, url, h); sukses++; }
                    catch (Exception ex) { AuditLog.Tulis("Salinan tandai terkirim", "GAGAL " + it.Base + ": " + ex.Message); }
                }
                else
                {
                    MessageBox.Show(h.Error + " baris gagal. Rincian ada di berkas " + it.Base + ".hdterr (folder salinan).",
                        "Kirim ke HRIS", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    break;
                }
            }
            Muat();
            lblInfo.Text = sukses + " dari " + p.Count + " salinan terkirim penuh. " + lblInfo.Text;
        }

        void OnHapus()
        {
            List<SalinanItem> p = Dipilih();
            if (p.Count == 0) { MessageBox.Show("Centang salinan yang mau dihapus."); return; }
            string tanya = "Pindahkan " + p.Count + " salinan (" + Salinan.Ukuran(p) + ") ke tempat sampah?\r\n\r\n" +
                "Masih bisa dipulihkan selama " + Salinan.HariSimpan + " hari, setelah itu terhapus permanen otomatis.\r\n" +
                "Hanya berkas di komputer ini; mesin tidak disentuh.";
            if (MessageBox.Show(tanya, "Hapus ke sampah", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
            if (!KonfirmasiBelumTerkirim(p)) return;
            int n = Salinan.KeSampah(st, p);
            Muat();
            lblInfo.Text = n + " salinan dipindah ke sampah. " + lblInfo.Text;
        }

        void OnPulih()
        {
            List<SalinanItem> p = Dipilih();
            if (p.Count == 0) { MessageBox.Show("Centang salinan yang mau dipulihkan."); return; }
            int n = Salinan.Pulihkan(st, p);
            Muat();
            lblInfo.Text = n + " dari " + p.Count + " salinan dipulihkan. " + lblInfo.Text;
        }

        void OnPermanen()
        {
            List<SalinanItem> p = Dipilih();
            if (!Peran.Boleh("HapusPermanenSalinan")) return; if (p.Count == 0) { MessageBox.Show("Centang salinan yang mau dihapus permanen."); return; }
            string tanya = "HAPUS PERMANEN " + p.Count + " salinan (" + Salinan.Ukuran(p) + ")?\r\n\r\nTidak bisa dipulihkan lagi.";
            if (MessageBox.Show(tanya, "Hapus permanen", MessageBoxButtons.YesNo, MessageBoxIcon.Warning, MessageBoxDefaultButton.Button2) != DialogResult.Yes) return;
            if (!KonfirmasiBelumTerkirim(p)) return;
            int n = Salinan.HapusPermanen(st, p);
            Muat();
            lblInfo.Text = n + " salinan dihapus permanen. " + lblInfo.Text;
        }

        void OnKosong()
        {
            if (!Peran.Boleh("HapusPermanenSalinan")) return; List<SalinanItem> semua = Salinan.DaftarSampah(st);
            if (semua.Count == 0) { MessageBox.Show("Tempat sampah sudah kosong."); return; }
            string tanya = "Kosongkan seluruh tempat sampah: " + semua.Count + " salinan (" + Salinan.Ukuran(semua) + ") dihapus PERMANEN?\r\n\r\nTidak bisa dipulihkan lagi.";
            if (MessageBox.Show(tanya, "Kosongkan sampah", MessageBoxButtons.YesNo, MessageBoxIcon.Warning, MessageBoxDefaultButton.Button2) != DialogResult.Yes) return;
            if (!KonfirmasiBelumTerkirim(semua)) return;
            int n = Salinan.HapusPermanen(st, semua);
            Muat();
            lblInfo.Text = n + " salinan dihapus permanen. " + lblInfo.Text;
        }
    }
}
