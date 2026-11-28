using System;
using System.Collections.Generic;
using System.Data.SQLite;
using System.Globalization;

namespace HrisDeviceTool.Data
{
    public class RincianTap
    {
        public string Id = "";
        public string Waktu = "";
        public string Mesin = "";
        public int Verifikasi;
        public int Status;
        public int WorkCode;
    }

    public class RekapOrang
    {
        public string Id = "";
        public string Nama = "";
        public string Departemen = "";
        public int Tap;
        public int Hari;
        public string Terakhir = "";
        public string Catatan = "";
    }

    public class StatusMesin
    {
        public string Mesin = "";
        public long TapDiDb;
        public string TapTerbaru = "";
        public string TerakhirDitarik = "";
        public long? LogDiMesin;
        public long? Kapasitas;
        public long? SelisihJam;
        public string InfoDiambil = "";
        public int Persen = -1;
        public List<string> Peringatan = new List<string>();

        public string TeksPeringatan { get { return string.Join("; ", Peringatan.ToArray()); } }
    }

    // Kueri laporan log absensi dari database lokal. Hanya membaca.
    public static class LaporanLog
    {
        const string Fmt = "yyyy-MM-dd HH:mm:ss";

        static string Fm(DateTime d) { return d.ToString(Fmt, CultureInfo.InvariantCulture); }

        static string T(SQLiteDataReader r, int i)
        {
            return r.IsDBNull(i) ? "" : Convert.ToString(r.GetValue(i), CultureInfo.InvariantCulture).Trim();
        }

        static long? N(SQLiteDataReader r, int i)
        {
            return r.IsDBNull(i) ? (long?)null : Convert.ToInt64(r.GetValue(i), CultureInfo.InvariantCulture);
        }

        static bool Baca(string s, out DateTime d)
        {
            return DateTime.TryParseExact(s, Fmt, CultureInfo.InvariantCulture, DateTimeStyles.None, out d);
        }

        // Periode: dari (termasuk) sampai sampai (tidak termasuk). mesin = null berarti semua mesin.
        public static List<RincianTap> Rincian(SQLiteConnection c, DateTime dari, DateTime sampai, string mesin)
        {
            List<RincianTap> h = new List<RincianTap>();
            string sql = "SELECT id_mesin, waktu, mesin, verifikasi, status, workcode FROM log_absensi WHERE waktu >= @a AND waktu < @b"
                + (mesin == null ? "" : " AND mesin = @m") + " ORDER BY waktu DESC, id_mesin";
            using (SQLiteCommand cmd = new SQLiteCommand(sql, c))
            {
                cmd.Parameters.AddWithValue("@a", Fm(dari));
                cmd.Parameters.AddWithValue("@b", Fm(sampai));
                if (mesin != null) { cmd.Parameters.AddWithValue("@m", mesin); }
                using (SQLiteDataReader r = cmd.ExecuteReader())
                {
                    while (r.Read())
                    {
                        RincianTap t = new RincianTap();
                        t.Id = T(r, 0);
                        t.Waktu = T(r, 1);
                        t.Mesin = T(r, 2);
                        t.Verifikasi = (int)(N(r, 3) ?? 0);
                        t.Status = (int)(N(r, 4) ?? 0);
                        t.WorkCode = (int)(N(r, 5) ?? 0);
                        h.Add(t);
                    }
                }
            }
            return h;
        }

        static bool AdaDiMesin(Karyawan k, string mesin)
        {
            foreach (RincianMesin m in k.Rincian) { if (string.Equals(m.Mesin, mesin, StringComparison.Ordinal)) { return true; } }
            return false;
        }

        public static List<RekapOrang> Rekap(SQLiteConnection c, DateTime dari, DateTime sampai, string mesin, IDictionary<string, Karyawan> orang)
        {
            Dictionary<string, RekapOrang> peta = new Dictionary<string, RekapOrang>(StringComparer.Ordinal);
            string sql = "SELECT id_mesin, COUNT(*), COUNT(DISTINCT substr(waktu, 1, 10)), MAX(waktu) FROM log_absensi WHERE waktu >= @a AND waktu < @b"
                + (mesin == null ? "" : " AND mesin = @m") + " GROUP BY id_mesin";
            using (SQLiteCommand cmd = new SQLiteCommand(sql, c))
            {
                cmd.Parameters.AddWithValue("@a", Fm(dari));
                cmd.Parameters.AddWithValue("@b", Fm(sampai));
                if (mesin != null) { cmd.Parameters.AddWithValue("@m", mesin); }
                using (SQLiteDataReader r = cmd.ExecuteReader())
                {
                    while (r.Read())
                    {
                        RekapOrang x = new RekapOrang();
                        x.Id = T(r, 0);
                        x.Tap = (int)(N(r, 1) ?? 0);
                        x.Hari = (int)(N(r, 2) ?? 0);
                        x.Terakhir = T(r, 3);
                        peta[x.Id] = x;
                    }
                }
            }
            foreach (KeyValuePair<string, Karyawan> kv in orang)
            {
                if (mesin != null && !AdaDiMesin(kv.Value, mesin)) { continue; }
                if (!peta.ContainsKey(kv.Key))
                {
                    RekapOrang n = new RekapOrang();
                    n.Id = kv.Key;
                    peta[kv.Key] = n;
                }
            }
            List<RekapOrang> hasil = new List<RekapOrang>(peta.Values);
            foreach (RekapOrang x in hasil)
            {
                Karyawan k;
                if (orang.TryGetValue(x.Id, out k))
                {
                    x.Nama = k.Nama;
                    x.Departemen = k.Departemen;
                    if (mesin != null && !AdaDiMesin(k, mesin)) { x.Catatan = "User tidak terdaftar di mesin ini"; }
                }
                else
                {
                    x.Catatan = "ID tidak ada di data user";
                }
                if (x.Tap == 0) { x.Catatan = "Tidak pernah tap"; }
            }
            hasil.Sort(delegate (RekapOrang a, RekapOrang b) { return DaftarKaryawan.BandingId(a.Id, b.Id); });
            return hasil;
        }

        public static List<StatusMesin> Status(SQLiteConnection c, DateTime sekarang)
        {
            List<string> nama = new List<string>();
            using (SQLiteCommand cmd = new SQLiteCommand("SELECT nama FROM mesin UNION SELECT DISTINCT mesin FROM log_absensi ORDER BY 1", c))
            using (SQLiteDataReader r = cmd.ExecuteReader())
            {
                while (r.Read()) { string n = T(r, 0); if (n.Length > 0) { nama.Add(n); } }
            }
            List<StatusMesin> hasil = new List<StatusMesin>();
            foreach (string n in nama)
            {
                StatusMesin s = new StatusMesin();
                s.Mesin = n;
                using (SQLiteCommand q = new SQLiteCommand("SELECT jumlah_log, kapasitas_log, selisih_jam_detik, info_diambil FROM mesin WHERE nama = @m", c))
                {
                    q.Parameters.AddWithValue("@m", n);
                    using (SQLiteDataReader r = q.ExecuteReader())
                    {
                        if (r.Read())
                        {
                            s.LogDiMesin = N(r, 0);
                            s.Kapasitas = N(r, 1);
                            s.SelisihJam = N(r, 2);
                            s.InfoDiambil = T(r, 3);
                        }
                    }
                }
                using (SQLiteCommand q = new SQLiteCommand("SELECT COUNT(*), MAX(waktu) FROM log_absensi WHERE mesin = @m", c))
                {
                    q.Parameters.AddWithValue("@m", n);
                    using (SQLiteDataReader r = q.ExecuteReader())
                    {
                        if (r.Read()) { s.TapDiDb = N(r, 0) ?? 0; s.TapTerbaru = T(r, 1); }
                    }
                }
                using (SQLiteCommand q = new SQLiteCommand("SELECT MAX(selesai) FROM tarikan_log WHERE mesin = @m AND sumber = 'tarik' AND berhasil = 1", c))
                {
                    q.Parameters.AddWithValue("@m", n);
                    s.TerakhirDitarik = Convert.ToString(q.ExecuteScalar(), CultureInfo.InvariantCulture);
                }

                DateTime t;
                if (s.TapDiDb == 0) { s.Peringatan.Add("Belum ada log di database"); }
                else if (Baca(s.TapTerbaru, out t) && (sekarang - t).TotalDays > 7) { s.Peringatan.Add("Log terbaru lebih dari 7 hari lalu (belum ditarik?)"); }
                if (s.LogDiMesin.HasValue && s.Kapasitas.HasValue && s.Kapasitas.Value > 0)
                {
                    s.Persen = (int)(s.LogDiMesin.Value * 100 / s.Kapasitas.Value);
                    if (s.Persen >= 80) { s.Peringatan.Add("Log mesin " + s.Persen + "% dari kapasitas"); }
                }
                if (s.SelisihJam.HasValue && Math.Abs(s.SelisihJam.Value) > 60) { s.Peringatan.Add("Jam mesin beda " + s.SelisihJam.Value + " dtk"); }
                hasil.Add(s);
            }
            return hasil;
        }

        // Mesin yang log terbarunya jauh sebelum akhir periode, sehingga rekap bisa kurang.
        public static List<string> MesinBelumLengkap(List<StatusMesin> status, string mesin, DateTime sampaiEksklusif, DateTime sekarang)
        {
            DateTime akhir = sampaiEksklusif.AddSeconds(-1);
            if (akhir > sekarang) { akhir = sekarang; }
            DateTime batas = akhir.Date.AddDays(-3);
            List<string> h = new List<string>();
            foreach (StatusMesin s in status)
            {
                if (mesin != null && s.Mesin != mesin) { continue; }
                DateTime t;
                if (s.TapDiDb == 0) { h.Add(s.Mesin + " (belum ada log)"); }
                else if (Baca(s.TapTerbaru, out t) && t < batas) { h.Add(s.Mesin); }
            }
            return h;
        }
    }
}