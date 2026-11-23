using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Windows.Forms;

namespace HrisDeviceTool
{
    public class UserData
    {
        public string Id = "";
        public string Nama = "";
        public int Priv = 0;
        public bool Aktif = true;
        public SortedDictionary<int, string> Jari = new SortedDictionary<int, string>();
    }

    public class BarisBanding
    {
        public string Id = "", NamaA = "", NamaB = "", PrivA = "", PrivB = "", JariA = "", JariB = "", Hasil = "", Kategori = "sama";
    }

    public static class BacaSemua
    {
        public static string Hash(string s)
        {
            using (SHA256 sha = SHA256.Create())
            {
                byte[] b = sha.ComputeHash(Encoding.UTF8.GetBytes(s));
                StringBuilder sb = new StringBuilder();
                foreach (byte x in b) sb.Append(x.ToString("x2"));
                return sb.ToString();
            }
        }

        // Hanya membaca. Mengembalikan null bila dibatalkan.
        public static Dictionary<string, UserData> Baca(object zkObj, Func<bool> batal, Action<string> progres)
        {
            dynamic zk = zkObj;
            Dictionary<string, UserData> hasil = new Dictionary<string, UserData>();
            List<UserData> daftar = new List<UserData>();
            bool okAll = zk.ReadAllUserID(1);
            if (!okAll) return hasil;
            string id = "", name = "", pwd = "";
            int priv = 0;
            bool en = false;
            while (daftar.Count < 20000)
            {
                bool ok = zk.SSR_GetAllUserInfo(1, ref id, ref name, ref pwd, ref priv, ref en);
                if (!ok) break;
                UserData u = new UserData();
                u.Id = id.Trim('\0').Trim();
                u.Nama = name.Trim('\0').Trim();
                u.Priv = priv;
                u.Aktif = en;
                if (u.Id.Length == 0 || hasil.ContainsKey(u.Id)) continue;
                hasil[u.Id] = u;
                daftar.Add(u);
            }
            progres("daftar user terbaca: " + daftar.Count);
            try { zk.ReadAllTemplate(1); } catch { }
            int n = 0;
            foreach (UserData u in daftar)
            {
                if (batal()) return null;
                n++;
                progres(n + " dari " + daftar.Count + " (ID " + u.Id + ")");
                for (int f = 0; f <= 9; f++)
                {
                    int flag = 0, len = 0;
                    string tmp = "";
                    bool ok = false;
                    try { ok = zk.GetUserTmpExStr(1, u.Id, f, ref flag, ref tmp, ref len); }
                    catch { ok = false; }
                    if (ok && !string.IsNullOrEmpty(tmp))
                        u.Jari[f] = flag + "|" + len + "|" + Hash(tmp);
                }
            }
            return hasil;
        }
    }

    public class BandingkanForm : Form
    {
        Store st;
        Func<MesinItem, object> opener;
        ComboBox cmbA, cmbB;
        Button btnGo, btnBatal, btnEkspor;
        CheckBox chkBeda;
        Label lblStatus, lblRingkas;
        ListView lv;
        List<BarisBanding> rows = new List<BarisBanding>();
        bool batal = false;
        bool jalan = false;
        string namaA = "A", namaB = "B";
        static readonly string[] Kol = new string[] { "ID", "Nama A", "Nama B", "Priv A", "Priv B", "Jari A", "Jari B", "Hasil" };

        public BandingkanForm(Store store, Func<MesinItem, object> open)
        {
            st = store;
            opener = open;
            Text = "Bandingkan dua mesin (hanya membaca)";
            ClientSize = new Size(1100, 620);
            StartPosition = FormStartPosition.CenterParent;

            Controls.Add(MakeLabel("Mesin A", 10, 14));
            cmbA = new ComboBox();
            cmbA.DropDownStyle = ComboBoxStyle.DropDownList;
            cmbA.Location = new Point(70, 10);
            cmbA.Width = 200;
            Controls.Add(cmbA);
            Controls.Add(MakeLabel("Mesin B", 290, 14));
            cmbB = new ComboBox();
            cmbB.DropDownStyle = ComboBoxStyle.DropDownList;
            cmbB.Location = new Point(350, 10);
            cmbB.Width = 200;
            Controls.Add(cmbB);
            foreach (MesinItem m in st.Data.Mesin)
            {
                cmbA.Items.Add(m);
                cmbB.Items.Add(m);
            }
            if (cmbA.Items.Count > 0) cmbA.SelectedIndex = 0;
            if (cmbB.Items.Count > 1) cmbB.SelectedIndex = 1;

            btnGo = new Button();
            btnGo.Text = "Bandingkan";
            btnGo.Location = new Point(570, 8);
            btnGo.Size = new Size(110, 28);
            btnGo.Click += delegate { OnGo(); };
            Controls.Add(btnGo);
            btnBatal = new Button();
            btnBatal.Text = "Batal";
            btnBatal.Location = new Point(690, 8);
            btnBatal.Size = new Size(80, 28);
            btnBatal.Enabled = false;
            btnBatal.Click += delegate { batal = true; };
            Controls.Add(btnBatal);
            btnEkspor = new Button();
            btnEkspor.Text = "Ekspor CSV";
            btnEkspor.Location = new Point(780, 8);
            btnEkspor.Size = new Size(100, 28);
            btnEkspor.Click += delegate { OnEkspor(); };
            Controls.Add(btnEkspor);
            chkBeda = new CheckBox();
            chkBeda.Text = "Hanya yang bermasalah";
            chkBeda.Location = new Point(890, 12);
            chkBeda.AutoSize = true;
            chkBeda.CheckedChanged += delegate { Tampil(); };
            Controls.Add(chkBeda);

            lblStatus = MakeLabel("Pilih dua mesin lalu klik Bandingkan. Hanya membaca, tidak mengubah apa pun.", 10, 46);
            Controls.Add(lblStatus);
            lblRingkas = MakeLabel("", 10, 66);
            Controls.Add(lblRingkas);

            lv = new ListView();
            lv.View = View.Details;
            lv.FullRowSelect = true;
            lv.GridLines = true;
            lv.Location = new Point(10, 90);
            lv.Size = new Size(1080, 520);
            lv.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right;
            int[] w = new int[] { 80, 170, 170, 55, 55, 110, 110, 310 };
            for (int i = 0; i < Kol.Length; i++) lv.Columns.Add(Kol[i], w[i]);
            Controls.Add(lv);
        }

        Label MakeLabel(string t, int x, int y)
        {
            Label l = new Label();
            l.Text = t;
            l.Location = new Point(x, y);
            l.AutoSize = true;
            return l;
        }

        void Status(string s)
        {
            lblStatus.Text = s;
            Application.DoEvents();
        }

        Dictionary<string, UserData> BacaMesin(MesinItem m, string tag)
        {
            object zk = opener(m);
            if (zk == null) return null;
            try
            {
                return BacaSemua.Baca(zk, delegate { return batal; },
                    delegate (string s) { Status("Mesin " + tag + " (" + m.Nama + "): " + s); });
            }
            catch (Exception e)
            {
                MessageBox.Show(e.Message, "Gagal membaca " + m.Nama, MessageBoxButtons.OK, MessageBoxIcon.Warning);
                return null;
            }
            finally
            {
                Dev.Disconnect(zk);
                Cursor = Cursors.Default;
            }
        }

        void OnGo()
        {
            if (jalan) return;
            MesinItem a = cmbA.SelectedItem as MesinItem;
            MesinItem b = cmbB.SelectedItem as MesinItem;
            if (a == null || b == null) { MessageBox.Show("Pilih mesin A dan B."); return; }
            if (object.ReferenceEquals(a, b)) { MessageBox.Show("Mesin A dan B harus berbeda."); return; }
            jalan = true;
            batal = false;
            btnGo.Enabled = false;
            btnBatal.Enabled = true;
            try
            {
                Dictionary<string, UserData> da = BacaMesin(a, "A");
                if (da == null) { Status("Dibatalkan atau gagal membaca mesin A."); return; }
                Dictionary<string, UserData> db = BacaMesin(b, "B");
                if (db == null) { Status("Dibatalkan atau gagal membaca mesin B."); return; }
                namaA = a.Nama;
                namaB = b.Nama;
                rows = Banding(da, db);
                int sama = 0, mirip = 0, hanya = 0, idbeda = 0, konflik = 0, beda = 0;
                foreach (BarisBanding r in rows)
                {
                    if (r.Kategori == "sama") sama++;
                    else if (r.Kategori == "mirip") mirip++;
                    else if (r.Kategori == "idbeda") idbeda++;
                    else if (r.Kategori == "hanya") hanya++;
                    else if (r.Kategori == "konflik") konflik++;
                    else beda++;
                }
                lblRingkas.Text = namaA + ": " + da.Count + " user | " + namaB + ": " + db.Count + " user | sama: " + sama +
                    " | nama mirip: " + mirip + " | hanya di satu mesin: " + hanya + " | nama sama ID beda: " + idbeda + " | KONFLIK nama: " + konflik + " | beda jari/privilege: " + beda;
                Status("Selesai " + DateTime.Now.ToString("HH:mm:ss") + ". Hanya membaca, tidak ada yang diubah.");
                Tampil();
            }
            finally
            {
                jalan = false;
                btnGo.Enabled = true;
                btnBatal.Enabled = false;
            }
        }

        void Tampil()
        {
            lv.BeginUpdate();
            lv.Items.Clear();
            foreach (BarisBanding r in rows)
            {
                if (chkBeda.Checked && (r.Kategori == "sama" || r.Kategori == "mirip")) continue;
                ListViewItem it = new ListViewItem(r.Id);
                it.SubItems.Add(r.NamaA);
                it.SubItems.Add(r.NamaB);
                it.SubItems.Add(r.PrivA);
                it.SubItems.Add(r.PrivB);
                it.SubItems.Add(r.JariA);
                it.SubItems.Add(r.JariB);
                it.SubItems.Add(r.Hasil);
                if (r.Kategori == "konflik") it.BackColor = Color.MistyRose;
                else if (r.Kategori == "hanya") it.BackColor = Color.LightYellow;
                else if (r.Kategori == "beda") it.BackColor = Color.AliceBlue;
                else if (r.Kategori == "idbeda") it.BackColor = Color.MistyRose;
                else if (r.Kategori == "mirip") it.BackColor = Color.Honeydew;
                lv.Items.Add(it);
            }
            lv.EndUpdate();
        }

        void OnEkspor()
        {
            if (rows.Count == 0) { MessageBox.Show("Klik Bandingkan dulu."); return; }
            string path = Path.Combine(st.DataDir, "banding_" + namaA + "_" + namaB + "_" + DateTime.Now.ToString("yyyyMMdd_HHmmss") + ".csv");
            foreach (char c in Path.GetInvalidFileNameChars()) path = path.Replace(c.ToString(), c == '\\' || c == ':' ? c.ToString() : "_");
            StringBuilder sb = new StringBuilder();
            sb.AppendLine(string.Join(";", Kol));
            foreach (BarisBanding r in rows)
            {
                string[] f = new string[] { r.Id, r.NamaA, r.NamaB, r.PrivA, r.PrivB, r.JariA, r.JariB, r.Hasil };
                for (int i = 0; i < f.Length; i++) f[i] = f[i].Replace(";", ",");
                sb.AppendLine(string.Join(";", f));
            }
            File.WriteAllText(path, sb.ToString(), new UTF8Encoding(true));
            MessageBox.Show("Diekspor ke:\r\n" + path, "Ekspor");
        }

        // ---------- logika perbandingan ----------
        static string Norm(string s)
        {
            string[] p = s.Trim().ToLowerInvariant().Split(new char[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
            return string.Join(" ", p);
        }

        static string JoinInts(List<int> l)
        {
            StringBuilder sb = new StringBuilder();
            foreach (int i in l)
            {
                if (sb.Length > 0) sb.Append(",");
                sb.Append(i);
            }
            return sb.ToString();
        }

        static string JariText(UserData u)
        {
            if (u == null || u.Jari.Count == 0) return "-";
            List<int> l = new List<int>();
            foreach (int k in u.Jari.Keys) l.Add(k);
            return JoinInts(l);
        }

        static Dictionary<string, List<string>> IndeksNama(Dictionary<string, UserData> d)
        {
            Dictionary<string, List<string>> r = new Dictionary<string, List<string>>();
            foreach (UserData u in d.Values)
            {
                string n = Norm(u.Nama);
                if (n.Length == 0) continue;
                List<string> l;
                if (!r.TryGetValue(n, out l)) { l = new List<string>(); r[n] = l; }
                l.Add(u.Id);
            }
            return r;
        }

                static string NormLonggar(string s)
        {
            StringBuilder sb = new StringBuilder();
            int depth = 0;
            foreach (char c in s.ToLowerInvariant())
            {
                if (c == '(' || c == '[') { depth++; continue; }
                if (c == ')' || c == ']') { if (depth > 0) depth--; continue; }
                if (depth > 0) continue;
                if (char.IsLetterOrDigit(c)) sb.Append(c); else sb.Append(' ');
            }
            string[] parts = sb.ToString().Split(new char[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
            return string.Join(" ", parts);
        }

        static int Rank(string k)
        {
            if (k == "konflik") return 3;
            if (k == "beda") return 2;
            if (k == "mirip") return 1;
            return 0;
        }

        static string Naik(string cur, string kandidat)
        {
            return Rank(kandidat) > Rank(cur) ? kandidat : cur;
        }

        static Dictionary<string, List<string>> IndeksLonggar(Dictionary<string, UserData> d)
        {
            Dictionary<string, List<string>> r = new Dictionary<string, List<string>>();
            foreach (UserData u in d.Values)
            {
                string n = NormLonggar(u.Nama);
                if (n.Length == 0) continue;
                List<string> l;
                if (!r.TryGetValue(n, out l)) { l = new List<string>(); r[n] = l; }
                l.Add(u.Id);
            }
            return r;
        }

        static List<BarisBanding> Banding(Dictionary<string, UserData> a, Dictionary<string, UserData> b)
        {
            Dictionary<string, List<string>> idxA = IndeksLonggar(a);
            Dictionary<string, List<string>> idxB = IndeksLonggar(b);
            List<string> ids = new List<string>();
            foreach (string k in a.Keys) ids.Add(k);
            foreach (string k in b.Keys) if (!a.ContainsKey(k)) ids.Add(k);
            ids.Sort(delegate (string x, string y)
            {
                long nx, ny;
                if (long.TryParse(x, out nx) && long.TryParse(y, out ny)) return nx.CompareTo(ny);
                return string.Compare(x, y, StringComparison.OrdinalIgnoreCase);
            });

            List<BarisBanding> hasil = new List<BarisBanding>();
            foreach (string id in ids)
            {
                UserData ua, ub;
                a.TryGetValue(id, out ua);
                b.TryGetValue(id, out ub);
                BarisBanding r = new BarisBanding();
                r.Id = id;
                r.NamaA = ua != null ? ua.Nama : "";
                r.NamaB = ub != null ? ub.Nama : "";
                r.PrivA = ua != null ? ua.Priv.ToString() : "";
                r.PrivB = ub != null ? ub.Priv.ToString() : "";
                r.JariA = ua != null ? JariText(ua) : "";
                r.JariB = ub != null ? JariText(ub) : "";

                if (ua == null || ub == null)
                {
                    r.Kategori = "hanya";
                    UserData ada = ua != null ? ua : ub;
                    r.Hasil = ua != null ? "Hanya di A" : "Hanya di B";
                    Dictionary<string, List<string>> lain = ua != null ? idxB : idxA;
                    List<string> sama;
                    if (lain.TryGetValue(NormLonggar(ada.Nama), out sama))
                    {
                        r.Hasil += ". Nama sama atau mirip di mesin lain dengan ID " + string.Join(",", sama.ToArray()) + " (kemungkinan salah daftar)";
                        r.Kategori = "idbeda";
                    }
                    hasil.Add(r);
                    continue;
                }

                List<string> msg = new List<string>();
                if (Norm(ua.Nama) != Norm(ub.Nama))
                {
                    string la = NormLonggar(ua.Nama);
                    if (la.Length > 0 && la == NormLonggar(ub.Nama))
                    {
                        msg.Add("nama mirip (beda tulisan)");
                        r.Kategori = Naik(r.Kategori, "mirip");
                    }
                    else
                    {
                        msg.Add("KONFLIK: ID sama, nama beda");
                        r.Kategori = Naik(r.Kategori, "konflik");
                    }
                }
                if (ua.Priv != ub.Priv)
                {
                    msg.Add("privilege beda");
                    r.Kategori = Naik(r.Kategori, "beda");
                }
                int identik = 0;
                List<int> diff = new List<int>(), onlyA = new List<int>(), onlyB = new List<int>();
                foreach (KeyValuePair<int, string> kv in ua.Jari)
                {
                    string v;
                    if (ub.Jari.TryGetValue(kv.Key, out v))
                    {
                        if (v == kv.Value) identik++;
                        else diff.Add(kv.Key);
                    }
                    else onlyA.Add(kv.Key);
                }
                foreach (int k in ub.Jari.Keys) if (!ua.Jari.ContainsKey(k)) onlyB.Add(k);
                if (diff.Count > 0) msg.Add("isi jari beda (bukan salinan): " + JoinInts(diff));
                if (onlyA.Count > 0) msg.Add("jari hanya di A: " + JoinInts(onlyA));
                if (onlyB.Count > 0) msg.Add("jari hanya di B: " + JoinInts(onlyB));
                if (diff.Count > 0 || onlyA.Count > 0 || onlyB.Count > 0) r.Kategori = Naik(r.Kategori, "beda");
                if (identik > 0) msg.Add("jari identik (salinan): " + identik);
                if (ua.Jari.Count == 0 && ub.Jari.Count == 0) msg.Add("tanpa jari di kedua mesin");
                r.Hasil = msg.Count == 0 ? "Sama" : string.Join("; ", msg.ToArray());
                hasil.Add(r);
            }
            return hasil;
        }
    }
}
