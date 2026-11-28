using System;
using System.Collections.Generic;
using System.Data.SQLite;
using System.Drawing;
using System.IO;
using System.Security.Cryptography;
using System.Text;
using System.Windows.Forms;
using HrisDeviceTool.Data;

namespace HrisDeviceTool
{
    public class OpsiTarik
    {
        public List<MesinItem> Mesin = new List<MesinItem>();
        public bool Semua = true;
        public DateTime Dari;
        public DateTime SampaiEksklusif;
    }

    // Dialog: pilih mesin dan cakupan tarikan (semua log atau rentang tanggal).
    public static class DialogTarikBanyak
    {
        public static OpsiTarik Tanya(IWin32Window pemilik, IEnumerable<MesinItem> mesin)
        {
            List<MesinItem> daftar = new List<MesinItem>(mesin);
            OpsiTarik hasil = null;
            using (Form f = new Form())
            {
                f.Text = "Tarik log banyak mesin";
                f.FormBorderStyle = FormBorderStyle.FixedDialog;
                f.StartPosition = FormStartPosition.CenterParent;
                f.MaximizeBox = false;
                f.MinimizeBox = false;
                f.ClientSize = new Size(440, 480);

                Label l1 = new Label();
                l1.Text = "Pilih mesin:";
                l1.AutoSize = true;
                l1.Location = new Point(12, 12);
                f.Controls.Add(l1);

                CheckedListBox lb = new CheckedListBox();
                lb.CheckOnClick = true;
                lb.Location = new Point(12, 34);
                lb.Size = new Size(416, 190);
                foreach (MesinItem m in daftar) { lb.Items.Add(m.Nama, true); }
                f.Controls.Add(lb);

                Button bAll = new Button();
                bAll.Text = "Pilih semua";
                bAll.Location = new Point(12, 230);
                bAll.Size = new Size(100, 26);
                bAll.Click += delegate { for (int i = 0; i < lb.Items.Count; i++) { lb.SetItemChecked(i, true); } };
                f.Controls.Add(bAll);

                Button bNone = new Button();
                bNone.Text = "Kosongkan";
                bNone.Location = new Point(120, 230);
                bNone.Size = new Size(100, 26);
                bNone.Click += delegate { for (int i = 0; i < lb.Items.Count; i++) { lb.SetItemChecked(i, false); } };
                f.Controls.Add(bNone);

                Label l2 = new Label();
                l2.Text = "Cakupan tarikan:";
                l2.AutoSize = true;
                l2.Location = new Point(12, 272);
                f.Controls.Add(l2);

                RadioButton rbSemua = new RadioButton();
                rbSemua.Text = "Semua log di mesin (bawaan)";
                rbSemua.AutoSize = true;
                rbSemua.Checked = true;
                rbSemua.Location = new Point(24, 294);
                f.Controls.Add(rbSemua);

                RadioButton rbRentang = new RadioButton();
                rbRentang.Text = "Rentang tanggal:";
                rbRentang.AutoSize = true;
                rbRentang.Location = new Point(24, 320);
                f.Controls.Add(rbRentang);

                DateTime h = DateTime.Today;
                DateTimePicker dtDari = new DateTimePicker();
                dtDari.Format = DateTimePickerFormat.Custom;
                dtDari.CustomFormat = "dd-MM-yyyy";
                dtDari.Width = 110;
                dtDari.Location = new Point(48, 346);
                dtDari.Value = new DateTime(h.Year, h.Month, 1);
                dtDari.Enabled = false;
                f.Controls.Add(dtDari);

                Label l3 = new Label();
                l3.Text = "s/d";
                l3.AutoSize = true;
                l3.Location = new Point(168, 350);
                f.Controls.Add(l3);

                DateTimePicker dtSampai = new DateTimePicker();
                dtSampai.Format = DateTimePickerFormat.Custom;
                dtSampai.CustomFormat = "dd-MM-yyyy";
                dtSampai.Width = 110;
                dtSampai.Location = new Point(196, 346);
                dtSampai.Value = h;
                dtSampai.Enabled = false;
                f.Controls.Add(dtSampai);

                rbRentang.CheckedChanged += delegate { dtDari.Enabled = rbRentang.Checked; dtSampai.Enabled = rbRentang.Checked; };

                Label info = new Label();
                info.Text = "Mesin hanya dibaca, tidak ada yang dihapus. Baris yang sudah ada di database dilewati. Penyaringan tanggal dilakukan di aplikasi, jadi mesin tetap dibaca seluruhnya (waktu baca sama dengan Semua log).";
                info.Location = new Point(12, 384);
                info.Size = new Size(416, 52);
                f.Controls.Add(info);

                Button ok = new Button();
                ok.Text = "Mulai tarik";
                ok.Location = new Point(236, 444);
                ok.Size = new Size(100, 28);
                f.Controls.Add(ok);

                Button batal = new Button();
                batal.Text = "Batal";
                batal.Location = new Point(344, 444);
                batal.Size = new Size(84, 28);
                batal.DialogResult = DialogResult.Cancel;
                f.Controls.Add(batal);
                f.CancelButton = batal;

                ok.Click += delegate
                {
                    if (lb.CheckedIndices.Count == 0) { MessageBox.Show("Pilih minimal satu mesin.", "Tarik log banyak mesin"); return; }
                    if (rbRentang.Checked && dtSampai.Value.Date < dtDari.Value.Date) { MessageBox.Show("Tanggal Sampai harus sama dengan atau setelah Dari.", "Tarik log banyak mesin"); return; }
                    OpsiTarik o = new OpsiTarik();
                    foreach (int idx in lb.CheckedIndices) { o.Mesin.Add(daftar[idx]); }
                    o.Semua = !rbRentang.Checked;
                    o.Dari = dtDari.Value.Date;
                    o.SampaiEksklusif = dtSampai.Value.Date.AddDays(1);
                    hasil = o;
                    f.DialogResult = DialogResult.OK;
                };

                if (f.ShowDialog(pemilik) != DialogResult.OK) { return null; }
            }
            return hasil;
        }
    }

    // Menarik log dari banyak mesin satu per satu: CSV + manifest + database lokal. Mesin hanya dibaca.
    public static class TarikBanyak
    {
        static string Durasi(TimeSpan w)
        {
            if (w.TotalMinutes >= 1) { return (int)w.TotalMinutes + " mnt " + w.Seconds + " dtk"; }
            return Math.Round(w.TotalSeconds, 1).ToString(System.Globalization.CultureInfo.InvariantCulture) + " dtk";
        }

        static string Aman(string s)
        {
            foreach (char ch in Path.GetInvalidFileNameChars()) { s = s.Replace(ch, '_'); }
            return s;
        }

        static string HashFile(string berkas)
        {
            using (SHA256 sha = SHA256.Create())
            using (FileStream fs = File.OpenRead(berkas))
            {
                byte[] h = sha.ComputeHash(fs);
                StringBuilder sb = new StringBuilder();
                foreach (byte b in h) { sb.Append(b.ToString("x2")); }
                return sb.ToString();
            }
        }

        static void TulisCsv(string dataDir, string mesin, List<BarisLog> rows, int diMesin)
        {
            string dir = Path.Combine(dataDir, "tarikan");
            Directory.CreateDirectory(dir);
            string baseName = "tarikan_" + Aman(mesin) + "_" + DateTime.Now.ToString("yyyyMMdd_HHmmss");
            string csv = Path.Combine(dir, baseName + ".csv");
            StringBuilder sb = new StringBuilder();
            sb.Append("device_user_id;punch_time;verify_mode;punch_status_raw;workcode\r\n");
            foreach (BarisLog x in rows)
            {
                sb.Append(x.Id).Append(';')
                  .Append(x.Waktu.ToString("yyyy-MM-dd HH:mm:ss")).Append(';')
                  .Append(x.Verifikasi).Append(';')
                  .Append(x.Status).Append(';')
                  .Append(x.WorkCode).Append("\r\n");
            }
            File.WriteAllText(csv, sb.ToString(), new UTF8Encoding(false));
            string hash = HashFile(csv);
            StringBuilder mf = new StringBuilder();
            mf.Append("format=hdt-log-1\r\n");
            mf.Append("otomatis=ya\r\n");
            mf.Append("mesin=" + mesin + "\r\n");
            mf.Append("diekspor=" + DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss") + "\r\n");
            mf.Append("baris=" + rows.Count + "\r\n");
            mf.Append("rentang_awal=" + rows[0].Waktu.ToString("yyyy-MM-dd HH:mm:ss") + "\r\n");
            mf.Append("rentang_akhir=" + rows[rows.Count - 1].Waktu.ToString("yyyy-MM-dd HH:mm:ss") + "\r\n");
            mf.Append("jumlah_di_mesin=" + diMesin + "\r\n");
            mf.Append("sha256=" + hash + "\r\n");
            File.WriteAllText(Path.Combine(dir, baseName + ".hdtman"), mf.ToString(), new UTF8Encoding(false));
            AuditLog.Tulis("Salinan otomatis", "mesin " + mesin + ", baris " + rows.Count + ", berkas " + baseName + ".csv, sha256 " + hash);
        }

        // buka: koneksi ke mesin (null bila gagal). tutup: putuskan koneksi.
        public static string Jalankan(IWin32Window pemilik, OpsiTarik o, string dataDir, Func<MesinItem, object> buka, Action<object> tutup)
        {
            StringBuilder sb = new StringBuilder();
            int berhasil = 0, gagal = 0, totalBaru = 0, totalTerbaca = 0;
            System.Diagnostics.Stopwatch swTotal = System.Diagnostics.Stopwatch.StartNew();
            bool batal = false;

            Form pf = new Form();
            pf.Text = "Tarik log banyak mesin";
            pf.FormBorderStyle = FormBorderStyle.FixedDialog;
            pf.StartPosition = FormStartPosition.CenterParent;
            pf.ControlBox = false;
            pf.ClientSize = new Size(520, 110);
            Label lbl = new Label();
            lbl.Location = new Point(12, 12);
            lbl.Size = new Size(496, 44);
            lbl.UseMnemonic = false;
            pf.Controls.Add(lbl);
            Button bb = new Button();
            bb.Text = "Batal";
            bb.Location = new Point(12, 68);
            bb.Size = new Size(90, 28);
            bb.Click += delegate { batal = true; bb.Enabled = false; lbl.Text = "Membatalkan setelah langkah ini selesai..."; };
            pf.Controls.Add(bb);

            try
            {
                pf.Show(pemilik);
                Application.DoEvents();
                DateTime? dari = null;
                DateTime? sampai = null;
                if (!o.Semua) { dari = o.Dari; sampai = o.SampaiEksklusif; }

                using (SQLiteConnection c = HdtDatabase.Buka(HdtDatabase.BerkasDefault()))
                {
                    for (int i = 0; i < o.Mesin.Count; i++)
                    {
                        if (batal) { sb.AppendLine("Dibatalkan. Mesin yang belum diproses dilewati."); break; }
                        MesinItem m = o.Mesin[i];
                        string awal = "Mesin " + (i + 1) + " dari " + o.Mesin.Count + ": " + m.Nama;
                        lbl.Text = awal + " - menyambung...";
                        Application.DoEvents();
                        System.Diagnostics.Stopwatch sw = System.Diagnostics.Stopwatch.StartNew();
                        object zk = buka(m);
                        if (zk == null)
                        {
                            gagal++;
                            sb.AppendLine(m.Nama + " : GAGAL tersambung");
                            try { LogDb.CatatGagal(c, m.Nama, "tarik", "Tidak bisa terhubung"); } catch { }
                            continue;
                        }
                        try
                        {
                            int diMesin = BacaLog.Hitung(zk);
                            int tidakValid;
                            List<LogRow> rows = BacaLog.Baca(zk, delegate { return batal; }, delegate (string s) { lbl.Text = awal + " - " + s; Application.DoEvents(); }, out tidakValid);
                            if (rows == null) { sb.AppendLine(m.Nama + " : dibatalkan saat membaca"); break; }

                            List<BarisLog> semua = new List<BarisLog>();
                            foreach (LogRow x in rows)
                            {
                                BarisLog b = new BarisLog();
                                b.Id = x.Id;
                                b.Waktu = x.Waktu;
                                b.Verifikasi = x.Verify;
                                b.Status = x.InOut;
                                b.WorkCode = x.WorkCode;
                                semua.Add(b);
                            }
                            semua.Sort(delegate (BarisLog a, BarisLog b2)
                            {
                                int cmp = a.Waktu.CompareTo(b2.Waktu);
                                return cmp != 0 ? cmp : string.CompareOrdinal(a.Id, b2.Id);
                            });

                            if (semua.Count == 0 && diMesin > 0)
                            {
                                gagal++;
                                string cat = "Terbaca 0 padahal mesin berisi " + diMesin;
                                sb.AppendLine(m.Nama + " : GAGAL (" + cat + ")");
                                try { LogDb.CatatGagal(c, m.Nama, "tarik", cat); } catch { }
                                continue;
                            }

                            List<BarisLog> pakai = SaringLog.Tanggal(semua, dari, sampai);
                            lbl.Text = awal + " - menyimpan...";
                            Application.DoEvents();
                            string infoCsv = "";
                            if (pakai.Count > 0)
                            {
                                try { TulisCsv(dataDir, m.Nama, pakai, diMesin); }
                                catch (Exception ex) { infoCsv = " | CSV GAGAL: " + ex.Message; }
                            }
                            HasilSimpan h = LogDb.Simpan(c, m.Nama, pakai, "tarik", diMesin, o.Semua ? "" : "rentang " + o.Dari.ToString("yyyy-MM-dd") + " s/d " + o.SampaiEksklusif.AddDays(-1).ToString("yyyy-MM-dd"));
                            string infoMesin = "";
                            try { InfoMesin.Simpan(c, m.Nama, m.Ip, Dev.InfoRows(zk)); }
                            catch (Exception exI) { infoMesin = " | info mesin tidak tersimpan: " + exI.Message; }

                            berhasil++;
                            totalBaru += h.Baru;
                            totalTerbaca += semua.Count;
                            sb.AppendLine(m.Nama + " : terbaca " + semua.Count + (o.Semua ? "" : ", masuk rentang " + pakai.Count)
                                + ", baru " + h.Baru + ", sudah ada " + h.Dilewati + (tidakValid > 0 ? ", tidak valid " + tidakValid : "")
                                + (diMesin >= 0 && diMesin != semua.Count + tidakValid ? " | PERHATIAN: mesin melaporkan " + diMesin : "")
                                + " | durasi " + Durasi(sw.Elapsed) + infoCsv + infoMesin);
                            AuditLog.Tulis("Tarik banyak mesin", "mesin " + m.Nama + ", terbaca " + semua.Count + ", disimpan " + pakai.Count + ", baru " + h.Baru);
                        }
                        catch (Exception ex)
                        {
                            gagal++;
                            sb.AppendLine(m.Nama + " : GAGAL (" + ex.Message + ")");
                            try { LogDb.CatatGagal(c, m.Nama, "tarik", ex.Message); } catch { }
                        }
                        finally
                        {
                            tutup(zk);
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                sb.AppendLine("GAGAL: " + ex.Message);
            }
            finally
            {
                pf.Close();
                pf.Dispose();
            }
            AuditLog.Tulis("Tarik banyak mesin", "selesai, berhasil " + berhasil + ", gagal " + gagal + ", baru " + totalBaru);
            string kepala = "Tarik banyak mesin selesai.\r\nBerhasil: " + berhasil + ", gagal: " + gagal + ", baris baru di database: " + totalBaru + ". Tidak ada yang diubah di mesin.\r\nTotal waktu: " + Durasi(swTotal.Elapsed) + ".\r\n\r\n";
            return kepala + sb.ToString();
        }
    }
}