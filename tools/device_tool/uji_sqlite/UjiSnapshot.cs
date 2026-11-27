using System;
using System.Collections.Generic;
using System.Data.SQLite;
using System.IO;
using HrisDeviceTool.Data;

namespace UjiSnapshot
{
    internal static class Program
    {
        private static int gagal = 0;

        private static void Cek(string nama, bool ok, string info)
        {
            if (!ok) { gagal++; }
            Console.WriteLine("{0}  {1}{2}", ok ? "OK   " : "GAGAL", nama,
                string.IsNullOrEmpty(info) ? "" : "  |  " + info);
        }

        private static object Skalar(SQLiteConnection c, string sql)
        {
            using (SQLiteCommand cmd = new SQLiteCommand(sql, c)) { return cmd.ExecuteScalar(); }
        }

        private static string Teks(SQLiteConnection c, string sql)
        {
            object o = Skalar(c, sql);
            return (o == null || o is DBNull) ? null : Convert.ToString(o);
        }

        private static long Jumlah(SQLiteConnection c, string sql)
        {
            return Convert.ToInt64(Skalar(c, sql));
        }

        private static int Main(string[] args)
        {
            Console.WriteLine("Uji SnapshotUser (src\\SnapshotUser.cs)");
            string akar = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "data_uji_snapshot");
            if (Directory.Exists(akar)) { Directory.Delete(akar, true); }
            Directory.CreateDirectory(akar);
            try { return Uji(akar); }
            catch (Exception ex)
            {
                Console.WriteLine("GAGAL  galat tidak tertangani: " + ex.GetType().Name + ": " + ex.Message);
                return 2;
            }
        }

        private static int Uji(string akar)
        {
            string db = Path.Combine(Path.Combine(akar, "db"), "hdt.sqlite");
            using (SQLiteConnection c = HdtDatabase.Buka(db))
            {
                List<string[]> a = new List<string[]>();
                a.Add(new string[] { "99901", "ANDI", "0", "aktif", "1", "1234567" });
                a.Add(new string[] { "99902", "BUDI", "3", "aktif", "0", "0" });
                a.Add(new string[] { "99903", "CICI", "0", "nonaktif", "0", "" });
                a.Add(new string[] { "", "TANPA ID", "0", "aktif", "0", "" });
                HasilSnapshot h1 = SnapshotUser.Simpan(c, "UJI-A", "10.0.0.1", a);
                Cek("S1 snapshot pertama: sebelum 0, sesudah 3, 1 baris tanpa id dilewati",
                    h1.Sebelum == 0 && h1.Sesudah == 3 && h1.Dilewati == 1,
                    "sebelum=" + h1.Sebelum + " sesudah=" + h1.Sesudah + " dilewati=" + h1.Dilewati);

                Cek("S2 nilai tersimpan: privilege, aktif, penanda sandi, kartu ('0' dianggap kosong)",
                    Teks(c, "select privilege from user_mesin where mesin='UJI-A' and id_mesin='99902'") == "3"
                    && Teks(c, "select aktif from user_mesin where mesin='UJI-A' and id_mesin='99903'") == "0"
                    && Teks(c, "select ada_sandi from user_mesin where mesin='UJI-A' and id_mesin='99901'") == "1"
                    && Teks(c, "select nomor_kartu from user_mesin where mesin='UJI-A' and id_mesin='99901'") == "1234567"
                    && Teks(c, "select nomor_kartu from user_mesin where mesin='UJI-A' and id_mesin='99902'") == null,
                    "");

                List<string[]> b = new List<string[]>();
                b.Add(new string[] { "99901", "ANDI", "0", "aktif", "0", "555" });
                SnapshotUser.Simpan(c, "UJI-B", "10.0.0.2", b);

                List<string[]> a2 = new List<string[]>();
                a2.Add(new string[] { "99901", "ANDI BARU", "0", "aktif", "0", "" });
                a2.Add(new string[] { "99904", "DEDI", "0", "aktif", "0", "" });
                HasilSnapshot h2 = SnapshotUser.Simpan(c, "UJI-A", "10.0.0.9", a2);
                Cek("S3 snapshot ulang mengganti yang lama: sebelum 3, sesudah 2, user yang hilang dari mesin terhapus",
                    h2.Sebelum == 3 && h2.Sesudah == 2
                    && Jumlah(c, "select count(*) from user_mesin where mesin='UJI-A' and id_mesin in ('99902','99903')") == 0
                    && Teks(c, "select nama from user_mesin where mesin='UJI-A' and id_mesin='99901'") == "ANDI BARU",
                    "sebelum=" + h2.Sebelum + " sesudah=" + h2.Sesudah);

                Cek("S4 mesin lain tidak terpengaruh", Jumlah(c, "select count(*) from user_mesin where mesin='UJI-B'") == 1, "");

                Cek("S5 tabel mesin ikut diperbarui (ip terbaru)",
                    Teks(c, "select ip from mesin where nama='UJI-A'") == "10.0.0.9"
                    && Jumlah(c, "select count(*) from mesin") == 2, "");

                string jm = Teks(c, "select jumlah_mesin from v_karyawan_lokal where id='99901'");
                string kartu = Teks(c, "select kartu_di_mesin from v_karyawan_lokal where id='99901'");
                Cek("S6 view v_karyawan_lokal: id di dua mesin, jumlah_mesin 2, kartu di mesin terbawa",
                    jm == "2" && kartu == "555", "jumlah_mesin=" + jm + " kartu=" + kartu);

                Cek("S7 id yang hanya di mesin muncul di view tanpa profil aplikasi lama",
                    Teks(c, "select ada_di_aplikasi_lama from v_karyawan_lokal where id='99904'") == "0", "");
            }

            Console.WriteLine();
            Console.WriteLine(gagal == 0 ? "SEMUA UJI LULUS" : gagal + " UJI GAGAL");
            return gagal == 0 ? 0 : 1;
        }
    }
}
