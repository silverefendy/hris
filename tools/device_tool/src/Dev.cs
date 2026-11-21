using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Sockets;
using System.Text;

namespace HrisDeviceTool
{
    // Semua panggilan ke mesin (zkemkeeper, late binding lewat dynamic).
    // Objek COM selalu dibawa sebagai "object" agar pemanggil tidak memakai dynamic.
    public static class Dev
    {
        public static bool PortOpen(string ip, int port, int ms)
        {
            try
            {
                TcpClient c = new TcpClient();
                IAsyncResult r = c.BeginConnect(ip, port, null, null);
                bool ok = r.AsyncWaitHandle.WaitOne(ms, false);
                if (ok) c.EndConnect(r);
                c.Close();
                return ok;
            }
            catch
            {
                return false;
            }
        }

        public static object Connect(MesinItem m, string key)
        {
            Type t = Type.GetTypeFromProgID("zkemkeeper.ZKEM");
            if (t == null)
                throw new Exception("Komponen mesin (zkemkeeper) belum terpasang di PC ini. Lihat panduan pemulihan.");
            if (!PortOpen(m.Ip, m.Port, 3000))
                throw new Exception("Mesin tidak menjawab di " + m.Ip + ":" + m.Port + ". Periksa kabel, VPN, atau alamat IP.");
            dynamic zk = Activator.CreateInstance(t);
            int k;
            if (!string.IsNullOrEmpty(key) && int.TryParse(key, out k)) zk.SetCommPassword(k);
            bool ok = zk.Connect_Net(m.Ip, m.Port);
            if (!ok)
                throw new Exception("Connect gagal (kode " + Err((object)zk) + "). Periksa Comm Key.");
            return zk;
        }

        public static void Disconnect(object zkObj)
        {
            if (zkObj == null) return;
            dynamic zk = zkObj;
            try { zk.Disconnect(); } catch { }
        }

        public static string Err(object zkObj)
        {
            dynamic zk = zkObj;
            try
            {
                int e = 0;
                zk.GetLastError(ref e);
                return e.ToString();
            }
            catch
            {
                return "?";
            }
        }

        static string Opt(object zkObj, string key)
        {
            dynamic zk = zkObj;
            try
            {
                string v = "";
                bool ok = zk.GetSysOption(1, key, ref v);
                return ok ? v : "(gagal baca)";
            }
            catch (Exception e)
            {
                return "(error: " + e.Message + ")";
            }
        }

        static string St(object zkObj, int idx)
        {
            dynamic zk = zkObj;
            try
            {
                int v = 0;
                bool ok = zk.GetDeviceStatus(1, idx, ref v);
                return ok ? v.ToString() : "(gagal)";
            }
            catch
            {
                return "(error)";
            }
        }

        public static string ShortInfo(object zkObj)
        {
            dynamic zk = zkObj;
            try
            {
                string prod = "", fw = "";
                zk.GetProductCode(1, ref prod);
                zk.GetFirmwareVersion(1, ref fw);
                return "Tipe: " + prod + "\r\nFirmware: " + fw;
            }
            catch (Exception e)
            {
                return "(info tidak terbaca: " + e.Message + ")";
            }
        }

        public static string Info(object zkObj)
        {
            dynamic zk = zkObj;
            string nl = Environment.NewLine;
            StringBuilder sb = new StringBuilder();
            try
            {
                string prod = "", fw = "", sn = "";
                zk.GetProductCode(1, ref prod);
                zk.GetFirmwareVersion(1, ref fw);
                zk.GetSerialNumber(1, out sn);
                sb.Append("Product  : " + prod + nl);
                sb.Append("Firmware : " + fw + nl);
                sb.Append("Serial   : " + sn + nl);
            }
            catch (Exception e)
            {
                sb.Append("Info dasar error: " + e.Message + nl);
            }
            sb.Append("Versi jari (~ZKFPVersion) : " + Opt(zkObj, "~ZKFPVersion") + nl);
            sb.Append("Versi wajah (ZKFaceVersion): " + Opt(zkObj, "ZKFaceVersion") + nl);
            sb.Append("Fitur wajah aktif (FaceFunOn): " + Opt(zkObj, "FaceFunOn") + nl);
            sb.Append("Admin           : " + St(zkObj, 1) + nl);
            sb.Append("User            : " + St(zkObj, 2) + nl);
            sb.Append("Template jari   : " + St(zkObj, 3) + nl);
            sb.Append("Log absensi     : " + St(zkObj, 6) + nl);
            sb.Append("Wajah           : " + St(zkObj, 21) + nl);
            sb.Append("Kapasitas (angka mentah, arti perlu verifikasi SDK) 7=" + St(zkObj, 7)
                + " 8=" + St(zkObj, 8) + " 9=" + St(zkObj, 9) + " 22=" + St(zkObj, 22) + nl);
            try
            {
                int y = 0, mo = 0, d = 0, h = 0, mi = 0, s = 0;
                bool ok = zk.GetDeviceTime(1, ref y, ref mo, ref d, ref h, ref mi, ref s);
                if (ok)
                {
                    DateTime dt = new DateTime(y, mo, d, h, mi, s);
                    double diff = (dt - DateTime.Now).TotalSeconds;
                    sb.Append("Jam mesin : " + dt.ToString("dd-MM-yyyy HH:mm:ss")
                        + "  (selisih dengan PC: " + Math.Round(diff) + " detik)" + nl);
                }
            }
            catch (Exception e)
            {
                sb.Append("Jam mesin error: " + e.Message + nl);
            }
            return sb.ToString();
        }

        public static bool GetUser(object zkObj, string uid, out string name, out int priv, out bool enabled)
        {
            dynamic zk = zkObj;
            string n = "", pwd = "";
            int p = 0;
            bool en = false;
            bool ada = zk.SSR_GetUserInfo(1, uid, ref n, ref pwd, ref p, ref en);
            name = n;
            priv = p;
            enabled = en;
            return ada;
        }

        public static bool CreateUser(object zkObj, string uid, string nama)
        {
            dynamic zk = zkObj;
            bool ok = zk.SSR_SetUserInfo(1, uid, nama, "", 0, true);
            return ok;
        }

        public static List<string[]> ListUsers(object zkObj, int max)
        {
            dynamic zk = zkObj;
            List<string[]> rows = new List<string[]>();
            bool okAll = zk.ReadAllUserID(1);
            if (!okAll) return rows;
            string id = "", name = "", pwd = "";
            int priv = 0;
            bool en = false;
            while (rows.Count < max)
            {
                bool ok = zk.SSR_GetAllUserInfo(1, ref id, ref name, ref pwd, ref priv, ref en);
                if (!ok) break;
                rows.Add(new string[] { id.Trim('\0'), name.Trim('\0'), priv.ToString(), en ? "aktif" : "nonaktif" });
            }
            return rows;
        }

        public static List<string[]> InfoRows(object zkObj)
        {
            dynamic zk = zkObj;
            List<string[]> r = new List<string[]>();
            string prod = "", fw = "", sn = "";
            try { zk.GetProductCode(1, ref prod); } catch { }
            try { zk.GetFirmwareVersion(1, ref fw); } catch { }
            try { zk.GetSerialNumber(1, out sn); } catch { }
            r.Add(new string[] { "Identitas", "Tipe (product code)", prod });
            r.Add(new string[] { "Identitas", "Firmware", fw });
            r.Add(new string[] { "Identitas", "Serial", sn });
            r.Add(new string[] { "Algoritma", "Versi jari", Opt(zkObj, "~ZKFPVersion") });
            r.Add(new string[] { "Algoritma", "Versi wajah", Opt(zkObj, "ZKFaceVersion") });
            r.Add(new string[] { "Algoritma", "Fitur wajah aktif", Opt(zkObj, "FaceFunOn") });
            r.Add(new string[] { "Identitas", "Nama perangkat", Opt(zkObj, "~DeviceName") });
            r.Add(new string[] { "Identitas", "Platform", Opt(zkObj, "~Platform") });
            r.Add(new string[] { "Identitas", "Vendor", Opt(zkObj, "~OEMVendor") });
            r.Add(new string[] { "Isi data", "Password terdaftar", St(zkObj, 4) });
            r.Add(new string[] { "Isi data", "Catatan operasi", St(zkObj, 5) });
            r.Add(new string[] { "Sisa kapasitas (BELUM terverifikasi)", "Sisa jari (10)", St(zkObj, 10) });
            r.Add(new string[] { "Sisa kapasitas (BELUM terverifikasi)", "Sisa user (11)", St(zkObj, 11) });
            r.Add(new string[] { "Sisa kapasitas (BELUM terverifikasi)", "Sisa log (12)", St(zkObj, 12) });
            r.Add(new string[] { "Isi data", "Admin", St(zkObj, 1) });
            r.Add(new string[] { "Isi data", "User", St(zkObj, 2) });
            r.Add(new string[] { "Isi data", "Template jari", St(zkObj, 3) });
            r.Add(new string[] { "Isi data", "Template wajah", St(zkObj, 21) });
            r.Add(new string[] { "Isi data", "Log absensi", St(zkObj, 6) });
            r.Add(new string[] { "Kapasitas (arti BELUM terverifikasi)", "Angka 7", St(zkObj, 7) });
            r.Add(new string[] { "Kapasitas (arti BELUM terverifikasi)", "Angka 8", St(zkObj, 8) });
            r.Add(new string[] { "Kapasitas (arti BELUM terverifikasi)", "Angka 9", St(zkObj, 9) });
            r.Add(new string[] { "Kapasitas (arti BELUM terverifikasi)", "Angka 22", St(zkObj, 22) });
            try
            {
                int y = 0, mo = 0, d = 0, h = 0, mi = 0, s = 0;
                bool ok = zk.GetDeviceTime(1, ref y, ref mo, ref d, ref h, ref mi, ref s);
                if (ok)
                {
                    DateTime dt = new DateTime(y, mo, d, h, mi, s);
                    double diff = (dt - DateTime.Now).TotalSeconds;
                    r.Add(new string[] { "Jam", "Jam mesin", dt.ToString("dd-MM-yyyy HH:mm:ss") });
                    r.Add(new string[] { "Jam", "Selisih dengan PC (detik)", Math.Round(diff).ToString() });
                }
            }
            catch (Exception e)
            {
                r.Add(new string[] { "Jam", "Jam mesin", "error: " + e.Message });
            }
            return r;
        }

        // Urutan: versi jari, versi wajah, user, template jari, wajah, log, selisih jam (detik)
        public static string[] Ringkas(object zkObj)
        {
            dynamic zk = zkObj;
            string selisih = "?";
            try
            {
                int y = 0, mo = 0, d = 0, h = 0, mi = 0, s = 0;
                bool ok = zk.GetDeviceTime(1, ref y, ref mo, ref d, ref h, ref mi, ref s);
                if (ok)
                {
                    DateTime dt = new DateTime(y, mo, d, h, mi, s);
                    double diff = (dt - DateTime.Now).TotalSeconds;
                    selisih = Math.Round(diff).ToString();
                }
            }
            catch { }
            return new string[] { Opt(zkObj, "~ZKFPVersion"), Opt(zkObj, "ZKFaceVersion"),
                St(zkObj, 2), St(zkObj, 3), St(zkObj, 21), St(zkObj, 6), selisih };
        }

        static string Safe(string s)
        {
            foreach (char c in Path.GetInvalidFileNameChars()) s = s.Replace(c, '_');
            return s;
        }

        public static int ReadTemplates(object zkObj, string uid, string mesin, string dir, Action<string> log)
        {
            dynamic zk = zkObj;
            try { zk.RefreshData(1); } catch { }
            int found = 0;
            for (int f = 0; f <= 9; f++)
            {
                int flag = 0, len = 0;
                string tmp = "";
                bool ok = false;
                try
                {
                    ok = zk.GetUserTmpExStr(1, uid, f, ref flag, ref tmp, ref len);
                }
                catch (Exception e)
                {
                    log("Jari " + f + ": error " + e.Message);
                    continue;
                }
                if (ok && tmp != null && tmp.Length > 0)
                {
                    found++;
                    string path = Path.Combine(dir, "tmpl_" + Safe(mesin) + "_" + uid + "_jari" + f + ".hdttmpl");
                    File.WriteAllText(path, tmp);
                    log("Jari " + f + ": ADA (flag " + flag + ", panjang " + len + ") -> " + path);
                }
            }
            return found;
        }

        public static bool StartEnroll(object zkObj, string uid, int jari)
        {
            dynamic zk = zkObj;
            try { zk.CancelOperation(); } catch { }
            bool ok = zk.StartEnrollEx(uid, jari, 1);
            return ok;
        }
    }
}
