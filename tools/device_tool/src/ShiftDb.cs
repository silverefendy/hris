using System;
using System.Collections;
using System.Collections.Generic;
using System.Data.SQLite;
using System.Globalization;
using System.Web.Script.Serialization;

namespace HrisDeviceTool.Data
{
    public class JadwalBaris
    {
        public string Id = "";
        public string Tanggal = "";
        public string Shift = "";
        public int Wajib;
        public int Works;
        public int Libur;
        public int Off;
        public string Sumber = "";
    }

    public class AturanShift
    {
        public string Nama = "";
        public string Mulai = "";
        public string Selesai = "";
        public int LewatTengahMalam;
        public int Durasi;
        public int Istirahat;
        public int ToleransiTelat;
        public int ToleransiPulang;
        public int JendelaSebelum;
        public int BatasTelat;
        public int JendelaSesudah;
        public int MinPulang;
        public int LemburMin;
    }

    public class JadwalHris
    {
        public DateTime Dari;
        public DateTime Sampai;
        public List<JadwalBaris> Baris = new List<JadwalBaris>();
        public List<AturanShift> Shift = new List<AturanShift>();
        public int Diproses;
        public List<string> Peringatan = new List<string>();
    }

    // Jadwal shift dari HRIS: membaca balasan server dan menyimpannya ke database lokal.
    // Tidak menyentuh jaringan maupun mesin.
    public static class ShiftDb
    {
        public const int MaksHari = 62;
        const string FmtTanggal = "yyyy-MM-dd";

        static IDictionary<string, object> Objek(object o, string nama)
        {
            IDictionary<string, object> d = o as IDictionary<string, object>;
            if (d == null) { throw new FormatException("Balasan server tidak sesuai: bagian \"" + nama + "\" tidak ada."); }
            return d;
        }

        static object Ambil(IDictionary<string, object> d, string kunci)
        {
            object v;
            if (!d.TryGetValue(kunci, out v)) { throw new FormatException("Balasan server tidak sesuai: \"" + kunci + "\" tidak ada."); }
            return v;
        }

        static IList Daftar(object o, string nama)
        {
            IList l = o as IList;
            if (l == null) { throw new FormatException("Balasan server tidak sesuai: \"" + nama + "\" bukan daftar."); }
            return l;
        }

        static string Teks(object o)
        {
            return o == null ? "" : Convert.ToString(o, CultureInfo.InvariantCulture).Trim();
        }

        static int Angka(object o)
        {
            return o == null ? 0 : Convert.ToInt32(o, CultureInfo.InvariantCulture);
        }

        static DateTime Tanggal(string s)
        {
            DateTime d;
            if (!DateTime.TryParseExact(s, FmtTanggal, CultureInfo.InvariantCulture, DateTimeStyles.None, out d))
            {
                throw new FormatException("Tanggal dari server tidak dikenali: " + s);
            }
            return d;
        }

        public static JadwalHris BacaRespons(string json)
        {
            JavaScriptSerializer js = new JavaScriptSerializer();
            js.MaxJsonLength = int.MaxValue;
            IDictionary<string, object> akar = Objek(js.DeserializeObject(json), "akar");
            IDictionary<string, object> m = Objek(Ambil(akar, "message"), "message");

            JadwalHris h = new JadwalHris();
            h.Dari = Tanggal(Teks(Ambil(m, "dari")));
            h.Sampai = Tanggal(Teks(Ambil(m, "sampai")));
            h.Diproses = Angka(Ambil(m, "diproses"));
            foreach (object p in Daftar(Ambil(m, "peringatan"), "peringatan")) { h.Peringatan.Add(Teks(p)); }

            List<string> kolom = new List<string>();
            foreach (object k in Daftar(Ambil(m, "kolom"), "kolom")) { kolom.Add(Teks(k)); }
            string[] perlu = new string[] { "id", "tanggal", "shift", "wajib", "works", "libur", "off", "sumber" };
            int[] p2 = new int[perlu.Length];
            for (int i = 0; i < perlu.Length; i++)
            {
                p2[i] = kolom.IndexOf(perlu[i]);
                if (p2[i] < 0) { throw new FormatException("Kolom \"" + perlu[i] + "\" tidak ada di balasan server."); }
            }

            foreach (object o in Daftar(Ambil(m, "baris"), "baris"))
            {
                IList r = Daftar(o, "isi baris");
                if (r.Count != kolom.Count) { throw new FormatException("Jumlah kolom pada satu baris tidak sama."); }
                JadwalBaris b = new JadwalBaris();
                b.Id = Teks(r[p2[0]]);
                b.Tanggal = Teks(r[p2[1]]);
                b.Shift = Teks(r[p2[2]]);
                b.Wajib = Angka(r[p2[3]]);
                b.Works = Angka(r[p2[4]]);
                b.Libur = Angka(r[p2[5]]);
                b.Off = Angka(r[p2[6]]);
                b.Sumber = Teks(r[p2[7]]);
                DateTime t = Tanggal(b.Tanggal);
                if (b.Id.Length == 0 || t < h.Dari || t > h.Sampai)
                {
                    throw new FormatException("Baris jadwal tidak sah (ID kosong atau tanggal di luar rentang): " + b.Tanggal);
                }
                h.Baris.Add(b);
            }

            foreach (KeyValuePair<string, object> kv in Objek(Ambil(m, "shift"), "shift"))
            {
                IDictionary<string, object> d = Objek(kv.Value, kv.Key);
                AturanShift a = new AturanShift();
                a.Nama = kv.Key;
                a.Mulai = Teks(Ambil(d, "start_time"));
                a.Selesai = Teks(Ambil(d, "end_time"));
                a.LewatTengahMalam = Angka(Ambil(d, "crosses_midnight"));
                a.Durasi = Angka(Ambil(d, "duration_minutes"));
                a.Istirahat = Angka(Ambil(d, "break_minutes"));
                a.ToleransiTelat = Angka(Ambil(d, "late_tolerance_min"));
                a.ToleransiPulang = Angka(Ambil(d, "early_leave_tolerance_min"));
                a.JendelaSebelum = Angka(Ambil(d, "window_before_min"));
                a.BatasTelat = Angka(Ambil(d, "late_limit_min"));
                a.JendelaSesudah = Angka(Ambil(d, "window_after_min"));
                a.MinPulang = Angka(Ambil(d, "min_out_after_in_min"));
                a.LemburMin = Angka(Ambil(d, "overtime_min_minutes"));
                h.Shift.Add(a);
            }
            return h;
        }

        static void Jalan(SQLiteConnection c, SQLiteTransaction t, string sql, params object[] nilai)
        {
            using (SQLiteCommand cmd = new SQLiteCommand(sql, c, t))
            {
                for (int i = 0; i < nilai.Length; i++) { cmd.Parameters.AddWithValue("@p" + i, nilai[i]); }
                cmd.ExecuteNonQuery();
            }
        }

        // Mengganti jadwal lokal pada rentang tanggal yang disalin, beserta seluruh aturan shift.
        // Satu transaksi: bila gagal, data lama tetap utuh.
        public static void Simpan(SQLiteConnection c, JadwalHris h, DateTime sekarang)
        {
            if (h.Baris.Count == 0)
            {
                throw new InvalidOperationException("Server tidak mengirim satu pun baris jadwal. Data lama tidak diubah.");
            }
            string waktu = sekarang.ToString("yyyy-MM-dd HH:mm:ss", CultureInfo.InvariantCulture);
            string dari = h.Dari.ToString(FmtTanggal, CultureInfo.InvariantCulture);
            string sampai = h.Sampai.ToString(FmtTanggal, CultureInfo.InvariantCulture);
            using (SQLiteTransaction t = c.BeginTransaction())
            {
                Jalan(c, t, "DELETE FROM jadwal_shift WHERE tanggal >= @p0 AND tanggal <= @p1", dari, sampai);
                using (SQLiteCommand cmd = new SQLiteCommand(
                    "INSERT INTO jadwal_shift (id_mesin, tanggal, shift, wajib, works, libur, off, sumber) "
                    + "VALUES (@id, @tgl, @shift, @wajib, @works, @libur, @off, @sumber)", c, t))
                {
                    string[] nama = new string[] { "@id", "@tgl", "@shift", "@wajib", "@works", "@libur", "@off", "@sumber" };
                    foreach (string n in nama) { cmd.Parameters.Add(new SQLiteParameter(n)); }
                    foreach (JadwalBaris b in h.Baris)
                    {
                        object[] v = new object[] { b.Id, b.Tanggal, b.Shift, b.Wajib, b.Works, b.Libur, b.Off, b.Sumber };
                        for (int i = 0; i < v.Length; i++) { cmd.Parameters[i].Value = v[i]; }
                        cmd.ExecuteNonQuery();
                    }
                }
                Jalan(c, t, "DELETE FROM aturan_shift");
                foreach (AturanShift a in h.Shift)
                {
                    Jalan(c, t, "INSERT INTO aturan_shift (nama, mulai, selesai, lewat_tengah_malam, durasi, istirahat, toleransi_telat, "
                        + "toleransi_pulang, jendela_sebelum, batas_telat, jendela_sesudah, min_pulang, lembur_min) "
                        + "VALUES (@p0, @p1, @p2, @p3, @p4, @p5, @p6, @p7, @p8, @p9, @p10, @p11, @p12)",
                        a.Nama, a.Mulai, a.Selesai, a.LewatTengahMalam, a.Durasi, a.Istirahat, a.ToleransiTelat,
                        a.ToleransiPulang, a.JendelaSebelum, a.BatasTelat, a.JendelaSesudah, a.MinPulang, a.LemburMin);
                }
                Jalan(c, t, "INSERT INTO salin_shift (waktu, dari, sampai, baris, karyawan, peringatan) VALUES (@p0, @p1, @p2, @p3, @p4, @p5)",
                    waktu, dari, sampai, h.Baris.Count, h.Diproses, string.Join("; ", h.Peringatan.ToArray()));
                t.Commit();
            }
        }
    }
}