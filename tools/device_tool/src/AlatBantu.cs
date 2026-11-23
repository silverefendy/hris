using System;
using System.Drawing;
using System.IO;
using System.Windows.Forms;

namespace HrisDeviceTool
{
    // Catatan aktivitas per menu: data\log\<kategori>\<kategori>_<tanggal>.hdtlog
    // Tidak pernah menulis Comm Key, token, atau kata sandi.
    public static class AuditLog
    {
        public static string Dir = "";
        public static string Kat = "sistem";

        static string Peta(string aksi)
        {
            if (aksi.StartsWith("Tarik log", StringComparison.Ordinal) ||
                aksi.StartsWith("Ekspor log", StringComparison.Ordinal) ||
                aksi.StartsWith("Salinan", StringComparison.Ordinal)) return "tarik-log";
            if (aksi.StartsWith("Bandingkan", StringComparison.Ordinal) ||
                aksi.StartsWith("Ekspor bandingkan", StringComparison.Ordinal)) return "bandingkan";
            return Kat;
        }

        public static string Berkas(string kat)
        {
            if (Dir.Length == 0) return Path.Combine(Path.GetTempPath(), "hdt_" + kat + ".hdtlog");
            string d = Path.Combine(Dir, kat);
            Directory.CreateDirectory(d);
            return Path.Combine(d, kat + "_" + DateTime.Now.ToString("yyyyMMdd") + ".hdtlog");
        }

        public static void Tulis(string aksi, string rincian)
        {
            try
            {
                string t = aksi;
                if (rincian != null && rincian.Length > 0) t += ": " + rincian;
                string baris = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") + "  [" + Environment.UserName + "@" + Environment.MachineName + " / " + Peran.NamaAktif + "]  " + t;
                File.AppendAllText(Berkas(Peta(aksi)), baris + Environment.NewLine);
            }
            catch { }
        }
    }

    // Kotak pilihan mesin yang tampil seperti tabel: No, Nama, IP, Port
    public static class PilihMesin
    {
        public static void Gaya(ComboBox c)
        {
            c.DrawMode = DrawMode.OwnerDrawFixed;
            c.ItemHeight = 18;
            c.DropDownWidth = 400;
            c.DrawItem += delegate (object s, DrawItemEventArgs e)
            {
                e.DrawBackground();
                if (e.Index < 0) return;
                MesinItem m = c.Items[e.Index] as MesinItem;
                if (m == null) return;
                bool tertutup = (e.State & DrawItemState.ComboBoxEdit) == DrawItemState.ComboBoxEdit;
                Brush br = ((e.State & DrawItemState.Selected) == DrawItemState.Selected) ? SystemBrushes.HighlightText : SystemBrushes.WindowText;
                Rectangle r = e.Bounds;
                if (tertutup)
                {
                    e.Graphics.DrawString((e.Index + 1) + ". " + m.Nama + "  " + m.Ip, e.Font, br, r.X + 2, r.Y + 2);
                }
                else
                {
                    e.Graphics.DrawString((e.Index + 1).ToString(), e.Font, br, r.X + 4, r.Y + 2);
                    e.Graphics.DrawString(m.Nama, e.Font, br, r.X + 40, r.Y + 2);
                    e.Graphics.DrawString(m.Ip, e.Font, br, r.X + 190, r.Y + 2);
                    e.Graphics.DrawString(m.Port.ToString(), e.Font, br, r.X + 320, r.Y + 2);
                    using (Pen p = new Pen(Color.Gainsboro))
                    {
                        e.Graphics.DrawLine(p, r.X, r.Bottom - 1, r.Right, r.Bottom - 1);
                    }
                }
            };
        }
    }
}
