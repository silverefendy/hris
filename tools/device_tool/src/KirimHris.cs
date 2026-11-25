using System;
using System.Collections.Generic;
using System.Drawing;
using System.Globalization;
using System.IO;
using System.Net;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using System.Windows.Forms;

namespace HrisDeviceTool
{
    public sealed class KirimOpsi
    {
        public string UrlDasar;      // contoh: http://10.1.0.26:8001
        public string Token;
        public string NamaDiHris;    // nama dokumen HRIS Device, harus persis
        public string[] BarisCsv;    // seluruh baris berkas salinan
        public int UkuranBatch = 500;
        public int TimeoutDetik = 120;
    }

    public sealed class KirimHasil
    {
        public int TotalBaris, Diterima, Created, Duplicate, Error, BatchSelesai, BatchTotal;
        public bool Dibatalkan, Berhenti;
        public string Pesan = "";
        public List<string> DetailError = new List<string>();

        public string Ringkas()
        {
            return string.Format("Total {0} baris | diterima {1} | created {2} | duplicate {3} | error {4}",
                TotalBaris, Diterima, Created, Duplicate, Error);
        }
    }

    internal sealed class Punch
    {
        public int NoBaris;
        public string Id;
        public DateTime Waktu;
        public string WaktuTeks;
        public string Verify;
        public string Status;
        public string Workcode;
    }

    public static class KirimHris
    {
        const string Jalur = "/api/method/hris.hris_attendance.integrations.agent_api.push_punches";
        const string FormatWaktu = "yyyy-MM-dd HH:mm:ss";

        public delegate void Lapor(int batchKe, int batchTotal, int selesai, int total,
            int created, int duplicate, int error, string status);

        internal static string Esc(string s)
        {
            StringBuilder sb = new StringBuilder();
            foreach (char c in (s ?? ""))
            {
                switch (c)
                {
                    case '"': sb.Append("\\\""); break;
                    case '\\': sb.Append("\\\\"); break;
                    case '\n': sb.Append("\\n"); break;
                    case '\r': sb.Append("\\r"); break;
                    case '\t': sb.Append("\\t"); break;
                    default:
                        if (c < ' ') sb.AppendFormat("\\u{0:x4}", (int)c);
                        else sb.Append(c);
                        break;
                }
            }
            return sb.ToString();
        }

        internal static void SiapkanJaringan(string url)
        {
            ServicePointManager.Expect100Continue = false;
            if (url.StartsWith("https", StringComparison.OrdinalIgnoreCase))
                ServicePointManager.SecurityProtocol = (SecurityProtocolType)3072; // TLS 1.2
        }

        internal static string Post(string url, string token, string body, int timeoutMs, out int kode)
        {
            HttpWebRequest req = (HttpWebRequest)WebRequest.Create(url);
            req.Method = "POST";
            req.ContentType = "application/json";
            req.Accept = "application/json";
            req.Headers["X-HRIS-Token"] = token;
            req.Proxy = null;
            req.Timeout = timeoutMs;
            req.ReadWriteTimeout = timeoutMs;
            byte[] data = new UTF8Encoding(false).GetBytes(body);
            req.ContentLength = data.Length;
            try
            {
                using (Stream s = req.GetRequestStream()) { s.Write(data, 0, data.Length); }
                using (HttpWebResponse r = (HttpWebResponse)req.GetResponse())
                {
                    kode = (int)r.StatusCode;
                    return Baca(r);
                }
            }
            catch (WebException ex)
            {
                HttpWebResponse r = ex.Response as HttpWebResponse;
                if (r != null)
                {
                    kode = (int)r.StatusCode;
                    return Baca(r);
                }
                kode = 0;
                return ex.Message;
            }
        }

        static string Baca(HttpWebResponse r)
        {
            using (StreamReader sr = new StreamReader(r.GetResponseStream(), Encoding.UTF8))
            {
                return sr.ReadToEnd();
            }
        }

        internal static string Potong(string s, int n)
        {
            s = (s ?? "").Replace("\r", " ").Replace("\n", " ");
            return s.Length <= n ? s : s.Substring(0, n) + "...";
        }

        static string PesanServer(string isi)
        {
            Match m = Regex.Match(isi ?? "", "\"exception\"\\s*:\\s*\"((?:[^\"\\\\]|\\\\.)*)\"");
            if (!m.Success) return Potong(isi, 300);
            string s = m.Groups[1].Value.Replace("\\\"", "\"").Replace("\\\\", "\\");
            int i = s.IndexOf(": ", StringComparison.Ordinal);
            if (i > 0 && s.Substring(0, i).IndexOf(' ') < 0) s = s.Substring(i + 2);
            return Potong(s, 300);
        }

        static string PesanGagal(int kode, string isi)
        {
            if (kode == 401)
                return "Token ditolak (HTTP 401). Pengiriman dihentikan agar tidak memicu blokir "
                     + "(10 kegagalan per 10 menit per IP). Periksa token dan saklar Agent Enabled.";
            if (kode == 417)
                return "Server menolak permintaan (HTTP 417): " + PesanServer(isi) + " "
                     + "(Periksa Via Windows Agent dan status aktif di HRIS Device.)";
            if (kode == 0)
                return "Tidak dapat terhubung ke server: " + Potong(isi, 300);
            return "Gagal (HTTP " + kode + "): " + Potong(isi, 400);
        }

        static bool AmbilInt(string s, string kunci, out int nilai)
        {
            nilai = 0;
            Match m = Regex.Match(s, "\"" + kunci + "\"\\s*:\\s*(\\d+)");
            return m.Success && int.TryParse(m.Groups[1].Value, out nilai);
        }

        // Tes koneksi: kirim daftar kosong (heartbeat). Satu permintaan saja, tanpa percobaan ulang.
        public static bool TesKoneksi(string urlDasar, string token, string namaDiHris, out string pesan)
        {
            SiapkanJaringan(urlDasar);
            string url = urlDasar.TrimEnd('/') + Jalur;
            string body = "{\"device\":\"" + Esc(namaDiHris) + "\",\"punches\":[]}";
            int kode;
            string resp = Post(url, token, body, 30000, out kode);
            if (kode == 200)
            {
                pesan = "Koneksi berhasil (HTTP 200). Balasan: " + Potong(resp, 200);
                return true;
            }
            pesan = PesanGagal(kode, resp);
            return false;
        }

        internal static List<Punch> BacaCsv(string[] baris, KirimHasil h)
        {
            List<Punch> hasil = new List<Punch>();
            for (int i = 0; i < baris.Length; i++)
            {
                string b = (baris[i] ?? "").Trim();
                if (b.Length == 0) continue;
                if (i == 0 && b.StartsWith("device_user_id", StringComparison.OrdinalIgnoreCase)) continue;
                string[] p = b.Split(';');
                DateTime w;
                if (p.Length < 4 || !DateTime.TryParseExact(p[1].Trim(), FormatWaktu,
                        CultureInfo.InvariantCulture, DateTimeStyles.None, out w))
                {
                    h.Error++;
                    if (h.DetailError.Count < 5000)
                        h.DetailError.Add("baris " + (i + 1) + ";format tidak dikenali;" + b);
                    continue;
                }
                Punch x = new Punch();
                x.NoBaris = i + 1;
                x.Id = p[0].Trim();
                x.Waktu = w;
                x.WaktuTeks = w.ToString(FormatWaktu, CultureInfo.InvariantCulture);
                x.Verify = p[2].Trim();
                x.Status = p[3].Trim();
                string wc = p.Length > 4 ? p[4].Trim() : "0";
                x.Workcode = Regex.IsMatch(wc, "^\\d+$") ? wc : "0";
                hasil.Add(x);
            }
            hasil.Sort(delegate (Punch a, Punch c)
            {
                int d = a.Waktu.CompareTo(c.Waktu);
                return d != 0 ? d : a.NoBaris.CompareTo(c.NoBaris);
            });
            return hasil;
        }

        static string BuatBody(string device, List<Punch> list, int awal, int n)
        {
            StringBuilder sb = new StringBuilder();
            sb.Append("{\"device\":\"").Append(Esc(device)).Append("\",\"punches\":[");
            for (int i = 0; i < n; i++)
            {
                Punch p = list[awal + i];
                if (i > 0) sb.Append(',');
                string payload = "{\"via\":\"Device Tool\",\"workcode\":" + p.Workcode + "}";
                sb.Append("{\"device_user_id\":\"").Append(Esc(p.Id)).Append("\"");
                sb.Append(",\"punch_time\":\"").Append(p.WaktuTeks).Append("\"");
                sb.Append(",\"verify_mode\":\"").Append(Esc(p.Verify)).Append("\"");
                sb.Append(",\"punch_status_raw\":\"").Append(Esc(p.Status)).Append("\"");
                sb.Append(",\"raw_payload\":\"").Append(Esc(payload)).Append("\"}");
            }
            sb.Append("]}");
            return sb.ToString();
        }

        public static KirimHasil Jalankan(KirimOpsi o, Lapor lapor, Func<bool> batal)
        {
            KirimHasil h = new KirimHasil();
            if (o.BarisCsv == null) o.BarisCsv = new string[0];
            List<Punch> list = BacaCsv(o.BarisCsv, h);
            h.TotalBaris = list.Count + h.Error;
            int ukuran = Math.Max(1, Math.Min(500, o.UkuranBatch));
            h.BatchTotal = (list.Count + ukuran - 1) / ukuran;
            SiapkanJaringan(o.UrlDasar);
            string url = o.UrlDasar.TrimEnd('/') + Jalur;
            int selesai = 0;

            if (list.Count == 0)
            {
                h.Pesan = "Tidak ada baris valid untuk dikirim.";
                return h;
            }

            for (int b = 0; b < h.BatchTotal; b++)
            {
                if (batal())
                {
                    h.Dibatalkan = true;
                    h.Pesan = "Dibatalkan pengguna. Batch selesai: " + b + " dari " + h.BatchTotal + ".";
                    break;
                }
                int awal = b * ukuran;
                int n = Math.Min(ukuran, list.Count - awal);
                lapor(b + 1, h.BatchTotal, selesai, list.Count, h.Created, h.Duplicate, h.Error,
                    string.Format("Mengirim batch {0} dari {1} ({2} baris)...", b + 1, h.BatchTotal, n));

                int kode;
                string resp = Post(url, o.Token, BuatBody(o.NamaDiHris, list, awal, n),
                    o.TimeoutDetik * 1000, out kode);
                if (kode != 200)
                {
                    h.Berhenti = true;
                    h.Pesan = PesanGagal(kode, resp) + " (berhenti di batch " + (b + 1) + ")";
                    break;
                }

                int rec, cr, du, er;
                if (!AmbilInt(resp, "received", out rec) || !AmbilInt(resp, "created", out cr)
                    || !AmbilInt(resp, "duplicate", out du) || !AmbilInt(resp, "error", out er))
                {
                    h.Berhenti = true;
                    h.Pesan = "Balasan server tidak dikenali (batch " + (b + 1) + "): " + Potong(resp, 300);
                    break;
                }
                h.Diterima += rec; h.Created += cr; h.Duplicate += du; h.Error += er;

                foreach (Match m in Regex.Matches(resp,
                    "\\{[^{}]*\"status\"\\s*:\\s*\"error\"[^{}]*\\}"))
                {
                    int idx; int.TryParse(Regex.Match(m.Value, "\"index\"\\s*:\\s*(\\d+)").Groups[1].Value, out idx);
                    string msg = Regex.Match(m.Value, "\"message\"\\s*:\\s*\"((?:[^\"\\\\]|\\\\.)*)\"").Groups[1].Value;
                    int pos = awal + idx;
                    string asal = pos < list.Count ? ("baris " + list[pos].NoBaris + ";" + list[pos].Id + " " + list[pos].WaktuTeks) : "?";
                    if (h.DetailError.Count < 5000) h.DetailError.Add(asal + ";" + Potong(msg, 200));
                }

                selesai += n;
                h.BatchSelesai = b + 1;
                lapor(b + 1, h.BatchTotal, selesai, list.Count, h.Created, h.Duplicate, h.Error,
                    string.Format("Batch {0} dari {1} selesai.", b + 1, h.BatchTotal));
            }
            return h;
        }

        public static void TulisError(string path, KirimHasil h)
        {
            if (h.DetailError.Count == 0) return;
            File.WriteAllLines(path, h.DetailError.ToArray(), new UTF8Encoding(false));
        }
    }

    // Dialog progress: bar, angka, penghitung waktu yang terus bergerak (tanda aplikasi tidak hang), tombol Batal.
    public sealed class KirimProgressForm : Form
    {
        readonly KirimOpsi _o;
        KirimHasil _hasil;
        volatile bool _batal;
        bool _selesai;
        ProgressBar _bar;
        Label _lblStatus, _lblAngka, _lblHitung, _lblWaktu, _lblAkhir;
        Button _btnBatal, _btnTutup;
        System.Windows.Forms.Timer _timer;
        DateTime _mulai;
        int _tik;
        string _statusTerakhir = "Menyiapkan...";
        Thread _th;

        public static KirimHasil Tampilkan(IWin32Window owner, KirimOpsi o, string judul)
        {
            using (KirimProgressForm f = new KirimProgressForm(o, judul))
            {
                f.ShowDialog(owner);
                return f._hasil;
            }
        }

        KirimProgressForm(KirimOpsi o, string judul)
        {
            _o = o;
            Text = judul;
            FormBorderStyle = FormBorderStyle.FixedDialog;
            StartPosition = FormStartPosition.CenterParent;
            MaximizeBox = false; MinimizeBox = false; ControlBox = false;
            ClientSize = new Size(480, 220);

            _lblStatus = new Label(); _lblStatus.SetBounds(16, 14, 448, 20);
            _bar = new ProgressBar(); _bar.SetBounds(16, 40, 448, 24); _bar.Minimum = 0; _bar.Maximum = 100;
            _lblAngka = new Label(); _lblAngka.SetBounds(16, 72, 448, 20);
            _lblHitung = new Label(); _lblHitung.SetBounds(16, 94, 448, 20);
            _lblWaktu = new Label(); _lblWaktu.SetBounds(16, 116, 448, 20);
            _lblAkhir = new Label(); _lblAkhir.SetBounds(16, 140, 448, 40);
            _btnBatal = new Button(); _btnBatal.Text = "Batal"; _btnBatal.SetBounds(384, 184, 80, 28);
            _btnTutup = new Button(); _btnTutup.Text = "Tutup"; _btnTutup.SetBounds(384, 184, 80, 28);
            _btnTutup.Visible = false; _btnTutup.DialogResult = DialogResult.OK;
            _btnBatal.Click += delegate
            {
                _batal = true;
                _btnBatal.Enabled = false;
                _statusTerakhir = "Membatalkan setelah batch yang sedang berjalan selesai...";
            };
            Controls.AddRange(new Control[] { _lblStatus, _bar, _lblAngka, _lblHitung, _lblWaktu, _lblAkhir, _btnBatal, _btnTutup });
            AcceptButton = _btnTutup;

            _timer = new System.Windows.Forms.Timer();
            _timer.Interval = 400;
            _timer.Tick += delegate
            {
                _tik++;
                string[] spin = new string[] { "|", "/", "-", "\\" };
                TimeSpan t = DateTime.Now - _mulai;
                _lblStatus.Text = _statusTerakhir;
                _lblWaktu.Text = string.Format("Berjalan {0:00}:{1:00}  {2}  (aplikasi bekerja)",
                    (int)t.TotalMinutes, t.Seconds, spin[_tik % 4]);
            };
        }

        protected override void OnShown(EventArgs e)
        {
            base.OnShown(e);
            _mulai = DateTime.Now;
            _timer.Start();
            _th = new Thread(Kerja);
            _th.IsBackground = true;
            _th.Start();
        }

        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            if (!_selesai) e.Cancel = true;
            base.OnFormClosing(e);
        }

        void Kerja()
        {
            KirimHasil h;
            try
            {
                h = KirimHris.Jalankan(_o, LaporUi, delegate { return _batal; });
            }
            catch (Exception ex)
            {
                h = new KirimHasil();
                h.Berhenti = true;
                h.Pesan = "Kesalahan tak terduga: " + ex.Message;
            }
            _hasil = h;
            if (IsHandleCreated && !IsDisposed) BeginInvoke(new MethodInvoker(Selesai));
        }

        void LaporUi(int batchKe, int batchTotal, int selesai, int total, int cr, int du, int er, string status)
        {
            if (!IsHandleCreated || IsDisposed) return;
            BeginInvoke(new MethodInvoker(delegate
            {
                _statusTerakhir = status;
                int pct = total > 0 ? (int)((long)selesai * 100 / total) : 0;
                _bar.Value = Math.Max(0, Math.Min(100, pct));
                _lblAngka.Text = string.Format("Baris {0:N0} dari {1:N0} ({2}%)  |  Batch {3}/{4}",
                    selesai, total, pct, batchKe, batchTotal);
                _lblHitung.Text = string.Format("Created {0:N0}  |  Duplicate {1:N0}  |  Error {2:N0}", cr, du, er);
            }));
        }

        void Selesai()
        {
            _selesai = true;
            _timer.Stop();
            ControlBox = true;
            if (!_hasil.Berhenti && !_hasil.Dibatalkan) _bar.Value = 100;
            _lblStatus.Text = _hasil.Berhenti ? "BERHENTI karena kegagalan" : (_hasil.Dibatalkan ? "DIBATALKAN" : "SELESAI");
            _lblAngka.Text = _hasil.Ringkas();
            _lblAkhir.Text = _hasil.Pesan;
            _btnBatal.Visible = false;
            _btnTutup.Visible = true;
            _btnTutup.Focus();
        }
    }
}