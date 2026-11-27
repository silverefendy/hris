using System;
using System.Collections.Generic;
using System.Drawing;
using System.Windows.Forms;

namespace HrisDeviceTool
{
    // Dialog centang mesin untuk pekerjaan yang membaca banyak mesin sekaligus.
    public static class PilihBanyakMesin
    {
        // awal = null: semua tercentang. Selain itu hanya mesin tersebut. Kembalian null = batal.
        public static List<MesinItem> Tanya(IWin32Window induk, List<MesinItem> daftar, string judul, string keterangan, MesinItem awal)
        {
            using (Form f = new Form())
            {
                f.Text = judul;
                f.FormBorderStyle = FormBorderStyle.FixedDialog;
                f.StartPosition = FormStartPosition.CenterParent;
                f.MinimizeBox = false;
                f.MaximizeBox = false;
                f.ClientSize = new Size(400, 390);

                Label l = new Label();
                l.Text = keterangan;
                l.Location = new Point(12, 10);
                l.Size = new Size(376, 52);
                f.Controls.Add(l);

                CheckedListBox cl = new CheckedListBox();
                cl.CheckOnClick = true;
                cl.IntegralHeight = false;
                cl.Location = new Point(12, 68);
                cl.Size = new Size(376, 230);
                foreach (MesinItem m in daftar) cl.Items.Add(m, awal == null || m == awal);
                f.Controls.Add(cl);

                Button semua = Gaya.Tombol("Centang semua", 120, delegate { for (int i = 0; i < cl.Items.Count; i++) cl.SetItemChecked(i, true); });
                semua.Location = new Point(12, 306);
                Button kosong = Gaya.Tombol("Kosongkan", 100, delegate { for (int i = 0; i < cl.Items.Count; i++) cl.SetItemChecked(i, false); });
                kosong.Location = new Point(140, 306);
                Button ok = Gaya.Tombol("Mulai", 90, null);
                ok.DialogResult = DialogResult.OK;
                ok.Location = new Point(204, 348);
                Gaya.Utama(ok);
                Button batal = Gaya.Tombol("Batal", 90, null);
                batal.DialogResult = DialogResult.Cancel;
                batal.Location = new Point(298, 348);
                f.Controls.Add(semua);
                f.Controls.Add(kosong);
                f.Controls.Add(ok);
                f.Controls.Add(batal);
                f.AcceptButton = ok;
                f.CancelButton = batal;

                if (f.ShowDialog(induk) != DialogResult.OK) return null;
                List<MesinItem> hasil = new List<MesinItem>();
                foreach (object o in cl.CheckedItems) hasil.Add((MesinItem)o);
                if (hasil.Count == 0)
                {
                    MessageBox.Show("Tidak ada mesin yang dicentang.", judul);
                    return null;
                }
                return hasil;
            }
        }
    }
}
