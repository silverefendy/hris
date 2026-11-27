using System;
using System.Collections.Generic;
using System.Data.SQLite;
using System.Globalization;
using System.Text;

namespace HrisDeviceTool.Data
{
    // Satu karyawan di satu mesin (satu baris tabel user_mesin).
    public class RincianMesin
    {
        public string Mesin = "";
        public string Nama = "";
        public string Diambil = "";
        public int Privilege;
        public bool Aktif;
        public bool AdaKartu;
        public int Jari = -1; // -1 = template mesin ini belum pernah diambil
    }

    // Satu baris daftar gabungan: satu ID, bisa ada di banyak mesin.
    public class Karyawan
    {
        public string Id = "";
        public string Nama = "";
        public string Departemen = "";
        public List<RincianMesin> Rincian = new List<RincianMesin>();
        public int JariTersimpan; // jumlah nomor jari berbeda yang templatenya ada di database
        public bool NamaBeda;
        public int Jari = -1;     // terbanyak di satu mesin; -1 = belum diketahui

        public bool TanpaJari { get { return Jari == 0; } }
        public bool HanyaSatuMesin { get { return Rincian.Count == 1; } }

        public string DaftarMesin
        {
            get
            {
                List<string> n = new List<string>();
                foreach (RincianMesin r in Rincian) { n.Add(r.Mesin); }
                return string.Join(", ", n.ToArray());
            }
        }

        public string TeksJari { get { return Jari < 0 ? "?" : Jari.ToString(CultureInfo.InvariantCulture); } }

        public string Catatan
        {
            get
            {
                List<string> c = new List<string>();
                if (NamaBeda) { c.Add("Nama berbeda"); }
                if (TanpaJari) { c.Add("Tanpa sidik jari"); }
                if (Jari < 0) { c.Add("Jari belum diambil"); }
                return string.Join(", ", c.ToArray());
            }
        }
    }

    public enum SaringKaryawan { Semua = 0, NamaBeda = 1, TanpaJari = 2, SatuMesin = 3 }

    // Daftar karyawan gabungan dari database lokal. Hanya membaca.
    public static class DaftarKaryawan
    {
        public static List<Karyawan> Muat(SQLiteConnection c)
        {
            Dictionary<string, Karyawan> peta = new Dictionary<string, Karyawan>(StringComparer.Ordinal);

            using (SQLiteCommand cmd = new SQLiteCommand(
                "select id_mesin, mesin, nama, privilege, aktif, nomor_kartu, jumlah_jari, diambil from user_mesin order by mesin", c))
            using (SQLiteDataReader r = cmd.ExecuteReader())
            {
                while (r.Read())
                {
                    string id = Teks(r, 0);
                    if (id.Length == 0) { continue; }
                    Karyawan k;
                    if (!peta.TryGetValue(id, out k))
                    {
                        k = new Karyawan();
                        k.Id = id;
                        peta[id] = k;
                    }
                    RincianMesin m = new RincianMesin();
                    m.Mesin = Teks(r, 1);
                    m.Nama = Teks(r, 2);
                    m.Privilege = Angka(r, 3, 0);
                    m.Aktif = Angka(r, 4, 0) != 0;
                    m.AdaKartu = Teks(r, 5).Length > 0;
                    m.Jari = Angka(r, 6, -1);
                    m.Diambil = Teks(r, 7);
                    k.Rincian.Add(m);
                }
            }

            using (SQLiteCommand cmd = new SQLiteCommand(
                "select id_mesin, count(distinct jari) from template_jari group by id_mesin", c))
            using (SQLiteDataReader r = cmd.ExecuteReader())
            {
                while (r.Read())
                {
                    Karyawan k;
                    if (peta.TryGetValue(Teks(r, 0), out k)) { k.JariTersimpan = Angka(r, 1, 0); }
                }
            }

            // Departemen: salinan HRIS didahulukan, lalu data aplikasi absensi lama.
            IsiDepartemen(c, "select id_finger, department from karyawan_hris", peta);
            IsiDepartemen(c, "select id_akun, departemen from induk_aplikasi_lama", peta);

            List<Karyawan> hasil = new List<Karyawan>(peta.Values);
            foreach (Karyawan k in hasil) { Hitung(k); }
            hasil.Sort(delegate (Karyawan a, Karyawan b) { return BandingId(a.Id, b.Id); });
            return hasil;
        }

        static void IsiDepartemen(SQLiteConnection c, string sql, Dictionary<string, Karyawan> peta)
        {
            using (SQLiteCommand cmd = new SQLiteCommand(sql, c))
            using (SQLiteDataReader r = cmd.ExecuteReader())
            {
                while (r.Read())
                {
                    Karyawan k;
                    string dept = Teks(r, 1);
                    if (dept.Length > 0 && peta.TryGetValue(Teks(r, 0), out k) && k.Departemen.Length == 0) { k.Departemen = dept; }
                }
            }
        }

        static void Hitung(Karyawan k)
        {
            // Nama yang ditampilkan: yang paling sering muncul; bila seri, yang paling panjang.
            Dictionary<string, int> jumlah = new Dictionary<string, int>(StringComparer.Ordinal);
            foreach (RincianMesin m in k.Rincian)
            {
                string s = Samakan(m.Nama);
                if (s.Length == 0) { continue; }
                int n;
                jumlah.TryGetValue(s, out n);
                jumlah[s] = n + 1;
            }
            k.NamaBeda = jumlah.Count > 1;
            int terbaik = 0;
            foreach (RincianMesin m in k.Rincian)
            {
                string s = Samakan(m.Nama);
                if (s.Length == 0) { continue; }
                int n = jumlah[s];
                string rapi = string.Join(" ", m.Nama.Split(new char[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries));
                if (n > terbaik || (n == terbaik && rapi.Length > k.Nama.Length))
                {
                    terbaik = n;
                    k.Nama = rapi;
                }
            }

            int maks = -1;
            bool adaBelum = false;
            foreach (RincianMesin m in k.Rincian)
            {
                if (m.Jari < 0) { adaBelum = true; }
                else if (m.Jari > maks) { maks = m.Jari; }
            }
            // "0" hanya bila semua mesin tempat ID ini berada sudah diambil templatenya.
            if (maks > 0) { k.Jari = maks; }
            else if (maks == 0 && !adaBelum) { k.Jari = 0; }
            else { k.Jari = -1; }
        }

        // Huruf besar/kecil dan spasi ganda tidak dianggap beda nama.
        public static string Samakan(string nama)
        {
            if (nama == null) { return ""; }
            string[] bagian = nama.Split(new char[] { ' ', '\t' }, StringSplitOptions.RemoveEmptyEntries);
            return string.Join(" ", bagian).ToUpperInvariant();
        }

        public static int BandingId(string a, string b)
        {
            long x, y;
            bool ax = long.TryParse(a, out x);
            bool by = long.TryParse(b, out y);
            if (ax && by && x != y) { return x.CompareTo(y); }
            if (ax != by) { return ax ? -1 : 1; }
            return string.CompareOrdinal(a, b);
        }

        public static bool Cocok(Karyawan k, SaringKaryawan saring, string cari)
        {
            if (saring == SaringKaryawan.NamaBeda && !k.NamaBeda) { return false; }
            if (saring == SaringKaryawan.TanpaJari && !k.TanpaJari) { return false; }
            if (saring == SaringKaryawan.SatuMesin && !k.HanyaSatuMesin) { return false; }
            string q = (cari ?? "").Trim();
            if (q.Length == 0) { return true; }
            if (Ada(k.Id, q) || Ada(k.Departemen, q)) { return true; }
            foreach (RincianMesin m in k.Rincian) { if (Ada(m.Nama, q)) { return true; } }
            return false;
        }

        static bool Ada(string teks, string cari)
        {
            return teks.IndexOf(cari, StringComparison.OrdinalIgnoreCase) >= 0;
        }

        public static string Csv(IEnumerable<Karyawan> daftar)
        {
            StringBuilder sb = new StringBuilder();
            sb.Append("ID;Nama;Departemen;Jumlah mesin;Daftar mesin;Sidik jari;Jari tersimpan;Catatan\r\n");
            foreach (Karyawan k in daftar)
            {
                sb.Append(Sel(k.Id)).Append(';').Append(Sel(k.Nama)).Append(';').Append(Sel(k.Departemen)).Append(';')
                  .Append(k.Rincian.Count).Append(';').Append(Sel(k.DaftarMesin)).Append(';').Append(k.TeksJari).Append(';')
                  .Append(k.JariTersimpan).Append(';').Append(Sel(k.Catatan)).Append("\r\n");
            }
            return sb.ToString();
        }

        // Teks dari mesin tidak boleh dibaca Excel sebagai rumus.
        static string Sel(string s)
        {
            if (s == null) { s = ""; }
            if (s.Length > 0 && "=+-@\t\r".IndexOf(s[0]) >= 0) { s = "'" + s; }
            return "\"" + s.Replace("\"", "\"\"") + "\"";
        }

        static string Teks(SQLiteDataReader r, int i)
        {
            return r.IsDBNull(i) ? "" : Convert.ToString(r.GetValue(i), CultureInfo.InvariantCulture).Trim();
        }

        static int Angka(SQLiteDataReader r, int i, int bawaan)
        {
            return r.IsDBNull(i) ? bawaan : Convert.ToInt32(r.GetValue(i), CultureInfo.InvariantCulture);
        }
    }
}
