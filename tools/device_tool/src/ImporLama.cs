using System;
using System.Collections.Generic;
using System.Data.SQLite;
using System.Globalization;
using System.IO;
using System.Text;

namespace HrisDeviceTool.Data
{
    public class HasilAnalisis
    {
        public string Berkas;
        public string Sandi;
        public string Pemisah;
        public List<string> Judul = new List<string>();
        public List<string> Peta = new List<string>();
        public List<Dictionary<string, string>> Baris = new List<Dictionary<string, string>>();
        public int TotalBaris;
        public int TanpaIdAkun;
        public int GandaDalamBerkas;
        public int TanggalTakTerbaca;
    }

    public class HasilTulis
    {
        public int Baru;
        public int Diperbarui;
    }

    // Impor CSV aplikasi absensi lama ke tabel induk_aplikasi_lama.
    public static class ImporLama
    {
        public static readonly string[] Kolom = {
            "id_akun", "no_induk", "nama", "kelamin", "warga_negara", "gelar", "tgl_lahir",
            "nomor_kartu", "telp_kantor", "no_ponsel", "alamat", "departemen", "mulai_bekerja", "batasan"
        };

        private static readonly string[] KolomTanggal = { "tgl_lahir", "mulai_bekerja" };

        private static readonly string[] FormatTgl = {
            "dd/MM/yyyy", "d/M/yyyy", "dd-MM-yyyy", "d-M-yyyy", "yyyy-MM-dd", "yyyy/MM/dd",
            "dd.MM.yyyy", "d.M.yyyy", "dd/MM/yyyy HH:mm:ss", "d/M/yyyy H:mm:ss",
            "yyyy-MM-dd HH:mm:ss", "dd MMM yyyy", "d MMM yyyy", "dd-MMM-yyyy", "d-MMM-yyyy"
        };

        public static string Norm(string s)
        {
            StringBuilder sb = new StringBuilder();
            foreach (char c in (s ?? "").ToLowerInvariant())
            {
                if (char.IsLetterOrDigit(c)) { sb.Append(c); }
            }
            return sb.ToString();
        }

        private static void Tambah(Dictionary<string, string> d, string kolom, params string[] kunci)
        {
            foreach (string k in kunci) { d[k] = kolom; }
        }

        private static Dictionary<string, string> BangunSinonim(string berkasPemetaan)
        {
            Dictionary<string, string> d = new Dictionary<string, string>();
            Tambah(d, "id_akun", "noakun", "nomorakun", "akun", "idakun", "accountno", "accountnumber", "userid");
            Tambah(d, "no_induk", "noinduk", "nomorinduk", "induk", "nip", "employeeno");
            Tambah(d, "nama", "nama", "name", "namalengkap", "namakaryawan");
            Tambah(d, "kelamin", "kelamin", "jeniskelamin", "gender", "sex");
            Tambah(d, "warga_negara", "warganegara", "kewarganegaraan", "wn");
            Tambah(d, "gelar", "gelar", "jabatan", "title");
            Tambah(d, "tgl_lahir", "tgllahir", "tanggallahir", "lahir", "birthdate", "dob");
            Tambah(d, "nomor_kartu", "nomorkartu", "nokartu", "kartu", "cardno", "cardnumber");
            Tambah(d, "telp_kantor", "telpkantor", "teleponkantor", "telkantor", "phoneoffice");
            Tambah(d, "no_ponsel", "noponsel", "nomorponsel", "ponsel", "nohp", "hp", "handphone", "mobile");
            Tambah(d, "alamat", "alamat", "alamatrumah", "address");
            Tambah(d, "departemen", "departemen", "department", "dept", "bagian");
            Tambah(d, "mulai_bekerja", "mulaibekerja", "tglmulai", "tanggalmulai", "tglmasuk", "tanggalmasuk", "hiredate");
            Tambah(d, "batasan", "batasan", "privilege", "hakakses");

            if (!string.IsNullOrEmpty(berkasPemetaan) && File.Exists(berkasPemetaan))
            {
                foreach (string baris in File.ReadAllLines(berkasPemetaan))
                {
                    string b = baris.Trim();
                    if (b.Length == 0 || b.StartsWith("#")) { continue; }
                    int p = b.IndexOf('=');
                    if (p < 1) { continue; }
                    string judul = Norm(b.Substring(0, p));
                    string kolom = b.Substring(p + 1).Trim();
                    if (judul.Length > 0 && Array.IndexOf(Kolom, kolom) >= 0) { d[judul] = kolom; }
                }
            }
            return d;
        }

        private static string BacaTeks(string berkas, out string sandi)
        {
            byte[] b = File.ReadAllBytes(berkas);
            if (b.Length >= 2 && b[0] == 0xFF && b[1] == 0xFE)
            {
                sandi = "UTF-16";
                return Encoding.Unicode.GetString(b, 2, b.Length - 2);
            }
            if (b.Length >= 2 && b[0] == 0xFE && b[1] == 0xFF)
            {
                sandi = "UTF-16";
                return Encoding.BigEndianUnicode.GetString(b, 2, b.Length - 2);
            }
            int mulai = 0;
            if (b.Length >= 3 && b[0] == 0xEF && b[1] == 0xBB && b[2] == 0xBF) { mulai = 3; }
            try
            {
                UTF8Encoding u = new UTF8Encoding(false, true);
                string t = u.GetString(b, mulai, b.Length - mulai);
                sandi = "UTF-8";
                return t;
            }
            catch (DecoderFallbackException)
            {
                sandi = "Windows-1252";
                return Encoding.GetEncoding(1252).GetString(b, mulai, b.Length - mulai);
            }
        }

        private static int Hitung(string s, char c)
        {
            int n = 0;
            foreach (char x in s) { if (x == c) { n++; } }
            return n;
        }

        private static List<List<string>> ParseCsv(string t, char sep)
        {
            List<List<string>> rows = new List<List<string>>();
            List<string> row = new List<string>();
            StringBuilder f = new StringBuilder();
            bool q = false;
            int n = t.Length;
            for (int i = 0; i < n; i++)
            {
                char c = t[i];
                if (q)
                {
                    if (c == '"')
                    {
                        if (i + 1 < n && t[i + 1] == '"') { f.Append('"'); i++; }
                        else { q = false; }
                    }
                    else { f.Append(c); }
                }
                else
                {
                    if (c == '"') { q = true; }
                    else if (c == sep) { row.Add(f.ToString()); f.Length = 0; }
                    else if (c == '\r') { }
                    else if (c == '\n')
                    {
                        row.Add(f.ToString());
                        f.Length = 0;
                        rows.Add(row);
                        row = new List<string>();
                    }
                    else { f.Append(c); }
                }
            }
            if (f.Length > 0 || row.Count > 0)
            {
                row.Add(f.ToString());
                rows.Add(row);
            }
            return rows;
        }

        private static bool TanggalIso(string s, out string iso)
        {
            DateTime d;
            string x = s.Trim();
            bool ok = DateTime.TryParseExact(x, FormatTgl, CultureInfo.InvariantCulture, DateTimeStyles.None, out d);
            if (!ok)
            {
                try
                {
                    ok = DateTime.TryParseExact(x, FormatTgl, new CultureInfo("id-ID"), DateTimeStyles.None, out d);
                }
                catch (ArgumentException)
                {
                    ok = false;
                    d = DateTime.MinValue;
                }
            }
            if (ok && d.Year >= 1900 && d.Year <= 2100)
            {
                iso = d.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);
                return true;
            }
            iso = null;
            return false;
        }

        // Membaca dan menganalisis berkas. Tidak menulis apa pun ke database.
        public static HasilAnalisis Analisis(string berkas, string berkasPemetaan)
        {
            HasilAnalisis h = new HasilAnalisis();
            h.Berkas = berkas;
            string sandi;
            string t = BacaTeks(berkas, out sandi);
            h.Sandi = sandi;

            int e = t.IndexOf('\n');
            string baris1 = e < 0 ? t : t.Substring(0, e);
            int cK = Hitung(baris1, ',');
            int cS = Hitung(baris1, ';');
            int cT = Hitung(baris1, '\t');
            char sep = ',';
            if (cS > cK && cS >= cT) { sep = ';'; }
            else if (cT > cK && cT > cS) { sep = '\t'; }
            h.Pemisah = sep == '\t' ? "tab" : sep.ToString();

            List<List<string>> rows = ParseCsv(t, sep);
            if (rows.Count == 0) { throw new InvalidDataException("Berkas kosong."); }

            Dictionary<string, string> peta = BangunSinonim(berkasPemetaan);
            Dictionary<string, bool> terpakai = new Dictionary<string, bool>();
            List<string> judul = rows[0];
            for (int j = 0; j < judul.Count; j++)
            {
                string jd = judul[j].Trim();
                h.Judul.Add(jd);
                string kolom;
                if (peta.TryGetValue(Norm(jd), out kolom) && !terpakai.ContainsKey(kolom))
                {
                    terpakai[kolom] = true;
                    h.Peta.Add(kolom);
                }
                else
                {
                    h.Peta.Add(null);
                }
            }
            if (!terpakai.ContainsKey("id_akun"))
            {
                throw new InvalidDataException(
                    "Kolom No. Akun tidak dikenali. Tambahkan baris 'Judul Asli=id_akun' di " + berkasPemetaan);
            }

            Dictionary<string, int> indeks = new Dictionary<string, int>();
            for (int r = 1; r < rows.Count; r++)
            {
                List<string> sel = rows[r];
                bool kosong = true;
                foreach (string x in sel)
                {
                    if (x.Trim().Length > 0) { kosong = false; break; }
                }
                if (kosong) { continue; }
                h.TotalBaris++;

                Dictionary<string, string> b = new Dictionary<string, string>();
                List<string> lain = new List<string>();
                for (int j = 0; j < sel.Count && j < h.Judul.Count; j++)
                {
                    string nilai = sel[j].Trim();
                    if (nilai.Length == 0) { continue; }
                    string kolom = h.Peta[j];
                    if (kolom == null) { lain.Add(h.Judul[j] + "=" + nilai); continue; }
                    if (Array.IndexOf(KolomTanggal, kolom) >= 0)
                    {
                        string iso;
                        if (TanggalIso(nilai, out iso)) { nilai = iso; }
                        else
                        {
                            h.TanggalTakTerbaca++;
                            lain.Add(h.Judul[j] + "(mentah)=" + nilai);
                            continue;
                        }
                    }
                    b[kolom] = nilai;
                }

                string id;
                if (!b.TryGetValue("id_akun", out id) || id.Length == 0) { h.TanpaIdAkun++; continue; }
                if (lain.Count > 0) { b["data_lain"] = string.Join(" | ", lain.ToArray()); }

                int pos;
                if (indeks.TryGetValue(id, out pos))
                {
                    h.Baris[pos] = b;
                    h.GandaDalamBerkas++;
                }
                else
                {
                    indeks[id] = h.Baris.Count;
                    h.Baris.Add(b);
                }
            }
            return h;
        }

        private static string BangunUpsert()
        {
            List<string> k = new List<string>(Kolom);
            k.Add("data_lain");
            k.Add("sumber");
            k.Add("diimpor");
            List<string> par = new List<string>();
            List<string> set = new List<string>();
            foreach (string x in k)
            {
                par.Add("@" + x);
                if (x != "id_akun") { set.Add(x + "=excluded." + x); }
            }
            return "INSERT INTO induk_aplikasi_lama (" + string.Join(",", k.ToArray()) + ") VALUES ("
                + string.Join(",", par.ToArray()) + ") ON CONFLICT(id_akun) DO UPDATE SET "
                + string.Join(",", set.ToArray());
        }

        // Menulis hasil analisis dalam satu transaksi (upsert berdasarkan id_akun).
        public static HasilTulis Tulis(SQLiteConnection c, HasilAnalisis h)
        {
            HasilTulis r = new HasilTulis();
            string waktu = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss", CultureInfo.InvariantCulture);
            string sumber = Path.GetFileName(h.Berkas);
            string sql = BangunUpsert();
            using (SQLiteTransaction t = c.BeginTransaction())
            {
                foreach (Dictionary<string, string> b in h.Baris)
                {
                    long ada;
                    using (SQLiteCommand q = new SQLiteCommand("select count(*) from induk_aplikasi_lama where id_akun=@id", c, t))
                    {
                        q.Parameters.AddWithValue("@id", b["id_akun"]);
                        ada = Convert.ToInt64(q.ExecuteScalar());
                    }
                    using (SQLiteCommand cmd = new SQLiteCommand(sql, c, t))
                    {
                        foreach (string k in Kolom)
                        {
                            string v;
                            cmd.Parameters.AddWithValue("@" + k, b.TryGetValue(k, out v) ? (object)v : DBNull.Value);
                        }
                        string lain;
                        cmd.Parameters.AddWithValue("@data_lain", b.TryGetValue("data_lain", out lain) ? (object)lain : DBNull.Value);
                        cmd.Parameters.AddWithValue("@sumber", sumber);
                        cmd.Parameters.AddWithValue("@diimpor", waktu);
                        cmd.ExecuteNonQuery();
                    }
                    if (ada > 0) { r.Diperbarui++; } else { r.Baru++; }
                }
                t.Commit();
            }
            return r;
        }
    }
}
