using System;
using System.Collections.Generic;
using System.Drawing;
using System.Windows.Forms;

namespace HrisDeviceTool
{
    // Dialog pemilih mesin: tabel dengan kotak cari. Hanya memilih, tidak menyentuh mesin.
    public class PilihMesinForm : Form
    {
        List<MesinItem> semua;
        TextBox txtCari;
        ListView lv;
        Label lblJumlah;
        public MesinItem Hasil;

        public static string KeyText(MesinItem m)
        {
            if (m.TanpaKey) return "Tanpa";
            if (m.IngatKey) return "Ingat";
            return "Tanya";
        }

        public PilihMesinForm(List<MesinItem> daftar, MesinItem awal, string judul)
        {
            semua = daftar;
            Text = judul;
            FormBorderStyle = FormBorderStyle.FixedDialog;
            StartPosition = FormStartPosition.CenterParent;
            MinimizeBox = false;
            MaximizeBox = false;
            ClientSize = new Size(520, 400);

            Label l = new Label();
            l.Text = "Cari (nama atau IP)";
            l.Location = new Point(12, 14);
            l.AutoSize = true;

            txtCari = new TextBox();
            txtCari.Location = new Point(130, 10);
            txtCari.Width = 378;

            lv = new ListView();
            lv.View = View.Details;
            lv.FullRowSelect = true;
            lv.GridLines = true;
            lv.HideSelection = false;
            lv.MultiSelect = false;
            lv.Location = new Point(12, 42);
            lv.Size = new Size(496, 300);
            lv.Columns.Add("No", 45);
            lv.Columns.Add("Nama", 175);
            lv.Columns.Add("IP", 125);
            lv.Columns.Add("Port", 55);
            lv.Columns.Add("Key", 70);

            lblJumlah = new Label();
            lblJumlah.Location = new Point(12, 350);
            lblJumlah.AutoSize = true;

            Button ok = new Button();
            ok.Text = "Pilih";
            ok.Location = new Point(338, 364);
            ok.Size = new Size(80, 28);
            Button cancel = new Button();
            cancel.Text = "Batal";
            cancel.Location = new Point(428, 364);
            cancel.Size = new Size(80, 28);
            cancel.DialogResult = DialogResult.Cancel;

            Controls.Add(l);
            Controls.Add(txtCari);
            Controls.Add(lv);
            Controls.Add(lblJumlah);
            Controls.Add(ok);
            Controls.Add(cancel);
            AcceptButton = ok;
            CancelButton = cancel;

            ok.Click += delegate { Pilih(); };
            lv.DoubleClick += delegate { Pilih(); };
            txtCari.TextChanged += delegate { Isi(null); };

            Isi(awal);
            ActiveControl = txtCari;
        }

        void Isi(MesinItem pilih)
        {
            string q = txtCari.Text.Trim();
            lv.BeginUpdate();
            lv.Items.Clear();
            int no = 0;
            int tampil = 0;
            foreach (MesinItem m in semua)
            {
                no++;
                if (q.Length > 0 &&
                    m.Nama.IndexOf(q, StringComparison.OrdinalIgnoreCase) < 0 &&
                    m.Ip.IndexOf(q, StringComparison.OrdinalIgnoreCase) < 0) continue;
                ListViewItem it = new ListViewItem(no.ToString());
                it.SubItems.Add(m.Nama);
                it.SubItems.Add(m.Ip);
                it.SubItems.Add(m.Port.ToString());
                it.SubItems.Add(KeyText(m));
                it.Tag = m;
                lv.Items.Add(it);
                tampil++;
                if (pilih != null && object.ReferenceEquals(m, pilih)) it.Selected = true;
            }
            if (lv.SelectedItems.Count == 0 && lv.Items.Count > 0) lv.Items[0].Selected = true;
            lv.EndUpdate();
            lblJumlah.Text = "Menampilkan " + tampil + " dari " + semua.Count + " mesin. Klik ganda atau Enter untuk memilih.";
        }

        void Pilih()
        {
            if (lv.SelectedItems.Count == 0)
            {
                MessageBox.Show("Pilih satu mesin dulu.", "HRIS Device Tool");
                return;
            }
            Hasil = (MesinItem)lv.SelectedItems[0].Tag;
            DialogResult = DialogResult.OK;
        }
    }

    // Pengganti ComboBox mesin: kotak teks + tombol "..." yang membuka PilihMesinForm.
    // Anggota Items, SelectedItem, SelectedIndex dibuat sama dengan ComboBox agar kode lama tetap jalan.
    public class MesinPicker : Panel
    {
        public List<MesinItem> Items = new List<MesinItem>();
        MesinItem terpilih = null;
        TextBox txt;
        Button btn;

        public MesinPicker()
        {
            Size = new Size(200, 23);
            txt = new TextBox();
            txt.ReadOnly = true;
            txt.BackColor = SystemColors.Window;
            txt.Location = new Point(0, 0);
            txt.Size = new Size(170, 22);
            txt.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
            btn = new Button();
            btn.Text = "...";
            btn.Location = new Point(171, 0);
            btn.Size = new Size(29, 23);
            btn.Anchor = AnchorStyles.Top | AnchorStyles.Right;
            txt.Click += delegate { Buka(); };
            btn.Click += delegate { Buka(); };
            Controls.Add(txt);
            Controls.Add(btn);
        }

        public MesinItem SelectedItem
        {
            get { return terpilih; }
        }

        public int SelectedIndex
        {
            get { return terpilih == null ? -1 : Items.IndexOf(terpilih); }
            set
            {
                terpilih = (value >= 0 && value < Items.Count) ? Items[value] : null;
                Tampil();
            }
        }

        void Tampil()
        {
            txt.Text = (terpilih == null) ? "" : terpilih.Nama + "  " + terpilih.Ip;
        }

        void Buka()
        {
            if (Items.Count == 0)
            {
                MessageBox.Show("Belum ada mesin terdaftar.", "HRIS Device Tool");
                return;
            }
            PilihMesinForm f = new PilihMesinForm(Items, terpilih, "Pilih mesin");
            if (f.ShowDialog(FindForm()) == DialogResult.OK)
            {
                terpilih = f.Hasil;
                Tampil();
            }
            f.Dispose();
        }
    }
}