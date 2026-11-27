using System;
using System.Collections.Generic;
using System.Data.SQLite;
using System.Globalization;
using System.Security.Cryptography;
using System.Text;

namespace HrisDeviceTool.Data
{
    public class BarisTemplate
    {
        public string Id = "";
        public int Jari;
        public int Flag;
        public int Panjang;
        public string Isi = "";
    }

    public class HasilTemplate
    {
        public int Disimpan;
        public int Cocok;
        public int TotalMesin;
    }

    // Template jari terenkripsi. Kunci 64 byte: 32 untuk AES-256-CBC, 32 untuk HMAC-SHA256.
    // Bentuk data: iv(16) + sandi + mac(32). Mac ikut mengikat mesin, id, dan nomor jari.
    public static class TemplateStore
    {
        public static byte[] KunciBaru()
        {
            byte[] k = new byte[64];
            RandomNumberGenerator.Create().GetBytes(k);
            return k;
        }

        public static string Konteks(string mesin, string id, int jari)
        {
            return mesin + "|" + id + "|" + jari.ToString(CultureInfo.InvariantCulture);
        }

        static byte[] Potong(byte[] a, int mulai, int n)
        {
            byte[] r = new byte[n];
            Buffer.BlockCopy(a, mulai, r, 0, n);
            return r;
        }

        static byte[] Mac(byte[] kunci, byte[] blob, int panjang, string konteks)
        {
            byte[] ktx = Encoding.UTF8.GetBytes(konteks);
            byte[] semua = new byte[panjang + ktx.Length];
            Buffer.BlockCopy(blob, 0, semua, 0, panjang);
            Buffer.BlockCopy(ktx, 0, semua, panjang, ktx.Length);
            using (HMACSHA256 h = new HMACSHA256(Potong(kunci, 32, 32))) { return h.ComputeHash(semua); }
        }

        public static byte[] Segel(byte[] kunci, string isi, string konteks)
        {
            using (Aes aes = Aes.Create())
            {
                aes.Key = Potong(kunci, 0, 32);
                aes.GenerateIV();
                byte[] data = Encoding.UTF8.GetBytes(isi);
                byte[] enc = aes.CreateEncryptor().TransformFinalBlock(data, 0, data.Length);
                byte[] blob = new byte[16 + enc.Length + 32];
                Buffer.BlockCopy(aes.IV, 0, blob, 0, 16);
                Buffer.BlockCopy(enc, 0, blob, 16, enc.Length);
                Buffer.BlockCopy(Mac(kunci, blob, 16 + enc.Length, konteks), 0, blob, 16 + enc.Length, 32);
                return blob;
            }
        }

        public static bool TryBuka(byte[] kunci, byte[] blob, string konteks, out string isi)
        {
            isi = "";
            if (blob == null || blob.Length < 64) { return false; }
            int n = blob.Length - 32;
            byte[] mac = Mac(kunci, blob, n, konteks);
            int beda = 0;
            for (int i = 0; i < 32; i++) { beda |= mac[i] ^ blob[n + i]; }
            if (beda != 0) { return false; }
            using (Aes aes = Aes.Create())
            {
                aes.Key = Potong(kunci, 0, 32);
                aes.IV = Potong(blob, 0, 16);
                byte[] data = aes.CreateDecryptor().TransformFinalBlock(blob, 16, n - 16);
                isi = Encoding.UTF8.GetString(data);
                return true;
            }
        }

        static string Hash(string s)
        {
            using (SHA256 sha = SHA256.Create())
            {
                StringBuilder sb = new StringBuilder();
                foreach (byte x in sha.ComputeHash(Encoding.UTF8.GetBytes(s))) { sb.Append(x.ToString("x2")); }
                return sb.ToString();
            }
        }

        // Menambah atau menimpa (tidak menghapus), lalu membaca balik. Satu saja tidak cocok = semua dibatalkan.
        public static HasilTemplate Simpan(SQLiteConnection c, string mesin, int versi, List<BarisTemplate> baris, byte[] kunci)
        {
            HasilTemplate h = new HasilTemplate();
            string waktu = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss", CultureInfo.InvariantCulture);
            using (SQLiteTransaction t = c.BeginTransaction())
            {
                foreach (BarisTemplate b in baris)
                {
                    using (SQLiteCommand q = new SQLiteCommand("insert or replace into template_jari (mesin,id_mesin,jari,flag,versi,panjang,hash,data,diambil) values (@m,@i,@j,@f,@v,@p,@h,@d,@t)", c, t))
                    {
                        q.Parameters.AddWithValue("@m", mesin);
                        q.Parameters.AddWithValue("@i", b.Id);
                        q.Parameters.AddWithValue("@j", b.Jari);
                        q.Parameters.AddWithValue("@f", b.Flag);
                        q.Parameters.AddWithValue("@v", versi);
                        q.Parameters.AddWithValue("@p", b.Panjang);
                        q.Parameters.AddWithValue("@h", Hash(b.Isi));
                        q.Parameters.AddWithValue("@d", Segel(kunci, b.Isi, Konteks(mesin, b.Id, b.Jari)));
                        q.Parameters.AddWithValue("@t", waktu);
                        q.ExecuteNonQuery();
                    }
                    h.Disimpan++;
                }
                foreach (BarisTemplate b in baris)
                {
                    using (SQLiteCommand q = new SQLiteCommand("select data from template_jari where mesin=@m and id_mesin=@i and jari=@j", c, t))
                    {
                        q.Parameters.AddWithValue("@m", mesin);
                        q.Parameters.AddWithValue("@i", b.Id);
                        q.Parameters.AddWithValue("@j", b.Jari);
                        string balik;
                        if (TryBuka(kunci, q.ExecuteScalar() as byte[], Konteks(mesin, b.Id, b.Jari), out balik) && balik == b.Isi) { h.Cocok++; }
                    }
                }
                if (h.Cocok != h.Disimpan)
                {
                    throw new InvalidOperationException("Verifikasi gagal: cocok " + h.Cocok + " dari " + h.Disimpan + ". Tidak ada yang disimpan.");
                }
                using (SQLiteCommand u = new SQLiteCommand("update user_mesin set jumlah_jari=(select count(*) from template_jari x where x.mesin=user_mesin.mesin and x.id_mesin=user_mesin.id_mesin) where mesin=@m", c, t))
                {
                    u.Parameters.AddWithValue("@m", mesin);
                    u.ExecuteNonQuery();
                }
                using (SQLiteCommand n = new SQLiteCommand("select count(*) from template_jari where mesin=@m", c, t))
                {
                    n.Parameters.AddWithValue("@m", mesin);
                    h.TotalMesin = Convert.ToInt32(n.ExecuteScalar());
                }
                t.Commit();
            }
            return h;
        }

        // Kunci terbungkus: satu baris per akun.
        public static Dictionary<string, byte[]> BacaKunci(SQLiteConnection c)
        {
            Dictionary<string, byte[]> d = new Dictionary<string, byte[]>();
            using (SQLiteCommand q = new SQLiteCommand("select peran, data from kunci_template", c))
            using (SQLiteDataReader r = q.ExecuteReader())
            {
                while (r.Read()) { d[r.GetString(0)] = (byte[])r[1]; }
            }
            return d;
        }

        public static void SimpanKunci(SQLiteConnection c, string peran, byte[] data)
        {
            using (SQLiteCommand q = new SQLiteCommand("insert or replace into kunci_template (peran,data,diubah) values (@p,@d,@t)", c))
            {
                q.Parameters.AddWithValue("@p", peran);
                q.Parameters.AddWithValue("@d", data);
                q.Parameters.AddWithValue("@t", DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss", CultureInfo.InvariantCulture));
                q.ExecuteNonQuery();
            }
        }

        public static void HapusKunci(SQLiteConnection c, string peran)
        {
            using (SQLiteCommand q = new SQLiteCommand("delete from kunci_template where peran=@p", c))
            {
                q.Parameters.AddWithValue("@p", peran);
                q.ExecuteNonQuery();
            }
        }

        public static long JumlahTemplate(SQLiteConnection c)
        {
            using (SQLiteCommand q = new SQLiteCommand("select count(*) from template_jari", c)) { return Convert.ToInt64(q.ExecuteScalar()); }
        }
    }
}
