using System;
using System.Collections.Generic;
using System.Data.SQLite;
using System.IO;
using HrisDeviceTool.Data;

namespace UjiKaryawan
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

        private static Karyawan Cari(List<Karyawan> d, string id)
        {
            foreach (Karyawan k in d) { if (k.Id == id) { return k; } }
            return null;
        }

        private static int Hitung(List<Karyawan> d, SaringKaryawan s, string q)
        {
            int n = 0;
            foreach (Karyawan k in d) { if (DaftarKaryawan.Cocok(k, s, q)) { n++; } }
            return n;
        }

        private static int Main(string[] args)
        {
            Console.WriteLine("Uji DaftarKaryawan (src\\Karyawan.cs), memakai database sementara berisi data fiktif");
            string akar = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "data_uji_karyawan");
            if (Directory.Exists(akar)) { Directory.Delete(akar, true); }
            Directory.CreateDirectory(akar);
            try { return Uji(Path.Combine(akar, "hdt.sqlite")); }
            catch (Exception ex)
            {
                Console.WriteLine("GAGAL  galat tidak tertangani: " + ex.GetType().Name + ": " + ex.Message);
                return 2;
            }
        }

        private static int Uji(string db)
        {
            using (SQLiteConnection c = HdtDatabase.Buka(db))
            {
                Cek("K0 database kosong menghasilkan daftar kosong", DaftarKaryawan.Muat(c).Count == 0, "");
                const string u = "insert into user_mesin (mesin,id_mesin,nama,privilege,aktif,diambil,nomor_kartu,jumlah_jari) values ";
                // 99901: tiga mesin, satu nama berbeda
                Jalan(c, u + "('UJI-A','99901','UJI SATU',0,1,'2026-11-27 10:00:00',null,2)");
                Jalan(c, u + "('UJI-B','99901','uji  satu',0,1,'2026-11-27 10:00:00','123',1)");
                Jalan(c, u + "('UJI-C','99901','UJI 1',2,1,'2026-11-27 10:00:00',null,null)");
                // 99902: dua mesin, hanya beda huruf besar kecil dan satu nama kosong
                Jalan(c, u + "('UJI-A','99902','Uji Dua',0,1,'',null,0)");
                Jalan(c, u + "('UJI-B','99902','',0,1,'',null,0)");
                // 99903: jari belum pernah diambil
                Jalan(c, u + "('UJI-C','99903','=RUMUS',0,0,'',null,null)");
                // 99904: satu mesin 0, satu mesin belum diambil
                Jalan(c, u + "('UJI-A','99904','UJI EMPAT',0,1,'',null,0)");
                Jalan(c, u + "('UJI-C','99904','UJI EMPAT',0,1,'',null,null)");
                // ID pendek untuk uji urutan angka
                Jalan(c, u + "('UJI-A','277','UJI PENDEK',0,1,'',null,1)");
                const string t = "insert into template_jari (mesin,id_mesin,jari) values ";
                Jalan(c, t + "('UJI-A','99901',5)");
                Jalan(c, t + "('UJI-A','99901',6)");
                Jalan(c, t + "('UJI-B','99901',5)");
                Jalan(c, "insert into induk_aplikasi_lama (id_akun,departemen) values ('99901','DEPT LAMA')");
                Jalan(c, "insert into induk_aplikasi_lama (id_akun,departemen) values ('99902','DEPT LAMA')");
                Jalan(c, "insert into induk_aplikasi_lama (id_akun,departemen) values ('88888','TIDAK ADA DI MESIN')");
                Jalan(c, "insert into karyawan_hris (dokumen,id_finger,department) values ('D1','99901','DEPT HRIS')");

                List<Karyawan> d = DaftarKaryawan.Muat(c);
                Cek("K1 satu baris per ID, data aplikasi lama tidak menambah baris", d.Count == 5, "jumlah " + d.Count);
                Cek("K2 urutan ID sebagai angka", d[0].Id == "277" && d[1].Id == "99901", d[0].Id + ", " + d[1].Id);
                Karyawan a = Cari(d, "99901");
                Cek("K3 nama terbanyak dipakai dan beda nama ditandai", a.NamaBeda && DaftarKaryawan.Samakan(a.Nama) == "UJI SATU", a.Nama);
                Cek("K4 daftar mesin dan rincian", a.Rincian.Count == 3 && a.DaftarMesin == "UJI-A, UJI-B, UJI-C", a.DaftarMesin);
                Cek("K5 jari terbanyak dan jari tersimpan tanpa dobel", a.Jari == 2 && a.JariTersimpan == 2, a.Jari + " / " + a.JariTersimpan);
                Cek("K6 departemen HRIS didahulukan", a.Departemen == "DEPT HRIS", a.Departemen);
                Karyawan b = Cari(d, "99902");
                Cek("K7 huruf besar kecil dan nama kosong bukan beda nama", !b.NamaBeda && b.Nama == "Uji Dua", b.Nama);
                Cek("K8 tanpa sidik jari bila semua mesin sudah diambil", b.TanpaJari && b.Departemen == "DEPT LAMA", b.TeksJari);
                Karyawan e = Cari(d, "99903");
                Cek("K9 belum diambil tampil tanda tanya, bukan tanpa jari", e.Jari == -1 && e.TeksJari == "?" && !e.TanpaJari, e.Catatan);
                Karyawan f = Cari(d, "99904");
                Cek("K10 sebagian belum diambil tidak disebut tanpa jari", f.Jari == -1 && !f.TanpaJari, f.TeksJari);
                Cek("K11 saringan", Hitung(d, SaringKaryawan.Semua, "") == 5 && Hitung(d, SaringKaryawan.NamaBeda, "") == 1
                    && Hitung(d, SaringKaryawan.TanpaJari, "") == 1 && Hitung(d, SaringKaryawan.SatuMesin, "") == 2, "");
                Cek("K12 cari nama dari mesin mana pun, ID, departemen", Hitung(d, SaringKaryawan.Semua, "uji 1") == 1
                    && Hitung(d, SaringKaryawan.Semua, "277") == 1 && Hitung(d, SaringKaryawan.Semua, "hris") == 1, "");
                string csv = DaftarKaryawan.Csv(d);
                Cek("K13 CSV: judul, 5 baris, rumus Excel dinetralkan", csv.Split('\n').Length == 7 && csv.Contains("\"'=RUMUS\""), "");
            }
            Console.WriteLine();
            Console.WriteLine(gagal == 0 ? "SEMUA UJI LULUS" : "ADA " + gagal + " UJI GAGAL");
            return gagal == 0 ? 0 : 1;
        }
    }
}
