using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Data.SQLite;
using System.Drawing;
using System.IO;
using System.Text;
using System.Windows.Forms;
using HrisDeviceTool.Data;

namespace HrisDeviceTool
{
    // Warna dan tombol seragam untuk tampilan baru.
    public static class Gaya
    {
        public static readonly Color Biru = Color.FromArgb(11, 83, 148);
        public static readonly Color Pilih = Color.FromArgb(214, 230, 247);
        public static readonly Color Oranye = Color.FromArgb(255, 226, 191);
        public static readonly Color Judul = Color.FromArgb(238, 241, 245);

        public static Button Tombol(string teks, int lebar, EventHandler h)
        {
            Button b = new Button();
            b.Text = teks;
            b.Size = new Size(lebar, 30);
            b.Click += h;
            return b;
        }

        public static void Utama(Button b)
        {
            b.FlatStyle = FlatStyle.Flat;
            b.BackColor = Biru;
            b.ForeColor = Color.White;
            b.FlatAppearance.BorderColor = Biru;
        }

        public static DataGridView Tabel(string[] judul, int[] bobot)
        {
            DataGridView g = new DataGridView();
            g.ReadOnly = true;
            g.AllowUserToAddRows = false;
            g.AllowUserToDeleteRows = false;
            g.AllowUserToResizeRows = false;
            g.RowHeadersVisible = false;
            g.SelectionMode = DataGridViewSelectionMode.FullRowSelect;
            g.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill;
            g.BackgroundColor = Color.White;
            g.BorderStyle = BorderStyle.FixedSingle;
            g.GridColor = Color.FromArgb(228, 232, 237);
            g.EnableHeadersVisualStyles = false;
            g.ColumnHeadersDefaultCellStyle.BackColor = Judul;
            g.ColumnHeadersDefaultCellStyle.SelectionBackColor = Judul;
            g.DefaultCellStyle.SelectionBackColor = Pilih;
            g.DefaultCellStyle.SelectionForeColor = Color.Black;
            g.ClipboardCopyMode = DataGridViewClipboardCopyMode.EnableWithAutoHeaderText;
            for (int i = 0; i < judul.Length; i++)
            {
                int n = g.Columns.Add("k" + i, judul[i]);
                g.Columns[n].FillWeight = bobot[i];
            }
            return g;
        }
    }

    // Layar Karyawan: satu baris per ID, rincian per mesin di bawah. Hanya membaca database lokal.
    public class KaryawanPanel : Panel
    {
        static readonly string[] NamaSaring = { "Semua", "Nama berbeda", "Tanpa sidik jari", "Hanya 1 mesin" };

        List<Karyawan> semua = new List<Karyawan>();
        SaringKaryawan saring = SaringKaryawan.Semua;
        TextBox txtCari;
        RadioButton[] pilihan = new RadioButton[4];
        DataGridView grid, rinci;
        Label lblInfo, lblRinci;
        bool mengisi;
        string idTerpilih = "";

        public KaryawanPanel(EventHandler ambilUser, EventHandler ambilJari)
        {
            Dock = DockStyle.Fill;
            Padding = new Padding(8);

            // Baris 1: cari (kiri) dan tombol (kanan)
            Panel baris1 = new Panel();
            baris1.Dock = DockStyle.Top;
            baris1.Height = 38;
            Label lc = new Label();
            lc.Text = "Cari";
            lc.AutoSize = true;
            lc.Location = new Point(0, 9);
            txtCari = new TextBox();
            txtCari.Location = new Point(34, 6);
            txtCari.Width = 240;
            txtCari.TextChanged += delegate { Isi(); };
            FlowLayoutPanel kanan = new FlowLayoutPanel();
            kanan.Dock = DockStyle.Right;
            kanan.FlowDirection = FlowDirection.RightToLeft;
            kanan.WrapContents = false;
            kanan.Width = 560;
            Button bUser = Gaya.Tombol("Ambil user dari mesin...", 180, ambilUser);
            Gaya.Utama(bUser);
            kanan.Controls.Add(bUser);
            kanan.Controls.Add(Gaya.Tombol("Ambil sidik jari...", 140, ambilJari));
            kanan.Controls.Add(Gaya.Tombol("Ekspor CSV", 100, delegate { if (!Peran.Boleh("OnEksporKaryawan")) return; AuditLog.Kat = "sistem"; Ekspor(); }));
            kanan.Controls.Add(Gaya.Tombol("Muat ulang", 100, delegate { Muat(); }));
            baris1.Controls.Add(lc);
            baris1.Controls.Add(txtCari);
            baris1.Controls.Add(kanan);

            // Baris 2: saringan
            FlowLayoutPanel baris2 = new FlowLayoutPanel();
            baris2.Dock = DockStyle.Top;
            baris2.Height = 36;
            baris2.WrapContents = false;
            Label lt = new Label();
            lt.Text = "Tampilkan:";
            lt.AutoSize = true;
            lt.Margin = new Padding(0, 8, 6, 0);
            baris2.Controls.Add(lt);
            for (int i = 0; i < NamaSaring.Length; i++)
            {
                RadioButton rb = new RadioButton();
                rb.Appearance = Appearance.Button;
                rb.FlatStyle = FlatStyle.Flat;
                rb.TextAlign = ContentAlignment.MiddleCenter;
                rb.Size = new Size(160, 28);
                rb.Text = NamaSaring[i];
                rb.Checked = (i == 0);
                int nomor = i;
                WarnaiSaringan(rb);
                rb.CheckedChanged += delegate
                {
                    WarnaiSaringan(pilihan[nomor]);
                    if (!pilihan[nomor].Checked) return;
                    saring = (SaringKaryawan)nomor;
                    Isi();
                };
                pilihan[i] = rb;
                baris2.Controls.Add(rb);
            }

            lblInfo = new Label();
            lblInfo.Dock = DockStyle.Top;
            lblInfo.Height = 24;
            lblInfo.TextAlign = ContentAlignment.MiddleLeft;

            grid = Gaya.Tabel(new string[] { "ID", "Nama", "Departemen", "Jml mesin", "Ada di mesin", "Sidik jari", "Jari tersimpan", "Catatan" },
                new int[] { 60, 150, 100, 55, 170, 55, 70, 130 });
            grid.Dock = DockStyle.Fill;
            grid.MultiSelect = true;
            grid.SelectionChanged += delegate { TampilRinci(); };
            grid.SortCompare += delegate (object o, DataGridViewSortCompareEventArgs e)
            {
                if (e.Column.Index == 0)
                {
                    e.SortResult = DaftarKaryawan.BandingId(Convert.ToString(e.CellValue1), Convert.ToString(e.CellValue2));
                    e.Handled = true;
                }
            };

            Panel bawah = new Panel();
            bawah.Dock = DockStyle.Bottom;
            bawah.Height = 180;
            lblRinci = new Label();
            lblRinci.Dock = DockStyle.Top;
            lblRinci.Height = 26;
            lblRinci.TextAlign = ContentAlignment.MiddleLeft;
            lblRinci.Font = new Font(Font, FontStyle.Bold);
            rinci = Gaya.Tabel(new string[] { "Mesin", "Nama di mesin", "Privilege", "Status", "Kartu", "Jari", "User diambil" },
                new int[] { 100, 170, 90, 70, 55, 50, 130 });
            rinci.Dock = DockStyle.Fill;
            bawah.Controls.Add(rinci);
            bawah.Controls.Add(lblRinci);

            Splitter garis = new Splitter();
            garis.Dock = DockStyle.Bottom;
            garis.Height = 6;

            // Urutan penambahan menentukan susunan Dock: yang Fill lebih dulu.
            Controls.Add(grid);
            Controls.Add(garis);
            Controls.Add(bawah);
            Controls.Add(lblInfo);
            Controls.Add(baris2);
            Controls.Add(baris1);
        }

        // Saringan yang aktif berwarna gelap agar jelas terlihat.
        static void WarnaiSaringan(RadioButton rb)
        {
            Color gelap = Color.FromArgb(27, 36, 48);
            rb.BackColor = rb.Checked ? gelap : Color.White;
            rb.ForeColor = rb.Checked ? Color.White : Color.Black;
            rb.FlatAppearance.CheckedBackColor = gelap;
        }

        public void Muat()
        {
            try
            {
                string berkas = HdtDatabase.BerkasDefault();
                if (!File.Exists(berkas)) { semua = new List<Karyawan>(); }
                else
                {
                    using (SQLiteConnection c = HdtDatabase.Buka(berkas)) { semua = DaftarKaryawan.Muat(c); }
                }
                int[] n = new int[4];
                foreach (Karyawan k in semua)
                {
                    for (int i = 0; i < 4; i++) { if (DaftarKaryawan.Cocok(k, (SaringKaryawan)i, "")) n[i]++; }
                }
                for (int i = 0; i < 4; i++) { pilihan[i].Text = NamaSaring[i] + " (" + n[i] + ")"; }
                Isi();
            }
            catch (Exception ex)
            {
                lblInfo.Text = "Gagal memuat daftar karyawan: " + ex.Message;
            }
        }

        void Isi()
        {
            mengisi = true;
            string ingat = idTerpilih;
            grid.SuspendLayout();
            // Urutan kolom pilihan pengguna dilepas dulu, lalu diterapkan lagi setelah baris diisi.
            DataGridViewColumn urut = grid.SortedColumn;
            ListSortDirection arah = grid.SortOrder == SortOrder.Descending ? ListSortDirection.Descending : ListSortDirection.Ascending;
            if (urut != null)
            {
                urut.SortMode = DataGridViewColumnSortMode.NotSortable;
                urut.SortMode = DataGridViewColumnSortMode.Automatic;
            }
            grid.Rows.Clear();
            List<DataGridViewRow> baris = new List<DataGridViewRow>();
            foreach (Karyawan k in semua)
            {
                if (!DaftarKaryawan.Cocok(k, saring, txtCari.Text)) continue;
                DataGridViewRow r = new DataGridViewRow();
                r.CreateCells(grid, k.Id, k.Nama, k.Departemen, k.Rincian.Count, k.DaftarMesin, k.TeksJari, k.JariTersimpan, k.Catatan);
                r.Tag = k;
                if (k.NamaBeda || k.TanpaJari) r.Cells[7].Style.BackColor = Gaya.Oranye;
                baris.Add(r);
            }
            grid.Rows.AddRange(baris.ToArray());
            if (urut != null) grid.Sort(urut, arah);
            grid.ResumeLayout();
            grid.ClearSelection();
            DataGridViewRow pilih = null;
            foreach (DataGridViewRow r in grid.Rows) { if (((Karyawan)r.Tag).Id == ingat) { pilih = r; break; } }
            if (pilih == null && grid.Rows.Count > 0) pilih = grid.Rows[0];
            if (pilih != null)
            {
                grid.CurrentCell = pilih.Cells[0];
                pilih.Selected = true;
            }
            mengisi = false;
            lblInfo.Text = semua.Count == 0
                ? "Belum ada data. Klik \"Ambil user dari mesin\" (butuh peran manager ke atas)."
                : "Menampilkan " + grid.Rows.Count + " dari " + semua.Count + " ID.   Tanda ? pada Sidik jari = template mesin itu belum diambil.";
            TampilRinci();
        }

        void TampilRinci()
        {
            if (mengisi) return;
            rinci.Rows.Clear();
            if (grid.CurrentRow == null || grid.CurrentRow.Tag == null)
            {
                lblRinci.Text = "Rincian per mesin";
                return;
            }
            Karyawan k = (Karyawan)grid.CurrentRow.Tag;
            idTerpilih = k.Id;
            lblRinci.Text = k.Id + "  " + k.Nama + "  -  rincian per mesin";
            foreach (RincianMesin m in k.Rincian)
            {
                int n = rinci.Rows.Add(m.Mesin, m.Nama, NamaPrivilege(m.Privilege), m.Aktif ? "Aktif" : "Nonaktif",
                    m.AdaKartu ? "Ada" : "Tidak", m.Jari < 0 ? "?" : m.Jari.ToString(), m.Diambil);
                if (k.NamaBeda && DaftarKaryawan.Samakan(m.Nama) != DaftarKaryawan.Samakan(k.Nama))
                    rinci.Rows[n].Cells[1].Style.BackColor = Gaya.Oranye;
            }
            rinci.ClearSelection();
        }

        static string NamaPrivilege(int p)
        {
            switch (p)
            {
                case 0: return "User";
                case 1: return "Enroller";
                case 2: return "Admin";
                case 3: return "Super admin";
            }
            return p.ToString();
        }

        void Ekspor()
        {
            List<Karyawan> tampil = new List<Karyawan>();
            foreach (DataGridViewRow r in grid.Rows) tampil.Add((Karyawan)r.Tag);
            if (tampil.Count == 0) { MessageBox.Show("Tidak ada baris untuk diekspor.", "Ekspor CSV"); return; }
            if (MessageBox.Show("Berkas CSV berisi data pribadi karyawan. Simpan di tempat yang aman.\r\n\r\nLanjutkan?",
                "Ekspor CSV", MessageBoxButtons.YesNo, MessageBoxIcon.Warning) != DialogResult.Yes) return;
            using (SaveFileDialog dlg = new SaveFileDialog())
            {
                dlg.Title = "Ekspor daftar karyawan";
                dlg.Filter = "CSV (*.csv)|*.csv";
                dlg.FileName = "karyawan_" + DateTime.Now.ToString("yyyyMMdd_HHmm") + ".csv";
                if (dlg.ShowDialog(this) != DialogResult.OK) return;
                try
                {
                    File.WriteAllText(dlg.FileName, DaftarKaryawan.Csv(tampil), new UTF8Encoding(true));
                    AuditLog.Tulis("Ekspor karyawan", tampil.Count + " baris");
                    MessageBox.Show("Selesai:\r\n" + dlg.FileName, "Ekspor CSV");
                }
                catch (Exception ex)
                {
                    MessageBox.Show("Gagal menyimpan: " + ex.Message, "Ekspor CSV", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                }
            }
        }
    }
}
