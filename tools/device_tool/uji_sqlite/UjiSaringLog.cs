using System;
using System.Collections.Generic;
using System.Globalization;
using HrisDeviceTool.Data;

public static class UjiSaringLog
{
    static int gagal = 0;

    static void Cek(string kode, string uraian, bool ok, string info)
    {
        if (!ok) { gagal++; }
        Console.WriteLine((ok ? "OK     " : "GAGAL  ") + kode + " " + uraian + (info.Length > 0 ? "  |  " + info : ""));
    }

    static DateTime W(string s)
    {
        return DateTime.ParseExact(s, "yyyy-MM-dd HH:mm:ss", CultureInfo.InvariantCulture);
    }

    static BarisLog B(string id, string w)
    {
        BarisLog b = new BarisLog();
        b.Id = id;
        b.Waktu = W(w);
        return b;
    }

    public static int Main()
    {
        Console.WriteLine("Uji SaringLog (data fiktif)");
        List<BarisLog> l = new List<BarisLog>();
        l.Add(B("1", "2026-10-31 23:59:59"));
        l.Add(B("2", "2026-11-01 00:00:00"));
        l.Add(B("3", "2026-11-15 08:00:00"));
        l.Add(B("4", "2026-11-30 23:59:59"));
        l.Add(B("5", "2026-12-01 00:00:00"));

        int n1 = SaringLog.Tanggal(l, null, null).Count;
        Cek("T1", "tanpa batas: semua 5", n1 == 5, "hasil " + n1);
        int n2 = SaringLog.Tanggal(l, W("2026-11-01 00:00:00"), W("2026-12-01 00:00:00")).Count;
        Cek("T2", "November: awal masuk, akhir (eksklusif) tidak, hasil 3", n2 == 3, "hasil " + n2);
        int n3 = SaringLog.Tanggal(l, W("2026-11-15 08:00:00"), null).Count;
        Cek("T3", "dari saja (termasuk): 3", n3 == 3, "hasil " + n3);
        int n4 = SaringLog.Tanggal(l, null, W("2026-11-01 00:00:00")).Count;
        Cek("T4", "sampai saja (eksklusif): 1", n4 == 1, "hasil " + n4);
        int n5 = SaringLog.Tanggal(l, null, W("2026-11-15 08:00:00")).Count;
        Cek("T5", "batas eksklusif tepat pada baris: baris itu tidak masuk, hasil 2", n5 == 2, "hasil " + n5);
        int n6 = SaringLog.Tanggal(new List<BarisLog>(), W("2026-11-01 00:00:00"), null).Count;
        Cek("T6", "daftar kosong: 0", n6 == 0, "hasil " + n6);
        Cek("T7", "daftar asli tidak berubah", l.Count == 5, "jumlah " + l.Count);

        Console.WriteLine();
        Console.WriteLine(gagal == 0 ? "SEMUA LULUS" : "ADA YANG GAGAL: " + gagal);
        return gagal == 0 ? 0 : 1;
    }
}