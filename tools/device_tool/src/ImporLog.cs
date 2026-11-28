using System;
using System.Collections.Generic;
using System.Data.SQLite;
using System.Globalization;
using System.IO;
using System.Security.Cryptography;
using System.Text;

namespace HrisDeviceTool.Data
{
    public class HasilImporLog
    {
        public int BerkasDiimpor;
        public int BerkasDilewati;
        public long Terbaca;
        public long Baru;
        public long Rusak;
        public List<string> Catatan = new List<string>();
    }

    // Mengimpor salinan CSV tarikan (dengan manifest .hdtman) ke tabel log_absensi.
    // Hanya membaca berkas; tidak mengubah atau menghapus berkas dan tidak menyentuh mesin.
    public static class ImporLog
    {
        public static HasilImporLog Folder(SQLiteConnection c, string folder, Action<string> progres)
        {
            HasilImporLog h = new HasilImporLog();
            string[] man = Directory.GetFiles(folder, "*.hdtman");
            Array.Sort(man, StringComparer.Ordinal);
            foreach (string m in man)
            {
                string csv = Path.Combine(folder, Path.GetFileNameWithoutExtension(m) + ".csv");
                try { Satu(c, m, csv, h, progres); }
                catch (Exception e)
                {
                    h.BerkasDilewati++;
                    h.Catatan.Add(Path.GetFileName(csv) + ": GAGAL (" + e.Message + ")");
                }
            }
            return h;
        }

        static void Satu(SQLiteConnection c, string berkasMan, string csv, HasilImporLog h, Action<string> progres)
        {
            string nama = Path.GetFileName(csv);
            if (!File.Exists(csv))
            {
                h.BerkasDilewati++;
                h.Catatan.Add(nama + ": CSV tidak ada, dilewati");
                return;
            }
            Dictionary<string, string> man = BacaManifest(berkasMan);
            string mesin, sha;
            man.TryGetValue("mesin", out mesin);
            man.TryGetValue("sha256", out sha);
            if (string.IsNullOrEmpty(mesin) || string.IsNullOrEmpty(sha))
            {
                h.BerkasDilewati++;
                h.Catatan.Add(nama + ": manifest tanpa mesin atau sha256, dilewati");
                return;
            }
            if (SudahDiimpor(c, nama)) { h.BerkasDilewati++; return; }
            if (!string.Equals(HashFile(csv), sha.Trim(), StringComparison.OrdinalIgnoreCase))
            {
                h.BerkasDilewati++;
                h.Catatan.Add(nama + ": sha256 tidak cocok dengan manifest, dilewati");
                return;
            }

            List<BarisLog> baris = new List<BarisLog>();
            long rusak = 0;
            using (StreamReader r = new StreamReader(csv, Encoding.UTF8))
            {
                string head = r.ReadLine();
                if (head == null || !head.StartsWith("device_user_id;punch_time", StringComparison.Ordinal))
                {
                    h.BerkasDilewati++;
                    h.Catatan.Add(nama + ": judul kolom tidak dikenal, dilewati");
                    return;
                }
                string line;
                while ((line = r.ReadLine()) != null)
                {
                    if (line.Length == 0) { continue; }
                    string[] f = line.Split(';');
                    DateTime w;
                    int v, s, k;
                    if (f.Length < 5 || f[0].Trim().Length == 0 ||
                        !DateTime.TryParseExact(f[1].Trim(), "yyyy-MM-dd HH:mm:ss", CultureInfo.InvariantCulture, DateTimeStyles.None, out w) ||
                        !int.TryParse(f[2], out v) || !int.TryParse(f[3], out s) || !int.TryParse(f[4], out k))
                    {
                        rusak++;
                        continue;
                    }
                    BarisLog b = new BarisLog();
                    b.Id = f[0].Trim();
                    b.Waktu = w;
                    b.Verifikasi = v;
                    b.Status = s;
                    b.WorkCode = k;
                    baris.Add(b);
                }
            }
            h.Rusak += rusak;
            if (rusak > 0) { h.Catatan.Add(nama + ": " + rusak + " baris rusak dilewati"); }
            if (baris.Count == 0)
            {
                h.BerkasDilewati++;
                h.Catatan.Add(nama + ": tidak ada baris valid, dilewati");
                return;
            }
            if (progres != null) { progres("Impor " + nama + ": " + baris.Count + " baris"); }
            HasilSimpan hs = LogDb.Simpan(c, mesin, baris, "impor-csv", -1, nama);
            h.BerkasDiimpor++;
            h.Terbaca += hs.Terbaca;
            h.Baru += hs.Baru;
        }

        static bool SudahDiimpor(SQLiteConnection c, string namaCsv)
        {
            using (SQLiteCommand cmd = new SQLiteCommand(
                "SELECT COUNT(*) FROM tarikan_log WHERE sumber = 'impor-csv' AND berhasil = 1 AND catatan = @f", c))
            {
                cmd.Parameters.AddWithValue("@f", namaCsv);
                return Convert.ToInt64(cmd.ExecuteScalar()) > 0;
            }
        }

        static Dictionary<string, string> BacaManifest(string berkas)
        {
            Dictionary<string, string> d = new Dictionary<string, string>();
            foreach (string line in File.ReadAllLines(berkas, Encoding.UTF8))
            {
                int i = line.IndexOf('=');
                if (i <= 0) { continue; }
                d[line.Substring(0, i).Trim()] = line.Substring(i + 1).Trim();
            }
            return d;
        }

        static string HashFile(string path)
        {
            using (SHA256 sha = SHA256.Create())
            using (FileStream fs = File.OpenRead(path))
            {
                byte[] b = sha.ComputeHash(fs);
                StringBuilder sb = new StringBuilder();
                foreach (byte x in b) { sb.Append(x.ToString("x2")); }
                return sb.ToString();
            }
        }
    }
}