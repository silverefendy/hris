using System;
using System.Collections.Generic;
using System.Data;
using System.Data.SQLite;
using System.Drawing;
using System.IO;
using System.Text;
using System.Windows.Forms;

namespace HrisDeviceTool
{
    // Penampil database lokal (hanya baca): v_karyawan_lokal, induk_aplikasi_lama, user_mesin, mesin.
    public class DatabaseForm : Form
    {
        const int BatasBaris = 5000;
        static readonly string[] Objek = { "v_karyawan_lokal", "induk_aplikasi_lama", "user_mesin", "mesin" };

        ComboBox cmb;
        TextBox txtCari;
        DataGridView grid;
        Label lblInfo;
        DataTable tabel;
        DataView tampilan;
        CheckBox chkKosong;
        string berkasDb;
        bool terpotong;

        public DatabaseForm()
        {
            Text = "Database lokal (hanya baca)";
            StartPosition = FormStartPosition.CenterParent;
            ClientSize = new Size(1000, 560);
            MinimumSize = new Size(700, 400);
            berkasDb = global::HrisDeviceTool.Data.HdtDatabase.BerkasDefault();

            Panel atas = new Panel();
            atas.Dock = DockStyle.Top;
            atas.Height = 40;
            Label l1 = new Label();
            l1.Text = "Tabel:";
            l1.Location = new Point(10, 13);
            l1.AutoSize = true;
            cmb = new ComboBox();
            cmb.DropDownStyle = ComboBoxStyle.DropDownList;
            cmb.Location = new Point(55, 9);
            cmb.Width = 200;
            foreach (string o in Objek) { cmb.Items.Add(o); }
            Label l2 = new Label();
            l2.Text = "Cari:";
            l2.Location = new Point(275, 13);
            l2.AutoSize = true;
            txtCari = new TextBox();
            txtCari.Location = new Point(315, 9);
            txtCari.Width = 260;
            atas.Controls.Add(l1);
            atas.Controls.Add(cmb);
            atas.Controls.Add(l2);
            atas.Controls.Add(txtCari);
            chkKosong = new CheckBox();
            chkKosong.Text = "Sembunyikan kolom kosong";
            chkKosong.Checked = true;
            chkKosong.AutoSize = true;
            chkKosong.Location = new Point(600, 11);
            chkKosong.CheckedChanged += delegate { AturKolom(); };
            atas.Controls.Add(chkKosong);

            Panel bawah = new Panel();
            bawah.Dock = DockStyle.Bottom;
            bawah.Height = 40;
            lblInfo = new Label();
            lblInfo.Location = new Point(10, 13);
            lblInfo.AutoSize = true;
            Button btnEkspor = new Button();
            btnEkspor.Text = "Ekspor CSV";
            btnEkspor.Size = new Size(110, 28);
            btnEkspor.Anchor = AnchorStyles.Top | AnchorStyles.Right;
            btnEkspor.Location = new Point(ClientSize.Width - 240, 6);
            btnEkspor.Click += delegate { Ekspor(); };
            Button btnTutup = new Button();
            btnTutup.Text = "Tutup";
            btnTutup.Size = new Size(100, 28);
            btnTutup.Anchor = AnchorStyles.Top | AnchorStyles.Right;
            btnTutup.Location = new Point(ClientSize.Width - 120, 6);
            btnTutup.Click += delegate { Close(); };
            bawah.Controls.Add(lblInfo);
            bawah.Controls.Add(btnEkspor);
            bawah.Controls.Add(btnTutup);

            grid = new DataGridView();
            grid.Dock = DockStyle.Fill;
            grid.ReadOnly = true;
            grid.AllowUserToAddRows = false;
            grid.AllowUserToDeleteRows = false;
            grid.RowHeadersVisible = false;
            grid.SelectionMode = DataGridViewSelectionMode.FullRowSelect;
            grid.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.DisplayedCells;
            grid.DataBindingComplete += delegate { AturKolom(); };

            Controls.Add(grid);
            Controls.Add(bawah);
            Controls.Add(atas);

            cmb.SelectedIndexChanged += delegate { Muat(); };
            txtCari.TextChanged += delegate { Terapkan(); };
            cmb.SelectedIndex = 0;
        }

        void Muat()
        {
            try
            {
                string objek = (string)cmb.SelectedItem;
                DataTable t = new DataTable();
                using (SQLiteConnection c = global::HrisDeviceTool.Data.HdtDatabase.Buka(berkasDb))
                using (SQLiteCommand cmd = new SQLiteCommand("select * from " + objek + " limit " + (BatasBaris + 1), c))
                using (SQLiteDataAdapter da = new SQLiteDataAdapter(cmd))
                {
                    da.Fill(t);
                }
                terpotong = t.Rows.Count > BatasBaris;
                if (terpotong) { t.Rows.RemoveAt(t.Rows.Count - 1); }
                tabel = t;
                tampilan = new DataView(t);
                grid.DataSource = tampilan;
                Terapkan();
            }
            catch (Exception ex)
            {
                MessageBox.Show("Gagal membuka database: " + ex.Message, "Database lokal", MessageBoxButtons.OK, MessageBoxIcon.Warning);
            }
        }

        void AturKolom()
        {
            if (tabel == null || grid.Columns.Count == 0) { return; }
            bool sembunyi = chkKosong.Checked;
            List<DataGridViewColumn> depan = new List<DataGridViewColumn>();
            List<DataGridViewColumn> isi = new List<DataGridViewColumn>();
            List<DataGridViewColumn> kosong = new List<DataGridViewColumn>();
            foreach (DataColumn dc in tabel.Columns)
            {
                DataGridViewColumn gc = grid.Columns[dc.ColumnName];
                if (gc == null) { continue; }
                bool ada = false;
                foreach (DataRow r in tabel.Rows)
                {
                    object v = r[dc];
                    if (v != null && !(v is DBNull) && Convert.ToString(v).Trim().Length > 0) { ada = true; break; }
                }
                if (dc.ColumnName == "id") { depan.Add(gc); }
                else if (ada) { isi.Add(gc); }
                else { kosong.Add(gc); }
            }
            int i = 0;
            foreach (DataGridViewColumn gc in depan) { gc.Visible = true; gc.DisplayIndex = i++; }
            foreach (DataGridViewColumn gc in isi) { gc.Visible = true; gc.DisplayIndex = i++; }
            foreach (DataGridViewColumn gc in kosong) { gc.Visible = !sembunyi; gc.DisplayIndex = i++; }
        }

        static string Esc(string s)
        {
            return s.Replace("'", "''").Replace("[", "[[]").Replace("%", "[%]").Replace("*", "[*]");
        }

        void Terapkan()
        {
            if (tampilan == null) { return; }
            string q = txtCari.Text.Trim();
            if (q.Length == 0)
            {
                tampilan.RowFilter = "";
            }
            else
            {
                string e = Esc(q);
                List<string> bagian = new List<string>();
                foreach (DataColumn col in tabel.Columns)
                {
                    bagian.Add("Convert([" + col.ColumnName + "], 'System.String') LIKE '%" + e + "%'");
                }
                try { tampilan.RowFilter = string.Join(" OR ", bagian.ToArray()); }
                catch (Exception) { tampilan.RowFilter = "1 = 0"; }
            }
            lblInfo.Text = "menampilkan " + tampilan.Count + " dari " + tabel.Rows.Count + " baris"
                + (terpotong ? " (dibatasi " + BatasBaris + " baris pertama, gunakan Cari atau Ekspor lewat skrip)" : "");
        }

        static string Q(string s)
        {
            if (s == null) { s = ""; }
            return "\"" + s.Replace("\"", "\"\"") + "\"";
        }

        void Ekspor()
        {
            if (tampilan == null || tampilan.Count == 0)
            {
                MessageBox.Show("Tidak ada baris untuk diekspor.", "Ekspor CSV");
                return;
            }
            if (MessageBox.Show("Berkas CSV berisi data pribadi karyawan. Simpan di tempat yang aman.\r\n\r\nLanjutkan?",
                "Ekspor CSV", MessageBoxButtons.YesNo, MessageBoxIcon.Warning) != DialogResult.Yes) { return; }
            using (SaveFileDialog dlg = new SaveFileDialog())
            {
                dlg.Title = "Ekspor tampilan ke CSV";
                dlg.Filter = "CSV (*.csv)|*.csv";
                dlg.FileName = (string)cmb.SelectedItem + "_" + DateTime.Now.ToString("yyyyMMdd_HHmm") + ".csv";
                if (dlg.ShowDialog(this) != DialogResult.OK) { return; }
                StringBuilder sb = new StringBuilder();
                List<string> judul = new List<string>();
                foreach (DataColumn col in tabel.Columns) { judul.Add(Q(col.ColumnName)); }
                sb.AppendLine(string.Join(",", judul.ToArray()));
                foreach (DataRowView r in tampilan)
                {
                    List<string> nilai = new List<string>();
                    foreach (DataColumn col in tabel.Columns) { nilai.Add(Q(Convert.ToString(r[col.ColumnName]))); }
                    sb.AppendLine(string.Join(",", nilai.ToArray()));
                }
                File.WriteAllText(dlg.FileName, sb.ToString(), new UTF8Encoding(true));
                AuditLog.Tulis("Ekspor database", (string)cmb.SelectedItem + ": " + tampilan.Count + " baris");
                MessageBox.Show("Selesai:\r\n" + dlg.FileName, "Ekspor CSV");
            }
        }
    }
}
