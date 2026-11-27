using System;
using System.Windows.Forms;

namespace HrisDeviceTool
{
    static class Program
    {
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Store st = new Store(AppDomain.CurrentDomain.BaseDirectory);
            try
            {
                st.Load();
            }
            catch (Exception e)
            {
                MessageBox.Show("Gagal membaca data pengaturan:\r\n" + e.Message +
                    "\r\n\r\nPeriksa folder data di samping aplikasi (bisa ditulis? berkas rusak?).",
                    "HRIS Device Tool", MessageBoxButtons.OK, MessageBoxIcon.Error);
                return;
            }
            bool pertama = true;
            while (true)
            {
                if (!Akun.Masuk(st)) return;
                if (pertama)
                {
                    st.UnlockAtStartup();
                    pertama = false;
                }
                AuditLog.Dir = st.LogDir;
                Salinan.BersihkanOtomatis(st);
                MainForm utama = new MainForm(st);
                utama.Text += "   [" + Peran.NamaAktif + "]";
                Application.Run(utama);
                if (!utama.KeluarAkun) return;
                Peran.Level = 0;
                Brankas.Keluar();
            }
        }
    }
}