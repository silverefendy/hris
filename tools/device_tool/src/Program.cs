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
            st.UnlockAtStartup();
            Application.Run(new MainForm(st));
        }
    }
}
