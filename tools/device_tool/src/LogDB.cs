using System;
using System.Collections.Generic;
using System.Data.SQLite;
using System.Globalization;

namespace HrisDeviceTool.Data
{
    public class BarisLog
    {
        public string Id = "";
        public DateTime Waktu;
        public int Verifikasi;
        public int Status;
        public int WorkCode;
    }

    public class HasilSimpan
    {
        public int Terbaca;
        public int Baru;
        public int Dilewati;
    }

    // Penyimpanan log absensi di SQLite. Hanya menambah baris; tidak pernah menghapus.
    public static class LogDb
    {
        const string Fmt = "yyyy-MM-dd HH:mm:ss";

        // Menyimpan hasil satu tarikan. diMesin: jumlah log menurut mesin, -1 bila tidak diketahui.
        public static HasilSimpan Simpan(SQLiteConnection c, string mesin, IList<BarisLog> baris,
            string sumber, int diMesin, string catatan)
        {
            if (string.IsNullOrEmpty(mesin)) { throw new ArgumentException("Nama mesin kosong."); }
            if (baris == null) { baris = new List<BarisLog>(); }
            HasilSimpan h = new HasilSimpan();
            h.Terbaca = baris.Count;
            string mulai = DateTime.Now.ToString(Fmt, CultureInfo.InvariantCulture);
            using (SQLiteTransaction t = c.BeginTransaction())
            {
                using (SQLiteCommand cmd = new SQLiteCommand(
                    "INSERT OR IGNORE INTO log_absensi (mesin, id_mesin, waktu, verifikasi, status, workcode, diambil) " +
                    "VALUES (@m, @i, @w, @v, @s, @k, @d)", c, t))
                {
                    SQLiteParameter pm = new SQLiteParameter("@m");
                    SQLiteParameter pi = new SQLiteParameter("@i");
                    SQLiteParameter pw = new SQLiteParameter("@w");
                    SQLiteParameter pv = new SQLiteParameter("@v");
                    SQLiteParameter ps = new SQLiteParameter("@s");
                    SQLiteParameter pk = new SQLiteParameter("@k");
                    SQLiteParameter pd = new SQLiteParameter("@d");
                    cmd.Parameters.Add(pm); cmd.Parameters.Add(pi); cmd.Parameters.Add(pw);
                    cmd.Parameters.Add(pv); cmd.Parameters.Add(ps); cmd.Parameters.Add(pk);
                    cmd.Parameters.Add(pd);
                    pm.Value = mesin;
                    pd.Value = mulai;
                    foreach (BarisLog b in baris)
                    {
                        pi.Value = b.Id;
                        pw.Value = b.Waktu.ToString(Fmt, CultureInfo.InvariantCulture);
                        pv.Value = b.Verifikasi;
                        ps.Value = b.Status;
                        pk.Value = b.WorkCode;
                        h.Baru += cmd.ExecuteNonQuery();
                    }
                }
                h.Dilewati = h.Terbaca - h.Baru;
                CatatRiwayat(c, t, mesin, mulai, h.Terbaca, h.Baru, diMesin, sumber, 1, catatan);
                t.Commit();
            }
            return h;
        }

        // Mencatat tarikan yang gagal (tanpa baris log).
        public static void CatatGagal(SQLiteConnection c, string mesin, string sumber, string catatan)
        {
            string mulai = DateTime.Now.ToString(Fmt, CultureInfo.InvariantCulture);
            using (SQLiteTransaction t = c.BeginTransaction())
            {
                CatatRiwayat(c, t, mesin, mulai, 0, 0, -1, sumber, 0, catatan);
                t.Commit();
            }
        }

        static void CatatRiwayat(SQLiteConnection c, SQLiteTransaction t, string mesin, string mulai,
            int terbaca, int baru, int diMesin, string sumber, int berhasil, string catatan)
        {
            using (SQLiteCommand cmd = new SQLiteCommand(
                "INSERT INTO tarikan_log (mesin, mulai, selesai, terbaca, baru, di_mesin, sumber, berhasil, catatan) " +
                "VALUES (@m, @a, @b, @t, @n, @d, @s, @h, @c)", c, t))
            {
                cmd.Parameters.AddWithValue("@m", mesin);
                cmd.Parameters.AddWithValue("@a", mulai);
                cmd.Parameters.AddWithValue("@b", DateTime.Now.ToString(Fmt, CultureInfo.InvariantCulture));
                cmd.Parameters.AddWithValue("@t", terbaca);
                cmd.Parameters.AddWithValue("@n", baru);
                if (diMesin >= 0) { cmd.Parameters.AddWithValue("@d", diMesin); }
                else { cmd.Parameters.AddWithValue("@d", DBNull.Value); }
                cmd.Parameters.AddWithValue("@s", sumber == null ? "" : sumber);
                cmd.Parameters.AddWithValue("@h", berhasil);
                cmd.Parameters.AddWithValue("@c", catatan == null ? "" : catatan);
                cmd.ExecuteNonQuery();
            }
        }

        // Jumlah baris log. mesin = null berarti semua mesin.
        public static long Jumlah(SQLiteConnection c, string mesin)
        {
            string sql = "SELECT COUNT(*) FROM log_absensi" + (mesin == null ? "" : " WHERE mesin = @m");
            using (SQLiteCommand cmd = new SQLiteCommand(sql, c))
            {
                if (mesin != null) { cmd.Parameters.AddWithValue("@m", mesin); }
                return Convert.ToInt64(cmd.ExecuteScalar());
            }
        }
    }
}