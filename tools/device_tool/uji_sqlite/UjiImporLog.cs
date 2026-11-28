using System;
using System.Collections.Generic;
using System.Data.SQLite;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using HrisDeviceTool.Data;

public static class UjiImporLog
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

    static string Hash(string p)
    {
        using (SHA256 s = SHA256.Create())
        {
            StringBuilder sb = new StringBuilder();
            foreach (byte x in s.ComputeHash(File.ReadAllBytes(p))) { sb.Append(x.ToString("x2")); }
            return sb.ToString();
        }
    }

    static void Tulis(string folder, string nama, string[] baris, string mesin, string shaPaksa)
    {
        string csv = Path.Combine(folder, nama + ".csv");
        File.WriteAllText(csv, string.Join("\r\n", baris) + "\r\n", new UTF8Encoding(false));
        string sha = shaPaksa != null ? shaPaksa : Hash(csv);
        File.WriteAllText(Path.Combine(folder, nama + ".hdtman"),
            "format=hdt-log-1\r\nmesin=" + mesin + "\r\nsha256=" + sha + "\r\n", new UTF8Encoding(false));
    }

    public static int Main()
    {
        string akar = Path.Combine(Path.GetTempPath(), "hdt_uji_imporlog_" + Guid.NewGuid().ToString("N"));
        string folder = Path.Combine(akar, "tarikan");
        Directory.CreateDirectory(folder);
        try { Uji(akar, folder); }
        catch (Exception e) { Console.WriteLine("GAGAL  galat tak terduga: " + e); gagal++; }
        finally { try { SQLiteConnection.ClearAllPools(); Directory.Delete(akar, true); } catch { } }
        Console.WriteLine();
        Console.WriteLine(gagal == 0 ? "SEMUA LULUS" : "ADA YANG GAGAL: " + gagal);
        return gagal == 0 ? 0 : 1;
    }

    static void Uji(string akar, string folder)
    {
        string head = "device_user_id;punch_time;verify_mode;punch_status_raw;workcode";
        Tulis(folder, "a_ok", new string[] { head, "5704;2026-11-27 07:55:00;1;0;0", "5704;2026-11-27 17:05:00;1;1;0", "5800;2026-11-27 08:00:00;15;0;0", "abc;bukan-waktu;1;0;0" }, "UJI-A", null);
        Tulis(folder, "b_sha_salah", new string[] { head, "1;2026-11-27 07:00:00;1;0;0" }, "UJI-A", "0000");
        File.WriteAllText(Path.Combine(folder, "c_tanpa_csv.hdtman"), "mesin=UJI-A\r\nsha256=abc\r\n");
        Tulis(folder, "d_tumpang", new string[] { head, "5704;2026-11-27 07:55:00;1;0;0", "5800;2026-11-27 08:00:00;15;0;0", "5900;2026-11-28 08:10:00;1;0;0" }, "UJI-A", null);
        Tulis(folder, "e_mesin_lain", new string[] { head, "5704;2026-11-27 07:55:00;1;0;0" }, "UJI-B", null);

        using (SQLiteConnection c = HdtDatabase.Buka(Path.Combine(akar, "uji.sqlite")))
        {
            HasilImporLog h = ImporLog.Folder(c, folder, null);
            Cek("M1", "berkas valid diimpor (a, d, e)", h.BerkasDiimpor == 3, "diimpor " + h.BerkasDiimpor);
            Cek("M2", "sha salah dan tanpa csv dilewati", h.BerkasDilewati == 2, "dilewati " + h.BerkasDilewati);
            Cek("M3", "baris rusak dihitung", h.Rusak == 1, "rusak " + h.Rusak);
            Cek("M4", "baris baru benar (3 + 1 + 1)", h.Baru == 5 && LogDb.Jumlah(c, null) == 5, "baru " + h.Baru + ", total " + LogDb.Jumlah(c, null));
            Cek("M5", "mesin berbeda tidak bentrok", LogDb.Jumlah(c, "UJI-A") == 4 && LogDb.Jumlah(c, "UJI-B") == 1, "");
            Cek("M6", "riwayat impor tercatat 3", Skalar(c, "select count(*) from tarikan_log where sumber='impor-csv'") == 3, "");

            HasilImporLog h2 = ImporLog.Folder(c, folder, null);
            Cek("M7", "impor ulang: tidak ada yang diimpor lagi", h2.BerkasDiimpor == 0 && h2.Baru == 0 && LogDb.Jumlah(c, null) == 5,
                "diimpor " + h2.BerkasDiimpor + ", total " + LogDb.Jumlah(c, null));
        }
    }
}