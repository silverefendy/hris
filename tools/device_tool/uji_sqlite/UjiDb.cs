using System;
using System.Collections.Generic;
using System.Data.SQLite;
using System.IO;
using HrisDeviceTool.Data;

namespace UjiDb
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

        private static long Jumlah(List<KeyValuePair<string, long>> rs, string tabel)
        {
            foreach (KeyValuePair<string, long> kv in rs)
            {
                if (kv.Key == tabel) { return kv.Value; }
            }
            return -1;
        }

        private static long Total(List<KeyValuePair<string, long>> rs)
        {
            long n = 0;
            foreach (KeyValuePair<string, long> kv in rs) { n += kv.Value; }
            return n;
        }

        private static int Main(string[] args)
        {
            Console.WriteLine("Uji HdtDatabase (src\\Db.cs)");
            Console.WriteLine("Proses: {0}-bit", IntPtr.Size * 8);
            string akar = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "data_uji_db");
            if (Directory.Exists(akar)) { Directory.Delete(akar, true); }
            Directory.CreateDirectory(akar);
            try
            {
                return Uji(akar);
            }
            catch (Exception ex)
            {
                Console.WriteLine("GAGAL  galat tidak tertangani: " + ex.GetType().Name + ": " + ex.Message);
                if (ex.InnerException != null)
                {
                    Console.WriteLine("       penyebab: " + ex.InnerException.GetType().Name + ": " + ex.InnerException.Message);
                }
                return 2;
            }
        }

        private static int Uji(string akar)
        {
            string berkas = Path.Combine(Path.Combine(akar, "asal"), "hdt.sqlite");

            using (SQLiteConnection c = HdtDatabase.Buka(berkas))
            {
                Cek("D1 berkas dibuat, skema versi 2",
                    File.Exists(berkas) && Convert.ToInt32(Skalar(c, "PRAGMA user_version")) == HdtDatabase.VersiSkema, berkas);

                List<KeyValuePair<string, long>> rs = HdtDatabase.Ringkasan(c);
                Cek("D2 delapan tabel, semuanya kosong", rs.Count == 8 && Total(rs) == 0, rs.Count + " tabel");

                string ik = "insert into induk_aplikasi_lama (id_akun,no_induk,nama,gelar,departemen,data_lain,sumber,diimpor) values ('{0}','{1}','{2}','OPERATOR','Sizing','Kolom Lain=nilai','uji','2026-01-01')";
                Jalan(c, string.Format(ik, "99901", "B-UJI-0001", "ANDI"));
                Jalan(c, string.Format(ik, "99902", "B-UJI-0002", "BUDI"));
                Jalan(c, string.Format(ik, "99903", "B-UJI-0003", "CICI"));
                Jalan(c, "insert into user_mesin (mesin,id_mesin,nama,privilege,aktif,diambil) values ('UJI-A','99901','ANDI',0,1,'2026-01-01')");
                Jalan(c, "insert into user_mesin (mesin,id_mesin,nama,privilege,aktif,diambil) values ('UJI-A','99902','BUDI',0,1,'2026-01-01')");

                rs = HdtDatabase.Ringkasan(c);
                Cek("D3 ringkasan menghitung benar",
                    Jumlah(rs, "induk_aplikasi_lama") == 3 && Jumlah(rs, "user_mesin") == 2,
                    "induk_aplikasi_lama=" + Jumlah(rs, "induk_aplikasi_lama") + ", user_mesin=" + Jumlah(rs, "user_mesin"));

                string cad = Path.Combine(Path.Combine(akar, "cadangan"), "hdt_cadangan.sqlite");
                HdtDatabase.Cadangkan(c, cad);
                using (SQLiteConnection c3 = HdtDatabase.Buka(cad))
                {
                    List<KeyValuePair<string, long>> rs3 = HdtDatabase.Ringkasan(c3);
                    string integ = Convert.ToString(Skalar(c3, "PRAGMA integrity_check"));
                    Cek("D5 cadangan konsisten dan utuh",
                        Jumlah(rs3, "induk_aplikasi_lama") == 3 && Jumlah(rs3, "user_mesin") == 2 && integ == "ok",
                        "integrity_check=" + integ);
                }
            }

            using (SQLiteConnection c2 = HdtDatabase.Buka(berkas))
            {
                List<KeyValuePair<string, long>> rs2 = HdtDatabase.Ringkasan(c2);
                Cek("D4 buka ulang: migrasi tidak mengubah data, skema tetap",
                    Jumlah(rs2, "induk_aplikasi_lama") == 3 && Convert.ToInt32(Skalar(c2, "PRAGMA user_version")) == HdtDatabase.VersiSkema,
                    "induk_aplikasi_lama=" + Jumlah(rs2, "induk_aplikasi_lama"));
            }

            string folderBaru = Path.Combine(akar, "folder baru dengan spasi");
            Directory.CreateDirectory(folderBaru);
            string salinan = Path.Combine(folderBaru, "hdt.sqlite");
            File.Copy(berkas, salinan);
            using (SQLiteConnection c4 = HdtDatabase.Buka(salinan))
            {
                List<KeyValuePair<string, long>> rs4 = HdtDatabase.Ringkasan(c4);
                string nama = Convert.ToString(Skalar(c4, "select nama from induk_aplikasi_lama where id_akun='99902'"));
                Cek("D6 salin-tempel ke folder lain lalu dibuka",
                    Jumlah(rs4, "induk_aplikasi_lama") == 3 && Jumlah(rs4, "user_mesin") == 2 && nama == "BUDI",
                    "folder: " + folderBaru);
            }

            string berkas2 = Path.Combine(Path.Combine(akar, "versi_baru"), "hdt.sqlite");
            Directory.CreateDirectory(Path.GetDirectoryName(berkas2));
            using (SQLiteConnection raw = new SQLiteConnection("Data Source=" + berkas2 + ";Version=3;"))
            {
                raw.Open();
                Jalan(raw, "PRAGMA user_version = 99");
            }
            bool ditolak = false;
            try
            {
                using (HdtDatabase.Buka(berkas2)) { }
            }
            catch (InvalidOperationException)
            {
                ditolak = true;
            }
            Cek("D7 database dari versi aplikasi lebih baru ditolak", ditolak, "skema 99");

            Console.WriteLine();
            Console.WriteLine(gagal == 0 ? "SEMUA UJI LULUS" : gagal + " UJI GAGAL");
            return gagal == 0 ? 0 : 1;
        }
    }
}
