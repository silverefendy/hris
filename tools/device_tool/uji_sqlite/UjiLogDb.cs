using System;
using System.Collections.Generic;
using System.Data.SQLite;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using HrisDeviceTool.Data;

public static class UjiLogDb
{
    static int gagal = 0;

    static void Cek(string kode, string uraian, bool ok, string info)
    {
        if (!ok) { gagal++; }
        Console.WriteLine((ok ? "OK     " : "GAGAL  ") + kode + " " + uraian + (info.Length > 0 ? "  |  " + info : ""));
    }

    static long Skalar(SQLiteConnection c, string sql)
    {
        using (SQLiteCommand cmd = new SQLiteCommand(sql, c)) { return Convert.ToInt64(cmd.ExecuteScalar()); }
    }

    static void Jalankan(string berkas, string sql)
    {
        using (SQLiteConnection c = new SQLiteConnection("Data Source=" + berkas + ";Version=3;"))
        {
            c.Open();
            using (SQLiteCommand cmd = new SQLiteCommand(sql, c)) { cmd.ExecuteNonQuery(); }
        }
    }

    static BarisLog B(string id, string waktu)
    {
        BarisLog b = new BarisLog();
        b.Id = id;
        b.Waktu = DateTime.ParseExact(waktu, "yyyy-MM-dd HH:mm:ss", CultureInfo.InvariantCulture);
        b.Verifikasi = 1;
        return b;
    }

    public static int Main()
    {
        string folder = Path.Combine(Path.GetTempPath(), "hdt_uji_logdb_" + Guid.NewGuid().ToString("N"));
        string berkas = Path.Combine(folder, "uji.sqlite");
        try { Uji(folder, berkas); }
        catch (Exception e) { Console.WriteLine("GAGAL  galat tak terduga: " + e); gagal++; }
        finally
        {
            try { SQLiteConnection.ClearAllPools(); Directory.Delete(folder, true); } catch { }
        }
        Console.WriteLine();
        Console.WriteLine(gagal == 0 ? "SEMUA LULUS" : "ADA YANG GAGAL: " + gagal);
        return gagal == 0 ? 0 : 1;
    }

    static void Uji(string folder, string berkas)
    {
        Console.WriteLine("Uji LogDb dan skema v4 (database sementara, data fiktif)");
        using (SQLiteConnection c = HdtDatabase.Buka(berkas))
        {
            Cek("L1", "database baru berskema 4", Skalar(c, "PRAGMA user_version") == 4,
                "user_version " + Skalar(c, "PRAGMA user_version"));
            Cek("L1b", "tabel log_absensi dan tarikan_log ada",
                Skalar(c, "select count(*) from sqlite_master where name in ('log_absensi','tarikan_log')") == 2, "");

            List<BarisLog> a = new List<BarisLog>();
            a.Add(B("5704", "2026-11-27 07:55:00"));
            a.Add(B("5704", "2026-11-27 07:56:00"));
            a.Add(B("5704", "2026-11-27 17:05:00"));
            HasilSimpan h = LogDb.Simpan(c, "UJI-A", a, "tarik", 3, "");
            Cek("L2", "simpan 3 baris baru", h.Baru == 3 && h.Dilewati == 0 && LogDb.Jumlah(c, "UJI-A") == 3,
                "baru " + h.Baru + ", dilewati " + h.Dilewati);

            h = LogDb.Simpan(c, "UJI-A", a, "tarik", 3, "");
            Cek("L3", "simpan ulang tidak menggandakan", h.Baru == 0 && h.Dilewati == 3 && LogDb.Jumlah(c, "UJI-A") == 3,
                "baru " + h.Baru + ", dilewati " + h.Dilewati);

            List<BarisLog> b2 = new List<BarisLog>();
            b2.Add(B("5704", "2026-11-27 07:55:00"));
            b2.Add(B("5704", "2026-11-27 17:05:00"));
            b2.Add(B("5800", "2026-11-28 08:00:00"));
            b2.Add(B("5800", "2026-11-28 17:10:00"));
            h = LogDb.Simpan(c, "UJI-A", b2, "tarik", 5, "");
            Cek("L4", "sebagian lama, sebagian baru", h.Baru == 2 && h.Dilewati == 2 && LogDb.Jumlah(c, "UJI-A") == 5,
                "baru " + h.Baru + ", dilewati " + h.Dilewati);

            h = LogDb.Simpan(c, "UJI-B", a, "tarik", 3, "");
            Cek("L5", "mesin berbeda dengan ID dan waktu sama tetap disimpan", h.Baru == 3 && LogDb.Jumlah(c, null) == 8,
                "total " + LogDb.Jumlah(c, null));

            LogDb.CatatGagal(c, "UJI-C", "tarik", "tidak bisa terhubung");
            Cek("L6", "riwayat tarikan tercatat (4 berhasil + 1 gagal)",
                Skalar(c, "select count(*) from tarikan_log") == 5 &&
                Skalar(c, "select count(*) from tarikan_log where berhasil = 0") == 1 &&
                Skalar(c, "select sum(baru) from tarikan_log") == 8,
                "baris riwayat " + Skalar(c, "select count(*) from tarikan_log"));

            List<BarisLog> besar = new List<BarisLog>();
            DateTime awal = new DateTime(2026, 1, 1, 0, 0, 0);
            for (int i = 0; i < 20000; i++)
            {
                BarisLog x = new BarisLog();
                x.Id = (10000 + (i % 500)).ToString();
                x.Waktu = awal.AddMinutes(i);
                besar.Add(x);
            }
            Stopwatch sw = Stopwatch.StartNew();
            h = LogDb.Simpan(c, "UJI-BESAR", besar, "tarik", -1, "");
            sw.Stop();
            Cek("L7", "20.000 baris masuk dengan cepat (< 5 detik)", h.Baru == 20000 && sw.ElapsedMilliseconds < 5000,
                sw.ElapsedMilliseconds + " ms");
            Cek("L7b", "kolom di_mesin kosong bila tidak diketahui",
                Skalar(c, "select count(*) from tarikan_log where mesin='UJI-BESAR' and di_mesin is null") == 1, "");

            Jalankan2(c);
        }

        // Naik dari v3 ke v4: data lama utuh dan ada cadangan.
        Jalankan(berkas, "DROP TABLE log_absensi; DROP TABLE tarikan_log; PRAGMA user_version = 3; " +
            "INSERT INTO user_mesin (mesin, id_mesin, nama) VALUES ('UJI-A', '1', 'Nama Fiktif');");
        using (SQLiteConnection c2 = HdtDatabase.Buka(berkas))
        {
            Cek("L8", "naik dari v3 ke v4", Skalar(c2, "PRAGMA user_version") == 4 &&
                Skalar(c2, "select count(*) from sqlite_master where name in ('log_absensi','tarikan_log')") == 2, "");
            Cek("L8b", "data lama (user_mesin) utuh", Skalar(c2, "select count(*) from user_mesin") == 1, "");
        }
        string[] cad = Directory.GetFiles(folder, "hdt_sebelum_v4_*.sqlite");
        bool cadOk = cad.Length == 1;
        if (cadOk)
        {
            using (SQLiteConnection cc = new SQLiteConnection("Data Source=" + cad[0] + ";Version=3;"))
            {
                cc.Open();
                cadOk = Skalar(cc, "PRAGMA user_version") == 3 && Skalar(cc, "select count(*) from user_mesin") == 1;
            }
        }
        Cek("L9", "cadangan sebelum naik ada dan berisi data v3", cadOk, "berkas cadangan " + cad.Length);

        // Skema lebih baru ditolak.
        Jalankan(berkas, "PRAGMA user_version = 5;");
        bool ditolak = false;
        try { HdtDatabase.Buka(berkas).Dispose(); }
        catch (InvalidOperationException) { ditolak = true; }
        Cek("L10", "database skema lebih baru ditolak", ditolak, "");
    }

    static void Jalankan2(SQLiteConnection c)
    {
        Cek("L11", "indeks waktu dan id ada",
            Skalar(c, "select count(*) from sqlite_master where name in ('ix_log_waktu','ix_log_id_waktu')") == 2, "");
    }
}