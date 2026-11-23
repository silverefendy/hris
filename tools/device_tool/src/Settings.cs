using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Windows.Forms;
using System.Xml.Serialization;

namespace HrisDeviceTool
{
    public class MesinItem
    {
        public string Nama = "";
        public string Ip = "";
        public int Port = 4370;
        public bool IngatKey = false;
        public bool TanpaKey = false;

        public override string ToString()
        {
            return Nama + "  (" + Ip + ")";
        }
    }

    public class AppData
    {
        public List<MesinItem> Mesin = new List<MesinItem>();
    }

    // Penyimpanan portabel: semua di folder "data" di samping exe.
    // Comm Key dienkripsi DPAPI Windows (terikat akun Windows di PC ini, tanpa kata sandi).
    public class Store
    {
        public string BaseDir, DataDir, MesinFile, RahasiaFile, CadanganDir, LogDir;
        public AppData Data = new AppData();
        public Dictionary<string, string> Keys = new Dictionary<string, string>();
        public bool SecretsLocked = false;

        public Store(string baseDir)
        {
            BaseDir = baseDir;
            DataDir = Path.Combine(baseDir, "data");
            MesinFile = Path.Combine(DataDir, "mesin.hdtdata");
            RahasiaFile = Path.Combine(DataDir, "rahasia.hdtsec");
            CadanganDir = Path.Combine(DataDir, "cadangan");
            LogDir = Path.Combine(DataDir, "log");
        }

        static string B64(string s)
        {
            return Convert.ToBase64String(Encoding.UTF8.GetBytes(s));
        }

        static string UnB64(string s)
        {
            return Encoding.UTF8.GetString(Convert.FromBase64String(s));
        }

        public void Load()
        {
            Directory.CreateDirectory(DataDir);
            Directory.CreateDirectory(CadanganDir);
            Directory.CreateDirectory(LogDir);
            if (File.Exists(MesinFile))
            {
                XmlSerializer xs = new XmlSerializer(typeof(AppData));
                using (FileStream fs = File.OpenRead(MesinFile))
                {
                    Data = (AppData)xs.Deserialize(fs);
                }
            }
        }

        public void SaveData()
        {
            XmlSerializer xs = new XmlSerializer(typeof(AppData));
            using (FileStream fs = File.Create(MesinFile))
            {
                xs.Serialize(fs, Data);
            }
        }

        // Membuka Comm Key tersimpan. Tanpa kata sandi (DPAPI).
        // Berkas format lama (bersandi) dimigrasi sekali.
        public void UnlockAtStartup()
        {
            if (!File.Exists(RahasiaFile)) return;
            byte[] raw = File.ReadAllBytes(RahasiaFile);
            string plain;
            if (Dpapi.Ada(raw))
            {
                if (Dpapi.TryBuka(raw, out plain))
                {
                    ParseSecrets(plain);
                    return;
                }
                CadangkanBerkas("pc_lain", true);
                AuditLog.Tulis("Comm Key", "berkas tersimpan tidak bisa dibuka di PC/akun ini, dicadangkan");
                MessageBox.Show("Comm Key tersimpan tidak bisa dibuka di PC atau akun Windows ini (kemungkinan berkas berasal dari PC lain).\r\n\r\n" +
                    "Berkas dicadangkan di folder data\\cadangan. Comm Key akan ditanyakan sekali saat menghubungkan mesin, lalu diingat di PC ini.",
                    "HRIS Device Tool", MessageBoxButtons.OK, MessageBoxIcon.Information);
                return;
            }
            MigrasiLama(raw);
        }

        void MigrasiLama(byte[] raw)
        {
            while (true)
            {
                string pw = Dlg.Prompt("Migrasi Comm Key (sekali saja)",
                    "Penyimpanan Comm Key kini memakai enkripsi Windows, tanpa kata sandi aplikasi.\r\nMasukkan kata sandi aplikasi LAMA satu kali untuk memindahkan Comm Key.",
                    true, false);
                if (pw == null)
                {
                    DialogResult jawab = MessageBox.Show(
                        "Lupa kata sandi lama?\r\n\r\n" +
                        "Ya = berkas lama dicadangkan, Comm Key diisi ulang sekali saat menghubungkan mesin.\r\n" +
                        "Tidak = lewati sekarang (Comm Key tersimpan tidak dibuka, dan Comm Key baru tidak bisa disimpan sampai migrasi selesai).",
                        "Migrasi Comm Key", MessageBoxButtons.YesNo, MessageBoxIcon.Question);
                    if (jawab == DialogResult.Yes)
                    {
                        CadangkanBerkas("sandi_lama", true);
                        AuditLog.Tulis("Comm Key", "sandi lama dilewati, berkas lama dicadangkan");
                        return;
                    }
                    SecretsLocked = true;
                    return;
                }
                string plain;
                if (Crypto.TryDecrypt(raw, pw, out plain))
                {
                    ParseSecrets(plain);
                    CadangkanBerkas("sebelum_migrasi", false);
                    try
                    {
                        File.WriteAllBytes(RahasiaFile, Dpapi.Lindungi(plain));
                        AuditLog.Tulis("Comm Key", "dimigrasi ke enkripsi Windows");
                        MessageBox.Show("Migrasi selesai. Comm Key kini disimpan dengan enkripsi Windows di PC ini; kata sandi aplikasi tidak diminta lagi.\r\n\r\n" +
                            "Salinan berkas lama ada di folder data\\cadangan (masih bersandi lama).",
                            "Migrasi Comm Key", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    }
                    catch (Exception e)
                    {
                        MessageBox.Show("Comm Key terbuka untuk sesi ini, tetapi gagal disimpan ke format baru:\r\n" + e.Message +
                            "\r\n\r\nBerkas lama tidak diubah; migrasi diulang saat aplikasi dibuka lagi.",
                            "Migrasi Comm Key", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    }
                    return;
                }
                MessageBox.Show("Kata sandi salah.", "HRIS Device Tool", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
        }

        // pindah = true: berkas dipindah; false: hanya disalin
        void CadangkanBerkas(string label, bool pindah)
        {
            try
            {
                string tujuan = Path.Combine(CadanganDir, "rahasia_" + label + "_" + DateTime.Now.ToString("yyyyMMdd_HHmmss") + ".hdtbak");
                if (pindah) File.Move(RahasiaFile, tujuan);
                else File.Copy(RahasiaFile, tujuan, true);
            }
            catch (Exception) { }
        }

        void ParseSecrets(string plain)
        {
            Keys.Clear();
            foreach (string line in plain.Split('\n'))
            {
                string s = line.Trim();
                if (s.Length == 0) continue;
                int i = s.IndexOf(':');
                if (i < 0) continue;
                try
                {
                    Keys[UnB64(s.Substring(0, i))] = UnB64(s.Substring(i + 1));
                }
                catch (FormatException) { }
            }
        }

        // true = berhasil (atau tidak ada yang perlu disimpan)
        public bool SaveSecrets()
        {
            StringBuilder sb = new StringBuilder();
            int n = 0;
            foreach (MesinItem m in Data.Mesin)
            {
                string k;
                if (m.IngatKey && Keys.TryGetValue(m.Nama, out k) && k.Length > 0)
                {
                    sb.Append(B64(m.Nama)).Append(':').Append(B64(k)).Append('\n');
                    n++;
                }
            }
            if (n == 0)
            {
                if (File.Exists(RahasiaFile) && !SecretsLocked) File.Delete(RahasiaFile);
                return true;
            }
            if (SecretsLocked)
            {
                MessageBox.Show("Berkas Comm Key lama belum dimigrasi (kata sandi lama dilewati), jadi Comm Key tidak bisa disimpan.\r\nTutup aplikasi, buka lagi, lalu selesaikan migrasi.",
                    "HRIS Device Tool", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return false;
            }
            try
            {
                File.WriteAllBytes(RahasiaFile, Dpapi.Lindungi(sb.ToString()));
                return true;
            }
            catch (Exception e)
            {
                MessageBox.Show("Comm Key tidak bisa disimpan:\r\n" + e.Message,
                    "HRIS Device Tool", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return false;
            }
        }
    }
}