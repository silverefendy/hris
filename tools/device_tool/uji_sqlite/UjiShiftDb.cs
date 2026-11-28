using System;
using System.Data.SQLite;
using System.IO;
using System.Text;
using HrisDeviceTool.Data;

public static class UjiShiftDb
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

    static string Aturan(string nama, string mulai, string selesai, int lewat, int durasi)
    {
        return "\"" + nama + "\":{\"start_time\":\"" + mulai + "\",\"end_time\":\"" + selesai + "\",\"crosses_midnight\":" + lewat
            + ",\"duration_minutes\":" + durasi + ",\"break_minutes\":60,\"late_tolerance_min\":0,\"early_leave_tolerance_min\":0,"
            + "\"window_before_min\":120,\"late_limit_min\":240,\"window_after_min\":240,\"min_out_after_in_min\":60,\"overtime_min_minutes\":30}";
    }

    static string Balasan(string dari, string sampai, string baris, int diproses, string peringatan)
    {
        return "{\"message\":{\"dari\":\"" + dari + "\",\"sampai\":\"" + sampai + "\","
            + "\"kolom\":[\"id\",\"tanggal\",\"shift\",\"wajib\",\"works\",\"libur\",\"off\",\"sumber\"],"
            + "\"baris\":[" + baris + "],\"shift\":{" + Aturan("Pagi Uji", "08:00:00", "17:00:00", 0, 540) + ","
            + Aturan("Malam Uji", "20:00:00", "08:00:00", 1, 720) + "},\"diproses\":" + diproses + ",\"peringatan\":[" + peringatan + "]}}";
    }

    static string B(string id, string tgl, string shift, int works, int libur)
    {
        return "[\"" + id + "\",\"" + tgl + "\",\"" + shift + "\",1," + works + "," + libur + ",0,\"Jadwal Mingguan\"]";
    }

    static bool Ditolak(string json)
    {
        try { ShiftDb.BacaRespons(json); return false; }
        catch (Exception) { return true; }
    }

    public static int Main()
    {
        string folder = Path.Combine(Path.GetTempPath(), "hdt_uji_shift_" + Guid.NewGuid().ToString("N"));
        try { Uji(folder); }
        catch (Exception e) { Console.WriteLine("GAGAL  galat tak terduga: " + e); gagal++; }
        finally { try { SQLiteConnection.ClearAllPools(); Directory.Delete(folder, true); } catch { } }
        Console.WriteLine();
        Console.WriteLine(gagal == 0 ? "SEMUA LULUS" : "ADA YANG GAGAL: " + gagal);
        return gagal == 0 ? 0 : 1;
    }

    static void Uji(string folder)
    {
        Console.WriteLine("Uji ShiftDb dan skema v5 (database sementara, data fiktif)");
        string json = Balasan("2026-11-01", "2026-11-30",
            B("5704", "2026-11-02", "Pagi Uji", 1, 0) + "," + B("5704", "2026-11-03", "", 0, 1) + "," + B("5800", "2026-11-02", "Malam Uji", 1, 0),
            2, "\"contoh peringatan\"");
        JadwalHris h = ShiftDb.BacaRespons(json);
        Cek("T1", "baca balasan: 3 baris, 2 shift, 2 karyawan", h.Baris.Count == 3 && h.Shift.Count == 2 && h.Diproses == 2, h.Baris.Count + " baris");
        Cek("T2", "isi baris libur tanpa shift terbaca", h.Baris[1].Shift == "" && h.Baris[1].Libur == 1 && h.Baris[1].Works == 0, "");
        AturanShift malam = null;
        foreach (AturanShift a in h.Shift) { if (a.Nama == "Malam Uji") { malam = a; } }
        Cek("T3", "aturan shift malam terbaca", malam != null && malam.LewatTengahMalam == 1 && malam.Durasi == 720 && malam.BatasTelat == 240, "");
        Cek("T4", "peringatan terbaca", h.Peringatan.Count == 1 && h.Peringatan[0] == "contoh peringatan", "");
        Cek("T5", "balasan bukan jadwal ditolak", Ditolak("{\"message\":\"x\"}") && Ditolak("<html>galat</html>") && Ditolak("{}"), "");
        Cek("T6", "tanggal di luar rentang ditolak",
            Ditolak(Balasan("2026-11-01", "2026-11-30", B("1", "2026-12-01", "Pagi Uji", 1, 0), 1, "")), "");

        StringBuilder besar = new StringBuilder();
        DateTime awal = new DateTime(2026, 10, 1);
        for (int i = 0; i < 1200; i++)
        {
            for (int d = 0; d < 61; d++)
            {
                if (besar.Length > 0) { besar.Append(','); }
                besar.Append(B((10000 + i).ToString(), awal.AddDays(d).ToString("yyyy-MM-dd"), "Pagi Uji", 1, 0));
            }
        }
        string jb = Balasan("2026-10-01", "2026-11-30", besar.ToString(), 1200, "");
        JadwalHris hb = ShiftDb.BacaRespons(jb);
        Cek("T7", "balasan besar (di atas batas bawaan 2 MB) terbaca", jb.Length > 4000000 && hb.Baris.Count == 73200, jb.Length + " karakter");

        string berkas = Path.Combine(folder, "uji.sqlite");
        using (SQLiteConnection c = HdtDatabase.Buka(berkas))
        {
            Cek("T8", "database baru berskema 5", Skalar(c, "PRAGMA user_version") == 5, "user_version " + Skalar(c, "PRAGMA user_version"));
            DateTime kini = new DateTime(2026, 11, 28, 14, 0, 0);
            System.Diagnostics.Stopwatch sw = System.Diagnostics.Stopwatch.StartNew();
            ShiftDb.Simpan(c, hb, kini);
            Cek("T9", "simpan 73.200 baris", Skalar(c, "select count(*) from jadwal_shift") == 73200, sw.ElapsedMilliseconds + " ms");
            ShiftDb.Simpan(c, h, kini);
            Cek("T10", "salin ulang November: hanya November diganti, Oktober utuh",
                Skalar(c, "select count(*) from jadwal_shift where tanggal >= '2026-11-01'") == 3
                && Skalar(c, "select count(*) from jadwal_shift where tanggal < '2026-11-01'") == 1200 * 31, "");
            Cek("T11", "aturan tidak berlipat", Skalar(c, "select count(*) from aturan_shift") == 2, "");
            Cek("T12", "riwayat salin tercatat", Skalar(c, "select count(*) from salin_shift") == 2, "");

            JadwalHris kosong = ShiftDb.BacaRespons(Balasan("2026-11-01", "2026-11-30", "", 0, ""));
            bool tolak = false;
            try { ShiftDb.Simpan(c, kosong, kini); } catch (InvalidOperationException) { tolak = true; }
            Cek("T13", "balasan kosong ditolak, data lama utuh",
                tolak && Skalar(c, "select count(*) from jadwal_shift where tanggal >= '2026-11-01'") == 3, "");

            JadwalHris dobel = ShiftDb.BacaRespons(Balasan("2026-11-01", "2026-11-30",
                B("1", "2026-11-02", "Pagi Uji", 1, 0) + "," + B("1", "2026-11-02", "Pagi Uji", 1, 0), 1, ""));
            bool galat = false;
            try { ShiftDb.Simpan(c, dobel, kini); } catch (SQLiteException) { galat = true; }
            Cek("T14", "gagal di tengah simpan: data lama utuh",
                galat && Skalar(c, "select count(*) from jadwal_shift where tanggal >= '2026-11-01'") == 3, "");
        }

        string lama = Path.Combine(folder, "lama", "uji.sqlite");
        using (SQLiteConnection c = HdtDatabase.Buka(lama))
        {
            using (SQLiteCommand cmd = new SQLiteCommand(
                "DROP TABLE jadwal_shift; DROP TABLE aturan_shift; DROP TABLE salin_shift; PRAGMA user_version = 4;"
                + "INSERT INTO log_absensi (mesin, id_mesin, waktu) VALUES ('UJI-A', '1', '2026-11-27 08:00:00')", c)) { cmd.ExecuteNonQuery(); }
        }
        SQLiteConnection.ClearAllPools();
        using (SQLiteConnection c = HdtDatabase.Buka(lama))
        {
            Cek("T15", "naik dari v4 ke v5, log lama utuh",
                Skalar(c, "PRAGMA user_version") == 5 && Skalar(c, "select count(*) from log_absensi") == 1
                && Skalar(c, "select count(*) from sqlite_master where name in ('jadwal_shift','aturan_shift','salin_shift')") == 3, "");
        }
        string[] cad = Directory.GetFiles(Path.Combine(folder, "lama"), "hdt_sebelum_v5_*.sqlite");
        Cek("T16", "cadangan dibuat sebelum naik versi", cad.Length == 1, cad.Length + " berkas");
    }
}