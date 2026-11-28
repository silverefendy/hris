using System;
using System.Collections.Generic;
using System.Data.SQLite;
using System.IO;
using HrisDeviceTool.Data;

public static class UjiLaporanLog
{
    static int gagal = 0;

    static void Cek(string kode, string uraian, bool ok, string info)
    {
        if (!ok) { gagal++; }
        Console.WriteLine((ok ? "OK     " : "GAGAL  ") + kode + " " + uraian + (info.Length > 0 ? "  |  " + info : ""));
    }

    static void Exec(SQLiteConnection c, string sql)
    {
        using (SQLiteCommand cmd = new SQLiteCommand(sql, c)) { cmd.ExecuteNonQuery(); }
    }

    static void Tap(SQLiteConnection c, string mesin, string id, string waktu)
    {
        Exec(c, "INSERT INTO log_absensi (mesin, id_mesin, waktu, verifikasi, status, workcode) VALUES ('" + mesin + "', '" + id + "', '" + waktu + "', 1, 0, 0)");
    }

    static RekapOrang Cari(List<RekapOrang> l, string id)
    {
        foreach (RekapOrang x in l) { if (x.Id == id) { return x; } }
        return null;
    }

    public static int Main()
    {
        string akar = Path.Combine(Path.GetTempPath(), "hdt_uji_laporan_" + Guid.NewGuid().ToString("N"));
        try { Uji(Path.Combine(akar, "uji.sqlite")); }
        catch (Exception e) { Console.WriteLine("GAGAL  galat tak terduga: " + e); gagal++; }
        finally { try { SQLiteConnection.ClearAllPools(); Directory.Delete(akar, true); } catch { } }
        Console.WriteLine();
        Console.WriteLine(gagal == 0 ? "SEMUA LULUS" : "ADA YANG GAGAL: " + gagal);
        return gagal == 0 ? 0 : 1;
    }

    static void Uji(string berkas)
    {
        Console.WriteLine("Uji LaporanLog (database sementara, data fiktif)");
        using (SQLiteConnection c = HdtDatabase.Buka(berkas))
        {
            Exec(c, "INSERT INTO user_mesin (mesin, id_mesin, nama, privilege, aktif) VALUES ('UJI-A', '5704', 'Nama A', 0, 1)");
            Exec(c, "INSERT INTO user_mesin (mesin, id_mesin, nama, privilege, aktif) VALUES ('UJI-A', '5800', 'Nama B', 0, 1)");
            Exec(c, "INSERT INTO user_mesin (mesin, id_mesin, nama, privilege, aktif) VALUES ('UJI-A', '9999', 'Tanpa Tap', 0, 1)");
            Exec(c, "INSERT INTO user_mesin (mesin, id_mesin, nama, privilege, aktif) VALUES ('UJI-B', '5704', 'NAMA A', 0, 1)");
            Exec(c, "INSERT INTO mesin (nama, ip, jumlah_log, kapasitas_log, selisih_jam_detik, info_diambil) VALUES ('UJI-A', '', 900, 1000, 120, '2026-11-28 08:00:00')");
            Exec(c, "INSERT INTO mesin (nama, ip) VALUES ('UJI-C', '')");

            Tap(c, "UJI-A", "5704", "2026-11-27 07:55:00");
            Tap(c, "UJI-A", "5704", "2026-11-27 07:56:00");
            Tap(c, "UJI-A", "5704", "2026-11-27 17:05:00");
            Tap(c, "UJI-A", "5800", "2026-11-28 08:00:00");
            Tap(c, "UJI-A", "5800", "2026-11-01 00:00:00");
            Tap(c, "UJI-A", "7777", "2026-11-27 09:00:00");
            Tap(c, "UJI-B", "5704", "2026-11-26 08:00:00");
            Tap(c, "UJI-B", "5800", "2026-10-31 23:59:59");
            Tap(c, "UJI-B", "5800", "2026-12-01 00:00:00");
            Tap(c, "UJI-OLD", "1", "2026-11-10 08:00:00");

            DateTime dari = new DateTime(2026, 11, 1);
            DateTime sampai = new DateTime(2026, 12, 1);
            DateTime sekarang = new DateTime(2026, 11, 28, 12, 0, 0);

            List<RincianTap> rin = LaporanLog.Rincian(c, dari, sampai, null);
            Cek("R1", "rincian: batas periode benar (8 tap)", rin.Count == 8, "jumlah " + rin.Count);
            Cek("R2", "rincian: terbaru di atas", rin.Count > 0 && rin[0].Waktu == "2026-11-28 08:00:00", rin.Count > 0 ? rin[0].Waktu : "");
            Cek("R3", "rincian: saring mesin", LaporanLog.Rincian(c, dari, sampai, "UJI-B").Count == 1, "");

            Dictionary<string, Karyawan> orang = new Dictionary<string, Karyawan>();
            foreach (Karyawan k in DaftarKaryawan.Muat(c)) { orang[k.Id] = k; }
            List<RekapOrang> rek = LaporanLog.Rekap(c, dari, sampai, null, orang);
            Cek("K1", "rekap: 5 baris (4 ID + 1 tak dikenal)", rek.Count == 5, "jumlah " + rek.Count);
            RekapOrang a = Cari(rek, "5704");
            Cek("K2", "rekap 5704: 4 tap, 2 hari, lintas mesin", a != null && a.Tap == 4 && a.Hari == 2, a == null ? "tidak ada" : a.Tap + " tap, " + a.Hari + " hari");
            RekapOrang b = Cari(rek, "5800");
            Cek("K3", "rekap 5800: batas awal masuk, batas akhir tidak", b != null && b.Tap == 2, b == null ? "tidak ada" : "tap " + b.Tap);
            RekapOrang n = Cari(rek, "9999");
            Cek("K4", "rekap 9999: tidak pernah tap", n != null && n.Tap == 0 && n.Catatan == "Tidak pernah tap", n == null ? "tidak ada" : n.Catatan);
            RekapOrang x = Cari(rek, "7777");
            Cek("K5", "rekap 7777: ID tanpa data user ditandai", x != null && x.Tap == 1 && x.Catatan.StartsWith("ID tidak ada"), x == null ? "tidak ada" : x.Catatan);
            Cek("K6", "rekap: nama dan departemen terisi dari data lokal", a != null && a.Nama.Length > 0, a == null ? "" : a.Nama);
            List<RekapOrang> rekB = LaporanLog.Rekap(c, dari, sampai, "UJI-B", orang);
            Cek("K7", "rekap saring mesin UJI-B: 1 baris, 1 tap", rekB.Count == 1 && rekB[0].Id == "5704" && rekB[0].Tap == 1, "jumlah " + rekB.Count);

            List<StatusMesin> st = LaporanLog.Status(c, sekarang);
            string urut = "";
            foreach (StatusMesin s in st) { urut += s.Mesin + " "; }
            Cek("S1", "status: 4 mesin, terurut", st.Count == 4 && urut.Trim() == "UJI-A UJI-B UJI-C UJI-OLD", urut.Trim());
            StatusMesin sa = st[0];
            Cek("S2", "status UJI-A: 90% dan 2 peringatan", sa.Persen == 90 && sa.Peringatan.Count == 2 && sa.TapDiDb == 6, "persen " + sa.Persen + ", " + sa.TeksPeringatan);
            Cek("S3", "status UJI-C: belum ada log", st[2].TapDiDb == 0 && st[2].TeksPeringatan.StartsWith("Belum ada log"), st[2].TeksPeringatan);
            Cek("S4", "status UJI-OLD: lebih dari 7 hari", st[3].TeksPeringatan.Contains("7 hari"), st[3].TeksPeringatan);
            Cek("S5", "status UJI-B: tidak diperingatkan", st[1].Peringatan.Count == 0, st[1].TeksPeringatan);

            List<string> belum = LaporanLog.MesinBelumLengkap(st, null, sampai, sekarang);
            Cek("P1", "mesin belum lengkap: UJI-C dan UJI-OLD", belum.Count == 2, string.Join(", ", belum.ToArray()));
        }
    }
}