using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Text;
using System.Text.RegularExpressions;
using System.Windows.Forms;

namespace HrisDeviceTool
{
    // Kirim snapshot daftar user satu mesin ke HRIS (endpoint push_device_users).
    // Template jari TIDAK dikirim: hanya jumlah jari yang dihitung dari hash yang terbaca.
    public class KirimUserForm : Form
    {
        const string Jalur = "/api/method/hris.hris_attendance.integrations.device_user_api.push_device_users";
        const int UkuranBatch = 500;
        const int TimeoutDetik = 120;

        Store st;
        Func<MesinItem, object> opener;
        ComboBox cmb;
        Label lblTujuan, lblStatus;
        Button btnKirim, btnBatal, btnTutup;
        bool jalan = false, batal = false;

        public KirimUserForm(Store store, Func<MesinItem, object> bukaMesin)
        {
            st = store;
            opener = bukaMesin;
            Text = "Kirim user ke HRIS";
            FormBorderStyle = FormBorderStyle.FixedDialog;
            StartPosition = FormStartPosition.CenterParent;
            MinimizeBox = false;
            MaximizeBox = false;
            ClientSize = new Size(520, 235);

            Label l1 = new Label();
            l1.Text = "Mesin (daftar di aplikasi ini)";
            l1.Location = new Point(12, 12);
            l1.AutoSize = true;

            cmb = new ComboBox();
            cmb.DropDownStyle = ComboBoxStyle.DropDownList;
            cmb.Location = new Point(12, 32);
            cmb.Width = 496;
            foreach (MesinItem m in st.Data.Mesin) cmb.Items.Add(m);
            if (cmb.Items.Count > 0) cmb.SelectedIndex = 0;
            cmb.SelectedIndexChanged += delegate { UpdateTujuan(); };

            lblTujuan = new Label();
            lblTujuan.Location = new Point(12, 66);
            lblTujuan.Size = new Size(496, 54);
            lblTujuan.BorderStyle = BorderStyle.FixedSingle;

            lblStatus = new Label();
            lblStatus.Location = new Point(12, 130);
            lblStatus.Size = new Size(496, 44);
            lblStatus.Text = "Tombol ini membaca user (dan jumlah jari) dari mesin lalu mengirim ke HRIS. Template jari tidak dikirim.";

            btnKirim = new Button();
            btnKirim.Text = "Baca dan kirim";
            btnKirim.Location = new Point(12, 190);
            btnKirim.Size = new Size(150, 30);
            btnKirim.Click += delegate { OnKirim(); };

            btnBatal = new Button();
            btnBatal.Text = "Batal";
            btnBatal.Location = new Point(172, 190);
            btnBatal.Size = new Size(90, 30);
            btnBatal.Enabled = false;
            btnBatal.Click += delegate { batal = true; Status("Membatalkan..."); };

            btnTutup = new Button();
            btnTutup.Text = "Tutup";
            btnTutup.Location = new Point(418, 190);
            btnTutup.Size = new Size(90, 30);
            btnTutup.Click += delegate { if (!jalan) Close(); };

            Controls.Add(l1);
            Controls.Add(cmb);
            Controls.Add(lblTujuan);
            Controls.Add(lblStatus);
            Controls.Add(btnKirim);
            Controls.Add(btnBatal);
            Controls.Add(btnTutup);
            FormClosing += delegate (object s, FormClosingEventArgs e) { if (jalan) e.Cancel = true; };
            UpdateTujuan();
        }

        void UpdateTujuan()
        {
            MesinItem m = cmb.SelectedItem as MesinItem;
            string url = (st.Data.UrlHris ?? "").Trim();
            string nama = (m == null) ? "" : (m.NamaDiHris ?? "").Trim();
            lblTujuan.Text = "Tujuan server: " + (url.Length == 0 ? "(belum diatur)" : url) +
                "\r\nNama mesin di HRIS: " + (nama.Length == 0 ? "(belum diisi)" : nama);
        }

        void Status(string s)
        {
            lblStatus.Text = s;
            Application.DoEvents();
        }

        static string SafeNama(string s)
        {
            return Regex.Replace(s ?? "", "[^A-Za-z0-9_-]+", "_");
        }

        static int Ambil(string json, string kunci)
        {
            Match m = Regex.Match(json, "\"" + kunci + "\"\\s*:\\s*(\\d+)");
            return m.Success ? int.Parse(m.Groups[1].Value) : 0;
        }

        static string AmbilTeks(string json, string kunci)
        {
            Match m = Regex.Match(json, "\"" + kunci + "\"\\s*:\\s*\"([^\"]*)\"");
            return m.Success ? m.Groups[1].Value : "";
        }

        void OnKirim()
        {
            if (jalan) return;
            MesinItem m = cmb.SelectedItem as MesinItem;
            if (m == null) { MessageBox.Show("Pilih mesin dulu.", "Kirim user ke HRIS"); return; }
            string namaHris = (m.NamaDiHris ?? "").Trim();
            string url = (st.Data.UrlHris ?? "").Trim().TrimEnd('/');
            string tok = HrisToken.Ambil(st);
            if (url.Length == 0 || !HrisToken.Valid(tok))
            {
                MessageBox.Show("Alamat server atau token HRIS belum diatur.\r\nMinta administrator mengisinya lewat tombol Pengaturan HRIS.",
                    "Kirim user ke HRIS", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }
            if (namaHris.Length == 0)
            {
                MessageBox.Show("Nama mesin di HRIS belum diisi untuk mesin ini.\r\nIsi lewat tombol Ubah pada daftar mesin.",
                    "Kirim user ke HRIS", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }
            jalan = true;
            batal = false;
            btnKirim.Enabled = false;
            btnBatal.Enabled = true;
            cmb.Enabled = false;
            try
            {
                Jalankan(m, namaHris, url, tok);
            }
            catch (Exception ex)
            {
                AuditLog.Tulis("Kirim user HRIS", "GAGAL " + m.Nama + ": " + ex.Message);
                MessageBox.Show(ex.Message, "Kirim user ke HRIS", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
            finally
            {
                jalan = false;
                btnKirim.Enabled = true;
                btnBatal.Enabled = false;
                cmb.Enabled = true;
                Cursor = Cursors.Default;
            }
        }

        void Jalankan(MesinItem m, string namaHris, string url, string tok)
        {
            // 1. Baca dari mesin (hanya membaca)
            object zk = opener(m);
            if (zk == null) return;
            Dictionary<string, UserData> data;
            try
            {
                data = BacaSemua.Baca(zk, delegate { return batal; },
                    delegate (string s) { Status("Membaca " + m.Nama + ": " + s); });
            }
            finally
            {
                Dev.Disconnect(zk);
                Cursor = Cursors.Default;
            }
            if (data == null)
            {
                Status("Dibatalkan saat membaca. Tidak ada yang dikirim.");
                AuditLog.Tulis("Kirim user HRIS", "dibatalkan saat membaca " + m.Nama);
                return;
            }
            if (data.Count == 0)
            {
                Status("Tidak ada user terbaca. Tidak ada yang dikirim.");
                AuditLog.Tulis("Kirim user HRIS", "0 user terbaca dari " + m.Nama + ", tidak dikirim");
                MessageBox.Show("Tidak ada user terbaca dari mesin.\r\nTidak ada yang dikirim (mencegah snapshot kosong menandai semua user hilang).\r\nPeriksa koneksi lalu coba lagi.",
                    "Kirim user ke HRIS", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return;
            }

            List<UserData> daftar = new List<UserData>(data.Values);
            daftar.Sort(delegate (UserData a, UserData b)
            {
                if (a.Id.Length != b.Id.Length) return a.Id.Length.CompareTo(b.Id.Length);
                return string.CompareOrdinal(a.Id, b.Id);
            });
            int totalJari = 0;
            foreach (UserData u in daftar) totalJari += u.Jari.Count;

            // 2. Simpan salinan CSV (tanpa template jari)
            string folder = Path.Combine(st.DataDir, "user");
            Directory.CreateDirectory(folder);
            string csv = Path.Combine(folder, "user_" + SafeNama(m.Nama) + "_" + DateTime.Now.ToString("yyyyMMdd_HHmmss") + ".csv");
            StringBuilder sbc = new StringBuilder();
            sbc.AppendLine("device_user_id;nama;privilege;aktif;jumlah_jari");
            foreach (UserData u in daftar)
                sbc.AppendLine(u.Id + ";" + u.Nama.Replace(";", ",") + ";" + u.Priv + ";" + (u.Aktif ? 1 : 0) + ";" + u.Jari.Count);
            File.WriteAllText(csv, sbc.ToString(), new UTF8Encoding(true));
            AuditLog.Tulis("Kirim user HRIS", "baca " + daftar.Count + " user dari " + m.Nama + ", salinan " + csv);

            // 3. Konfirmasi dengan tujuan yang jelas
            string tanya = "Terbaca " + daftar.Count.ToString("N0") + " user (" + totalJari.ToString("N0") + " jari) dari " + m.Nama + ".\r\n\r\n" +
                "Kirim ke server:\r\n" + url + "\r\nsebagai mesin HRIS: " + namaHris + "\r\n\r\n" +
                "Template jari tidak dikirim, hanya jumlah jari.\r\n" +
                "Kirim ulang aman: user yang sama diperbarui, bukan digandakan.\r\n" +
                "Salinan CSV: " + csv;
            if (MessageBox.Show(tanya, "Kirim user ke HRIS", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes)
            {
                Status("Tidak dikirim (dibatalkan di konfirmasi). Salinan CSV tetap tersimpan.");
                AuditLog.Tulis("Kirim user HRIS", "tidak dikirim (konfirmasi ditolak) " + m.Nama);
                return;
            }

            // 4. Kirim per batch
            string snap = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
            int batchTotal = (daftar.Count + UkuranBatch - 1) / UkuranBatch;
            int created = 0, updated = 0, unchanged = 0, error = 0, absen = 0;
            string site = "";
            string henti = "";
            bool penandaDijalankan = false;
            for (int b = 0; b < batchTotal; b++)
            {
                if (batal) { henti = "Dibatalkan sebelum batch " + (b + 1) + "."; break; }
                int dari = b * UkuranBatch;
                int sampai = Math.Min(dari + UkuranBatch, daftar.Count);
                bool terakhir = (b == batchTotal - 1);
                bool isLast = terakhir && error == 0;
                Status("Mengirim batch " + (b + 1) + " dari " + batchTotal + " (" + (sampai - dari) + " user)...");
                string body = BuatBody(namaHris, daftar, dari, sampai, snap, isLast);
                int kode;
                string res = KirimHris.Post(url + Jalur, tok, body, TimeoutDetik * 1000, out kode);
                if (kode != 200)
                {
                    henti = "Batch " + (b + 1) + " gagal (HTTP " + kode + "): " + KirimHris.Potong(res, 300);
                    break;
                }
                string atas = Regex.Replace(res, "\"results\"\\s*:\\s*\\[.*?\\]", "\"results\":[]", RegexOptions.Singleline);
                created += Ambil(atas, "created");
                updated += Ambil(atas, "updated");
                unchanged += Ambil(atas, "unchanged");
                error += Ambil(atas, "error");
                absen += Ambil(atas, "marked_absent");
                string s2 = AmbilTeks(atas, "site");
                if (s2.Length > 0) site = s2;
                if (isLast) penandaDijalankan = true;
            }

            string ringkas = "Mesin " + m.Nama + " -> HRIS \"" + namaHris + "\"\r\n" +
                "Dibuat " + created + " | diperbarui " + updated + " | sama " + unchanged + " | error " + error +
                " | ditandai hilang " + absen + "\r\n" +
                "Site tujuan (dari server): " + (site.Length > 0 ? site : "(server tidak melaporkan)");
            if (henti.Length > 0) ringkas = henti + "\r\n\r\n" + ringkas + "\r\n\r\nPenanda 'hilang dari snapshot' TIDAK dijalankan.";
            else if (!penandaDijalankan) ringkas += "\r\n\r\nAda baris error pada batch sebelumnya, penanda 'hilang dari snapshot' tidak dijalankan.";
            AuditLog.Tulis("Kirim user HRIS", ringkas.Replace("\r\n", " | "));
            Status(ringkas.Replace("\r\n", "   "));
            MessageBox.Show(ringkas, "Kirim user ke HRIS", MessageBoxButtons.OK,
                (henti.Length > 0 || error > 0) ? MessageBoxIcon.Warning : MessageBoxIcon.Information);
        }

        static string BuatBody(string namaHris, List<UserData> daftar, int dari, int sampai, string snap, bool isLast)
        {
            StringBuilder sb = new StringBuilder();
            sb.Append("{\"device\":\"").Append(KirimHris.Esc(namaHris)).Append("\",");
            sb.Append("\"snapshot_at\":\"").Append(snap).Append("\",");
            sb.Append("\"is_last\":").Append(isLast ? 1 : 0).Append(",\"users\":[");
            for (int i = dari; i < sampai; i++)
            {
                UserData u = daftar[i];
                if (i > dari) sb.Append(",");
                sb.Append("{\"device_user_id\":\"").Append(KirimHris.Esc(u.Id)).Append("\",");
                sb.Append("\"name\":\"").Append(KirimHris.Esc(u.Nama)).Append("\",");
                sb.Append("\"privilege\":").Append(u.Priv).Append(",");
                sb.Append("\"enabled\":").Append(u.Aktif ? 1 : 0).Append(",");
                sb.Append("\"finger_count\":").Append(u.Jari.Count).Append("}");
            }
            sb.Append("]}");
            return sb.ToString();
        }
    }
}