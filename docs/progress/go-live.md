# Rencana Go Live dan Checklist

Dibuat: 6 November 2026. Diperbarui terakhir: 6 November 2026.

Dokumen ini adalah **acuan utama menuju go live**. Roadmap (`roadmap.md`) hanya daftar tahap fitur dan sudah usang (terakhir 28 Okt); `status.md` memuat kondisi teknis. Setiap akhir sesi, checklist di bawah ini diperbarui (lihat "Cara memperbarui").

## 1. Definisi go live

Go live = **semua fitur yang diperlukan sudah dipakai HRD dan berjalan lancar**, bukan sekadar aplikasi terpasang di server. Syaratnya: parallel run minimal 3 bulan tanpa selisih yang belum terjelaskan, UAT lulus, dokumentasi ada, dan production aman (backup teruji).

HRD tidak dipaksa pindah mendadak: aplikasi lama **tidak dimatikan**, hanya tidak dipakai setelah cutover.

## 2. Keputusan perencanaan (disepakati 30 Okt 2026)

Belum diberi nomor K. Nomor diberikan saat dipindahkan ke `decisions/`.

| # | Keputusan |
|---|---|
| P1 | Parallel run minimal 3 bulan (minimal 3 siklus gaji penuh), seperti masa percobaan karyawan baru |
| P2 | Aplikasi lama tidak dimatikan setelah cutover, hanya tidak dipakai |
| P3 | Selisih hasil parallel run dicatat satu per satu; HRD yang memutuskan benar atau salah, hasilnya masuk `decisions/` |
| P4 | Persetujuan lulus tiap fase: Efendy untuk teknis, HRD untuk hasil hitung, atasan untuk slip gaji |
| P5 | Fase 3 (gaji) mengikuti aturan HRD yang berlaku, tidak dipaksa sama dengan aplikasi lama |
| P6 | Komponen gaji dapat ditambah sendiri oleh user (bukan hardcode) |
| P7 | Aturan lembur dan insentif disimpan sebagai pengaturan, bukan hardcode |
| P8 | Aturan hitung (uang) menempel ke **Department** lewat DocType baru (nama kerja: Department Rule) dengan tanggal berlaku. Jadwal shift tetap di Employee Group, Rotation, Assignment; `HRIS Shift` tetap definisi jam dan pengukuran waktu |
| P9 | Pinjam karyawan dihitung **per hari**: hari dipinjam memakai aturan Department peminjam; hari lain memakai Department asal. Department yang dipakai tiap hari disimpan sebagai snapshot di Working Hour, sehingga mutasi permanen tidak mengubah gaji lama |
| P10 | Department tanpa rule pada tanggal terkait: hitungan gaji **ditolak dan ada notifikasi**. Sebelum Payroll Run ada pemeriksaan kesiapan (Readiness Check) yang mendaftar semua kekurangan sekaligus |
| P11 | Pinjaman karyawan dimulai sederhana (pokok, cicilan, sisa saldo, tanpa bunga) kecuali HRD menyatakan lain |
| P12 | Biometrik: unduh dan simpan ke database dengan akses terbatas; kirim balik ke mesin lain ditunda. Data pribadi khusus: aturan persetujuan dan retensi diputuskan sebelum fitur dibuat |
| P13 | Karyawan melihat data sendiri (self service): belum perlu. Report Audit Trail: nanti bersama laporan lain (tab Audit Trail tetap ada) |
| P14 | Nama merek: "HRIS", atau "FnD" bila HRIS tidak bisa. Nama teknis app tetap `hris`. Diputuskan sebelum Fase 5 |
| P15 | Lisensi: belum diputuskan; batas waktu sebelum Fase 6 |
| P16 | HRIS tetap mandiri (K-18); fitur yang mungkin sudah ada di HRMS (cuti, pinjaman, potongan) dicek dulu dan dijelaskan sebelum dibangun |

## 3. Fase menuju go live

| Fase | Isi | Target | Syarat selesai (gate) |
|---|---|---|---|
| 0 | Semua keputusan terbuka dikunci dan dicatat | Berjalan terus | Tidak ada keputusan terbuka yang menghambat Fase 3 |
| 1 | Data mesin masuk dan tercocokkan ke karyawan nyata | Sekitar 1 minggu | Log semua mesin masuk tanpa input manual, tercocokkan ke Employee, 3 hari berturut-turut |
| 2 | Absensi lengkap: working hour, koreksi, cuti/izin, lembur, ekspor, laporan | Disesuaikan | Hasil working hour sama dengan hitungan manual HRD untuk satu periode |
| 3 | Gaji: data karyawan, pay, komponen, formula, pinjaman, potongan, slip | Disesuaikan | Hitungan HRIS cocok dengan sampel slip aplikasi lama |
| 4 | Parallel run | 3 bulan | Selisih nol atau semua selisih terjelaskan dan diputuskan HRD |
| 5 | UAT dan dokumentasi pengguna | Disesuaikan | HRD menjalankan satu siklus penuh sendiri tanpa bantuan |
| 6 | Production dan cutover | Singkat | Backup teruji pulih, hardening selesai, aplikasi lama tidak dipakai lagi |
| 7 | Hypercare | 1 sampai 2 siklus gaji | Tidak ada isu kritis terbuka |

Catatan urutan: Fase 4 sebaiknya dimulai secepat mungkin. Fase 2 dan 3 dibuat ringkas dulu; penyempurnaan dilakukan selama parallel run.

## 4. Checklist per fase

Status: **Selesai**, **Sebagian**, **Belum**, **Perlu verifikasi**. Sumber: `status.md` (5 Nov 2026) dan `decisions/`.

### Fase 0: Keputusan

| Keputusan | Status | Catatan |
|---|---|---|
| Definisi go live, parallel run, fase (P1 sampai P16) | Selesai | Bagian 2 |
| Aturan lembur lanjutan dan insentif | Belum | K-98: lembur x1,0 sebagai pengaturan; kepatuhan hukum perlu konfirmasi Kepala HRD |
| Komponen gaji spesifik (BPJS, PPh 21, THR, potongan lain) | Belum | Dikumpulkan dari HRD |
| Cuti dan izin selain sakit | Belum | Pengaturan dibuat fleksibel |
| Akuntansi gaji: jurnal otomatis atau laporan saja | Belum | "Posting" mungkin dipakai |
| Format slip gaji | Belum | Perlu konfirmasi atasan |
| Format file transfer bank | Belum | Minta dari HRD |
| Daftar laporan wajib | Belum | Minta dari HRD |
| Pembayaran selain bulanan (mingguan/harian) | Sebagian | K-95 sampai K-97 sudah memuat; daftar karyawan per jenis belum |
| Saldo awal (cuti, sisa pinjaman, akumulasi pajak) | Belum | Perlu sebelum parallel run |
| Konfirmasi asumsi working hour (`review_status`, `overtime_type`, detik dibuang, hari tanpa jadwal = Libur, toleransi 0) | Sebagian | Beberapa sudah dikonfirmasi 29 Okt; cek ulang di `decisions/README.md` |
| Istirahat Security | Belum | Sementara 0 menit |
| Merek dan lisensi | Belum | P14, P15 |
| Aturan biometrik (persetujuan, retensi) | Belum | UU PDP; sebelum fitur biometrik |
| Retensi Raw Log | Belum | Data tumbuh terus |

### Fase 1: Data mesin

| Item | Status | Catatan |
|---|---|---|
| `HRIS Device`, `HRIS Raw Log` | Selesai | K-26, K-48, K-57, K-58 |
| Tarik data via Pull (pyzk) | Selesai | Teruji ke satu mesin; mesin lain belum dicoba |
| Agen Windows (SDK) untuk mesin ber-Comm Key | Sebagian | Teruji di satu PC; sisa uji PC kedua, `allowed_ips`, rotasi token, mesin Solution lain |
| Konsol Mesin, Pull Run, Hapus Raw Log | Selesai | K-67 sampai K-77 |
| Autentikasi agen dan endpoint | Selesai | K-52, K-53 |
| Karyawan Active dengan `attendance_device_id` | Perlu verifikasi | Status 5 Nov mencatat 1.078 Employee ERPNext di site kerja, tetapi sebelumnya belum ada yang Active; cek jumlah Active dan ID mesin |
| "Cocokkan Ulang" (Raw Log Tidak Cocok ke Employee) | Belum | K-64; sesi tersendiri |
| Tarik celah data (tanggal yang dihapus saat uji) | Belum | Status 31 Okt |
| Mesin ketiga yang gagal via pyzk | Sebagian | Dijangkau lewat agen (K-72); uji lengkap menunggu |
| Penjadwalan tarikan rutin | Belum | `pause_scheduler` aktif; manual dulu (K-55) |
| Monitoring mesin (mesin offline, log tidak masuk) | Belum | Disarankan |
| Sinkron jam mesin (NTP) dan pengecekan jam | Belum | Jam mesin memengaruhi telat dan lembur |
| Impor log dari file | Belum | Wajib (P: impor), format menunggu contoh berkas |
| Perilaku mesin saat penuh | Belum | Cek manual |

### Fase 2: Absensi lengkap

| Item | Status | Catatan |
|---|---|---|
| Shift, Employee Group, Rotation, Holiday, Shift Assignment | Selesai | K-31 sampai K-34 |
| Working Hour (hitung per hari, potongan, lembur, status, tanda tinjauan) | Selesai | K-35 sampai K-44; teruji skrip |
| Hitung ulang per cakupan (5c-1) | Sebagian | Teruji skrip; browser dan job background belum |
| Warna list view dan Report ringkasan (5c-2) | Perlu verifikasi | Catatan sesi 29 Okt menyebut selesai (5406151), tetapi `status.md` masih menulis tertunda; sinkronkan |
| Uji dengan data nyata (shift Security lintas tengah malam, hari Libur, tumpang tindih jendela) | Belum | Menunggu Employee nyata |
| Koreksi absensi | Sebagian | Penyesuaian jam dan edit sumber dengan alasan sudah ada (K-25, K-42); alur koreksi lupa scan dan mesin mati belum dirancang |
| Cuti dan izin | Belum | Wajib |
| Pengaturan lembur (pengali, hari libur) | Belum | P7; K-98 |
| Pinjam karyawan: berdasarkan Department peminjam | Belum | Saat ini field "Dipinjam untuk Grup" (K-32, K-39); `borrowed_for_department` mengubah DocType berjalan, perlu konfirmasi dan penjelasan risiko dulu |
| Department Rule (aturan hitung per Department, tanggal berlaku) | Belum | P8; dirancang sebelum dibuat |
| Ekspor (Excel) | Belum | Wajib |
| Impor karyawan dari file | Belum | Wajib; terkait migrasi K-102 |
| Alur persetujuan (koreksi, cuti, lembur, pinjaman, Payroll Run) | Belum | Siapa membuat dan siapa menyetujui |
| Penguncian periode | Belum | Menunggu `HRIS Payroll Period` |
| Role HRIS: enam role lama | Selesai | K-11 |
| Role `HRIS Employee Admin`, `HRIS Payroll Manager`, `HRIS Direksi` | Sebagian | Ada di kode dan site uji; di site kerja menunggu `migrate` (K-116, K-120) |
| Matriks hak akses per role dan per company | Sebagian | `security/permissions.md`; pembatasan per company belum |
| Tab Audit Trail | Selesai | K-25, K-119 |
| Report Audit Trail | Belum | Ditunda (P13) |

### Fase 3: Gaji

| Item | Status | Catatan |
|---|---|---|
| `HRIS Payroll Schedule` | Selesai | K-105, K-106; ada di site kerja; 34 pemeriksaan skrip OK; uji browser belum |
| `HRIS Employee` (data karyawan lengkap) | Sebagian | K-116; diterapkan di site uji; belum di site kerja |
| Sinkron satu arah HRIS Employee ke Employee ERPNext (K-101) | Belum | Sesi 3c |
| Migrasi 1.077 Employee (K-102) | Belum | Uji di site uji dulu |
| Dokumen karyawan (KTP, kontrak, foto) | Belum | Perlu uji lampiran dengan role baca saja |
| `HRIS Employee Pay` (riwayat gaji, tanggal berlaku) | Belum | K-109 |
| `HRIS Payroll Period` (periode, status Final) | Belum | K-108 |
| Komponen gaji (dapat ditambah user) dan formula aman | Belum | P6; formula wajib dijalankan di lingkungan terbatas, bukan `eval` bebas (verifikasi dokumentasi Frappe) |
| `HRIS Payroll Slip` (termasuk Adjustment, K-111) | Belum | |
| Aturan hitung bulanan, mingguan, harian (K-96, K-97, K-99, K-107) | Disetujui, belum dibuat | Dasar: `business/payroll-rancangan.md` |
| Readiness Check sebelum Payroll Run (P10) | Belum | |
| Pro-rata (masuk/keluar di tengah periode), mutasi, final pay | Belum | Muncul tiap bulan |
| Pinjaman karyawan | Belum | P11 |
| Potongan dan pajak (BPJS, PPh 21, THR) | Belum | Tarif sebagai pengaturan; konfirmasi HRD atau konsultan pajak |
| Slip gaji cetak (PDF) | Belum | Format perlu konfirmasi atasan |
| File transfer bank | Belum | Format menunggu dari HRD |
| Laporan gaji dan laporan wajib | Belum | Daftar menunggu dari HRD |
| Posting ke akuntansi ERPNext | Belum | Opsional; K-19 |
| Uji otomatis rumus dari slip lama | Belum | Slip lama jadi kasus uji |
| Akses data gaji hanya role khusus (K-110) | Sebagian | Role dibuat di site uji; penegakan per baris perlu diuji |

### Fase 4: Parallel run (3 bulan)

| Item | Status |
|---|---|
| Mulai absensi di data nyata (mesin ke HRIS) | Belum |
| Siklus gaji 1 | Belum |
| Siklus gaji 2 | Belum |
| Siklus gaji 3 | Belum |
| Daftar selisih dan keputusannya | Belum |
| Gate: selisih nol atau terjelaskan, ditandatangani HRD | Belum |

### Fase 5: UAT dan dokumentasi

| Item | Status | Catatan |
|---|---|---|
| Uji browser per peran (tarik absensi, payroll, input karyawan, Kepala HRD, Direksi) | Belum | |
| Dokumentasi pengguna HRD | Belum | Perlu menyebut merek final |
| SOP bulanan (closing absensi dan gaji) dan SOP mesin mati | Belum | |
| Pelatihan HRD | Belum | |
| Dokumen teknis: `requirements/`, `business/business-rules.md`, `operations/*` | Belum | Masih berupa stub (kurang dari 150 byte) |
| Sinkron `data-model.md`, `api.md`, `attendance-flow.md`, `CLAUDE.md` | Belum | Tertunda di `status.md` |

### Fase 6: Production dan cutover

| Item | Status | Catatan |
|---|---|---|
| `developer_mode` mati | Belum | Setelah itu perubahan DocType hanya lewat git dan migrate |
| nginx dan HTTPS | Belum | K-56; estimasi singkat |
| supervisor atau service pengganti `honcho` di terminal | Belum | |
| Satu atau dua bench | Belum diputuskan | |
| Scheduler dan email keluar aktif | Belum | `pause_scheduler` aktif |
| Backup terjadwal dan uji restore | Belum | Uji pulih, bukan hanya backup |
| Prosedur update production (backup, pull, migrate, rollback) | Belum | |
| Rotasi token agen, `allowed_ips` | Belum | `architecture/agent-api.md` |
| Hardening (HTTPS, akses LAN, hak akses data sensitif) | Belum | |
| Site uji dibersihkan | Belum | K-117 |
| `migrate` di site kerja (role dan DocType baru) | Belum | Cadangan, latihan di salinan, baru site kerja |
| CI ke `main` (K-15), pre-commit, judul app | Belum | |
| Lisensi final | Belum | P15 |
| Cutover: aplikasi lama tidak dipakai | Belum | P2 |

### Fase 7: Hypercare

| Item | Status |
|---|---|
| Pembagian dukungan dan kecepatan respons | Belum |
| Pemantauan 1 sampai 2 siklus gaji | Belum |
| Daftar isu dan penutupannya | Belum |

## 5. Permintaan ke HRD (tanpa menunggu kode)

| Permintaan | Untuk |
|---|---|
| 3 sampai 5 contoh slip gaji nyata (berbagai jenis karyawan, termasuk lembur dan pinjaman) dan aturan tertulisnya | Fase 3, uji otomatis |
| Format file transfer bank | Fase 3 |
| Daftar laporan yang dipakai sekarang | Fase 2 dan 3 |
| Aturan cut-off, tanggal bayar, dan jenis pembayaran (bulanan, mingguan, harian) per kelompok karyawan | Fase 3 |
| Daftar potongan dan tunjangan yang berlaku | Fase 3 |
| Aturan cuti dan izin | Fase 2 |
| Saldo awal (cuti, sisa pinjaman, pajak berjalan) | Fase 4 |
| Alokasi waktu HRD untuk UAT dan pencocokan selama parallel run | Fase 4 dan 5 |

## 6. Risiko utama

1. Saldo awal dan pajak: salah baru ketahuan di slip gaji.
2. Pro-rata dan siklus hidup karyawan: jarang muncul di uji, muncul tiap bulan di data nyata.
3. Penguncian periode dan revisi: tanpa ini, perbandingan parallel run bergeser.
4. Uji otomatis dari slip lama: yang membuat "selisih nol" bisa dibuktikan.
5. Jalur data mesin untuk mesin berbeda firmware dan Comm Key berperilaku berbeda.
6. Data pribadi khusus (biometrik, KTP, rekening): aturan persetujuan dan retensi.

## 7. Cara memperbarui

- Akhir tiap sesi, ubah kolom Status baris yang berubah dan tambah baris di Log pembaruan.
- Gunakan status yang sama: Selesai, Sebagian, Belum, Perlu verifikasi.
- Item baru ditambahkan ke fase yang sesuai, bukan dihapus saat selesai.
- Keputusan baru dicatat di `decisions/`; bagian 2 hanya memuat ringkasan keputusan perencanaan.
- Bila `status.md` dan dokumen ini berbeda, periksa `git log` dan kode, lalu sinkronkan keduanya.

## 8. Log pembaruan

| Tanggal | Perubahan |
|---|---|
| 2026-11-06 | Dokumen dibuat. Checklist disusun dari `status.md` (5 Nov), `decisions/` (K-01 sampai K-121 menurut daftar), dan percakapan perencanaan 30 Okt |
