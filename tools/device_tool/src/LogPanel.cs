using System;
using System.Collections.Generic;
using System.Data.SQLite;
using System.Drawing;
using System.Globalization;
using System.IO;
using System.Text;
using System.Windows.Forms;
using HrisDeviceTool.Data;

namespace HrisDeviceTool
{
    // Layar lihat log absensi dari database lokal: Rincian, Rekap, Status mesin. Hanya membaca.
    public class LogPanel : Panel
    {
        const int BatasRincian = 5000;
        DateTimePicker dtDari, dtSampai;
        ComboBox cmbMesin;
        TextBox txtCari;
        CheckBox chkNol;
        Label lblPeringatan, lblInfo;
        TabControl sub;
        DataGridView gRincian, gRekap, gStatus;
        List<RincianTap> rincian = new List<RincianTap>();
        List<RekapOrang> rekap = new List<RekapOrang>();
        List<RincianTap> rincianTampil = new List<RincianTap>();
        List<RekapOrang> rekapTampil = new List<RekapOrang>();
        Dictionary<string, Karyawan> orang = new Dictionary<string, Karyawan>(StringComparer.Ordinal);
        bool sibuk;

        public LogPanel()
        {
            Panel b1 = new Panel();
            b1.Dock = DockStyle.Top;
            b1.Height = 34;
            b1.Controls.Add(Lbl("Dari", 0, 9));
            dtDari = Tgl(34, 5);
            b1.Controls.Add(dtDari);
            b1.Controls.Add(Lbl("Sampai", 160, 9));
            dtSampai = Tgl(210, 5);
            b1.Controls.Add(dtSampai);
            b1.Controls.Add(Tbl("Bulan ini", 340, 90, delegate { Rentang(0); }));
            b1.Controls.Add(Tbl("Bulan lalu", 436, 90, delegate { Rentang(1); }));
            b1.Controls.Add(Tbl("7 hari terakhir", 532, 120, delegate { Rentang(2); }));
            b1.Controls.Add(Tbl("Muat ulang", 658, 100, delegate { Muat(); }));

            Panel b2 = new Panel();
            b2.Dock = DockStyle.Top;
            b2.Height = 34;
            b2.Controls.Add(Lbl("Mesin", 0, 9));
            cmbMesin = new ComboBox();
            cmbMesin.DropDownStyle = ComboBoxStyle.DropDownList;
            cmbMesin.Location = new Point(45, 5);
            cmbMesin.Width = 170;
            b2.Controls.Add(cmbMesin);
            b2.Controls.Add(Lbl("Cari", 230, 9));
            txtCari = new TextBox();
            txtCari.Location = new Point(265, 5);
            txtCari.Width = 200;
            b2.Controls.Add(txtCari);
            chkNol = new CheckBox();
            chkNol.Text = "Hanya yang tidak pernah tap";
            chkNol.AutoSize = true;
            chkNol.Location = new Point(480, 8);
            b2.Controls.Add(chkNol);
            b2.Controls.Add(Tbl("Ekspor CSV", 700, 100, delegate { if (!Peran.Boleh("OnEksporLog")) return; AuditLog.Kat = "tarik-log"; Ekspor(); }));

            lblPeringatan = new Label();
            lblPeringatan.Dock = DockStyle.Top;
            lblPeringatan.Height = 22;
            lblPeringatan.TextAlign = ContentAlignment.MiddleLeft;
            lblPeringatan.AutoEllipsis = true;
            lblPeringatan.UseMnemonic = false;
            lblInfo = new Label();
            lblInfo.Dock = DockStyle.Top;
            lblInfo.Height = 22;
            lblInfo.TextAlign = ContentAlignment.MiddleLeft;
            lblInfo.AutoEllipsis = true;
            lblInfo.UseMnemonic = false;

            sub = new TabControl();
            sub.Dock = DockStyle.Fill;
            TabPage t1 = new TabPage("Rincian");
            gRincian = Gaya.Tabel(new string[] { "ID", "Nama", "Departemen", "Waktu", "Mesin", "Verifikasi", "Status", "Workcode" },
                new int[] { 50, 140, 100, 130, 90, 60, 50, 60 });
            gRincian.Dock = DockStyle.Fill;
            UrutAngka(gRincian, 0, 5, 6, 7);
            t1.Controls.Add(gRincian);
            TabPage t2 = new TabPage("Rekap");
            gRekap = Gaya.Tabel(new string[] { "ID", "Nama", "Departemen", "Jumlah tap", "Hari hadir", "Tap terakhir", "Catatan" },
                new int[] { 50, 150, 110, 60, 60, 130, 150 });
            gRekap.Dock = DockStyle.Fill;
            UrutAngka(gRekap, 0, 3, 4);
            t2.Controls.Add(gRekap);
            TabPage t3 = new TabPage("Status mesin");
            gStatus = Gaya.Tabel(new string[] { "Mesin", "Tap di database", "Tap terbaru", "Terakhir ditarik", "Log di mesin", "Kapasitas", "Terpakai", "Selisih jam (dtk)", "Info diambil", "Peringatan" },
                new int[] { 80, 60, 120, 120, 60, 60, 55, 60, 120, 200 });
            gStatus.Dock = DockStyle.Fill;
            UrutAngka(gStatus, 1, 4, 5);
            t3.Controls.Add(gStatus);
            sub.TabPages.Add(t1);
            sub.TabPages.Add(t2);
            sub.TabPages.Add(t3);

            // Urutan penambahan menentukan susunan Dock: yang Fill lebih dulu.
            Controls.Add(sub);
            Controls.Add(lblInfo);
            Controls.Add(lblPeringatan);
            Controls.Add(b2);
            Controls.Add(b1);

            sibuk = true;
            DateTime h = DateTime.Today;
            dtDari.Value = new DateTime(h.Year, h.Month, 1);
            dtSampai.Value = h;
            sibuk = false;
            dtDari.ValueChanged += delegate { if (!sibuk) Muat(); };
            dtSampai.ValueChanged += delegate { if (!sibuk) Muat(); };
            cmbMesin.SelectedIndexChanged += delegate { if (!sibuk) Muat(); };
            txtCari.TextChanged += delegate { Tampil(); };
            chkNol.CheckedChanged += delegate { Tampil(); };
        }

        static Label Lbl(string t, int x, int y)
        {
            Label l = new Label();
            l.Text = t;
            l.AutoSize = true;
            l.Location = new Point(x, y);
            return l;
        }

        static DateTimePicker Tgl(int x, int y)
        {
            DateTimePicker d = new DateTimePicker();
            d.Format = DateTimePickerFormat.Custom;
            d.CustomFormat = "dd-MM-yyyy";
            d.Location = new Point(x, y);
            d.Width = 110;
            return d;
        }

        static Button Tbl(string teks, int x, int w, EventHandler h)
        {
            Button b = Gaya.Tombol(teks, w, h);
            b.Location = new Point(x, 2);
            return b;
        }

        static void UrutAngka(DataGridView g, params int[] kolom)
        {
            g.SortCompare += delegate (object o, DataGridViewSortCompareEventArgs e)
            {
                if (Array.IndexOf(kolom, e.Column.Index) < 0) return;
                long a, b;
                if (long.TryParse(Convert.ToString(e.CellValue1), out a) && long.TryParse(Convert.ToString(e.CellValue2), out b))
                {
                    e.SortResult = a.CompareTo(b);
                    e.Handled = true;
                }
            };
        }

        void Rentang(int jenis)
        {
            DateTime h = DateTime.Today;
            DateTime dari, sampai;
            if (jenis == 0) { dari = new DateTime(h.Year, h.Month, 1); sampai = h; }
            else if (jenis == 1)
            {
                dari = new DateTime(h.Year, h.Month, 1).AddMonths(-1);
                sampai = dari.AddMonths(1).AddDays(-1);
            }
            else { dari = h.AddDays(-6); sampai = h; }
            sibuk = true;
            dtDari.Value = dari;
            dtSampai.Value = sampai;
            sibuk = false;
            Muat();
        }

        public void Muat()
        {
            if (sibuk) return;
            sibuk = true;
            Cursor = Cursors.WaitCursor;
            try
            {
                string berkas = HdtDatabase.BerkasDefault();
                if (!File.Exists(berkas)) { lblInfo.Text = "Database belum ada."; return; }
                DateTime dari = dtDari.Value.Date;
                DateTime sampai = dtSampai.Value.Date.AddDays(1);
                if (sampai <= dari) { lblInfo.Text = "Tanggal Sampai harus sama dengan atau setelah Dari."; return; }
                using (SQLiteConnection c = HdtDatabase.Buka(berkas))
                {
                    orang = new Dictionary<string, Karyawan>(StringComparer.Ordinal);
                    foreach (Karyawan k in DaftarKaryawan.Muat(c)) { orang[k.Id] = k; }
                    List<StatusMesin> status = LaporanLog.Status(c, DateTime.Now);
                    IsiPilihanMesin(status);
                    string mesin = cmbMesin.SelectedIndex > 0 ? (string)cmbMesin.SelectedItem : null;
                    rincian = LaporanLog.Rincian(c, dari, sampai, mesin);
                    rekap = LaporanLog.Rekap(c, dari, sampai, mesin, orang);
                    IsiStatus(status);
                    if (status.Count == 0)
                    {
                        lblPeringatan.Text = "Belum ada log di database. Gunakan Tarik log mesin atau Impor CSV ke database.";
                        lblPeringatan.ForeColor = Color.Firebrick;
                    }
                    else
                    {
                        List<string> belum = LaporanLog.MesinBelumLengkap(status, mesin, sampai, DateTime.Now);
                        if (belum.Count > 0)
                        {
                            lblPeringatan.Text = "Perhatian: log terbaru mesin " + string.Join(", ", belum.ToArray()) + " jauh sebelum akhir periode (belum ditarik?). Jumlah tap dan \"tidak pernah tap\" bisa kurang.";
                            lblPeringatan.ForeColor = Color.Firebrick;
                        }
                        else
                        {
                            lblPeringatan.Text = "Semua mesin yang dipilih punya log sampai akhir periode.";
                            lblPeringatan.ForeColor = Color.DarkGreen;
                        }
                    }
                }
                Tampil();
            }
            catch (Exception ex)
            {
                lblInfo.Text = "Gagal memuat log: " + ex.Message;
            }
            finally
            {
                Cursor = Cursors.Default;
                sibuk = false;
            }
        }

        void IsiPilihanMesin(List<StatusMesin> status)
        {
            string ingat = cmbMesin.SelectedIndex > 0 ? (string)cmbMesin.SelectedItem : null;
            cmbMesin.Items.Clear();
            cmbMesin.Items.Add("Semua mesin");
            foreach (StatusMesin s in status) { cmbMesin.Items.Add(s.Mesin); }
            int idx = ingat == null ? 0 : cmbMesin.Items.IndexOf(ingat);
            cmbMesin.SelectedIndex = idx < 0 ? 0 : idx;
        }

        static string Teks(long? v)
        {
            return v.HasValue ? v.Value.ToString(CultureInfo.InvariantCulture) : "-";
        }

        void IsiStatus(List<StatusMesin> status)
        {
            gStatus.Rows.Clear();
            foreach (StatusMesin s in status)
            {
                int n = gStatus.Rows.Add(s.Mesin, s.TapDiDb, s.TapTerbaru.Length > 0 ? s.TapTerbaru : "-",
                    s.TerakhirDitarik.Length > 0 ? s.TerakhirDitarik : "-", Teks(s.LogDiMesin), Teks(s.Kapasitas),
                    s.Persen >= 0 ? s.Persen + "%" : "-", Teks(s.SelisihJam), s.InfoDiambil.Length > 0 ? s.InfoDiambil : "-", s.TeksPeringatan);
                if (s.Peringatan.Count > 0) { gStatus.Rows[n].Cells[9].Style.BackColor = Gaya.Oranye; }
            }
            gStatus.ClearSelection();
        }

        static bool Ada(string teks, string cari)
        {
            return teks.IndexOf(cari, StringComparison.OrdinalIgnoreCase) >= 0;
        }

        bool CocokOrang(string id, string q)
        {
            if (q.Length == 0 || Ada(id, q)) return true;
            Karyawan k;
            if (orang.TryGetValue(id, out k)) { return Ada(k.Nama, q) || Ada(k.Departemen, q); }
            return false;
        }

        void Tampil()
        {
            string q = txtCari.Text.Trim();
            rincianTampil = new List<RincianTap>();
            foreach (RincianTap t in rincian) { if (CocokOrang(t.Id, q)) rincianTampil.Add(t); }
            rekapTampil = new List<RekapOrang>();
            foreach (RekapOrang x in rekap)
            {
                if (chkNol.Checked && x.Tap != 0) continue;
                if (q.Length > 0 && !Ada(x.Id, q) && !Ada(x.Nama, q) && !Ada(x.Departemen, q)) continue;
                rekapTampil.Add(x);
            }

            gRincian.SuspendLayout();
            gRincian.Rows.Clear();
            List<DataGridViewRow> baris = new List<DataGridViewRow>();
            int n = 0;
            foreach (RincianTap t in rincianTampil)
            {
                if (n++ >= BatasRincian) break;
                Karyawan k;
                string nama = "", dept = "";
                if (orang.TryGetValue(t.Id, out k)) { nama = k.Nama; dept = k.Departemen; }
                DataGridViewRow r = new DataGridViewRow();
                r.CreateCells(gRincian, t.Id, nama, dept, t.Waktu, t.Mesin, t.Verifikasi, t.Status, t.WorkCode);
                baris.Add(r);
            }
            gRincian.Rows.AddRange(baris.ToArray());
            gRincian.ResumeLayout();
            gRincian.ClearSelection();

            gRekap.SuspendLayout();
            gRekap.Rows.Clear();
            List<DataGridViewRow> baris2 = new List<DataGridViewRow>();
            foreach (RekapOrang x in rekapTampil)
            {
                DataGridViewRow r = new DataGridViewRow();
                r.CreateCells(gRekap, x.Id, x.Nama, x.Departemen, x.Tap, x.Hari, x.Terakhir, x.Catatan);
                if (x.Catatan.Length > 0) r.Cells[6].Style.BackColor = Gaya.Oranye;
                baris2.Add(r);
            }
            gRekap.Rows.AddRange(baris2.ToArray());
            gRekap.ResumeLayout();
            gRekap.ClearSelection();

            int hadir = 0, nol = 0;
            foreach (RekapOrang x in rekap) { if (x.Tap > 0) hadir++; else nol++; }
            lblInfo.Text = "Periode " + dtDari.Value.ToString("dd-MM-yyyy") + " s/d " + dtSampai.Value.ToString("dd-MM-yyyy")
                + ": " + rincian.Count + " tap, " + hadir + " ID hadir, " + nol + " ID tidak pernah tap.   Rincian menampilkan "
                + gRincian.Rows.Count + " dari " + rincianTampil.Count + (rincianTampil.Count > BatasRincian ? " (dibatasi, ekspor memuat semua)" : "") + ".";
        }

        static string Sel(string s)
        {
            if (s == null) { s = ""; }
            if (s.Length > 0 && "=+-@\t\r".IndexOf(s[0]) >= 0) { s = "'" + s; }
            return "\"" + s.Replace("\"", "\"\"") + "\"";
        }

        string CsvRincian()
        {
            StringBuilder sb = new StringBuilder();
            sb.Append("ID;Nama;Departemen;Waktu;Mesin;Verifikasi;Status;Workcode\r\n");
            foreach (RincianTap t in rincianTampil)
            {
                Karyawan k;
                string nama = "", dept = "";
                if (orang.TryGetValue(t.Id, out k)) { nama = k.Nama; dept = k.Departemen; }
                sb.Append(Sel(t.Id)).Append(';').Append(Sel(nama)).Append(';').Append(Sel(dept)).Append(';')
                  .Append(t.Waktu).Append(';').Append(Sel(t.Mesin)).Append(';').Append(t.Verifikasi).Append(';')
                  .Append(t.Status).Append(';').Append(t.WorkCode).Append("\r\n");
            }
            return sb.ToString();
        }

        string CsvRekap()
        {
            StringBuilder sb = new StringBuilder();
            sb.Append("ID;Nama;Departemen;Jumlah tap;Hari hadir;Tap terakhir;Catatan\r\n");
            foreach (RekapOrang x in rekapTampil)
            {
                sb.Append(Sel(x.Id)).Append(';').Append(Sel(x.Nama)).Append(';').Append(Sel(x.Departemen)).Append(';')
                  .Append(x.Tap).Append(';').Append(x.Hari).Append(';').Append(x.Terakhir).Append(';').Append(Sel(x.Catatan)).Append("\r\n");
            }
            return sb.ToString();
        }

        void Ekspor()
        {
            if (sub.SelectedIndex > 1) { MessageBox.Show("Ekspor tersedia untuk tab Rincian dan Rekap.", "Ekspor CSV"); return; }
            bool rek = sub.SelectedIndex == 1;
            int jml = rek ? rekapTampil.Count : rincianTampil.Count;
            if (jml == 0) { MessageBox.Show("Tidak ada baris untuk diekspor.", "Ekspor CSV"); return; }
            if (MessageBox.Show("Berkas CSV berisi data pribadi karyawan. Simpan di tempat yang aman.\r\n\r\nLanjutkan?",
                "Ekspor CSV", MessageBoxButtons.YesNo, MessageBoxIcon.Warning) != DialogResult.Yes) return;
            using (SaveFileDialog dlg = new SaveFileDialog())
            {
                dlg.Title = "Ekspor " + (rek ? "rekap" : "rincian") + " log";
                dlg.Filter = "CSV (*.csv)|*.csv";
                dlg.FileName = (rek ? "rekap_log_" : "rincian_log_") + dtDari.Value.ToString("yyyyMMdd") + "_" + dtSampai.Value.ToString("yyyyMMdd") + ".csv";
                if (dlg.ShowDialog(this) != DialogResult.OK) return;
                try
                {
                    File.WriteAllText(dlg.FileName, rek ? CsvRekap() : CsvRincian(), new UTF8Encoding(true));
                    AuditLog.Tulis("Ekspor log", (rek ? "rekap " : "rincian ") + jml + " baris");
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