using System;
using System.Collections.Generic;
using System.Data.SQLite;
using System.IO;
using System.Windows.Forms;
using HrisDeviceTool.Data;

namespace HrisDeviceTool
{
    // Membuka kunci template memakai kata sandi login. Hanya manager, direksi, administrator.
    // Sandi sesi hanya ada di memori dan dikosongkan saat keluar akun.
    public static class Brankas
    {
        public const int LevelMinimal = 3;
        static string sandi = "";

        public static void Masuk(int level, string kataSandi)
        {
            sandi = (level >= LevelMinimal) ? kataSandi : "";
        }

        public static void Keluar()
        {
            sandi = "";
        }

        static bool Coba(byte[] terbungkus, string kataSandi, out byte[] kunci)
        {
            kunci = null;
            string teks;
            if (!Crypto.TryDecrypt(terbungkus, kataSandi, out teks)) return false;
            try { kunci = Convert.FromBase64String(teks); }
            catch (FormatException) { return false; }
            return kunci.Length == 64;
        }

        static void Bungkus(SQLiteConnection c, string peran, byte[] kunci, string kataSandi)
        {
            TemplateStore.SimpanKunci(c, peran, Crypto.Encrypt(Convert.ToBase64String(kunci), kataSandi));
        }

        // null = tidak berhak atau dibatalkan
        public static byte[] Buka(SQLiteConnection c)
        {
            if (Peran.Level < LevelMinimal || sandi.Length == 0) return null;
            string peran = Peran.NamaAktif;
            Dictionary<string, byte[]> d = TemplateStore.BacaKunci(c);
            byte[] kunci;
            if (d.Count == 0)
            {
                if (TemplateStore.JumlahTemplate(c) > 0)
                {
                    MessageBox.Show("Database berisi template tetapi kuncinya tidak ada. Pulihkan database dari cadangan.", "Kunci template");
                    return null;
                }
                string tanya = "Kunci template baru akan dibuat dan dikunci dengan kata sandi login \"" + peran + "\".\r\n\r\n"
                    + "Bila semua kata sandi yang punya akses hilang, template tersimpan tidak bisa dibuka.";
                if (Akun.SandiBawaan(Peran.Level, sandi))
                    tanya += "\r\n\r\nPERINGATAN: Anda masih memakai kata sandi bawaan. Sebaiknya pilih Tidak, ganti sandi dulu.";
                if (MessageBox.Show(tanya + "\r\n\r\nLanjutkan?", "Kunci template", MessageBoxButtons.YesNo, MessageBoxIcon.Warning, MessageBoxDefaultButton.Button2) != DialogResult.Yes) return null;
                kunci = TemplateStore.KunciBaru();
                Bungkus(c, peran, kunci, sandi);
                AuditLog.Tulis("Kunci template", "dibuat oleh " + peran);
                return kunci;
            }
            byte[] milik;
            if (d.TryGetValue(peran, out milik) && Coba(milik, sandi, out kunci)) return kunci;
            while (true)
            {
                string lain = Dlg.Prompt("Buka kunci template",
                    "Akun \"" + peran + "\" belum punya akses di database ini.\r\nCukup sekali: masukkan kata sandi akun yang sudah punya akses\r\n("
                    + string.Join(", ", new List<string>(d.Keys).ToArray()) + "), sesuai sandi saat disimpan.", true, false);
                if (lain == null) return null;
                foreach (byte[] w in d.Values)
                {
                    if (Coba(w, lain, out kunci))
                    {
                        Bungkus(c, peran, kunci, sandi);
                        AuditLog.Tulis("Kunci template", "akses diberikan ke " + peran);
                        return kunci;
                    }
                }
                AuditLog.Tulis("Kunci template", "sandi salah saat membuka akses untuk " + peran);
                System.Threading.Thread.Sleep(800);
                MessageBox.Show("Kata sandi itu tidak membuka kunci.", "Kunci template");
            }
        }

        // Dipanggil setelah kata sandi akun diganti lewat aplikasi.
        public static void SandiDiganti(int level, string sandiBaru)
        {
            if (level < LevelMinimal) return;
            string peran = Peran.Nama[level - 1];
            try
            {
                string berkas = HdtDatabase.BerkasDefault();
                if (File.Exists(berkas))
                {
                    using (SQLiteConnection c = HdtDatabase.Buka(berkas))
                    {
                        if (TemplateStore.BacaKunci(c).Count > 0)
                        {
                            byte[] kunci = Buka(c);
                            if (kunci != null) Bungkus(c, peran, kunci, sandiBaru);
                            else if (TemplateStore.BacaKunci(c).Count > 1) TemplateStore.HapusKunci(c, peran);
                            if (kunci == null)
                                MessageBox.Show("Kunci template untuk \"" + peran + "\" belum diperbarui. Saat membuka template, sandi lama akan diminta.", "Kunci template");
                        }
                    }
                }
            }
            catch (Exception e)
            {
                MessageBox.Show("Kata sandi sudah diganti, tetapi kunci template gagal diperbarui:\r\n" + e.Message, "Kunci template");
            }
            if (level == Peran.Level) sandi = sandiBaru;
        }
    }
}
