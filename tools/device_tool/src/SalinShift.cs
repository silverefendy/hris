using System;
using System.Collections.Generic;
using System.Data.SQLite;
using System.Drawing;
using System.Globalization;
using System.Text;
using System.Text.RegularExpressions;
using System.Windows.Forms;
using HrisDeviceTool.Data;

namespace HrisDeviceTool
{
    // Tombol "Salin shift dari HRIS": mengambil jadwal (hanya baca di server) lalu menyimpannya lokal.
    public static class SalinShift
    {
        const string Jalur = "/api/method/hris.hris_attendance.integrations.shift_api.get_jadwal_shift";
        const string Judul = "Salin shift dari HRIS";

        static bool TanyaRentang(IWin32Window pemilik, out DateTime dari, out DateTime sampai)
        {
            DateTime h = DateTime.Today;
            DateTime awal = new DateTime(h.Year, h.Month, 1);
            dari = awal;
            sampai = awal.AddMonths(1).AddDays(-1);
            using (Form f = new Form())
            {
                f.Text = Judul;
                f.FormBorderStyle = FormBorderStyle.FixedDialog;
                f.StartPosition = FormStartPosition.CenterParent;
                f.MaximizeBox = false;
                f.MinimizeBox = false;
                f.ClientSize = new Size(420, 150);

                Label l1 = new Label();
                l1.Text = "Rentang tanggal (maksimal " + ShiftDb.MaksHari + " hari):";
                l1.AutoSize = true;
                l1.Location = new Point(12, 12);
                f.Controls.Add(l1);

                DateTimePicker d1 = Tgl(12, 38, dari);
                f.Controls.Add(d1);
                Label l2 = new Label();
                l2.Text = "s/d";
                l2.AutoSize = true;
                l2.Location = new Point(150, 42);
                f.Controls.Add(l2);
                DateTimePicker d2 = Tgl(190, 38, sampai);
                f.Controls.Add(d2);

                Label l3 = new Label();
                l3.Text = "Jadwal lokal pada rentang ini akan diganti.";
                l3.AutoSize = true;
                l3.Location = new Point(12, 74);
                f.Controls.Add(l3);

                Button ok = new Button();
                ok.Text = "Salin";
                ok.DialogResult = DialogResult.OK;
                ok.Location = new Point(222, 108);
                ok.Size = new Size(90, 28);
                f.Controls.Add(ok);
                Button batal = new Button();
                batal.Text = "Batal";
                batal.DialogResult = DialogResult.Cancel;
                batal.Location = new Point(318, 108);
                batal.Size = new Size(90, 28);
                f.Controls.Add(batal);
                f.AcceptButton = ok;
                f.CancelButton = batal;

                if (f.ShowDialog(pemilik) != DialogResult.OK) { return false; }
                dari = d1.Value.Date;
                sampai = d2.Value.Date;
                return true;
            }
        }

        static DateTimePicker Tgl(int x, int y, DateTime nilai)
        {
            DateTimePicker d = new DateTimePicker();
            d.Format = DateTimePickerFormat.Custom;
            d.CustomFormat = "dd-MM-yyyy";
            d.Width = 120;
            d.Location = new Point(x, y);
            d.Value = nilai;
            return d;
        }

        static string PesanGagal(int kode, string isi)
        {
            if (kode == 0) { return "Tidak dapat terhubung ke server: " + KirimHris.Potong(isi, 300); }
            if (kode == 401)
            {
                return "Token ditolak (HTTP 401). Periksa token dan saklar Agent Enabled di HRIS.\r\n"
                    + "Jangan diulang berkali-kali: 10 kegagalan dalam 10 menit memblokir IP ini sementara.";
            }
            Match m = Regex.Match(isi ?? "", "\"exception\"\\s*:\\s*\"((?:[^\"\\\\]|\\\\.)*)\"");
            string rinci = m.Success ? m.Groups[1].Value : isi;
            return "Server menolak permintaan (HTTP " + kode + "): " + KirimHris.Potong(rinci, 400)
                + "\r\n\r\nBila pesan menyebut shift_api tidak ditemukan: pastikan berkas ada di server itu lalu restart bench.";
        }

        public static void Jalankan(Form pemilik, Store st)
        {
            string url = (st.Data.UrlHris ?? "").Trim().TrimEnd('/');
            string token = HrisToken.Ambil(st);
            if (url.Length == 0 || token == null)
            {
                MessageBox.Show(pemilik, "Alamat server atau token belum ada di PC ini.\r\nIsi lewat Pengaturan > Koneksi HRIS (administrator).", Judul);
                return;
            }
            DateTime dari, sampai;
            if (!TanyaRentang(pemilik, out dari, out sampai)) { return; }
            int hari = (sampai - dari).Days + 1;
            if (hari < 1 || hari > ShiftDb.MaksHari)
            {
                MessageBox.Show(pemilik, "Rentang harus 1 sampai " + ShiftDb.MaksHari + " hari, dan tanggal akhir tidak boleh sebelum tanggal awal.", Judul);
                return;
            }
            Cursor lama = pemilik.Cursor;
            try
            {
                pemilik.Cursor = Cursors.WaitCursor;
                KirimHris.SiapkanJaringan(url);
                string body = "{\"dari\":\"" + dari.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture)
                    + "\",\"sampai\":\"" + sampai.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture) + "\"}";
                int kode;
                string resp = KirimHris.Post(url + Jalur, token, body, 120000, out kode);
                if (kode != 200)
                {
                    pemilik.Cursor = lama;
                    AuditLog.Tulis(Judul, "gagal, HTTP " + kode);
                    MessageBox.Show(pemilik, PesanGagal(kode, resp), Judul, MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    return;
                }
                JadwalHris j = ShiftDb.BacaRespons(resp);
                using (SQLiteConnection c = HdtDatabase.Buka(HdtDatabase.BerkasDefault()))
                {
                    ShiftDb.Simpan(c, j, DateTime.Now);
                }
                string ringkas = j.Baris.Count + " baris jadwal, " + j.Diproses + " karyawan, " + j.Shift.Count + " shift ("
                    + j.Dari.ToString("dd-MM-yyyy") + " s/d " + j.Sampai.ToString("dd-MM-yyyy") + ")";
                AuditLog.Tulis(Judul, ringkas);
                StringBuilder sb = new StringBuilder("Selesai disimpan:\r\n" + ringkas);
                foreach (string p in j.Peringatan) { sb.Append("\r\n\r\nPeringatan: " + p); }
                pemilik.Cursor = lama;
                MessageBox.Show(pemilik, sb.ToString(), Judul);
            }
            catch (Exception ex)
            {
                pemilik.Cursor = lama;
                AuditLog.Tulis(Judul, "gagal: " + ex.Message);
                MessageBox.Show(pemilik, "Salin shift GAGAL: " + ex.Message, Judul, MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
            finally { pemilik.Cursor = lama; }
        }
    }
}