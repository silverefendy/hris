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

        public override string ToString()
        {
            return Nama + "  (" + Ip + ")";
        }
    }

    public class AppData
    {
        public List<MesinItem> Mesin = new List<MesinItem>();
    }

    // Penyimpanan portabel: semua di folder "data" di samping exe
    public class Store
    {
        public string BaseDir, DataDir, MesinFile, RahasiaFile, CadanganDir, LogDir;
        public AppData Data = new AppData();
        public Dictionary<string, string> Keys = new Dictionary<string, string>();
        public string Password = "";
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

        public void UnlockAtStartup()
        {
            if (!File.Exists(RahasiaFile)) return;
            byte[] raw = File.ReadAllBytes(RahasiaFile);
            while (true)
            {
                string pw = Dlg.Prompt("Kata sandi aplikasi",
                    "Masukkan kata sandi aplikasi untuk membuka Comm Key yang tersimpan.\r\nBatal = lanjut tanpa Comm Key tersimpan.",
                    true, false);
                if (pw == null) { SecretsLocked = true; return; }
                string plain;
                if (Crypto.TryDecrypt(raw, pw, out plain))
                {
                    Password = pw;
                    ParseSecrets(plain);
                    return;
                }
                MessageBox.Show("Kata sandi salah.", "HRIS Device Tool", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
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
                MessageBox.Show("File rahasia terkunci (kata sandi dilewati saat dibuka), jadi Comm Key tidak bisa disimpan.\r\nTutup aplikasi lalu buka lagi dan masukkan kata sandi yang benar.",
                    "HRIS Device Tool", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return false;
            }
            if (Password.Length == 0)
            {
                string pw = Dlg.Prompt("Buat kata sandi aplikasi",
                    "Buat kata sandi aplikasi (minimal 6 karakter) untuk mengenkripsi Comm Key.\r\nCatat baik-baik: tidak bisa dipulihkan bila lupa.",
                    true, true);
                if (pw == null) return false;
                if (pw.Length < 6)
                {
                    MessageBox.Show("Kata sandi minimal 6 karakter.", "HRIS Device Tool", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                    return false;
                }
                Password = pw;
            }
            File.WriteAllBytes(RahasiaFile, Crypto.Encrypt(sb.ToString(), Password));
            return true;
        }
    }
}
