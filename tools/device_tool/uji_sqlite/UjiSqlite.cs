using System;
using System.Collections.Generic;
using System.Data;
using System.Data.SQLite;
using System.Diagnostics;
using System.IO;
using System.Security.Cryptography;

namespace UjiSqlite
{
    internal static class Program
    {
        private static int gagal = 0;

        private const string SKEMA = @"
CREATE TABLE meta (kunci TEXT PRIMARY KEY, nilai TEXT);
CREATE TABLE mesin (
    nama TEXT PRIMARY KEY,
    ip TEXT,
    versi_jari INTEGER,
    versi_wajah INTEGER,
    diperbarui TEXT
);
CREATE TABLE user_mesin (
    mesin TEXT NOT NULL,
    id_mesin TEXT NOT NULL,
    nama TEXT,
    privilege INTEGER,
    aktif INTEGER,
    diambil TEXT,
    PRIMARY KEY (mesin, id_mesin)
);
CREATE TABLE template_jari (
    mesin TEXT NOT NULL,
    id_mesin TEXT NOT NULL,
    jari INTEGER NOT NULL,
    flag INTEGER,
    versi INTEGER,
    panjang INTEGER,
    hash TEXT,
    data BLOB,
    diambil TEXT,
    PRIMARY KEY (mesin, id_mesin, jari)
);
CREATE TABLE induk_aplikasi_lama (
    id_akun TEXT PRIMARY KEY,
    no_induk TEXT,
    nama TEXT,
    gelar TEXT,
    departemen TEXT,
    mulai_bekerja TEXT,
    sumber TEXT,
    diimpor TEXT
);
CREATE INDEX ix_induk_lama_noinduk ON induk_aplikasi_lama (no_induk);
CREATE TABLE karyawan_hris (
    dokumen TEXT PRIMARY KEY,
    nama TEXT,
    id_finger TEXT,
    no_induk TEXT,
    department TEXT,
    status TEXT,
    disalin TEXT
);
CREATE INDEX ix_karyawan_idfinger ON karyawan_hris (id_finger);
CREATE INDEX ix_karyawan_noinduk ON karyawan_hris (no_induk);
CREATE TABLE department_hris (
    nama TEXT PRIMARY KEY,
    induk TEXT,
    aktif INTEGER,
    disalin TEXT
);
";

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

        private static void Param(SQLiteConnection c, SQLiteTransaction t, string sql, params object[] nilai)
        {
            using (SQLiteCommand cmd = new SQLiteCommand(sql, c, t))
            {
                for (int i = 0; i < nilai.Length; i++)
                {
                    cmd.Parameters.AddWithValue("@p" + i, nilai[i] ?? DBNull.Value);
                }
                cmd.ExecuteNonQuery();
            }
        }

        private static string Daftar(SQLiteConnection c, string sql)
        {
            List<string> hasil = new List<string>();
            using (SQLiteCommand cmd = new SQLiteCommand(sql, c))
            using (SQLiteDataReader r = cmd.ExecuteReader())
            {
                while (r.Read()) { hasil.Add(Convert.ToString(r[0])); }
            }
            return string.Join(",", hasil.ToArray());
        }

        private static string Hex(byte[] b)
        {
            return BitConverter.ToString(b).Replace("-", "").ToLowerInvariant();
        }

        private static string HashSha256(byte[] data)
        {
            using (SHA256 sha = SHA256.Create()) { return Hex(sha.ComputeHash(data)); }
        }

        private static int Main(string[] args)
        {
            Console.WriteLine("Uji SQLite untuk HRIS Device Tool");
            Console.WriteLine("Proses: {0}-bit, runtime .NET {1}", IntPtr.Size * 8, Environment.Version);
            string folder = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "data_uji");
            Directory.CreateDirectory(folder);
            string berkas = Path.Combine(folder, "uji_sqlite.sqlite");
            if (File.Exists(berkas)) { File.Delete(berkas); }
            try
            {
                return Uji(berkas);
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

        private static int Uji(string berkas)
        {
            string cs = "Data Source=" + berkas + ";Version=3;";
            string sekarang = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
            byte[] data = new byte[1700];
            new Random(12345).NextBytes(data);
            string hashAsli = HashSha256(data);

            using (SQLiteConnection c = new SQLiteConnection(cs))
            {
                c.Open();
                Cek("U1 buka berkas SQLite", c.State == ConnectionState.Open, berkas);
                Cek("U2 versi mesin SQLite", true, Convert.ToString(Skalar(c, "select sqlite_version()")));
                Jalan(c, SKEMA);
                Jalan(c, "PRAGMA user_version = 1");
                Cek("U3 skema dibuat", Convert.ToInt32(Skalar(c, "select count(*) from sqlite_master where type='table'")) == 7, "7 tabel");

                using (SQLiteTransaction t = c.BeginTransaction())
                {
                    string iu = "insert into user_mesin (mesin,id_mesin,nama,privilege,aktif,diambil) values (@p0,@p1,@p2,0,1,@p3)";
                    Param(c, t, iu, "UJI-A", "99901", "ANDI", sekarang);
                    Param(c, t, iu, "UJI-A", "99902", "BUDI (KRETA)", sekarang);
                    Param(c, t, iu, "UJI-A", "99903", "CICI", sekarang);
                    Param(c, t, iu, "UJI-B", "99901", "ANDI", sekarang);
                    Param(c, t, iu, "UJI-B", "99902", "BUDI", sekarang);
                    Param(c, t, iu, "UJI-B", "99904", "DEDI", sekarang);

                    string ih = "insert into karyawan_hris (dokumen,nama,id_finger,no_induk,department,status,disalin) values (@p0,@p1,@p2,@p3,@p4,@p5,@p6)";
                    Param(c, t, ih, "HRE-9901", "ANDI", "99901", "B-UJI-0001", "Sizing", "Aktif", sekarang);
                    Param(c, t, ih, "HRE-9902", "BUDI", "99902", "B-UJI-0099", "Sizing", "Aktif", sekarang);
                    Param(c, t, ih, "HRE-9903", "EKA", "99905", "B-UJI-0001", "Finishing", "Aktif", sekarang);
                    Param(c, t, ih, "HRE-9904", "FANI", "99903", "", "Finishing", "Resign", sekarang);

                    string il = "insert into induk_aplikasi_lama (id_akun,no_induk,nama,gelar,departemen,mulai_bekerja,sumber,diimpor) values (@p0,@p1,@p2,@p3,@p4,@p5,@p6,@p7)";
                    Param(c, t, il, "99901", "B-UJI-0001", "ANDI", "OPERATOR", "Sizing", "2020-09-16", "uji", sekarang);
                    Param(c, t, il, "99902", "B-UJI-0002", "BUDI", "OPERATOR", "Sizing", "2021-01-04", "uji", sekarang);

                    Param(c, t, "insert into template_jari (mesin,id_mesin,jari,flag,versi,panjang,hash,data,diambil) values (@p0,@p1,@p2,@p3,@p4,@p5,@p6,@p7,@p8)",
                        "UJI-A", "99901", 3, 1, 10, data.Length, hashAsli, data, sekarang);
                    t.Commit();
                }

                using (SQLiteCommand cmd = new SQLiteCommand("select data, hash from template_jari where mesin='UJI-A' and id_mesin='99901' and jari=3", c))
                using (SQLiteDataReader r = cmd.ExecuteReader())
                {
                    bool ada = r.Read();
                    byte[] balik = ada ? (byte[])r["data"] : new byte[0];
                    Cek("U4 BLOB template dibaca kembali utuh",
                        ada && balik.Length == data.Length && HashSha256(balik) == Convert.ToString(r["hash"]),
                        "panjang " + balik.Length + " byte");
                }

                bool ditolak = false;
                try
                {
                    Jalan(c, "insert into user_mesin (mesin,id_mesin,nama) values ('UJI-A','99901','DOBEL')");
                }
                catch (SQLiteException)
                {
                    ditolak = true;
                }
                Cek("U5 kunci ganda ditolak", ditolak, "mesin + ID harus unik");

                string q1 = Daftar(c, "select distinct u.id_mesin from user_mesin u left join karyawan_hris k on k.id_finger = u.id_mesin where k.dokumen is null order by 1");
                Cek("Q1 ada di mesin, tidak ada di HRIS", q1 == "99904", "hasil: " + q1 + " (harapan 99904)");

                string q2 = Daftar(c, "select k.id_finger from karyawan_hris k where k.status='Aktif' and not exists (select 1 from user_mesin u where u.id_mesin = k.id_finger) order by 1");
                Cek("Q2 aktif di HRIS, tidak ada di mesin", q2 == "99905", "hasil: " + q2 + " (harapan 99905)");

                string q3 = Daftar(c, "select distinct k.id_finger from karyawan_hris k join user_mesin u on u.id_mesin = k.id_finger where k.status='Resign' order by 1");
                Cek("Q3 resign tapi masih di mesin", q3 == "99903", "hasil: " + q3 + " (harapan 99903)");

                string q4 = Daftar(c, "select id_mesin from user_mesin group by id_mesin having count(distinct upper(nama)) > 1 order by 1");
                Cek("Q4 ID sama, nama beda antar mesin", q4 == "99902", "hasil: " + q4 + " (harapan 99902)");

                string q5 = Daftar(c, "select i.id_akun from induk_aplikasi_lama i join karyawan_hris k on k.id_finger = i.id_akun where upper(coalesce(i.no_induk,'')) <> upper(coalesce(k.no_induk,'')) order by 1");
                Cek("Q5 No Induk beda: aplikasi lama vs HRIS", q5 == "99902", "hasil: " + q5 + " (harapan 99902)");

                string q6 = Daftar(c, "select no_induk from karyawan_hris where no_induk is not null and no_induk <> '' group by no_induk having count(*) > 1 order by 1");
                Cek("Q6 No Induk ganda di HRIS", q6 == "B-UJI-0001", "hasil: " + q6 + " (harapan B-UJI-0001)");

                Jalan(c, "create table uji_massal (id integer primary key, nilai text)");
                Stopwatch sw = Stopwatch.StartNew();
                using (SQLiteTransaction t = c.BeginTransaction())
                using (SQLiteCommand cmd = new SQLiteCommand("insert into uji_massal (id, nilai) values (@a, @b)", c, t))
                {
                    SQLiteParameter pa = cmd.Parameters.Add("@a", DbType.Int64);
                    SQLiteParameter pb = cmd.Parameters.Add("@b", DbType.String);
                    for (int i = 1; i <= 50000; i++)
                    {
                        pa.Value = i;
                        pb.Value = "baris-" + i;
                        cmd.ExecuteNonQuery();
                    }
                    t.Commit();
                }
                sw.Stop();
                long n = Convert.ToInt64(Skalar(c, "select count(*) from uji_massal"));
                Cek("U7 tulis 50000 baris dalam satu transaksi", n == 50000, sw.ElapsedMilliseconds + " ms");
                Jalan(c, "drop table uji_massal");
            }

            using (SQLiteConnection c2 = new SQLiteConnection(cs))
            {
                c2.Open();
                int jumlah = Convert.ToInt32(Skalar(c2, "select count(*) from user_mesin"));
                int versi = Convert.ToInt32(Skalar(c2, "PRAGMA user_version"));
                string integritas = Convert.ToString(Skalar(c2, "PRAGMA integrity_check"));
                Cek("U8 data utuh setelah tutup dan buka lagi", jumlah == 6 && versi == 1 && integritas == "ok",
                    "user_mesin=" + jumlah + ", user_version=" + versi + ", integrity_check=" + integritas);
            }

            Console.WriteLine();
            Console.WriteLine("Berkas uji: " + berkas);
            Console.WriteLine(gagal == 0 ? "SEMUA UJI LULUS" : gagal + " UJI GAGAL");
            return gagal == 0 ? 0 : 1;
        }
    }
}
