using System;
using System.Data.SQLite;
using System.IO;
using System.Reflection;
using HrisDeviceTool.Data;

namespace UjiDbV2
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

        private static void Jalan(SQLiteConnection c, string sql)
        {
            using (SQLiteCommand cmd = new SQLiteCommand(sql, c)) { cmd.ExecuteNonQuery(); }
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

        private static int Versi(SQLiteConnection c)
        {
            return Convert.ToInt32(Skalar(c, "PRAGMA user_version"));
        }

        private static bool AdaKolom(SQLiteConnection c, string tabel, string kolom)
        {
            using (SQLiteCommand cmd = new SQLiteCommand("PRAGMA table_info(" + tabel + ")", c))
            using (SQLiteDataReader r = cmd.ExecuteReader())
            {
                while (r.Read())
                {
                    if (string.Equals(r.GetString(1), kolom, StringComparison.OrdinalIgnoreCase)) { return true; }
                }
            }
            return false;
        }

        private static int Main(string[] args)
        {
            Console.WriteLine("Uji skema v2 (src\\Db.cs)");
            string akar = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "data_uji_dbv2");
            if (Directory.Exists(akar)) { Directory.Delete(akar, true); }
            Directory.CreateDirectory(akar);
            try { return Uji(akar); }
            catch (Exception ex)
            {
                Console.WriteLine("GAGAL  galat tidak tertangani: " + ex.GetType().Name + ": " + ex.Message);
                if (ex.InnerException != null) { Console.WriteLine("       penyebab: " + ex.InnerException.Message); }
                return 2;
            }
        }

        private static int Uji(string akar)
        {
            string baru = Path.Combine(Path.Combine(akar, "baru"), "hdt.sqlite");
            using (SQLiteConnection c = HdtDatabase.Buka(baru))
            {
                bool kolom = AdaKolom(c, "user_mesin", "nomor_kartu") && AdaKolom(c, "user_mesin", "ada_sandi")
                    && AdaKolom(c, "user_mesin", "jumlah_jari") && AdaKolom(c, "user_mesin", "jumlah_wajah");
                long view = Convert.ToInt64(Skalar(c, "select count(*) from sqlite_master where type='view' and name='v_karyawan_lokal'"));
                Cek("V1 database baru: skema 2, empat kolom mesin baru, view ada", Versi(c) == 2 && kolom && view == 1,
                    "versi=" + Versi(c) + " kolom=" + kolom + " view=" + view);
                int tabel = HdtDatabase.Ringkasan(c).Count;
                Cek("V2 ringkasan tetap 7 tabel (view tidak dihitung)", tabel == 7, tabel + " tabel");
            }

            string lama = Path.Combine(Path.Combine(akar, "lama"), "hdt.sqlite");
            Directory.CreateDirectory(Path.GetDirectoryName(lama));
            string v1 = (string)typeof(HdtDatabase).GetField("SkemaV1", BindingFlags.NonPublic | BindingFlags.Static).GetRawConstantValue();
            using (SQLiteConnection raw = new SQLiteConnection("Data Source=" + lama + ";Version=3;"))
            {
                raw.Open();
                Jalan(raw, v1);
                Jalan(raw, "PRAGMA user_version = 1");
                Jalan(raw, "insert into induk_aplikasi_lama (id_akun,no_induk,nama) values ('99901','B-UJI-0001','ANDI')");
                Jalan(raw, "insert into user_mesin (mesin,id_mesin,nama,privilege,aktif,diambil) values ('UJI-A','99901','ANDI',0,1,'2026-01-01')");
            }

            using (SQLiteConnection c2 = HdtDatabase.Buka(lama))
            {
                long a = Convert.ToInt64(Skalar(c2, "select count(*) from induk_aplikasi_lama"));
                long b = Convert.ToInt64(Skalar(c2, "select count(*) from user_mesin"));
                string kartu = Teks(c2, "select nomor_kartu from user_mesin where id_mesin='99901'");
                Cek("V3 naik dari v1 berisi data: skema 2, data utuh, kolom baru kosong",
                    Versi(c2) == 2 && a == 1 && b == 1 && kartu == null, "versi=" + Versi(c2) + " induk=" + a + " mesin=" + b);

                Jalan(c2, "insert into user_mesin (mesin,id_mesin,nama,privilege,aktif,diambil) values ('UJI-B','99901','ANDI',0,1,'2026-01-01')");
                Jalan(c2, "insert into user_mesin (mesin,id_mesin,nama,privilege,aktif,diambil) values ('UJI-A','99950','TANPA PROFIL',0,1,'2026-01-01')");
                Jalan(c2, "insert into induk_aplikasi_lama (id_akun,no_induk,nama) values ('99960','B-UJI-0060','CICI')");

                long total = Convert.ToInt64(Skalar(c2, "select count(*) from v_karyawan_lokal"));
                Cek("V4 view: satu baris per id (3 id: ada di keduanya, hanya di mesin, hanya di aplikasi lama)", total == 3, "baris=" + total);

                string jm = Teks(c2, "select jumlah_mesin from v_karyawan_lokal where id='99901'");
                string ada = Teks(c2, "select ada_di_aplikasi_lama from v_karyawan_lokal where id='99901'");
                string ni = Teks(c2, "select no_induk from v_karyawan_lokal where id='99901'");
                string dm = Teks(c2, "select daftar_mesin from v_karyawan_lokal where id='99901'") ?? "";
                Cek("V5 view id di dua mesin: jumlah_mesin 2, ada di aplikasi lama, No Induk terbawa, daftar mesin lengkap",
                    jm == "2" && ada == "1" && ni == "B-UJI-0001" && dm.Contains("UJI-A") && dm.Contains("UJI-B"),
                    "jumlah_mesin=" + jm + " daftar=" + dm);

                string ada2 = Teks(c2, "select ada_di_aplikasi_lama from v_karyawan_lokal where id='99950'");
                string ni2 = Teks(c2, "select no_induk from v_karyawan_lokal where id='99950'");
                string jm2 = Teks(c2, "select jumlah_mesin from v_karyawan_lokal where id='99950'");
                Cek("V6 view id hanya di mesin: ada_di_aplikasi_lama 0, No Induk kosong, jumlah_mesin 1",
                    ada2 == "0" && ni2 == null && jm2 == "1", "ada=" + ada2 + " jumlah_mesin=" + jm2);

                string jm3 = Teks(c2, "select jumlah_mesin from v_karyawan_lokal where id='99960'");
                string nm3 = Teks(c2, "select nama_di_mesin from v_karyawan_lokal where id='99960'");
                Cek("V7 view id hanya di aplikasi lama: jumlah_mesin 0, nama di mesin kosong", jm3 == "0" && nm3 == null,
                    "jumlah_mesin=" + jm3);
            }

            using (SQLiteConnection c3 = HdtDatabase.Buka(lama)) { }
            using (SQLiteConnection c4 = HdtDatabase.Buka(lama))
            {
                long total = Convert.ToInt64(Skalar(c4, "select count(*) from v_karyawan_lokal"));
                Cek("V8 buka ulang berkali-kali aman: skema tetap 2, data tetap", Versi(c4) == 2 && total == 3, "versi=" + Versi(c4));
            }

            Console.WriteLine();
            Console.WriteLine(gagal == 0 ? "SEMUA UJI LULUS" : gagal + " UJI GAGAL");
            return gagal == 0 ? 0 : 1;
        }
    }
}
