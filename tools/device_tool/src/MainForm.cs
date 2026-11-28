using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.Drawing.Drawing2D;
using System.IO;
using System.Text;
using System.Windows.Forms;

namespace HrisDeviceTool
{
    // Pengurut kolom ListView: angka diurut sebagai angka, selain itu sebagai teks
    public class ListSorter : IComparer
    {
        public int Col = 0;
        public bool Asc = true;

        public int Compare(object a, object b)
        {
            string x = ((ListViewItem)a).SubItems[Col].Text;
            string y = ((ListViewItem)b).SubItems[Col].Text;
            long nx, ny;
            int r;
            if (long.TryParse(x, out nx) && long.TryParse(y, out ny)) r = nx.CompareTo(ny);
            else r = string.Compare(x, y, StringComparison.OrdinalIgnoreCase);
            return Asc ? r : -r;
        }
    }

    // Gambar dua tangan, jari bisa diklik. Hijau = terdaftar di mesin, kotak biru = terpilih
    public class HandPanel : Panel
    {
        public bool[] Found = new bool[10];
        public int Selected = 5;
        public event EventHandler SelectionChanged;
        static readonly int[] Hts = new int[] { 58, 78, 90, 78, 58 };

        public HandPanel()
        {
            DoubleBuffered = true;
            Size = new Size(360, 225);
        }

        public void Reset()
        {
            for (int i = 0; i < 10; i++) Found[i] = false;
            Invalidate();
        }

        Rectangle FingerRect(int f)
        {
            int hand = f / 5;
            int pos = f % 5;
            int ox = (hand == 0) ? 5 : 189;
            int h = Hts[pos];
            bool thumb = (f == 4 || f == 5);
            int top = 135 - h + (thumb ? 25 : 0);
            int hh = h - (thumb ? 25 : 0);
            return new Rectangle(ox + pos * 34, top, 30, hh);
        }

        protected override void OnPaint(PaintEventArgs e)
        {
            Graphics g = e.Graphics;
            g.SmoothingMode = SmoothingMode.AntiAlias;
            for (int hand = 0; hand < 2; hand++)
            {
                int ox = (hand == 0) ? 5 : 189;
                g.FillRectangle(Brushes.Gainsboro, ox, 135, 166, 60);
                g.DrawString(hand == 0 ? "Tangan kiri" : "Tangan kanan", Font, Brushes.Black, ox + 45, 200);
            }
            for (int f = 0; f < 10; f++)
            {
                Rectangle r = FingerRect(f);
                Brush b = Found[f] ? Brushes.MediumSeaGreen : Brushes.Gainsboro;
                g.FillEllipse(b, r.X, r.Y, r.Width, 30);
                g.FillRectangle(b, r.X, r.Y + 15, r.Width, r.Height - 15);
                g.DrawString(f.ToString(), Font, Brushes.Black, r.X + 10, r.Bottom - 20);
                if (f == Selected)
                {
                    using (Pen p = new Pen(Color.RoyalBlue, 3f))
                    {
                        g.DrawRectangle(p, r.X - 1, r.Y - 1, r.Width + 2, r.Height + 2);
                    }
                }
            }
        }

        protected override void OnMouseDown(MouseEventArgs e)
        {
            base.OnMouseDown(e);
            for (int f = 0; f < 10; f++)
            {
                Rectangle r = FingerRect(f);
                r.Inflate(2, 14);
                if (r.Contains(e.Location))
                {
                    Selected = f;
                    Invalidate();
                    if (SelectionChanged != null) SelectionChanged(this, EventArgs.Empty);
                    return;
                }
            }
        }
    }

    public class MainForm : Form
    {
        const string Versi = "0.9.2 (lihat log)";
        static readonly string[] NamaJari = new string[] {
            "Kelingking kiri", "Jari manis kiri", "Jari tengah kiri", "Telunjuk kiri", "Jempol kiri",
            "Jempol kanan", "Telunjuk kanan", "Jari tengah kanan", "Jari manis kanan", "Kelingking kanan" };
        static readonly string[] ColM = new string[] { "No", "Nama", "IP", "Port", "Key", "Status" };
        static readonly string[] ColU = new string[] { "ID", "Nama", "Privilege", "Status" };
        static readonly string[] ColS = new string[] { "Mesin", "Versi jari", "Versi wajah", "User", "Template jari", "Wajah", "Log", "Selisih jam (dtk)", "Catatan" };

        Store st;
        ListView lvMesin, lvInfo, lvUser, lvSum;
        ListSorter sM = new ListSorter();
        ListSorter sU = new ListSorter();
        ListSorter sS = new ListSorter();
        Dictionary<string, string> statusMesin = new Dictionary<string, string>();
        TextBox txtLog, txtUid, txtNama, txtUidFp, txtCari;
        ComboBox cmbJari;
        HandPanel hand;
        Label lblCount, lblInfoHead, lblRingkasLog, lblPeran;
        TabPage tpKaryawan, tpLog, tpSemua;
        TabControl tabsUtama;
        KaryawanPanel karyawan;
        LogPanel logPanel;
        Panel pnlCatatan;
        Label lblCatatanAkhir;
        Button btnCatatan;
        List<string[]> allUsers = new List<string[]>();
        object enrollZk = null;
        public bool KeluarAkun = false;
        string enrollMesin = "";
        string enrollUid = "";

        public MainForm(Store store)
        {
            st = store;
            Text = "HRIS Device Tool " + Versi;
            ClientSize = new Size(1200, 720);
            MinimumSize = new Size(1200, 720);
            StartPosition = FormStartPosition.CenterScreen;
            BuildUi();
            RefreshList(null);
            FormClosing += OnClosing;
            RefreshRingkasLog();
            AuditLog.Dir = st.LogDir;
            karyawan.Muat();
            Log("Aplikasi dibuka. Folder data: " + st.DataDir);
            if (st.Data.Mesin.Count == 0)
                Log("Belum ada mesin. Buka tab Mesin lalu klik Tambah untuk mendaftarkan mesin pertama.");
            if (st.SecretsLocked)
                Log("Comm Key tersimpan tidak dibuka (migrasi dari kata sandi lama dilewati). Comm Key akan ditanyakan saat menghubungkan.");
        }

        // ---------- UI ----------
        Button Btn(string text, int x, int y, int w, EventHandler h)
        {
            Button b = new Button();
            b.Text = text;
            b.Location = new Point(x, y);
            b.Size = new Size(w, 28);
            b.Click += h;
            return b;
        }

        Label Lbl(string text, int x, int y)
        {
            Label l = new Label();
            l.Text = text;
            l.Location = new Point(x, y);
            l.AutoSize = true;
            return l;
        }

        ListView MakeList(string[] names, int[] widths)
        {
            ListView lv = new ListView();
            lv.View = View.Details;
            lv.FullRowSelect = true;
            lv.GridLines = true;
            lv.HideSelection = false;
            lv.MultiSelect = false;
            for (int i = 0; i < names.Length; i++) lv.Columns.Add(names[i], widths[i]);
            return lv;
        }

        // Pilih banyak baris dan salin. Hasil dipisah tab, bisa ditempel ke Excel.
        void BisaSalin(ListView lv)
        {
            lv.MultiSelect = true;
            string sel = "";
            ContextMenuStrip menu = new ContextMenuStrip();
            menu.Items.Add("Salin sel ini", null, delegate { TaruhClipboard(sel); });
            menu.Items.Add("Salin baris terpilih (Ctrl+C)", null, delegate { SalinBaris(lv, false); });
            menu.Items.Add("Salin semua dengan judul", null, delegate { SalinBaris(lv, true); });
            menu.Items.Add("Pilih semua (Ctrl+A)", null, delegate { PilihSemua(lv); });
            lv.ContextMenuStrip = menu;
            lv.MouseDown += delegate (object o, MouseEventArgs e)
            {
                ListViewHitTestInfo h = lv.HitTest(e.Location);
                sel = (h.SubItem != null) ? h.SubItem.Text : "";
            };
            lv.KeyDown += delegate (object o, KeyEventArgs e)
            {
                if (e.Control && e.KeyCode == Keys.C) { SalinBaris(lv, false); e.Handled = true; }
                if (e.Control && e.KeyCode == Keys.A) { PilihSemua(lv); e.Handled = true; }
            };
        }

        void PilihSemua(ListView lv)
        {
            lv.BeginUpdate();
            foreach (ListViewItem it in lv.Items) it.Selected = true;
            lv.EndUpdate();
        }

        void SalinBaris(ListView lv, bool semua)
        {
            StringBuilder sb = new StringBuilder();
            if (semua)
            {
                for (int i = 0; i < lv.Columns.Count; i++) sb.Append((i > 0 ? "\t" : "") + lv.Columns[i].Text);
                sb.Append(Environment.NewLine);
            }
            foreach (ListViewItem it in lv.Items)
            {
                if (!semua && !it.Selected) continue;
                for (int i = 0; i < it.SubItems.Count; i++) sb.Append((i > 0 ? "\t" : "") + it.SubItems[i].Text);
                sb.Append(Environment.NewLine);
            }
            TaruhClipboard(sb.ToString());
        }

        void TaruhClipboard(string teks)
        {
            if (string.IsNullOrEmpty(teks)) return;
            try { Clipboard.SetText(teks); }
            catch (Exception ex) { Log("Gagal menyalin: " + ex.Message); }
        }

        void SetArrow(ListView lv, ListSorter s, string[] names)
        {
            string up = " " + (char)0x25B2;
            string dn = " " + (char)0x25BC;
            for (int i = 0; i < names.Length && i < lv.Columns.Count; i++)
                lv.Columns[i].Text = names[i] + (i == s.Col ? (s.Asc ? up : dn) : "");
        }

        void SortClick(ListView lv, ListSorter s, string[] names, int col)
        {
            if (col == s.Col) s.Asc = !s.Asc;
            else { s.Col = col; s.Asc = true; }
            SetArrow(lv, s, names);
            lv.Sort();
        }

        void BuildUi()
        {
            tabsUtama = new TabControl();
            tabsUtama.Dock = DockStyle.Fill;
            tabsUtama.Padding = new Point(16, 5);

            tpKaryawan = new TabPage("Karyawan");
            karyawan = new KaryawanPanel(
                delegate { if (!Peran.Boleh("OnSimpanUserMesin")) return; AuditLog.Kat = "sistem"; OnSimpanUserMesin(); },
                delegate { if (!Peran.Boleh("OnSimpanTemplate")) return; AuditLog.Kat = "sidik-jari"; OnSimpanTemplate(null); });
            tpKaryawan.Controls.Add(karyawan);
            tpLog = BuildTabLog();

            tabsUtama.TabPages.Add(tpKaryawan);
            tabsUtama.TabPages.Add(tpLog);
            tabsUtama.TabPages.Add(BuildTabMesin());
            tabsUtama.TabPages.Add(BuildTabPengaturan());
            tabsUtama.TabPages.Add(BuildTabBantuan());
            tabsUtama.SelectedIndexChanged += delegate
            {
                if (tabsUtama.SelectedTab == tpKaryawan) karyawan.Muat();
                if (tabsUtama.SelectedTab == tpLog) RefreshRingkasLog();
            };

            // Urutan penambahan menentukan susunan Dock: yang Fill lebih dulu.
            Controls.Add(tabsUtama);
            Controls.Add(BuildCatatan());
            Controls.Add(BuildAtas());
        }

        // Baris atas: akun yang sedang masuk.
        Control BuildAtas()
        {
            FlowLayoutPanel atas = new FlowLayoutPanel();
            atas.Dock = DockStyle.Top;
            atas.Height = 38;
            atas.FlowDirection = FlowDirection.RightToLeft;
            atas.WrapContents = false;
            atas.Padding = new Padding(0, 1, 6, 0);
            atas.Controls.Add(Gaya.Tombol("Keluar akun", 110, delegate { if (MessageBox.Show("Keluar dari akun \"" + Peran.NamaAktif + "\" dan kembali ke dialog Masuk?", "Keluar akun", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return; AuditLog.Kat = "sistem"; AuditLog.Tulis("Logout", "keluar akun " + Peran.NamaAktif); KeluarAkun = true; Close(); }));
            atas.Controls.Add(Gaya.Tombol("Ganti sandi", 110, delegate { AuditLog.Kat = "sistem"; Akun.Ganti(st); }));
            lblPeran = Lbl("Masuk sebagai: " + Peran.NamaAktif, 0, 0);
            lblPeran.Margin = new Padding(3, 10, 10, 0);
            atas.Controls.Add(lblPeran);
            return atas;
        }

        // Catatan aktivitas: satu baris di bawah, bisa dibuka.
        Control BuildCatatan()
        {
            pnlCatatan = new Panel();
            pnlCatatan.Dock = DockStyle.Bottom;
            pnlCatatan.Height = 36;
            pnlCatatan.Padding = new Padding(6, 0, 6, 0);

            txtLog = new TextBox();
            txtLog.Multiline = true;
            txtLog.ReadOnly = true;
            txtLog.ScrollBars = ScrollBars.Vertical;
            txtLog.Font = new Font("Consolas", 9f);
            txtLog.Dock = DockStyle.Fill;
            txtLog.Visible = false;

            Panel baris = new Panel();
            baris.Dock = DockStyle.Top;
            baris.Height = 36;
            lblCatatanAkhir = new Label();
            lblCatatanAkhir.Dock = DockStyle.Fill;
            lblCatatanAkhir.TextAlign = ContentAlignment.MiddleLeft;
            lblCatatanAkhir.AutoEllipsis = true;
            lblCatatanAkhir.UseMnemonic = false;
            btnCatatan = Gaya.Tombol("Buka catatan", 130, delegate { BukaCatatan(!txtLog.Visible); });
            btnCatatan.Dock = DockStyle.Right;
            Button bersih = Gaya.Tombol("Bersihkan log", 110, delegate { txtLog.Clear(); lblCatatanAkhir.Text = ""; });
            bersih.Dock = DockStyle.Right;
            baris.Controls.Add(lblCatatanAkhir);
            baris.Controls.Add(bersih);
            baris.Controls.Add(btnCatatan);

            pnlCatatan.Controls.Add(txtLog);
            pnlCatatan.Controls.Add(baris);
            return pnlCatatan;
        }

        void BukaCatatan(bool buka)
        {
            txtLog.Visible = buka;
            pnlCatatan.Height = buka ? 200 : 36;
            btnCatatan.Text = buka ? "Tutup catatan" : "Buka catatan";
            if (buka)
            {
                txtLog.SelectionStart = txtLog.TextLength;
                txtLog.ScrollToCaret();
            }
        }

        // Tab Mesin: daftar mesin di kiri, pekerjaan per mesin di kanan.
        TabPage BuildTabMesin()
        {
            TabPage p = new TabPage("Mesin");

            Panel kiri = new Panel();
            kiri.Dock = DockStyle.Left;
            kiri.Width = 458;
            kiri.AutoScroll = true;
            kiri.Controls.Add(Lbl("Daftar mesin", 8, 8));
            lvMesin = MakeList(ColM, new int[] { 32, 115, 95, 45, 50, 95 });
            lvMesin.Location = new Point(8, 28);
            lvMesin.Size = new Size(440, 320);
            lvMesin.ListViewItemSorter = sM;
            lvMesin.ColumnClick += delegate (object o, ColumnClickEventArgs e) { SortClick(lvMesin, sM, ColM, e.Column); };
            kiri.Controls.Add(lvMesin);
            kiri.Controls.Add(Btn("Tambah", 8, 356, 140, delegate { if (!Peran.Boleh("OnTambah")) return; AuditLog.Kat = "mesin"; OnTambah(); }));
            kiri.Controls.Add(Btn("Ubah", 158, 356, 140, delegate { if (!Peran.Boleh("OnUbah")) return; AuditLog.Kat = "mesin"; OnUbah(); }));
            kiri.Controls.Add(Btn("Hapus", 308, 356, 140, delegate { if (!Peran.Boleh("OnHapus")) return; AuditLog.Kat = "mesin"; OnHapus(); }));
            kiri.Controls.Add(Btn("Naik", 8, 390, 140, delegate { if (!Peran.Boleh("OnGeser")) return; AuditLog.Kat = "mesin"; OnGeser(-1); }));
            kiri.Controls.Add(Btn("Turun", 158, 390, 140, delegate { if (!Peran.Boleh("OnGeser")) return; AuditLog.Kat = "mesin"; OnGeser(1); }));
            kiri.Controls.Add(Btn("A-Z", 308, 390, 140, delegate { if (!Peran.Boleh("OnUrutAz")) return; AuditLog.Kat = "mesin"; OnUrutAz(); }));
            kiri.Controls.Add(Lbl("Hapus = hanya dari daftar aplikasi. Naik/Turun/A-Z = urutan tersimpan.", 8, 424));

            TabControl sub = new TabControl();
            sub.Dock = DockStyle.Fill;
            tpSemua = BuildTabSemua();
            tpSemua.Controls.Add(Btn("Cek semua", 315, 12, 110, delegate { if (!Peran.Boleh("OnCekSemua")) return; AuditLog.Kat = "mesin"; OnCekSemua(); }));
            tpSemua.Controls.Add(Btn("Bandingkan 2 mesin", 435, 12, 160, delegate { if (!Peran.Boleh("OnBanding")) return; AuditLog.Kat = "bandingkan"; OnBanding(); }));
            tpSemua.Controls.Add(Btn("Kirim user HRIS", 603, 12, 105, delegate { if (!Peran.Boleh("OnKirimHris")) return; AuditLog.Kat = "semua-mesin"; OnKirimUser(); }));
            sub.TabPages.Add(tpSemua);
            sub.TabPages.Add(BuildTabInfo());
            sub.TabPages.Add(BuildTabUser());
            sub.TabPages.Add(BuildTabJari());

            p.Controls.Add(sub);
            p.Controls.Add(kiri);
            return p;
        }

        // Tab Pengaturan: pilihan bagian di kiri, isinya di kanan.
        TabPage BuildTabPengaturan()
        {
            TabPage p = new TabPage("Pengaturan");
            ListBox menu = new ListBox();
            menu.Dock = DockStyle.Left;
            menu.Width = 200;
            menu.IntegralHeight = false;
            menu.ItemHeight = 20;
            Panel isi = new Panel();
            isi.Dock = DockStyle.Fill;

            List<Panel> bagian = new List<Panel>();
            Panel umum = Bagian(menu, isi, bagian, "Umum");
            umum.Controls.Add(Lbl("Versi: " + Versi, 20, 46));
            umum.Controls.Add(Lbl("Folder data:", 20, 76));
            umum.Controls.Add(KotakJalur(st.DataDir, 20, 96));
            umum.Controls.Add(Btn("Buka folder data", 20, 130, 160, delegate { BukaFolder(st.DataDir); }));

            Panel hris = Bagian(menu, isi, bagian, "Koneksi HRIS");
            Label lblUrl = Lbl("", 20, 46);
            lblUrl.UseMnemonic = false;
            Action tampilUrl = delegate
            {
                string u = (st.Data.UrlHris ?? "").Trim();
                lblUrl.Text = "Alamat server: " + (u.Length > 0 ? u : "(belum diisi)");
            };
            tampilUrl();
            hris.Controls.Add(lblUrl);
            hris.Controls.Add(Btn("Ubah alamat dan token...", 20, 76, 200, delegate
            {
                if (!Peran.Boleh("OnPengaturanHris")) return;
                AuditLog.Kat = "sistem";
                using (HrisDialog d = new HrisDialog(st)) { d.ShowDialog(this); }
                tampilUrl();
            }));

            Panel db = Bagian(menu, isi, bagian, "Database & cadangan");
            db.Controls.Add(Lbl("Berkas database (peran manager ke atas):", 20, 46));
            db.Controls.Add(KotakJalur(global::HrisDeviceTool.Data.HdtDatabase.BerkasDefault(), 20, 66));
            db.Controls.Add(Btn("Cek database", 20, 104, 160, delegate { if (!Peran.Boleh("OnCekDb")) return; AuditLog.Kat = "sistem"; OnCekDb(); }));
            db.Controls.Add(Btn("Cadangkan database", 190, 104, 160, delegate { if (!Peran.Boleh("OnCadangDb")) return; AuditLog.Kat = "sistem"; OnCadangDb(); }));
            db.Controls.Add(Btn("Lihat database", 360, 104, 160, delegate { if (!Peran.Boleh("OnLihatDb")) return; AuditLog.Kat = "sistem"; OnLihatDb(); }));
            db.Controls.Add(Lbl("Aplikasi absensi lama (dipakai sesekali):", 20, 160));
            db.Controls.Add(Btn("Impor aplikasi lama", 20, 182, 160, delegate { if (!Peran.Boleh("OnImporLama")) return; AuditLog.Kat = "sistem"; OnImporLama(); }));

            Panel akun = Bagian(menu, isi, bagian, "Akun & kata sandi");
            akun.Controls.Add(Lbl("Masuk sebagai: " + Peran.NamaAktif, 20, 46));
            akun.Controls.Add(Lbl("Urutan peran: user < supervisor < manager < direksi < administrator.", 20, 70));
            akun.Controls.Add(Btn("Ganti kata sandi", 20, 100, 160, delegate { AuditLog.Kat = "sistem"; Akun.Ganti(st); }));

            menu.SelectedIndexChanged += delegate
            {
                for (int i = 0; i < bagian.Count; i++) bagian[i].Visible = (i == menu.SelectedIndex);
            };
            menu.SelectedIndex = 0;

            p.Controls.Add(isi);
            p.Controls.Add(menu);
            return p;
        }

        Panel Bagian(ListBox menu, Panel isi, List<Panel> daftar, string judul)
        {
            Panel pn = new Panel();
            pn.Dock = DockStyle.Fill;
            pn.Visible = false;
            Label l = Lbl("", 20, 14);
            l.UseMnemonic = false;
            l.Text = judul;
            l.Font = new Font(Font.FontFamily, 11f, FontStyle.Bold);
            pn.Controls.Add(l);
            menu.Items.Add(judul);
            daftar.Add(pn);
            isi.Controls.Add(pn);
            return pn;
        }

        static TextBox KotakJalur(string teks, int x, int y)
        {
            TextBox t = new TextBox();
            t.ReadOnly = true;
            t.Text = teks;
            t.Location = new Point(x, y);
            t.Width = 640;
            return t;
        }

        TabPage BuildTabLog()
        {
            TabPage p = new TabPage("Log absensi");
            p.Size = new Size(1180, 560);
            p.Controls.Add(Btn("Tarik log mesin", 15, 12, 160, delegate { if (!Peran.Boleh("OnTarikLog")) return; AuditLog.Kat = "tarik-log"; OnTarikLog(); }));
            p.Controls.Add(Btn("Kelola salinan", 185, 12, 160, delegate { if (!Peran.Boleh("OnKelolaSalinan")) return; AuditLog.Kat = "tarik-log"; OnKelolaSalinan(); }));
            p.Controls.Add(Btn("Impor CSV ke database", 355, 12, 190, delegate { if (!Peran.Boleh("OnImporLog")) return; AuditLog.Kat = "tarik-log"; OnImporLog(); }));
            p.Controls.Add(Lbl("Alur kirim log ke HRIS:   1. Tarik log mesin   >   2. Kelola salinan   >   3. Kirim ke HRIS (dicentang)", 15, 54));
            p.Controls.Add(Lbl("Tarik log menyimpan salinan CSV di komputer ini. Kirim dilakukan dari Kelola salinan.\r\nKirim ulang aman: baris yang sudah ada di HRIS dihitung duplicate, bukan data ganda.", 15, 80));
            lblRingkasLog = Lbl("", 15, 128);
            lblRingkasLog.Font = new Font(Font, FontStyle.Bold);
            p.Controls.Add(lblRingkasLog);
            logPanel = new LogPanel();
            logPanel.Location = new Point(8, 156);
            logPanel.Size = new Size(1160, 392);
            logPanel.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;
            p.Controls.Add(logPanel);
            return p;
        }

        void RefreshRingkasLog()
        {
            if (lblRingkasLog == null) return;
            if (logPanel != null && tabsUtama != null && tabsUtama.SelectedTab == tpLog) logPanel.Muat();
            try
            {
                List<SalinanItem> l = Salinan.DaftarAktif(st);
                int belum = 0;
                foreach (SalinanItem it in l) { if (it.Terkirim.Length == 0) belum++; }
                lblRingkasLog.Text = "Salinan aktif: " + l.Count + "     Belum terkirim ke HRIS: " + belum;
                lblRingkasLog.ForeColor = belum > 0 ? Color.Firebrick : Color.DarkGreen;
            }
            catch (Exception) { lblRingkasLog.Text = ""; }
        }

        TabPage BuildTabInfo()
        {
            TabPage p = new TabPage("Info mesin");
            p.Size = new Size(722, 409);
            p.Controls.Add(Btn("Ambil info mesin", 15, 12, 160, delegate { if (!Peran.Boleh("OnInfo")) return; AuditLog.Kat = "info-mesin"; OnInfo(); }));
            lblInfoHead = Lbl("Pilih mesin di daftar kiri, lalu klik Ambil info mesin. Hanya membaca.", 190, 19);
            p.Controls.Add(lblInfoHead);
            lvInfo = MakeList(new string[] { "Kelompok", "Item", "Nilai" }, new int[] { 230, 190, 250 });
            lvInfo.Location = new Point(15, 50);
            lvInfo.Size = new Size(695, 345);
            lvInfo.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;
            p.Controls.Add(lvInfo);
            BisaSalin(lvInfo);
            return p;
        }

        TabPage BuildTabSemua()
        {
            TabPage p = new TabPage("Ringkasan semua");
            p.Size = new Size(722, 409);
            p.Controls.Add(Btn("Ringkas semua mesin", 15, 12, 170, delegate { if (!Peran.Boleh("OnRingkas")) return; AuditLog.Kat = "semua-mesin"; OnRingkas(); }));
            p.Controls.Add(Btn("Ekspor CSV", 195, 12, 110, delegate { if (!Peran.Boleh("OnEkspor")) return; AuditLog.Kat = "semua-mesin"; OnEkspor(); }));
            p.Controls.Add(Lbl("Hanya membaca. Baris kuning = selisih jam lebih dari 60 detik.", 15, 54));
            lvSum = MakeList(ColS, new int[] { 110, 75, 80, 60, 90, 55, 60, 120, 150 });
            lvSum.Location = new Point(15, 76);
            lvSum.Size = new Size(695, 319);
            lvSum.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;
            lvSum.ListViewItemSorter = sS;
            lvSum.ColumnClick += delegate (object o, ColumnClickEventArgs e) { SortClick(lvSum, sS, ColS, e.Column); };
            p.Controls.Add(lvSum);
            BisaSalin(lvSum);
            return p;
        }

        TabPage BuildTabUser()
        {
            TabPage p = new TabPage("User di mesin");
            p.Size = new Size(722, 409);
            p.Controls.Add(Lbl("ID user", 15, 20));
            txtUid = new TextBox();
            txtUid.Location = new Point(70, 17);
            txtUid.Width = 130;
            txtUid.Text = "99901";
            p.Controls.Add(txtUid);
            p.Controls.Add(Lbl("Nama", 220, 20));
            txtNama = new TextBox();
            txtNama.Location = new Point(265, 17);
            txtNama.Width = 200;
            p.Controls.Add(txtNama);
            p.Controls.Add(Btn("Cek user", 15, 52, 110, delegate { if (!Peran.Boleh("OnCekUser")) return; AuditLog.Kat = "user"; OnCekUser(); }));
            p.Controls.Add(Btn("Tambah user uji (999...)", 135, 52, 170, delegate { if (!Peran.Boleh("OnTambahUserUji")) return; AuditLog.Kat = "user"; OnTambahUserUji(); }));
            p.Controls.Add(Btn("List semua user", 315, 52, 130, delegate { if (!Peran.Boleh("OnDaftarUser")) return; AuditLog.Kat = "user"; OnDaftarUser(); }));

            p.Controls.Add(Lbl("Cari (nama atau ID)", 15, 96));
            txtCari = new TextBox();
            txtCari.Location = new Point(140, 92);
            txtCari.Width = 200;
            txtCari.TextChanged += delegate { ApplyFilter(); };
            p.Controls.Add(txtCari);
            lblCount = Lbl("", 355, 96);
            p.Controls.Add(lblCount);

            lvUser = MakeList(ColU, new int[] { 110, 290, 140, 90 });
            lvUser.Location = new Point(15, 124);
            lvUser.Size = new Size(695, 270);
            lvUser.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;
            lvUser.ListViewItemSorter = sU;
            lvUser.ColumnClick += delegate (object o, ColumnClickEventArgs e) { SortClick(lvUser, sU, ColU, e.Column); };
            p.Controls.Add(lvUser);
            BisaSalin(lvUser);
            return p;
        }

        TabPage BuildTabJari()
        {
            TabPage p = new TabPage("Sidik jari");
            p.Controls.Add(Lbl("ID user", 15, 20));
            txtUidFp = new TextBox();
            txtUidFp.Location = new Point(70, 17);
            txtUidFp.Width = 130;
            txtUidFp.Text = "99901";
            p.Controls.Add(txtUidFp);
            p.Controls.Add(Lbl("Jari", 220, 20));
            cmbJari = new ComboBox();
            cmbJari.DropDownStyle = ComboBoxStyle.DropDownList;
            for (int i = 0; i < 10; i++) cmbJari.Items.Add(i + " - " + NamaJari[i]);
            cmbJari.SelectedIndex = 5;
            cmbJari.Location = new Point(250, 17);
            cmbJari.Width = 190;
            cmbJari.SelectedIndexChanged += delegate
            {
                hand.Selected = cmbJari.SelectedIndex;
                hand.Invalidate();
            };
            p.Controls.Add(cmbJari);
            p.Controls.Add(Btn("Baca template (jari 0-9)", 15, 55, 190, delegate { if (!Peran.Boleh("OnBacaTemplate")) return; AuditLog.Kat = "sidik-jari"; OnBacaTemplate(); }));
            p.Controls.Add(Btn("Picu daftar dari PC", 215, 55, 170, delegate { if (!Peran.Boleh("OnPicu")) return; AuditLog.Kat = "sidik-jari"; OnPicu(); }));
            p.Controls.Add(Btn("Selesai daftar && baca", 395, 55, 170, delegate { if (!Peran.Boleh("OnSelesai")) return; AuditLog.Kat = "sidik-jari"; OnSelesai(); }));

            p.Controls.Add(Btn("Simpan ke database", 575, 55, 140, delegate { if (!Peran.Boleh("OnSimpanTemplate")) return; AuditLog.Kat = "sidik-jari"; MesinItem pilih = Selected(); if (pilih != null) OnSimpanTemplate(pilih); }));

            Label info = Lbl("Baca template: hanya membaca. Hasil disimpan di folder data\\cadangan (ekstensi .hdttmpl). Jari yang ditemukan berwarna hijau di gambar.\r\n\r\nPicu daftar: mesin dipaksa masuk mode daftar untuk ID tersebut (hanya ID uji berawalan 999) dan jari yang dipilih di kotak Jari. Minta rekan menempelkan jari di mesin, lalu klik 'Selesai daftar && baca'.\r\n\r\nSelama menunggu, aplikasi TIDAK membaca apa pun.\r\n\r\nNama jari: 0-4 tangan kiri (kelingking ke jempol), 5-9 tangan kanan (jempol ke kelingking).", 15, 100);
            info.AutoSize = false;
            info.Size = new Size(335, 270);
            p.Controls.Add(info);

            hand = new HandPanel();
            hand.Location = new Point(360, 95);
            hand.Selected = 5;
            hand.SelectionChanged += delegate { cmbJari.SelectedIndex = hand.Selected; };
            p.Controls.Add(hand);
            return p;
        }

        TabPage BuildTabBantuan()
        {
            TabPage p = new TabPage("Bantuan");
            p.Controls.Add(Btn("Diagnostik", 15, 15, 140, delegate { if (!Peran.Boleh("OnDiagnostik")) return; AuditLog.Kat = "bantuan"; OnDiagnostik(); }));
            p.Controls.Add(Btn("Buka folder data", 165, 15, 150, delegate { BukaFolder(st.DataDir); }));
            p.Controls.Add(Btn("Buka folder panduan", 325, 15, 170, delegate { if (!Peran.Boleh("OnPanduan")) return; AuditLog.Kat = "bantuan"; OnPanduan(); }));
            Label ket = Lbl("Pekerjaan harian: 1. Log absensi > Tarik log mesin.  2. Log absensi > Kelola salinan > Kirim ke HRIS.  3. Karyawan > periksa daftar gabungan.\r\n\r\nDiagnostik memeriksa: komponen mesin (zkemkeeper), folder data, dan koneksi ke semua mesin terdaftar.\r\n\r\nPindah ke PC lain: salin SELURUH folder aplikasi (exe + folder data).\r\nComm Key yang disimpan dienkripsi Windows (hanya terbaca di PC ini, tanpa kata sandi). Di PC lain, isi Comm Key dan token HRIS (Pengaturan > Koneksi HRIS) sekali lagi.\r\n\r\nPanduan lengkap ada di folder docs (ditambahkan setelah tahap ini teruji).\r\nVersi: " + Versi, 15, 60);
            ket.AutoSize = false;
            ket.Size = new Size(700, 300);
            ket.UseMnemonic = false;
            p.Controls.Add(ket);
            return p;
        }

        void OnTarikLog()
        {
            if (st.Data.Mesin.Count < 1) { Msg("Belum ada mesin terdaftar."); return; }
            LogForm f = new LogForm(st, delegate (MesinItem m) { return Open(m, false); });
            f.FormClosed += delegate { RefreshRingkasLog(); };
            f.ShowDialog(this);
        }

        void OnCekDb()
        {
            try
            {
                string berkas = global::HrisDeviceTool.Data.HdtDatabase.BerkasDefault();
                bool baru = !System.IO.File.Exists(berkas);
                using (global::System.Data.SQLite.SQLiteConnection c = global::HrisDeviceTool.Data.HdtDatabase.Buka(berkas))
                {
                    System.Text.StringBuilder sb = new System.Text.StringBuilder();
                    sb.AppendLine("Berkas: " + berkas);
                    sb.AppendLine(baru ? "Database BARU dibuat (skema v" + global::HrisDeviceTool.Data.HdtDatabase.VersiSkema + ")." : "Database sudah ada.");
                    sb.AppendLine();
                    foreach (System.Collections.Generic.KeyValuePair<string, long> kv in global::HrisDeviceTool.Data.HdtDatabase.Ringkasan(c))
                    {
                        sb.AppendLine(kv.Key + " : " + kv.Value + " baris");
                    }
                    AuditLog.Tulis("Cek database", "ringkasan tabel dibuka");
                    Msg(sb.ToString());
                }
            }
            catch (System.Exception ex)
            {
                Msg("Cek database GAGAL: " + ex.Message);
            }
        }

        void OnCadangDb()
        {
            try
            {
                string berkas = global::HrisDeviceTool.Data.HdtDatabase.BerkasDefault();
                using (SaveFileDialog dlg = new SaveFileDialog())
                {
                    dlg.Title = "Cadangkan database";
                    dlg.Filter = "Database SQLite (*.sqlite)|*.sqlite";
                    dlg.FileName = "hdt_cadangan_" + System.DateTime.Now.ToString("yyyyMMdd_HHmm") + ".sqlite";
                    if (dlg.ShowDialog(this) != DialogResult.OK) return;
                    if (System.IO.File.Exists(dlg.FileName)) System.IO.File.Delete(dlg.FileName);
                    using (global::System.Data.SQLite.SQLiteConnection c = global::HrisDeviceTool.Data.HdtDatabase.Buka(berkas))
                    {
                        global::HrisDeviceTool.Data.HdtDatabase.Cadangkan(c, dlg.FileName);
                    }
                    AuditLog.Tulis("Cadangkan database", "salinan dibuat");
                    Msg("Cadangan selesai:\r\n" + dlg.FileName);
                }
            }
            catch (System.Exception ex)
            {
                Msg("Cadangkan database GAGAL: " + ex.Message);
            }
        }

        void OnImporLama()
        {
            try
            {
                string berkas;
                using (OpenFileDialog dlg = new OpenFileDialog())
                {
                    dlg.Title = "Pilih berkas CSV aplikasi absensi lama";
                    dlg.Filter = "CSV / teks (*.csv;*.txt)|*.csv;*.txt|Semua berkas (*.*)|*.*";
                    if (dlg.ShowDialog(this) != DialogResult.OK) return;
                    berkas = dlg.FileName;
                }
                string db = global::HrisDeviceTool.Data.HdtDatabase.BerkasDefault();
                string pem = System.IO.Path.Combine(System.IO.Path.GetDirectoryName(db), "pemetaan_impor.txt");
                global::HrisDeviceTool.Data.HasilAnalisis h = global::HrisDeviceTool.Data.ImporLama.Analisis(berkas, pem);

                System.Text.StringBuilder sb = new System.Text.StringBuilder();
                sb.AppendLine("Berkas: " + System.IO.Path.GetFileName(berkas));
                sb.AppendLine("Penyandian: " + h.Sandi + "   Pemisah: " + h.Pemisah);
                sb.AppendLine("Baris data: " + h.TotalBaris + "   Akan diimpor: " + h.Baris.Count);
                sb.AppendLine("Tanpa No. Akun (dilewati): " + h.TanpaIdAkun);
                sb.AppendLine("No. Akun ganda di berkas (dipakai yang terakhir): " + h.GandaDalamBerkas);
                sb.AppendLine("Tanggal tidak terbaca (masuk data_lain): " + h.TanggalTakTerbaca);
                sb.AppendLine();
                sb.AppendLine("Pemetaan judul kolom:");
                for (int i = 0; i < h.Judul.Count; i++)
                {
                    sb.AppendLine("  " + h.Judul[i] + "  ->  " + (h.Peta[i] == null ? "(tidak dikenal, masuk data_lain)" : h.Peta[i]));
                }
                sb.AppendLine();
                sb.AppendLine("Lanjutkan impor ke database?");
                if (MessageBox.Show(sb.ToString(), "Impor aplikasi lama", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;

                using (global::System.Data.SQLite.SQLiteConnection c = global::HrisDeviceTool.Data.HdtDatabase.Buka(db))
                {
                    global::HrisDeviceTool.Data.HasilTulis w = global::HrisDeviceTool.Data.ImporLama.Tulis(c, h);
                    AuditLog.Tulis("Impor aplikasi lama", System.IO.Path.GetFileName(berkas) + ": baru " + w.Baru + ", diperbarui " + w.Diperbarui);
                    karyawan.Muat();
                    Msg("Impor selesai.\r\nBaru: " + w.Baru + "\r\nDiperbarui: " + w.Diperbarui + "\r\nDilewati (tanpa No. Akun): " + h.TanpaIdAkun);
                }
            }
            catch (System.Exception ex)
            {
                Msg("Impor GAGAL: " + ex.Message);
            }
        }

        void OnSimpanUserMesin()
        {
            try
            {
                if (st.Data.Mesin.Count < 1) { Msg("Belum ada mesin terdaftar."); return; }
                List<MesinItem> daftar = PilihBanyakMesin.Tanya(this, st.Data.Mesin, "Ambil user dari mesin",
                    "Daftar user disimpan ke database lokal. Mesin hanya dibaca. Data lama dari mesin yang sama diganti. Kata sandi mesin tidak disimpan.", null);
                if (daftar == null) return;

                System.Text.StringBuilder sb = new System.Text.StringBuilder();
                int totalUser = 0;
                int berhasil = 0;
                using (global::System.Data.SQLite.SQLiteConnection c = global::HrisDeviceTool.Data.HdtDatabase.Buka(global::HrisDeviceTool.Data.HdtDatabase.BerkasDefault()))
                {
                    foreach (MesinItem mi in daftar)
                    {
                        object zk = Open(mi, false);
                        if (zk == null) { sb.AppendLine(mi.Nama + " : GAGAL tersambung"); continue; }
                        try
                        {
                            System.Collections.Generic.List<string[]> rows = Dev.ListUsersLengkap(zk, 5000);
                            if (rows.Count == 0)
                            {
                                sb.AppendLine(mi.Nama + " : 0 user terbaca (tidak disimpan, snapshot lama dipertahankan)");
                                continue;
                            }
                            global::HrisDeviceTool.Data.HasilSnapshot h = global::HrisDeviceTool.Data.SnapshotUser.Simpan(c, mi.Nama, mi.Ip, rows);
                            sb.AppendLine(mi.Nama + " : " + h.Sesudah + " user (sebelumnya " + h.Sebelum + ", dilewati " + h.Dilewati + ")");
                            totalUser += h.Sesudah;
                            berhasil++;
                            Log("Snapshot user " + mi.Nama + ": " + h.Sesudah + " user tersimpan.");
                            try { global::HrisDeviceTool.Data.InfoMesin.Simpan(c, mi.Nama, mi.Ip, Dev.InfoRows(zk)); }
                            catch (System.Exception exInfo) { sb.AppendLine(mi.Nama + " : info mesin tidak tersimpan (" + exInfo.Message + ")"); }
                        }
                        catch (System.Exception ex)
                        {
                            sb.AppendLine(mi.Nama + " : GAGAL (" + ex.Message + ")");
                        }
                        finally
                        {
                            Done(zk);
                        }
                    }
                }
                AuditLog.Tulis("Simpan user mesin", berhasil + " dari " + daftar.Count + " mesin, " + totalUser + " user");
                karyawan.Muat();
                Msg("Simpan user mesin selesai.\r\n\r\n" + sb.ToString());
            }
            catch (System.Exception ex)
            {
                Msg("Simpan user mesin GAGAL: " + ex.Message);
            }
        }

        void OnLihatDb()
        {
            try
            {
                AuditLog.Tulis("Lihat database", "dialog dibuka");
                DatabaseForm f = new DatabaseForm();
                f.ShowDialog(this);
            }
            catch (System.Exception ex)
            {
                Msg("Lihat database GAGAL: " + ex.Message);
            }
        }

        void OnImporLog()
        {
            try
            {
                string folder = Path.Combine(st.DataDir, "tarikan");
                if (!Directory.Exists(folder)) { Msg("Folder tarikan belum ada: " + folder); return; }
                if (MessageBox.Show("Impor salinan CSV di folder tarikan ke database lokal?\r\n\r\n" + folder + "\r\n\r\nAman diulang: baris yang sudah ada dilewati dan berkas yang sudah pernah diimpor tidak dibaca lagi. Mesin tidak disentuh.", "Impor CSV ke database", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
                Cursor = Cursors.WaitCursor;
                global::HrisDeviceTool.Data.HasilImporLog h;
                using (global::System.Data.SQLite.SQLiteConnection c = global::HrisDeviceTool.Data.HdtDatabase.Buka(global::HrisDeviceTool.Data.HdtDatabase.BerkasDefault()))
                {
                    h = global::HrisDeviceTool.Data.ImporLog.Folder(c, folder, delegate (string s) { Log(s); Application.DoEvents(); });
                }
                Cursor = Cursors.Default;
                AuditLog.Tulis("Impor log CSV", "berkas " + h.BerkasDiimpor + ", dilewati " + h.BerkasDilewati + ", terbaca " + h.Terbaca + ", baru " + h.Baru + ", rusak " + h.Rusak);
                StringBuilder sb = new StringBuilder();
                sb.AppendLine("Impor selesai.");
                sb.AppendLine("Berkas diimpor: " + h.BerkasDiimpor);
                sb.AppendLine("Berkas dilewati: " + h.BerkasDilewati);
                sb.AppendLine("Baris terbaca: " + h.Terbaca);
                sb.AppendLine("Baris baru di database: " + h.Baru);
                sb.AppendLine("Baris rusak dilewati: " + h.Rusak);
                RefreshRingkasLog();
                int n = 0;
                foreach (string cat in h.Catatan) { if (n++ >= 15) { sb.AppendLine("..."); break; } sb.AppendLine(cat); }
                Msg(sb.ToString());
            }
            catch (Exception ex)
            {
                Cursor = Cursors.Default;
                Msg("Impor log GAGAL: " + ex.Message);
            }
        }

        void OnKelolaSalinan()
        {
            KelolaSalinanForm f = new KelolaSalinanForm(st);
            f.FormClosed += delegate { RefreshRingkasLog(); };
            f.ShowDialog(this);
        }

        void OnKirimUser()
        {
            if (st.Data.Mesin.Count < 1) { Msg("Belum ada mesin terdaftar."); return; }
            KirimUserForm f = new KirimUserForm(st, delegate (MesinItem m) { return Open(m, false); });
            f.ShowDialog(this);
        }

        void OnBanding()
        {
            if (st.Data.Mesin.Count < 2) { Msg("Butuh minimal dua mesin terdaftar."); return; }
            BandingkanForm f = new BandingkanForm(st, delegate (MesinItem m) { return Open(m, false); });
            f.ShowDialog(this);
        }

        // ---------- Bantu ----------
        void Msg(string s)
        {
            MessageBox.Show(s, "HRIS Device Tool", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        void Log(string s)
        {
            string line = DateTime.Now.ToString("HH:mm:ss") + "  " + s.Replace("\r\n", "\n").Replace("\n", "\r\n");
            txtLog.AppendText(line + "\r\n");
            lblCatatanAkhir.Text = line.Replace("\r\n", "  ");
            lblCatatanAkhir.Refresh();
            try
            {
                string f = AuditLog.Berkas(AuditLog.Kat);
                File.AppendAllText(f, DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") + "  [" + Environment.UserName + "@" + Environment.MachineName + " / " + Peran.NamaAktif + "]  " + s + Environment.NewLine);
            }
            catch { }
        }

        static string KeyText(MesinItem m)
        {
            if (m.TanpaKey) return "Tanpa";
            if (m.IngatKey) return "Ingat";
            return "Tanya";
        }

        void RefreshList(string pilih)
        {
            lvMesin.BeginUpdate();
            lvMesin.Items.Clear();
            sM.Col = 0;
            sM.Asc = true;
            int no = 0;
            foreach (MesinItem m in st.Data.Mesin)
            {
                no++;
                ListViewItem it = new ListViewItem(no.ToString());
                it.Tag = m;
                it.SubItems.Add(m.Nama);
                it.SubItems.Add(m.Ip);
                it.SubItems.Add(m.Port.ToString());
                it.SubItems.Add(KeyText(m));
                string s;
                it.SubItems.Add(statusMesin.TryGetValue(m.Nama, out s) ? s : "");
                lvMesin.Items.Add(it);
                if (pilih != null && m.Nama == pilih) it.Selected = true;
            }
            if (lvMesin.SelectedItems.Count == 0 && lvMesin.Items.Count > 0) lvMesin.Items[0].Selected = true;
            lvMesin.EndUpdate();
            SetArrow(lvMesin, sM, ColM);
        }

        MesinItem Selected()
        {
            if (lvMesin.SelectedItems.Count == 0)
            {
                Msg("Pilih mesin di tab Mesin (daftar kiri) dulu, atau klik Tambah.");
                return null;
            }
            return (MesinItem)lvMesin.SelectedItems[0].Tag;
        }

        string GetKey(MesinItem m)
        {
            if (m.TanpaKey) return "";
            string k;
            if (st.Keys.TryGetValue(m.Nama, out k)) return k;
            string r = Dlg.Prompt("Comm Key", "Comm Key untuk mesin " + m.Nama + "\r\n(kosongkan bila mesin tidak memakai Comm Key):", true, false);
            if (r == null) return null;
            st.Keys[m.Nama] = r;
            if (r.Length == 0 || r.Trim() == "0")
            {
                m.TanpaKey = true;
                st.SaveData();
                Log("Mesin " + m.Nama + " ditandai TANPA Comm Key, tidak akan ditanya lagi. Bila salah, klik Ubah lalu isi Comm Key.");
                RefreshList(m.Nama);
            }
            else if (!st.SecretsLocked &&
                MessageBox.Show("Ingat Comm Key mesin " + m.Nama + "?\r\n(Disimpan terenkripsi oleh Windows, hanya terbaca di PC ini. Tanpa kata sandi.)",
                "Comm Key", MessageBoxButtons.YesNo, MessageBoxIcon.Question) == DialogResult.Yes)
            {
                m.IngatKey = true;
                st.SaveData();
                if (!st.SaveSecrets())
                {
                    m.IngatKey = false;
                    st.SaveData();
                    Log("Comm Key TIDAK tersimpan (hanya untuk sesi ini).");
                }
                else Log("Comm Key mesin " + m.Nama + " tersimpan terenkripsi.");
                RefreshList(m.Nama);
            }
            return r;
        }

        object Open(MesinItem m)
        {
            return Open(m, false);
        }

        // quiet = true: tidak menampilkan kotak pesan saat gagal (dipakai saat memproses banyak mesin)
        object Open(MesinItem m, bool quiet)
        {
            string key = GetKey(m);
            if (key == null) return null;
            Cursor = Cursors.WaitCursor;
            Exception last = null;
            for (int i = 0; i < 2; i++)
            {
                try
                {
                    return Dev.Connect(m, key);
                }
                catch (Exception e)
                {
                    last = e;
                    if (i == 0)
                    {
                        Log("Koneksi " + m.Nama + " gagal, mencoba sekali lagi...");
                        System.Threading.Thread.Sleep(700);
                    }
                }
            }
            Cursor = Cursors.Default;
            Log("GAGAL " + m.Nama + ": " + last.Message);
            if (!quiet) MessageBox.Show(last.Message, "Tidak bisa terhubung", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return null;
        }

        void Done(object zk)
        {
            Dev.Disconnect(zk);
            Cursor = Cursors.Default;
        }

        void BukaFolder(string path)
        {
            if (Directory.Exists(path)) Process.Start("explorer.exe", "\"" + path + "\"");
            else Msg("Folder belum ada: " + path);
        }

        void OnClosing(object sender, FormClosingEventArgs e)
        {
            if (enrollZk != null) Dev.Disconnect(enrollZk);
        }

        static string SafeName(string s)
        {
            foreach (char c in Path.GetInvalidFileNameChars()) s = s.Replace(c, '_');
            return s;
        }

        static string PrivName(string p)
        {
            switch (p)
            {
                case "0": return "0 (User)";
                case "1": return "1 (Enroller)";
                case "2": return "2 (Admin)";
                case "3": return "3 (Super admin)";
            }
            return p;
        }

        // ---------- Daftar mesin ----------
        void OnTambah()
        {
            MesinDialog dlg = new MesinDialog(st, null, "");
            if (dlg.ShowDialog(this) != DialogResult.OK) return;
            st.Data.Mesin.Add(dlg.Result);
            if (dlg.KeyResult.Length > 0) st.Keys[dlg.Result.Nama] = dlg.KeyResult;
            st.SaveData();
            bool ok = st.SaveSecrets();
            if (dlg.Result.IngatKey && !ok) Log("Comm Key TIDAK tersimpan (hanya untuk sesi ini).");
            RefreshList(dlg.Result.Nama);
            Log("Mesin ditambah: " + dlg.Result.Nama + " (" + dlg.Result.Ip + ":" + dlg.Result.Port + ")");
        }

        void OnUbah()
        {
            MesinItem m = Selected();
            if (m == null) return;
            string oldName = m.Nama;
            string oldKey;
            st.Keys.TryGetValue(oldName, out oldKey);
            if (oldKey == null) oldKey = "";
            MesinDialog dlg = new MesinDialog(st, m, oldKey);
            if (dlg.ShowDialog(this) != DialogResult.OK) return;
            int i = st.Data.Mesin.IndexOf(m);
            st.Data.Mesin[i] = dlg.Result;
            st.Keys.Remove(oldName);
            statusMesin.Remove(oldName);
            if (dlg.KeyResult.Length > 0) st.Keys[dlg.Result.Nama] = dlg.KeyResult;
            st.SaveData();
            bool ok = st.SaveSecrets();
            if (dlg.Result.IngatKey && !ok) Log("Comm Key TIDAK tersimpan (hanya untuk sesi ini).");
            RefreshList(dlg.Result.Nama);
            Log("Mesin diubah: " + dlg.Result.Nama);
        }

        void OnHapus()
        {
            MesinItem m = Selected();
            if (m == null) return;
            if (MessageBox.Show("Hapus mesin " + m.Nama + " dari daftar aplikasi?\r\n(Tidak menghapus apa pun di mesin absensinya.)",
                "Konfirmasi", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
            st.Keys.Remove(m.Nama);
            statusMesin.Remove(m.Nama);
            st.Data.Mesin.Remove(m);
            st.SaveData();
            st.SaveSecrets();
            RefreshList(null);
            Log("Mesin dihapus dari daftar: " + m.Nama);
        }

        void OnGeser(int arah)
        {
            MesinItem m = Selected();
            if (m == null) return;
            int i = st.Data.Mesin.IndexOf(m);
            int j = i + arah;
            if (j < 0 || j >= st.Data.Mesin.Count) return;
            st.Data.Mesin[i] = st.Data.Mesin[j];
            st.Data.Mesin[j] = m;
            st.SaveData();
            RefreshList(m.Nama);
        }

        void OnUrutAz()
        {
            MesinItem pilih = (lvMesin.SelectedItems.Count > 0) ? (MesinItem)lvMesin.SelectedItems[0].Tag : null;
            st.Data.Mesin.Sort(delegate (MesinItem a, MesinItem b)
            {
                return string.Compare(a.Nama, b.Nama, StringComparison.OrdinalIgnoreCase);
            });
            st.SaveData();
            RefreshList(pilih != null ? pilih.Nama : null);
            Log("Daftar mesin diurutkan A-Z.");
        }

        void OnCekSemua()
        {
            MesinItem pilih = (lvMesin.SelectedItems.Count > 0) ? (MesinItem)lvMesin.SelectedItems[0].Tag : null;
            Cursor = Cursors.WaitCursor;
            foreach (MesinItem m in st.Data.Mesin)
            {
                bool ok = Dev.PortOpen(m.Ip, m.Port, 1500);
                statusMesin[m.Nama] = ok ? "port terbuka" : "TIDAK menjawab";
            }
            Cursor = Cursors.Default;
            RefreshList(pilih != null ? pilih.Nama : null);
            Log("Cek semua mesin selesai (hanya tes port, belum login ke mesin).");
        }

        // ---------- Info ----------
        void OnInfo()
        {
            MesinItem m = Selected();
            if (m == null) return;
            object zk = Open(m);
            if (zk == null) return;
            try
            {
                List<string[]> rows = Dev.InfoRows(zk);
                lvInfo.BeginUpdate();
                lvInfo.Items.Clear();
                foreach (string[] r in rows)
                {
                    ListViewItem it = new ListViewItem(r[0]);
                    it.SubItems.Add(r[1]);
                    it.SubItems.Add(r[2]);
                    lvInfo.Items.Add(it);
                }
                lvInfo.EndUpdate();
                lblInfoHead.Text = "Mesin: " + m.Nama + " (" + m.Ip + "), dibaca " + DateTime.Now.ToString("HH:mm:ss");
                Log("Info " + m.Nama + " dibaca (" + rows.Count + " baris, lihat tab Info mesin).");
            }
            catch (Exception e)
            {
                Log("Error: " + e.Message);
            }
            finally
            {
                Done(zk);
            }
        }

        // ---------- Semua mesin ----------
        void OnRingkas()
        {
            if (st.Data.Mesin.Count == 0) { Msg("Belum ada mesin."); return; }
            lvSum.BeginUpdate();
            lvSum.Items.Clear();
            foreach (MesinItem m in st.Data.Mesin)
            {
                Log("Ringkas: membaca " + m.Nama + " ...");
                ListViewItem it = new ListViewItem(m.Nama);
                object zk = Open(m, true);
                if (zk == null)
                {
                    for (int i = 1; i <= 7; i++) it.SubItems.Add("-");
                    it.SubItems.Add("GAGAL terhubung");
                    it.BackColor = Color.MistyRose;
                }
                else
                {
                    try
                    {
                        string[] r = Dev.Ringkas(zk);
                        for (int i = 0; i < r.Length; i++) it.SubItems.Add(r[i]);
                        long sel;
                        string cat = "";
                        if (long.TryParse(r[6], out sel) && Math.Abs(sel) > 60)
                        {
                            cat = "Jam beda lebih dari 60 dtk";
                            it.BackColor = Color.LightYellow;
                        }
                        it.SubItems.Add(cat);
                    }
                    catch (Exception e)
                    {
                        while (it.SubItems.Count < 8) it.SubItems.Add("-");
                        it.SubItems.Add("Error: " + e.Message);
                        it.BackColor = Color.MistyRose;
                    }
                    finally
                    {
                        Done(zk);
                    }
                }
                lvSum.Items.Add(it);
            }
            lvSum.EndUpdate();
            Cursor = Cursors.Default;
            Log("Ringkasan semua mesin selesai.");
        }

        void OnEkspor()
        {
            if (lvSum.Items.Count == 0) { Msg("Klik Ringkas semua mesin dulu."); return; }
            string path = Path.Combine(st.DataDir, "ringkasan_" + DateTime.Now.ToString("yyyyMMdd_HHmmss") + ".csv");
            StringBuilder sb = new StringBuilder();
            sb.AppendLine(string.Join(";", ColS));
            foreach (ListViewItem it in lvSum.Items)
            {
                List<string> cells = new List<string>();
                foreach (ListViewItem.ListViewSubItem s in it.SubItems) cells.Add(s.Text.Replace(";", ","));
                sb.AppendLine(string.Join(";", cells.ToArray()));
            }
            File.WriteAllText(path, sb.ToString(), new UTF8Encoding(true));
            Log("Ringkasan diekspor: " + path);
        }

        // ---------- User ----------
        void OnCekUser()
        {
            BukaCatatan(true);
            MesinItem m = Selected();
            if (m == null) return;
            string uid = txtUid.Text.Trim();
            if (uid.Length == 0) { Msg("Isi ID user dulu."); return; }
            object zk = Open(m);
            if (zk == null) return;
            try
            {
                string name;
                int priv;
                bool en;
                if (Dev.GetUser(zk, uid, out name, out priv, out en))
                    Log("User " + uid + " di " + m.Nama + ": ADA (nama " + name + ", privilege " + PrivName(priv.ToString()) + ", " + (en ? "aktif" : "nonaktif") + ")");
                else
                    Log("User " + uid + " di " + m.Nama + ": TIDAK ada");
            }
            catch (Exception e)
            {
                Log("Error: " + e.Message);
            }
            finally
            {
                Done(zk);
            }
        }

        void OnTambahUserUji()
        {
            BukaCatatan(true);
            MesinItem m = Selected();
            if (m == null) return;
            string uid = txtUid.Text.Trim();
            if (!uid.StartsWith("999", StringComparison.Ordinal))
            {
                Msg("Pada tahap ini hanya ID uji yang boleh ditambah lewat aplikasi (awalan 999, contoh 99901).");
                return;
            }
            string nama = txtNama.Text.Trim();
            if (nama.Length == 0) nama = "ZZ-UJI";
            if (MessageBox.Show("Tambah user " + uid + " (" + nama + ") ke mesin " + m.Nama + " (" + m.Ip + ")?",
                "Konfirmasi", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
            object zk = Open(m);
            if (zk == null) return;
            try
            {
                string n0;
                int p0;
                bool e0;
                if (Dev.GetUser(zk, uid, out n0, out p0, out e0))
                {
                    Log("User " + uid + " sudah ada (" + n0 + "), tidak diubah.");
                }
                else
                {
                    bool ok = Dev.CreateUser(zk, uid, nama);
                    Log("Tambah user " + uid + " di " + m.Nama + ": " + (ok ? "OK" : "GAGAL, kode " + Dev.Err(zk)));
                }
            }
            catch (Exception e)
            {
                Log("Error: " + e.Message);
            }
            finally
            {
                Done(zk);
            }
        }

        void OnDaftarUser()
        {
            MesinItem m = Selected();
            if (m == null) return;
            object zk = Open(m);
            if (zk == null) return;
            try
            {
                allUsers = Dev.ListUsers(zk, 5000);
                txtCari.Text = "";
                ApplyFilter();
                Log("List user " + m.Nama + ": " + allUsers.Count + " baris (bandingkan dengan jumlah user di Info mesin).");
            }
            catch (Exception e)
            {
                Log("Error: " + e.Message);
            }
            finally
            {
                Done(zk);
            }
        }

        void ApplyFilter()
        {
            string q = txtCari.Text.Trim();
            int shown = 0;
            lvUser.BeginUpdate();
            lvUser.Items.Clear();
            foreach (string[] r in allUsers)
            {
                if (q.Length > 0 &&
                    r[0].IndexOf(q, StringComparison.OrdinalIgnoreCase) < 0 &&
                    r[1].IndexOf(q, StringComparison.OrdinalIgnoreCase) < 0) continue;
                ListViewItem it = new ListViewItem(r[0]);
                it.SubItems.Add(r[1]);
                it.SubItems.Add(PrivName(r[2]));
                it.SubItems.Add(r[3]);
                lvUser.Items.Add(it);
                shown++;
            }
            lvUser.EndUpdate();
            SetArrow(lvUser, sU, ColU);
            lblCount.Text = "menampilkan " + shown + " dari " + allUsers.Count + " user";
        }

        // ---------- Sidik jari ----------
        int BacaDanTandai(object zk, string mesin, string uid)
        {
            DateTime since = DateTime.Now.AddSeconds(-1);
            hand.Reset();
            int n = Dev.ReadTemplates(zk, uid, mesin, st.CadanganDir, Log);
            List<string> names = new List<string>();
            for (int f = 0; f <= 9; f++)
            {
                string path = Path.Combine(st.CadanganDir, "tmpl_" + SafeName(mesin) + "_" + uid + "_jari" + f + ".hdttmpl");
                if (File.Exists(path) && File.GetLastWriteTime(path) >= since)
                {
                    hand.Found[f] = true;
                    names.Add(f + " " + NamaJari[f]);
                }
            }
            hand.Invalidate();
            if (n == 0) Log("HASIL: template BELUM ada di mesin saat dibaca");
            else Log("HASIL: " + n + " template: " + string.Join(", ", names.ToArray()));
            return n;
        }

        void OnBacaTemplate()
        {
            BukaCatatan(true);
            MesinItem m = Selected();
            if (m == null) return;
            string uid = txtUidFp.Text.Trim();
            if (uid.Length == 0) { Msg("Isi ID user dulu."); return; }
            object zk = Open(m);
            if (zk == null) return;
            try
            {
                Log("--- Baca template user " + uid + " di " + m.Nama + " (jari 0-9) ---");
                BacaDanTandai(zk, m.Nama, uid);
            }
            catch (Exception e)
            {
                Log("Error: " + e.Message);
            }
            finally
            {
                Done(zk);
            }
        }

        void OnSimpanTemplate(MesinItem awal)
        {
            if (enrollZk != null) { Msg("Sesi daftar masih terbuka. Klik 'Selesai daftar & baca' dulu."); return; }
            if (st.Data.Mesin.Count < 1) { Msg("Belum ada mesin terdaftar."); return; }
            List<MesinItem> daftar = PilihBanyakMesin.Tanya(this, st.Data.Mesin, "Ambil sidik jari",
                "Template disimpan terenkripsi di database lokal. Mesin hanya dibaca. Membaca banyak mesin bisa lama.", awal);
            if (daftar == null) return;
            try
            {
                StringBuilder sb = new StringBuilder();
                int total = 0, berhasil = 0;
                using (global::System.Data.SQLite.SQLiteConnection c = global::HrisDeviceTool.Data.HdtDatabase.Buka(global::HrisDeviceTool.Data.HdtDatabase.BerkasDefault()))
                {
                    byte[] kunci = Brankas.Buka(c);
                    if (kunci == null) { Log("Simpan template dibatalkan (kunci tidak dibuka)."); return; }
                    Enabled = false;
                    foreach (MesinItem mi in daftar)
                    {
                        object zk = Open(mi, true);
                        if (zk == null) { sb.AppendLine(mi.Nama + " : GAGAL tersambung"); continue; }
                        try
                        {
                            string nama = mi.Nama;
                            Log("Membaca template " + nama + "...");
                            List<global::HrisDeviceTool.Data.BarisTemplate> baris = Dev.BacaSemuaTemplate(zk, delegate (int n, int jml)
                            {
                                if (n % 100 == 0) Log(nama + ": user " + n + " dari " + jml);
                                if (n % 10 == 0) Application.DoEvents();
                            });
                            int diMesin = Dev.JumlahTemplateMesin(zk);
                            if (baris.Count == 0) { sb.AppendLine(nama + " : 0 template terbaca (mesin melaporkan " + diMesin + "), tidak disimpan"); continue; }
                            global::HrisDeviceTool.Data.HasilTemplate h = global::HrisDeviceTool.Data.TemplateStore.Simpan(c, nama, Dev.VersiJari(zk), baris, kunci);
                            string ringkas = nama + " : disimpan " + h.Disimpan + ", cocok " + h.Cocok + ", mesin melaporkan " + diMesin + ", total di database " + h.TotalMesin;
                            sb.AppendLine(ringkas);
                            Log(ringkas);
                            total += h.Disimpan;
                            berhasil++;
                        }
                        catch (Exception ex)
                        {
                            sb.AppendLine(mi.Nama + " : GAGAL (" + ex.Message + ")");
                        }
                        finally
                        {
                            Done(zk);
                        }
                    }
                }
                Enabled = true;
                AuditLog.Tulis("Simpan template", berhasil + " dari " + daftar.Count + " mesin, " + total + " template");
                karyawan.Muat();
                Msg("Simpan template selesai.\r\n\r\n" + sb.ToString());
            }
            catch (Exception ex)
            {
                Enabled = true;
                Msg("Simpan template GAGAL: " + ex.Message);
            }
            finally
            {
                Enabled = true;
                Cursor = Cursors.Default;
            }
        }

        void OnPicu()
        {
            BukaCatatan(true);
            if (enrollZk != null)
            {
                Msg("Sesi daftar masih terbuka. Klik 'Selesai daftar & baca' dulu.");
                return;
            }
            MesinItem m = Selected();
            if (m == null) return;
            string uid = txtUidFp.Text.Trim();
            if (!uid.StartsWith("999", StringComparison.Ordinal))
            {
                Msg("Pada tahap ini picu daftar hanya untuk ID uji (awalan 999, contoh 99901).");
                return;
            }
            int jari = cmbJari.SelectedIndex;
            object zk = Open(m);
            if (zk == null) return;
            bool ok = false;
            try
            {
                string nm;
                int pv;
                bool en;
                if (!Dev.GetUser(zk, uid, out nm, out pv, out en))
                {
                    if (!Dev.CreateUser(zk, uid, "ZZ-UJI"))
                    {
                        Log("Gagal membuat user uji " + uid + " (kode " + Dev.Err(zk) + "). Batal.");
                        Done(zk);
                        return;
                    }
                    Log("User uji " + uid + " dibuat.");
                }
                ok = Dev.StartEnroll(zk, uid, jari);
                Log("StartEnrollEx(" + uid + ", jari " + jari + " " + NamaJari[jari] + ") di " + m.Nama + ": " + ok + " (kode " + Dev.Err(zk) + ")");
            }
            catch (Exception e)
            {
                Log("Error: " + e.Message);
                ok = false;
            }
            if (ok)
            {
                enrollZk = zk;
                enrollMesin = m.Nama;
                enrollUid = uid;
                Cursor = Cursors.Default;
                Log("Minta rekan menempelkan " + NamaJari[jari] + " di mesin SEKARANG. Setelah selesai (atau menu hilang), klik 'Selesai daftar & baca'. Aplikasi tidak membaca apa pun selama menunggu.");
            }
            else
            {
                Done(zk);
            }
        }

        void OnSelesai()
        {
            BukaCatatan(true);
            if (enrollZk == null)
            {
                Msg("Belum ada sesi daftar. Klik 'Picu daftar dari PC' dulu.");
                return;
            }
            object zk = enrollZk;
            try
            {
                Log("--- Baca template user " + enrollUid + " di " + enrollMesin + " setelah daftar ---");
                BacaDanTandai(zk, enrollMesin, enrollUid);
            }
            catch (Exception e)
            {
                Log("Error: " + e.Message);
            }
            finally
            {
                enrollZk = null;
                Done(zk);
            }
        }

        // ---------- Bantuan ----------
        void OnDiagnostik()
        {
            BukaCatatan(true);
            Cursor = Cursors.WaitCursor;
            Log("=== Diagnostik ===");
            Log("Proses 32-bit: " + (IntPtr.Size == 4 ? "Ya (benar)" : "TIDAK - aplikasi harus dikompilasi x86"));
            Type t = Type.GetTypeFromProgID("zkemkeeper.ZKEM");
            Log(t != null ? "Komponen zkemkeeper: terdaftar" : "Komponen zkemkeeper: BELUM terdaftar. Lihat panduan pemulihan, bagian komponen mesin.");
            try
            {
                string p = Path.Combine(st.DataDir, "tes_tulis.tmp");
                File.WriteAllText(p, "x");
                File.Delete(p);
                Log("Folder data: bisa ditulis (" + st.DataDir + ")");
            }
            catch (Exception e)
            {
                Log("Folder data: TIDAK bisa ditulis (" + e.Message + "). Pindahkan aplikasi ke folder biasa, bukan Program Files.");
            }
            if (st.Data.Mesin.Count == 0) Log("Belum ada mesin terdaftar.");
            foreach (MesinItem m in st.Data.Mesin)
            {
                bool ok = Dev.PortOpen(m.Ip, m.Port, 2000);
                Log(m.Nama + " " + m.Ip + ":" + m.Port + " -> " + (ok ? "port terbuka" : "TIDAK menjawab (cek kabel, VPN, atau IP)"));
            }
            Log("=== Selesai ===");
            Cursor = Cursors.Default;
        }

        void OnPanduan()
        {
            string a = Path.Combine(st.BaseDir, "docs");
            string b = Path.GetFullPath(Path.Combine(st.BaseDir, "..\\docs"));
            if (Directory.Exists(a)) BukaFolder(a);
            else if (Directory.Exists(b)) BukaFolder(b);
            else Msg("Folder panduan belum ada. Panduan ditambahkan setelah tahap ini teruji.");
        }
    }
}
