using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Windows.Forms;

namespace HrisDeviceTool
{
    public class MainForm : Form
    {
        const string Versi = "0.1.0 (tahap 2)";
        Store st;
        ListBox lst;
        TextBox txtLog, txtUid, txtNama, txtUidFp;
        NumericUpDown numJari;
        ListView lvUser;
        object enrollZk = null;
        string enrollMesin = "";
        string enrollUid = "";

        public MainForm(Store store)
        {
            st = store;
            Text = "HRIS Device Tool " + Versi;
            ClientSize = new Size(1000, 680);
            MinimumSize = new Size(1000, 680);
            StartPosition = FormStartPosition.CenterScreen;
            BuildUi();
            RefreshList(null);
            FormClosing += OnClosing;
            Log("Aplikasi dibuka. Folder data: " + st.DataDir);
            if (st.Data.Mesin.Count == 0)
                Log("Belum ada mesin. Klik Tambah di kiri untuk mendaftarkan mesin pertama.");
            if (st.SecretsLocked)
                Log("Comm Key tersimpan tidak dibuka (kata sandi dilewati). Comm Key akan ditanyakan saat menghubungkan.");
        }

        // ---------- UI ----------
        Button Btn(string text, int x, int y, int w, EventHandler h)
        {
            Button b = new Button();
            b.Text = text;
            b.Location = new Point(x, y);
            b.Size = new Size(w, 28);
            b.Click += h;
            return b;
        }

        Label Lbl(string text, int x, int y)
        {
            Label l = new Label();
            l.Text = text;
            l.Location = new Point(x, y);
            l.AutoSize = true;
            return l;
        }

        void BuildUi()
        {
            txtLog = new TextBox();
            txtLog.Multiline = true;
            txtLog.ReadOnly = true;
            txtLog.ScrollBars = ScrollBars.Vertical;
            txtLog.Font = new Font("Consolas", 9f);
            txtLog.Location = new Point(10, 435);
            txtLog.Size = new Size(980, 235);
            txtLog.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;

            Label lm = Lbl("Daftar mesin", 10, 10);
            lst = new ListBox();
            lst.Location = new Point(10, 30);
            lst.Size = new Size(230, 250);

            TabControl tabs = new TabControl();
            tabs.Location = new Point(250, 10);
            tabs.Size = new Size(740, 415);
            tabs.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right;
            tabs.TabPages.Add(BuildTabInfo());
            tabs.TabPages.Add(BuildTabUser());
            tabs.TabPages.Add(BuildTabJari());
            tabs.TabPages.Add(BuildTabBantuan());

            Controls.Add(lm);
            Controls.Add(lst);
            Controls.Add(Btn("Tambah", 10, 286, 70, delegate { OnTambah(); }));
            Controls.Add(Btn("Ubah", 85, 286, 70, delegate { OnUbah(); }));
            Controls.Add(Btn("Hapus", 160, 286, 70, delegate { OnHapus(); }));
            Controls.Add(Btn("Bersihkan log", 10, 330, 120, delegate { txtLog.Clear(); }));
            Controls.Add(tabs);
            Controls.Add(txtLog);
        }

        TabPage BuildTabInfo()
        {
            TabPage p = new TabPage("Info mesin");
            Label l = Lbl("Membaca informasi mesin yang dipilih di daftar kiri: tipe, firmware, versi jari/wajah,\r\njumlah data, dan jam mesin. Hanya membaca, tidak mengubah apa pun di mesin.", 15, 15);
            p.Controls.Add(l);
            p.Controls.Add(Btn("Ambil info mesin", 15, 65, 180, delegate { OnInfo(); }));
            return p;
        }

        TabPage BuildTabUser()
        {
            TabPage p = new TabPage("User");
            p.Controls.Add(Lbl("ID user", 15, 20));
            txtUid = new TextBox();
            txtUid.Location = new Point(70, 17);
            txtUid.Width = 130;
            txtUid.Text = "99901";
            p.Controls.Add(txtUid);
            p.Controls.Add(Lbl("Nama", 220, 20));
            txtNama = new TextBox();
            txtNama.Location = new Point(265, 17);
            txtNama.Width = 200;
            p.Controls.Add(txtNama);
            p.Controls.Add(Btn("Cek user", 15, 52, 110, delegate { OnCekUser(); }));
            p.Controls.Add(Btn("Tambah user uji (999...)", 135, 52, 170, delegate { OnTambahUserUji(); }));
            p.Controls.Add(Btn("Daftar user", 315, 52, 110, delegate { OnDaftarUser(); }));
            lvUser = new ListView();
            lvUser.View = View.Details;
            lvUser.FullRowSelect = true;
            lvUser.GridLines = true;
            lvUser.Columns.Add("ID", 110);
            lvUser.Columns.Add("Nama", 280);
            lvUser.Columns.Add("Privilege", 80);
            lvUser.Columns.Add("Status", 90);
            lvUser.Location = new Point(15, 92);
            lvUser.Size = new Size(700, 285);
            lvUser.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;
            p.Controls.Add(lvUser);
            return p;
        }

        TabPage BuildTabJari()
        {
            TabPage p = new TabPage("Sidik jari");
            p.Controls.Add(Lbl("ID user", 15, 20));
            txtUidFp = new TextBox();
            txtUidFp.Location = new Point(70, 17);
            txtUidFp.Width = 130;
            txtUidFp.Text = "99901";
            p.Controls.Add(txtUidFp);
            p.Controls.Add(Lbl("Jari (0-9)", 220, 20));
            numJari = new NumericUpDown();
            numJari.Minimum = 0;
            numJari.Maximum = 9;
            numJari.Value = 5;
            numJari.Location = new Point(285, 17);
            numJari.Width = 50;
            p.Controls.Add(numJari);
            p.Controls.Add(Btn("Baca template (jari 0-9)", 15, 55, 190, delegate { OnBacaTemplate(); }));
            p.Controls.Add(Btn("Picu daftar dari PC", 215, 55, 170, delegate { OnPicu(); }));
            p.Controls.Add(Btn("Selesai daftar && baca", 395, 55, 170, delegate { OnSelesai(); }));
            p.Controls.Add(Lbl("Baca template: hanya membaca. Hasil disimpan di folder data\\cadangan (ekstensi .hdttmpl).\r\n\r\nPicu daftar: mesin dipaksa masuk mode daftar untuk ID tersebut (hanya ID uji berawalan 999).\r\nMinta rekan menempelkan jari di mesin, lalu klik 'Selesai daftar && baca'.\r\nSelama menunggu, aplikasi TIDAK membaca apa pun (pembacaan berulang diduga membatalkan mode daftar).", 15, 100));
            return p;
        }

        TabPage BuildTabBantuan()
        {
            TabPage p = new TabPage("Bantuan");
            p.Controls.Add(Btn("Diagnostik", 15, 15, 140, delegate { OnDiagnostik(); }));
            p.Controls.Add(Btn("Buka folder data", 165, 15, 150, delegate { BukaFolder(st.DataDir); }));
            p.Controls.Add(Btn("Buka folder panduan", 325, 15, 170, delegate { OnPanduan(); }));
            p.Controls.Add(Lbl("Diagnostik memeriksa: komponen mesin (zkemkeeper), folder data, dan koneksi ke semua mesin terdaftar.\r\n\r\nPindah ke PC lain: salin SELURUH folder aplikasi (exe + folder data).\r\nComm Key yang disimpan dibuka dengan kata sandi aplikasi.\r\n\r\nPanduan lengkap ada di folder docs (ditambahkan setelah tahap ini teruji).\r\nVersi: " + Versi, 15, 60));
            return p;
        }

        // ---------- Bantu ----------
        void Msg(string s)
        {
            MessageBox.Show(s, "HRIS Device Tool", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }

        void Log(string s)
        {
            string line = DateTime.Now.ToString("HH:mm") + "  " + s.Replace("\r\n", "\n").Replace("\n", "\r\n");
            txtLog.AppendText(line + "\r\n");
            try
            {
                string f = Path.Combine(st.LogDir, "app_" + DateTime.Now.ToString("yyyyMMdd") + ".hdtlog");
                File.AppendAllText(f, DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") + "  " + s + Environment.NewLine);
            }
            catch { }
        }

        void RefreshList(string pilih)
        {
            lst.Items.Clear();
            foreach (MesinItem m in st.Data.Mesin)
            {
                int i = lst.Items.Add(m);
                if (pilih != null && m.Nama == pilih) lst.SelectedIndex = i;
            }
            if (lst.SelectedIndex < 0 && lst.Items.Count > 0) lst.SelectedIndex = 0;
        }

        MesinItem Selected()
        {
            MesinItem m = lst.SelectedItem as MesinItem;
            if (m == null) Msg("Pilih mesin di daftar kiri dulu (atau klik Tambah).");
            return m;
        }

        string GetKey(MesinItem m)
        {
            string k;
            if (st.Keys.TryGetValue(m.Nama, out k)) return k;
            string r = Dlg.Prompt("Comm Key", "Comm Key untuk mesin " + m.Nama + "\r\n(kosongkan bila mesin tidak memakai Comm Key):", true, false);
            if (r == null) return null;
            st.Keys[m.Nama] = r;
            return r;
        }

        object Open(MesinItem m)
        {
            string key = GetKey(m);
            if (key == null) return null;
            Cursor = Cursors.WaitCursor;
            try
            {
                return Dev.Connect(m, key);
            }
            catch (Exception e)
            {
                Cursor = Cursors.Default;
                Log("GAGAL " + m.Nama + ": " + e.Message);
                MessageBox.Show(e.Message, "Tidak bisa terhubung", MessageBoxButtons.OK, MessageBoxIcon.Warning);
                if (e.Message.IndexOf("Comm Key", StringComparison.Ordinal) >= 0) st.Keys.Remove(m.Nama);
                return null;
            }
        }

        void Done(object zk)
        {
            Dev.Disconnect(zk);
            Cursor = Cursors.Default;
        }

        void BukaFolder(string path)
        {
            if (Directory.Exists(path)) Process.Start("explorer.exe", "\"" + path + "\"");
            else Msg("Folder belum ada: " + path);
        }

        void OnClosing(object sender, FormClosingEventArgs e)
        {
            if (enrollZk != null) Dev.Disconnect(enrollZk);
        }

        // ---------- Daftar mesin ----------
        void OnTambah()
        {
            MesinDialog dlg = new MesinDialog(st, null, "");
            if (dlg.ShowDialog(this) != DialogResult.OK) return;
            st.Data.Mesin.Add(dlg.Result);
            if (dlg.KeyResult.Length > 0) st.Keys[dlg.Result.Nama] = dlg.KeyResult;
            st.SaveData();
            bool ok = st.SaveSecrets();
            if (dlg.Result.IngatKey && !ok) Log("Comm Key TIDAK tersimpan (hanya untuk sesi ini).");
            RefreshList(dlg.Result.Nama);
            Log("Mesin ditambah: " + dlg.Result.Nama + " (" + dlg.Result.Ip + ":" + dlg.Result.Port + ")");
        }

        void OnUbah()
        {
            MesinItem m = Selected();
            if (m == null) return;
            string oldName = m.Nama;
            string oldKey;
            st.Keys.TryGetValue(oldName, out oldKey);
            if (oldKey == null) oldKey = "";
            MesinDialog dlg = new MesinDialog(st, m, oldKey);
            if (dlg.ShowDialog(this) != DialogResult.OK) return;
            int i = st.Data.Mesin.IndexOf(m);
            st.Data.Mesin[i] = dlg.Result;
            st.Keys.Remove(oldName);
            if (dlg.KeyResult.Length > 0) st.Keys[dlg.Result.Nama] = dlg.KeyResult;
            st.SaveData();
            bool ok = st.SaveSecrets();
            if (dlg.Result.IngatKey && !ok) Log("Comm Key TIDAK tersimpan (hanya untuk sesi ini).");
            RefreshList(dlg.Result.Nama);
            Log("Mesin diubah: " + dlg.Result.Nama);
        }

        void OnHapus()
        {
            MesinItem m = Selected();
            if (m == null) return;
            if (MessageBox.Show("Hapus mesin " + m.Nama + " dari daftar aplikasi?\r\n(Tidak menghapus apa pun di mesin absensinya.)",
                "Konfirmasi", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
            st.Keys.Remove(m.Nama);
            st.Data.Mesin.Remove(m);
            st.SaveData();
            st.SaveSecrets();
            RefreshList(null);
            Log("Mesin dihapus dari daftar: " + m.Nama);
        }

        // ---------- Info ----------
        void OnInfo()
        {
            MesinItem m = Selected();
            if (m == null) return;
            object zk = Open(m);
            if (zk == null) return;
            try
            {
                Log("=== Info " + m.Nama + " (" + m.Ip + ") ===");
                Log(Dev.Info(zk));
            }
            catch (Exception e)
            {
                Log("Error: " + e.Message);
            }
            finally
            {
                Done(zk);
            }
        }

        // ---------- User ----------
        void OnCekUser()
        {
            MesinItem m = Selected();
            if (m == null) return;
            string uid = txtUid.Text.Trim();
            if (uid.Length == 0) { Msg("Isi ID user dulu."); return; }
            object zk = Open(m);
            if (zk == null) return;
            try
            {
                string name;
                int priv;
                bool en;
                if (Dev.GetUser(zk, uid, out name, out priv, out en))
                    Log("User " + uid + " di " + m.Nama + ": ADA (nama " + name + ", privilege " + priv + ", " + (en ? "aktif" : "nonaktif") + ")");
                else
                    Log("User " + uid + " di " + m.Nama + ": TIDAK ada");
            }
            catch (Exception e)
            {
                Log("Error: " + e.Message);
            }
            finally
            {
                Done(zk);
            }
        }

        void OnTambahUserUji()
        {
            MesinItem m = Selected();
            if (m == null) return;
            string uid = txtUid.Text.Trim();
            if (!uid.StartsWith("999", StringComparison.Ordinal))
            {
                Msg("Pada tahap ini hanya ID uji yang boleh ditambah lewat aplikasi (awalan 999, contoh 99901).");
                return;
            }
            string nama = txtNama.Text.Trim();
            if (nama.Length == 0) nama = "ZZ-UJI";
            if (MessageBox.Show("Tambah user " + uid + " (" + nama + ") ke mesin " + m.Nama + " (" + m.Ip + ")?",
                "Konfirmasi", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes) return;
            object zk = Open(m);
            if (zk == null) return;
            try
            {
                string n0;
                int p0;
                bool e0;
                if (Dev.GetUser(zk, uid, out n0, out p0, out e0))
                {
                    Log("User " + uid + " sudah ada (" + n0 + "), tidak diubah.");
                }
                else
                {
                    bool ok = Dev.CreateUser(zk, uid, nama);
                    Log("Tambah user " + uid + " di " + m.Nama + ": " + (ok ? "OK" : "GAGAL, kode " + Dev.Err(zk)));
                }
            }
            catch (Exception e)
            {
                Log("Error: " + e.Message);
            }
            finally
            {
                Done(zk);
            }
        }

        void OnDaftarUser()
        {
            MesinItem m = Selected();
            if (m == null) return;
            object zk = Open(m);
            if (zk == null) return;
            try
            {
                List<string[]> rows = Dev.ListUsers(zk, 5000);
                lvUser.Items.Clear();
                foreach (string[] r in rows)
                {
                    ListViewItem it = new ListViewItem(r[0]);
                    it.SubItems.Add(r[1]);
                    it.SubItems.Add(r[2]);
                    it.SubItems.Add(r[3]);
                    lvUser.Items.Add(it);
                }
                Log("Daftar user " + m.Nama + ": " + rows.Count + " baris (fungsi ini belum teruji; bandingkan dengan jumlah user di Info mesin).");
            }
            catch (Exception e)
            {
                Log("Error: " + e.Message);
            }
            finally
            {
                Done(zk);
            }
        }

        // ---------- Sidik jari ----------
        void OnBacaTemplate()
        {
            MesinItem m = Selected();
            if (m == null) return;
            string uid = txtUidFp.Text.Trim();
            if (uid.Length == 0) { Msg("Isi ID user dulu."); return; }
            object zk = Open(m);
            if (zk == null) return;
            try
            {
                Log("--- Baca template user " + uid + " di " + m.Nama + " (jari 0-9) ---");
                int n = Dev.ReadTemplates(zk, uid, m.Nama, st.CadanganDir, Log);
                if (n == 0) Log("HASIL: template BELUM ada di mesin saat dibaca");
                else Log("HASIL: " + n + " template ditemukan");
            }
            catch (Exception e)
            {
                Log("Error: " + e.Message);
            }
            finally
            {
                Done(zk);
            }
        }

        void OnPicu()
        {
            if (enrollZk != null)
            {
                Msg("Sesi daftar masih terbuka. Klik 'Selesai daftar & baca' dulu.");
                return;
            }
            MesinItem m = Selected();
            if (m == null) return;
            string uid = txtUidFp.Text.Trim();
            if (!uid.StartsWith("999", StringComparison.Ordinal))
            {
                Msg("Pada tahap ini picu daftar hanya untuk ID uji (awalan 999, contoh 99901).");
                return;
            }
            int jari = (int)numJari.Value;
            object zk = Open(m);
            if (zk == null) return;
            bool ok = false;
            try
            {
                string nm;
                int pv;
                bool en;
                if (!Dev.GetUser(zk, uid, out nm, out pv, out en))
                {
                    if (!Dev.CreateUser(zk, uid, "ZZ-UJI"))
                    {
                        Log("Gagal membuat user uji " + uid + " (kode " + Dev.Err(zk) + "). Batal.");
                        Done(zk);
                        return;
                    }
                    Log("User uji " + uid + " dibuat.");
                }
                ok = Dev.StartEnroll(zk, uid, jari);
                Log("StartEnrollEx(" + uid + ", jari " + jari + ") di " + m.Nama + ": " + ok + " (kode " + Dev.Err(zk) + ")");
            }
            catch (Exception e)
            {
                Log("Error: " + e.Message);
                ok = false;
            }
            if (ok)
            {
                enrollZk = zk;
                enrollMesin = m.Nama;
                enrollUid = uid;
                Cursor = Cursors.Default;
                Log("Minta rekan menempelkan jari di mesin SEKARANG. Setelah selesai (atau menu hilang), klik 'Selesai daftar & baca'. Aplikasi tidak membaca apa pun selama menunggu.");
            }
            else
            {
                Done(zk);
            }
        }

        void OnSelesai()
        {
            if (enrollZk == null)
            {
                Msg("Belum ada sesi daftar. Klik 'Picu daftar dari PC' dulu.");
                return;
            }
            object zk = enrollZk;
            try
            {
                Log("--- Baca template user " + enrollUid + " di " + enrollMesin + " setelah daftar ---");
                int n = Dev.ReadTemplates(zk, enrollUid, enrollMesin, st.CadanganDir, Log);
                if (n == 0) Log("HASIL: template BELUM ada di mesin saat dibaca");
                else Log("HASIL: " + n + " template ditemukan");
            }
            catch (Exception e)
            {
                Log("Error: " + e.Message);
            }
            finally
            {
                enrollZk = null;
                Done(zk);
            }
        }

        // ---------- Bantuan ----------
        void OnDiagnostik()
        {
            Cursor = Cursors.WaitCursor;
            Log("=== Diagnostik ===");
            Log("Proses 32-bit: " + (IntPtr.Size == 4 ? "Ya (benar)" : "TIDAK - aplikasi harus dikompilasi x86"));
            Type t = Type.GetTypeFromProgID("zkemkeeper.ZKEM");
            Log(t != null ? "Komponen zkemkeeper: terdaftar" : "Komponen zkemkeeper: BELUM terdaftar. Lihat panduan pemulihan, bagian komponen mesin.");
            try
            {
                string p = Path.Combine(st.DataDir, "tes_tulis.tmp");
                File.WriteAllText(p, "x");
                File.Delete(p);
                Log("Folder data: bisa ditulis (" + st.DataDir + ")");
            }
            catch (Exception e)
            {
                Log("Folder data: TIDAK bisa ditulis (" + e.Message + "). Pindahkan aplikasi ke folder biasa, bukan Program Files.");
            }
            if (st.Data.Mesin.Count == 0) Log("Belum ada mesin terdaftar.");
            foreach (MesinItem m in st.Data.Mesin)
            {
                bool ok = Dev.PortOpen(m.Ip, m.Port, 2000);
                Log(m.Nama + " " + m.Ip + ":" + m.Port + " -> " + (ok ? "port terbuka" : "TIDAK menjawab (cek kabel, VPN, atau IP)"));
            }
            Log("=== Selesai ===");
            Cursor = Cursors.Default;
        }

        void OnPanduan()
        {
            string a = Path.Combine(st.BaseDir, "docs");
            string b = Path.GetFullPath(Path.Combine(st.BaseDir, "..\\docs"));
            if (Directory.Exists(a)) BukaFolder(a);
            else if (Directory.Exists(b)) BukaFolder(b);
            else Msg("Folder panduan belum ada. Panduan ditambahkan setelah tahap ini teruji.");
        }
    }
}
