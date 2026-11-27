using System;
using System.Collections.Generic;
using System.Data.SQLite;
using System.Globalization;

namespace HrisDeviceTool.Data
{
    // Menyimpan hasil Info mesin (baris: kelompok, item, nilai) ke tabel mesin.
    public static class InfoMesin
    {
        // { kolom, item, "1" bila angka }
        static readonly string[][] Peta = new string[][] {
            new string[] { "tipe", "Tipe (product code)", "0" },
            new string[] { "firmware", "Firmware", "0" },
            new string[] { "serial", "Serial", "0" },
            new string[] { "platform", "Platform", "0" },
            new string[] { "versi_jari", "Versi jari", "1" },
            new string[] { "versi_wajah", "Versi wajah", "1" },
            new string[] { "jumlah_user", "User", "1" },
            new string[] { "jumlah_admin", "Admin", "1" },
            new string[] { "jumlah_template_jari", "Template jari", "1" },
            new string[] { "jumlah_wajah", "Template wajah", "1" },
            new string[] { "jumlah_log", "Log absensi", "1" },
            new string[] { "kapasitas_jari", "Kapasitas jari", "1" },
            new string[] { "kapasitas_user", "Kapasitas user", "1" },
            new string[] { "kapasitas_log", "Kapasitas log", "1" },
            new string[] { "selisih_jam_detik", "Selisih dengan PC (detik)", "1" }
        };

        public static void Simpan(SQLiteConnection c, string mesin, string ip, List<string[]> rows)
        {
            Dictionary<string, string> nilai = new Dictionary<string, string>();
            foreach (string[] r in rows) { nilai[r[1]] = r[2]; }
            string waktu = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss", CultureInfo.InvariantCulture);
            using (SQLiteTransaction t = c.BeginTransaction())
            {
                using (SQLiteCommand a = new SQLiteCommand("insert or ignore into mesin (nama) values (@n)", c, t))
                {
                    a.Parameters.AddWithValue("@n", mesin);
                    a.ExecuteNonQuery();
                }
                string set = "ip=@ip, info_diambil=@t";
                foreach (string[] p in Peta) { set += ", " + p[0] + "=@" + p[0]; }
                using (SQLiteCommand u = new SQLiteCommand("update mesin set " + set + " where nama=@n", c, t))
                {
                    u.Parameters.AddWithValue("@n", mesin);
                    u.Parameters.AddWithValue("@ip", ip ?? "");
                    u.Parameters.AddWithValue("@t", waktu);
                    foreach (string[] p in Peta)
                    {
                        string s;
                        object v = DBNull.Value;
                        // Nilai gagal baca diawali "(" dan disimpan kosong, bukan angka palsu.
                        if (nilai.TryGetValue(p[1], out s) && s != null)
                        {
                            s = s.Trim('\0', ' ');
                            long angka;
                            if (s.Length > 0 && !s.StartsWith("(", StringComparison.Ordinal))
                            {
                                if (p[2] == "0") { v = s; }
                                else if (long.TryParse(s, out angka)) { v = angka; }
                            }
                        }
                        u.Parameters.AddWithValue("@" + p[0], v);
                    }
                    u.ExecuteNonQuery();
                }
                t.Commit();
            }
        }
    }
}
