using System;
using System.Collections.Generic;
using System.Data.SQLite;
using System.IO;
using System.Text;
using HrisDeviceTool.Data;

namespace UjiImpor
{
    internal static class Program
    {
        private static int gagal = 0;

        private static void Cek(string nama, bool ok, string info)
        {
            if (!ok) { gagal++; }
            Console.WriteLine("{0}  {1}{2}", ok ? "OK   " : "GAGAL", nama,
                string.IsNullOrEmpty(info) ? "" : "  |  " + info);
        }

        private static object Skalar(SQLiteConnection c, string sql)
        {
            using (SQLiteCommand cmd = new SQLiteCommand(sql, c)) { return cmd.ExecuteScalar(); }
        }

        private static string Nilai(SQLiteConnection c, string kolom, string id)
        {
            object o = Skalar(c, "select " + kolom + " from induk_aplikasi_lama where id_akun='" + id + "'");
            return o == null || o is DBNull ? null : Convert.ToString(o);
        }

        private static Dictionary<string, string> Cari(HasilAnalisis h, string id)
        {
            foreach (Dictionary<string, string> b in h.Baris)
            {
                if (b["id_akun"] == id) { return b; }
            }
            return null;
        }

        private static int Main(string[] args)
        {
            Console.WriteLine("Uji ImporLama (src\\ImporLama.cs)");
            string akar = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "data_uji_impor");
            if (Directory.Exists(akar)) { Directory.Delete(akar, true); }
            Directory.CreateDirectory(akar);
            try { return Uji(akar); }
            catch (Exception ex)
            {
                Console.WriteLine("GAGAL  galat tidak tertangani: " + ex.GetType().Name + ": " + ex.Message);
                return 2;
            }
        }

        private static int Uji(string akar)
        {
            string nl = "\r\n";
            string a = Path.Combine(akar, "uji_A.csv");
            string teksA =
                "No. Akun;No. Induk;Nama;Kelamin;WargaNegara;Gelar;Tgl Lahir;Nomor Kartu;Telp. Kantor;No. Ponsel;Alamat Rumah;Departemen;Mulai Bekerja;Batasan;Kolom Aneh" + nl +
                "99901;B-UJI-0001;ANDI;L;WNI;OPERATOR;05/03/1990;111;021-1;0811;\"Jl. Uji; No 1\";Sizing;01/02/2020;Pengguna;x1" + nl +
                "99902;B-UJI-0002;BUDI;L;WNI;OPERATOR;1991-04-06;222;;0812;\"Jl. Uji 2" + nl + "lantai 2\";Finishing;15/08/2019;Administrator;x2" + nl +
                "99903;B-UJI-0003;CICI;P;WNI;OPERATOR;31/31/2000;;;;;Kiri;;Pengguna;" + nl +
                ";B-UJI-0004;TANPA ID;;;;;;;;;;;;" + nl +
                "99901;B-UJI-0001;ANDI REVISI;L;WNI;OPERATOR;05/03/1990;111;021-1;0811;Jl;Sizing;01/02/2020;Pengguna;x1b" + nl;
            File.WriteAllText(a, teksA, new UTF8Encoding(true));

            HasilAnalisis h = ImporLama.Analisis(a, null);
            Cek("U1 berkas A terbaca: UTF-8, pemisah ;, 5 baris, 3 unik, 1 tanpa id, 1 ganda, 1 tanggal tak terbaca",
                h.Sandi == "UTF-8" && h.Pemisah == ";" && h.TotalBaris == 5 && h.Baris.Count == 3
                && h.TanpaIdAkun == 1 && h.GandaDalamBerkas == 1 && h.TanggalTakTerbaca == 1,
                h.Sandi + " " + h.Pemisah + " total=" + h.TotalBaris + " unik=" + h.Baris.Count
                + " tanpaId=" + h.TanpaIdAkun + " ganda=" + h.GandaDalamBerkas + " tglBuruk=" + h.TanggalTakTerbaca);

            int dikenal = 0, tidak = 0;
            foreach (string p in h.Peta) { if (p == null) { tidak++; } else { dikenal++; } }
            Cek("U2 pemetaan: 14 judul dikenal, 1 tidak dikenal", dikenal == 14 && tidak == 1, dikenal + " dikenal, " + tidak + " tidak");

            Dictionary<string, string> b2 = Cari(h, "99902");
            Dictionary<string, string> b1 = Cari(h, "99901");
            Cek("U3 nilai: tanggal ISO, alamat bertanda kutip dan baris baru utuh, batasan, baris ganda memakai yang terakhir",
                b2 != null && b2["tgl_lahir"] == "1991-04-06" && b2["mulai_bekerja"] == "2019-08-15"
                && b2["alamat"].Contains("lantai 2") && b2["batasan"] == "Administrator"
                && b1 != null && b1["nama"] == "ANDI REVISI" && b1["tgl_lahir"] == "1990-03-05",
                "");

            string db = Path.Combine(Path.Combine(akar, "db"), "hdt.sqlite");
            using (SQLiteConnection c = HdtDatabase.Buka(db))
            {
                HasilTulis w = ImporLama.Tulis(c, h);
                long n = Convert.ToInt64(Skalar(c, "select count(*) from induk_aplikasi_lama"));
                Cek("U4 tulis pertama: 3 baru, 0 diperbarui, 3 baris di tabel", w.Baru == 3 && w.Diperbarui == 0 && n == 3,
                    "baru=" + w.Baru + " diperbarui=" + w.Diperbarui + " baris=" + n);

                HasilTulis w2 = ImporLama.Tulis(c, h);
                long n2 = Convert.ToInt64(Skalar(c, "select count(*) from induk_aplikasi_lama"));
                Cek("U5 tulis ulang: 0 baru, 3 diperbarui, tetap 3 baris", w2.Baru == 0 && w2.Diperbarui == 3 && n2 == 3,
                    "baru=" + w2.Baru + " diperbarui=" + w2.Diperbarui + " baris=" + n2);

                string lain = Nilai(c, "data_lain", "99901");
                Cek("U6 isi tabel: nama terakhir, data_lain, sumber, tanggal mentah",
                    Nilai(c, "nama", "99901") == "ANDI REVISI" && lain != null && lain.Contains("Kolom Aneh=x1b")
                    && Nilai(c, "sumber", "99901") == "uji_A.csv"
                    && (Nilai(c, "data_lain", "99903") ?? "").Contains("(mentah)=31/31/2000"),
                    "data_lain 99901 = " + lain);

                string b = Path.Combine(akar, "uji_B.csv");
                string teksB = "Account No,Name,Dept,Tgl Lahir" + nl + "88801,Jos\u00e9,Kanan,5-3-1992" + nl + "88802,\"Smith, John\",Kiri,1992-03-05" + nl;
                File.WriteAllBytes(b, Encoding.GetEncoding(1252).GetBytes(teksB));
                HasilAnalisis hb = ImporLama.Analisis(b, null);
                Dictionary<string, string> r1 = Cari(hb, "88801");
                Dictionary<string, string> r2 = Cari(hb, "88802");
                Cek("U7 berkas B: Windows-1252, pemisah koma, nama bertanda baca, tanggal d-M-yyyy",
                    hb.Sandi == "Windows-1252" && hb.Pemisah == "," && hb.Baris.Count == 2
                    && r1 != null && r1["nama"] == "Jos\u00e9" && r1["tgl_lahir"] == "1992-03-05"
                    && r2 != null && r2["nama"] == "Smith, John" && r2["departemen"] == "Kiri",
                    hb.Sandi + " " + hb.Pemisah);
                ImporLama.Tulis(c, hb);
                long n3 = Convert.ToInt64(Skalar(c, "select count(*) from induk_aplikasi_lama"));
                Cek("U8 impor berkas kedua menambah, tidak menimpa yang lain (total 5 baris)", n3 == 5, "baris=" + n3);
            }

            string cf = Path.Combine(akar, "uji_C.csv");
            File.WriteAllText(cf, "Nama,Dept" + nl + "X,Y" + nl, new UTF8Encoding(false));
            bool ditolak = false;
            try { ImporLama.Analisis(cf, null); }
            catch (InvalidDataException) { ditolak = true; }
            Cek("U9 berkas tanpa kolom No. Akun ditolak dengan pesan jelas", ditolak, "");

            string df = Path.Combine(akar, "uji_D.csv");
            string pem = Path.Combine(akar, "pemetaan_impor.txt");
            File.WriteAllText(df, "Kode Karyawan,Nama" + nl + "77701,TES" + nl, new UTF8Encoding(false));
            File.WriteAllText(pem, "# komentar" + nl + "Kode Karyawan=id_akun" + nl, new UTF8Encoding(false));
            HasilAnalisis hd = ImporLama.Analisis(df, pem);
            Cek("U10 berkas pemetaan_impor.txt menambah pemetaan sendiri",
                hd.Baris.Count == 1 && hd.Baris[0]["id_akun"] == "77701" && hd.Baris[0]["nama"] == "TES", "");

            Console.WriteLine();
            Console.WriteLine(gagal == 0 ? "SEMUA UJI LULUS" : gagal + " UJI GAGAL");
            return gagal == 0 ? 0 : 1;
        }
    }
}
