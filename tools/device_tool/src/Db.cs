using System;
using System.Collections.Generic;
using System.Data;
using System.Data.SQLite;
using System.IO;

namespace HrisDeviceTool.Data
{
    // Database lokal HRIS Device Tool (SQLite, satu berkas, portabel).
    // Tidak menyimpan jalur absolut, jadi berkas bisa disalin antar PC.
    public static class HdtDatabase
    {
        public const int VersiSkema = 5;

        private const string SkemaV1 = @"
CREATE TABLE IF NOT EXISTS meta (kunci TEXT PRIMARY KEY, nilai TEXT);
CREATE TABLE IF NOT EXISTS mesin (
    nama TEXT PRIMARY KEY,
    ip TEXT,
    versi_jari INTEGER,
    versi_wajah INTEGER,
    diperbarui TEXT
);
CREATE TABLE IF NOT EXISTS user_mesin (
    mesin TEXT NOT NULL,
    id_mesin TEXT NOT NULL,
    nama TEXT,
    privilege INTEGER,
    aktif INTEGER,
    diambil TEXT,
    PRIMARY KEY (mesin, id_mesin)
);
CREATE TABLE IF NOT EXISTS template_jari (
    mesin TEXT NOT NULL,
    id_mesin TEXT NOT NULL,
    jari INTEGER NOT NULL,
    flag INTEGER,
    versi INTEGER,
    panjang INTEGER,
    hash TEXT,
    data BLOB,
    diambil TEXT,
    PRIMARY KEY (mesin, id_mesin, jari)
);
CREATE TABLE IF NOT EXISTS induk_aplikasi_lama (
    id_akun TEXT PRIMARY KEY,
    no_induk TEXT,
    nama TEXT,
    kelamin TEXT,
    warga_negara TEXT,
    gelar TEXT,
    tgl_lahir TEXT,
    nomor_kartu TEXT,
    telp_kantor TEXT,
    no_ponsel TEXT,
    alamat TEXT,
    departemen TEXT,
    mulai_bekerja TEXT,
    batasan TEXT,
    data_lain TEXT,
    sumber TEXT,
    diimpor TEXT
);
CREATE INDEX IF NOT EXISTS ix_induk_lama_noinduk ON induk_aplikasi_lama (no_induk);
CREATE TABLE IF NOT EXISTS karyawan_hris (
    dokumen TEXT PRIMARY KEY,
    nama TEXT,
    id_finger TEXT,
    no_induk TEXT,
    department TEXT,
    status TEXT,
    disalin TEXT
);
CREATE INDEX IF NOT EXISTS ix_karyawan_idfinger ON karyawan_hris (id_finger);
CREATE INDEX IF NOT EXISTS ix_karyawan_noinduk ON karyawan_hris (no_induk);
CREATE TABLE IF NOT EXISTS department_hris (
    nama TEXT PRIMARY KEY,
    induk TEXT,
    aktif INTEGER,
    disalin TEXT
);
";

        private const string SkemaV2 = @"
ALTER TABLE user_mesin ADD COLUMN nomor_kartu TEXT;
ALTER TABLE user_mesin ADD COLUMN ada_sandi INTEGER;
ALTER TABLE user_mesin ADD COLUMN jumlah_jari INTEGER;
ALTER TABLE user_mesin ADD COLUMN jumlah_wajah INTEGER;
DROP VIEW IF EXISTS v_karyawan_lokal;
CREATE VIEW v_karyawan_lokal AS
SELECT
    ids.id AS id,
    i.no_induk AS no_induk,
    i.nama AS nama,
    i.kelamin AS kelamin,
    i.warga_negara AS warga_negara,
    i.gelar AS gelar,
    i.tgl_lahir AS tgl_lahir,
    i.mulai_bekerja AS mulai_bekerja,
    i.nomor_kartu AS nomor_kartu,
    i.telp_kantor AS telp_kantor,
    i.no_ponsel AS no_ponsel,
    i.alamat AS alamat_rumah,
    i.departemen AS departemen,
    i.batasan AS batasan,
    CASE WHEN i.id_akun IS NULL THEN 0 ELSE 1 END AS ada_di_aplikasi_lama,
    (SELECT COUNT(*) FROM user_mesin u WHERE u.id_mesin = ids.id) AS jumlah_mesin,
    (SELECT group_concat(u.mesin, ', ') FROM user_mesin u WHERE u.id_mesin = ids.id) AS daftar_mesin,
    (SELECT MAX(u.nama) FROM user_mesin u WHERE u.id_mesin = ids.id) AS nama_di_mesin,
    (SELECT MAX(u.privilege) FROM user_mesin u WHERE u.id_mesin = ids.id) AS privilege_mesin,
    (SELECT MAX(u.nomor_kartu) FROM user_mesin u WHERE u.id_mesin = ids.id) AS kartu_di_mesin,
    (SELECT MAX(u.jumlah_jari) FROM user_mesin u WHERE u.id_mesin = ids.id) AS jari_terbanyak
FROM (SELECT id_akun AS id FROM induk_aplikasi_lama UNION SELECT id_mesin FROM user_mesin) ids
LEFT JOIN induk_aplikasi_lama i ON i.id_akun = ids.id;
";

        private const string SkemaV3 = @"
ALTER TABLE mesin ADD COLUMN tipe TEXT;
ALTER TABLE mesin ADD COLUMN firmware TEXT;
ALTER TABLE mesin ADD COLUMN serial TEXT;
ALTER TABLE mesin ADD COLUMN platform TEXT;
ALTER TABLE mesin ADD COLUMN jumlah_user INTEGER;
ALTER TABLE mesin ADD COLUMN jumlah_admin INTEGER;
ALTER TABLE mesin ADD COLUMN jumlah_template_jari INTEGER;
ALTER TABLE mesin ADD COLUMN jumlah_wajah INTEGER;
ALTER TABLE mesin ADD COLUMN jumlah_log INTEGER;
ALTER TABLE mesin ADD COLUMN kapasitas_user INTEGER;
ALTER TABLE mesin ADD COLUMN kapasitas_jari INTEGER;
ALTER TABLE mesin ADD COLUMN kapasitas_log INTEGER;
ALTER TABLE mesin ADD COLUMN selisih_jam_detik INTEGER;
ALTER TABLE mesin ADD COLUMN info_diambil TEXT;
CREATE TABLE IF NOT EXISTS kunci_template (peran TEXT PRIMARY KEY, data BLOB NOT NULL, diubah TEXT);
";

        private const string SkemaV4 = @"
CREATE TABLE IF NOT EXISTS log_absensi (
    mesin TEXT NOT NULL,
    id_mesin TEXT NOT NULL,
    waktu TEXT NOT NULL,
    verifikasi INTEGER,
    status INTEGER,
    workcode INTEGER,
    diambil TEXT,
    PRIMARY KEY (mesin, id_mesin, waktu)
);
CREATE INDEX IF NOT EXISTS ix_log_waktu ON log_absensi (waktu);
CREATE INDEX IF NOT EXISTS ix_log_id_waktu ON log_absensi (id_mesin, waktu);
CREATE TABLE IF NOT EXISTS tarikan_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mesin TEXT NOT NULL,
    mulai TEXT,
    selesai TEXT,
    terbaca INTEGER,
    baru INTEGER,
    di_mesin INTEGER,
    sumber TEXT,
    berhasil INTEGER,
    catatan TEXT
);
CREATE INDEX IF NOT EXISTS ix_tarikan_mesin ON tarikan_log (mesin, mulai);
";

        private const string SkemaV5 = @"
CREATE TABLE IF NOT EXISTS jadwal_shift (
    id_mesin TEXT NOT NULL,
    tanggal TEXT NOT NULL,
    shift TEXT,
    wajib INTEGER,
    works INTEGER,
    libur INTEGER,
    off INTEGER,
    sumber TEXT,
    PRIMARY KEY (id_mesin, tanggal)
);
CREATE INDEX IF NOT EXISTS ix_jadwal_tanggal ON jadwal_shift (tanggal);
CREATE TABLE IF NOT EXISTS aturan_shift (
    nama TEXT PRIMARY KEY,
    mulai TEXT,
    selesai TEXT,
    lewat_tengah_malam INTEGER,
    durasi INTEGER,
    istirahat INTEGER,
    toleransi_telat INTEGER,
    toleransi_pulang INTEGER,
    jendela_sebelum INTEGER,
    batas_telat INTEGER,
    jendela_sesudah INTEGER,
    min_pulang INTEGER,
    lembur_min INTEGER
);
CREATE TABLE IF NOT EXISTS salin_shift (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    waktu TEXT,
    dari TEXT,
    sampai TEXT,
    baris INTEGER,
    karyawan INTEGER,
    peringatan TEXT
);
";

        // Skema v5: jadwal shift salinan dari HRIS. Hanya menambah.
        public static void MigrasiV5(SQLiteConnection c)
        {
            int versi = Convert.ToInt32(Skalar(c, "PRAGMA user_version"));
            if (versi >= 5) { return; }
            using (SQLiteTransaction t = c.BeginTransaction())
            {
                using (SQLiteCommand cmd = new SQLiteCommand(SkemaV5, c, t)) { cmd.ExecuteNonQuery(); }
                using (SQLiteCommand cmd2 = new SQLiteCommand("PRAGMA user_version = 5", c, t)) { cmd2.ExecuteNonQuery(); }
                t.Commit();
            }
        }
        // Skema v4: log absensi dan riwayat tarikan. Hanya menambah.
        public static void MigrasiV4(SQLiteConnection c)
        {
            int versi = Convert.ToInt32(Skalar(c, "PRAGMA user_version"));
            if (versi >= 4) { return; }
            using (SQLiteTransaction t = c.BeginTransaction())
            {
                using (SQLiteCommand cmd = new SQLiteCommand(SkemaV4, c, t)) { cmd.ExecuteNonQuery(); }
                using (SQLiteCommand cmd2 = new SQLiteCommand("PRAGMA user_version = 4", c, t)) { cmd2.ExecuteNonQuery(); }
                t.Commit();
            }
        }

        // Sebelum naik versi skema, simpan salinan database lama di samping berkas aslinya.
        public static void CadangkanBilaNaik(SQLiteConnection c)
        {
            int versi = Convert.ToInt32(Skalar(c, "PRAGMA user_version"));
            if (versi < 1 || versi >= VersiSkema) { return; }
            string folder = Path.GetDirectoryName(c.FileName);
            string tujuan = Path.Combine(folder, "hdt_sebelum_v" + VersiSkema + "_" + DateTime.Now.ToString("yyyyMMdd_HHmmss") + ".sqlite");
            Cadangkan(c, tujuan);
        }

        // Skema v3: info mesin dan kunci template terbungkus per akun. Hanya menambah.
        public static void MigrasiV3(SQLiteConnection c)
        {
            int versi = Convert.ToInt32(Skalar(c, "PRAGMA user_version"));
            if (versi >= 3) { return; }
            using (SQLiteTransaction t = c.BeginTransaction())
            {
                using (SQLiteCommand cmd = new SQLiteCommand(SkemaV3, c, t)) { cmd.ExecuteNonQuery(); }
                using (SQLiteCommand cmd2 = new SQLiteCommand("PRAGMA user_version = 3", c, t)) { cmd2.ExecuteNonQuery(); }
                t.Commit();
            }
        }

        // Skema v2: kolom data mesin dan tampilan gabungan per id. Hanya menambah.
        public static void MigrasiV2(SQLiteConnection c)
        {
            int versi = Convert.ToInt32(Skalar(c, "PRAGMA user_version"));
            if (versi >= 2) { return; }
            using (SQLiteTransaction t = c.BeginTransaction())
            {
                using (SQLiteCommand cmd = new SQLiteCommand(SkemaV2, c, t)) { cmd.ExecuteNonQuery(); }
                using (SQLiteCommand cmd2 = new SQLiteCommand("PRAGMA user_version = 2", c, t)) { cmd2.ExecuteNonQuery(); }
                t.Commit();
            }
        }

        public static string FolderDefault()
        {
            return Path.Combine(AppDomain.CurrentDomain.BaseDirectory, Path.Combine("data", "db"));
        }

        public static string BerkasDefault()
        {
            return Path.Combine(FolderDefault(), "hdt.sqlite");
        }

        // Membuka (atau membuat) database, lalu menjalankan migrasi skema.
        public static SQLiteConnection Buka(string berkas)
        {
            string folder = Path.GetDirectoryName(berkas);
            if (!string.IsNullOrEmpty(folder))
            {
                Directory.CreateDirectory(folder);
            }
            SQLiteConnection c = new SQLiteConnection("Data Source=" + berkas + ";Version=3;Default Timeout=10;");
            try
            {
                c.Open();
                CadangkanBilaNaik(c);
                Migrasi(c);
                MigrasiV2(c);
                MigrasiV3(c);
                MigrasiV4(c);
                MigrasiV5(c);
                return c;
            }
            catch
            {
                c.Dispose();
                throw;
            }
        }

        public static void Migrasi(SQLiteConnection c)
        {
            int versi = Convert.ToInt32(Skalar(c, "PRAGMA user_version"));
            if (versi > VersiSkema)
            {
                throw new InvalidOperationException(
                    "Database dibuat oleh versi aplikasi yang lebih baru (skema " + versi + "). Perbarui aplikasi.");
            }
            if (versi < 1)
            {
                using (SQLiteTransaction t = c.BeginTransaction())
                {
                    using (SQLiteCommand cmd = new SQLiteCommand(SkemaV1, c, t)) { cmd.ExecuteNonQuery(); }
                    using (SQLiteCommand cmd2 = new SQLiteCommand("PRAGMA user_version = 1", c, t)) { cmd2.ExecuteNonQuery(); }
                    t.Commit();
                }
            }
        }

        // Jumlah baris per tabel.
        public static List<KeyValuePair<string, long>> Ringkasan(SQLiteConnection c)
        {
            List<string> tabel = new List<string>();
            using (SQLiteCommand cmd = new SQLiteCommand(
                "select name from sqlite_master where type='table' and name not like 'sqlite_%' order by name", c))
            using (SQLiteDataReader r = cmd.ExecuteReader())
            {
                while (r.Read()) { tabel.Add(r.GetString(0)); }
            }
            List<KeyValuePair<string, long>> hasil = new List<KeyValuePair<string, long>>();
            foreach (string nama in tabel)
            {
                long n = Convert.ToInt64(Skalar(c, "select count(*) from \"" + nama + "\""));
                hasil.Add(new KeyValuePair<string, long>(nama, n));
            }
            return hasil;
        }

        // Salinan konsisten ke berkas lain, aman walau database sedang terbuka.
        public static void Cadangkan(SQLiteConnection sumber, string berkasTujuan)
        {
            string folder = Path.GetDirectoryName(berkasTujuan);
            if (!string.IsNullOrEmpty(folder))
            {
                Directory.CreateDirectory(folder);
            }
            if (File.Exists(berkasTujuan))
            {
                throw new IOException("Berkas tujuan sudah ada: " + berkasTujuan);
            }
            using (SQLiteConnection tujuan = new SQLiteConnection("Data Source=" + berkasTujuan + ";Version=3;"))
            {
                tujuan.Open();
                sumber.BackupDatabase(tujuan, "main", "main", -1, null, 0);
            }
        }

        private static object Skalar(SQLiteConnection c, string sql)
        {
            using (SQLiteCommand cmd = new SQLiteCommand(sql, c)) { return cmd.ExecuteScalar(); }
        }
    }
}
