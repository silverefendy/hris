using System;
using System.Collections.Generic;
using System.Data.SQLite;
using System.Globalization;

namespace HrisDeviceTool.Data
{
    public class HasilSnapshot
    {
        public int Sebelum;
        public int Sesudah;
        public int Dilewati;
    }

    // Menyimpan snapshot user satu mesin ke tabel user_mesin (menggantikan snapshot lama mesin itu).
    public static class SnapshotUser
    {
        // Baris: [0] id, [1] nama, [2] privilege, [3] "aktif"/"nonaktif", [4] ada sandi "1"/"0", [5] nomor kartu.
        public static HasilSnapshot Simpan(SQLiteConnection c, string mesin, string ip, List<string[]> baris)
        {
            if (string.IsNullOrEmpty(mesin)) { throw new ArgumentException("Nama mesin kosong."); }
            HasilSnapshot h = new HasilSnapshot();
            string waktu = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss", CultureInfo.InvariantCulture);
            const string sql = "insert or replace into user_mesin (mesin,id_mesin,nama,privilege,aktif,diambil,nomor_kartu,ada_sandi) values (@mesin,@id,@nama,@priv,@aktif,@diambil,@kartu,@sandi)";

            using (SQLiteTransaction t = c.BeginTransaction())
            {
                using (SQLiteCommand q = new SQLiteCommand("select count(*) from user_mesin where mesin=@m", c, t))
                {
                    q.Parameters.AddWithValue("@m", mesin);
                    h.Sebelum = Convert.ToInt32(q.ExecuteScalar());
                }
                using (SQLiteCommand d = new SQLiteCommand("delete from user_mesin where mesin=@m", c, t))
                {
                    d.Parameters.AddWithValue("@m", mesin);
                    d.ExecuteNonQuery();
                }

                foreach (string[] r in baris)
                {
                    string id = (r.Length > 0 && r[0] != null) ? r[0].Trim() : "";
                    if (id.Length == 0) { h.Dilewati++; continue; }
                    string nama = (r.Length > 1 && r[1] != null) ? r[1].Trim() : "";
                    int priv = 0;
                    if (r.Length > 2) { int.TryParse(r[2], out priv); }
                    int aktif = (r.Length > 3 && r[3] == "aktif") ? 1 : 0;
                    object sandi = DBNull.Value;
                    if (r.Length > 4 && !string.IsNullOrEmpty(r[4])) { sandi = (r[4] == "1") ? 1 : 0; }
                    string kartu = (r.Length > 5 && r[5] != null) ? r[5].Trim() : "";
                    if (kartu == "0") { kartu = ""; }

                    using (SQLiteCommand cmd = new SQLiteCommand(sql, c, t))
                    {
                        cmd.Parameters.AddWithValue("@mesin", mesin);
                        cmd.Parameters.AddWithValue("@id", id);
                        cmd.Parameters.AddWithValue("@nama", nama);
                        cmd.Parameters.AddWithValue("@priv", priv);
                        cmd.Parameters.AddWithValue("@aktif", aktif);
                        cmd.Parameters.AddWithValue("@diambil", waktu);
                        cmd.Parameters.AddWithValue("@kartu", kartu.Length > 0 ? (object)kartu : DBNull.Value);
                        cmd.Parameters.AddWithValue("@sandi", sandi);
                        cmd.ExecuteNonQuery();
                    }
                }

                using (SQLiteCommand m = new SQLiteCommand(
                    "insert into mesin (nama,ip,diperbarui) values (@n,@ip,@t) on conflict(nama) do update set ip=excluded.ip, diperbarui=excluded.diperbarui", c, t))
                {
                    m.Parameters.AddWithValue("@n", mesin);
                    m.Parameters.AddWithValue("@ip", ip ?? "");
                    m.Parameters.AddWithValue("@t", waktu);
                    m.ExecuteNonQuery();
                }

                using (SQLiteCommand q2 = new SQLiteCommand("select count(*) from user_mesin where mesin=@m", c, t))
                {
                    q2.Parameters.AddWithValue("@m", mesin);
                    h.Sesudah = Convert.ToInt32(q2.ExecuteScalar());
                }
                t.Commit();
            }
            return h;
        }
    }
}
