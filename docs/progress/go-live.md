# Rencana Go Live dan Checklist

Dibuat: 6 November 2026. Diperbarui terakhir: 10 November 2026.

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

Status: **Selesai**, **Sebagian**, **Belum**, **Perlu verifikasi**. Sumber: `status.md` (5 Nov 2026), `decisions/`, dan hasil kerja 6 sampai 7 Nov 2026.

### Fase 0: Keputusan

| Keputusan | Status | Catatan |
|---|---|---|
| Definisi go live, parallel run, fase (P1 sampai P16) | Selesai | Bagian 2 |
| Aturan lembur lanjutan dan insentif | Sebagian | **Pembulatan durasi sudah diputuskan dan diterapkan (K-38):** minimal 30 menit, kelipatan 30 menit, dibulatkan ke bawah, dihitung dari jam selesai shift sampai paling lama `window_after_min`. Contoh shift selesai 17.00: 17.01 sampai 17.25 = 0; 17.01 sampai 17.59 = 30 menit; 17.01 sampai 18.55 = 90 menit. **Terverifikasi 7 Nov:** kode `services/working_hour.py` (`(min(over, window_after_min) // step) * step`) dan data produksi (delapan Shift: `overtime_min_minutes` = 30, `window_after_min` = 240). Belum diputuskan: pengali (K-98: x1,0 sebagai pengaturan; kepatuhan hukum perlu konfirmasi Kepala HRD), aturan hari libur, insentif. Catatan desain: satu field `overtime_min_minutes` berfungsi sebagai minimal sekaligus kelipatan; dipisah bila HRD menginginkan ambang dan langkah berbeda |
| Komponen gaji spesifik (BPJS, PPh 21, THR, potongan lain) | Belum | Dikumpulkan dari HRD |
| Cuti dan izin selain sakit | Belum | Pengaturan dibuat fleksibel |
| Akuntansi gaji: jurnal otomatis atau laporan saja | Belum | "Posting" mungkin dipakai |
| Format slip gaji | Belum | Perlu konfirmasi atasan |
| Format file transfer bank | Belum | Minta dari HRD |
| Daftar laporan wajib | Belum | Minta dari HRD |
| Pembayaran selain bulanan (mingguan/harian) | Sebagian | K-95 sampai K-97 sudah memuat; K-127 menegaskan upah mingguan disimpan per hari (jenis gaji Harian, jadwal gaji Mingguan); daftar karyawan per jenis belum |
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
| Karyawan Active dengan `attendance_device_id` | Selesai | Diagnosa produksi 7 Nov 2026: 1.078 Employee, semuanya Active, `attendance_device_id` terisi dan unik pada semuanya. Selisih dengan 1.077 di rencana migrasi tuntas: 1.077 dibuat pada impor 1 Nov, satu lagi pada 2 Nov, dan Efendy mengonfirmasi semuanya karyawan sungguhan. Ulangi `diag_db_k102.sh` tepat sebelum migrasi karena jumlah dapat berubah |
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
| Working Hour (hitung per hari, potongan, lembur, status, tanda tinjauan) | Selesai | K-35 sampai K-44; teruji skrip. Uji tampilan D1 sampai D4 lulus (6 sampai 7 Nov) |
| Klasifikasi absen hari Tidak Hadir (K-131) | Sebagian | Field klasifikasi di `HRIS Working Hour` (097a946): teruji skrip (OK 33) dan browser di site uji, termasuk Lainnya dengan catatan dan Dipotong Gaji manual (9 Nov). Aturan karyawan Harian (89f0c63): Tidak Hadir Harian tidak ditandai dan tidak menghalangi Final; uji skrip OK 11, uji browser belum (site uji belum punya baris gaji karyawan). Belum di produksi. `HRIS Absence` menggantikan field ini kelak; belum dirancang |
| Hitung ulang per cakupan (5c-1) | Sebagian | Teruji skrip; browser dan job background belum |
| Warna list view dan Report ringkasan (5c-2) | Perlu verifikasi | Catatan sesi 29 Okt menyebut selesai (5406151), tetapi `status.md` masih menulis tertunda; sinkronkan |
| Uji dengan data nyata (shift Security lintas tengah malam, hari Libur, tumpang tindih jendela) | Belum | Menunggu Employee nyata |
| Koreksi absensi | Sebagian | Penyesuaian jam dan edit sumber dengan alasan sudah ada (K-25, K-42); alur koreksi lupa scan dan mesin mati belum dirancang |
| Cuti dan izin | Belum | Wajib |
| Pengaturan lembur: pengali dan hari libur | Belum | P7; K-98. Durasi dan pembulatan 30 menit sudah selesai (K-38) |
| Pinjam karyawan: berdasarkan Department peminjam | Belum | Saat ini field "Dipinjam untuk Grup" (K-32, K-39); `borrowed_for_department` mengubah DocType berjalan, perlu konfirmasi dan penjelasan risiko dulu |
| Department Rule (aturan hitung per Department, tanggal berlaku) | Belum | P8; dirancang sebelum dibuat |
| Ekspor (Excel) | Belum | Wajib |
| Impor karyawan dari file | Belum | Wajib; terkait migrasi K-102 |
| Alur persetujuan (koreksi, cuti, lembur, pinjaman, Payroll Run) | Sebagian | Periode gaji sudah ada alurnya (K-128: Tinjau oleh Payroll Admin atau Manager, Final dan buka kembali hanya Payroll Manager). Sisanya belum; siapa Payroll Manager belum diputuskan |
| Penguncian periode | Sebagian | K-128: periode Final mengunci edit dan hitung ulang `HRIS Working Hour` serta baris `HRIS Employee Pay` berlaku mundur; teruji di site uji (9 Nov). Belum di produksi |
| Role HRIS: enam role lama | Selesai | K-11 |
| Role `HRIS Employee Admin`, `HRIS Payroll Manager`, `HRIS Direksi` | Sebagian | Ada di kode dan site uji. Di produksi (`erp.ciptamebel.co.id`) belum ada: role dibuat saat `migrate` produksi, bagian dari migrasi K-102 (K-116, K-120) |
| Matriks hak akses per role dan per company | Sebagian | `security/permissions.md`; pembatasan per company belum |
| Tab Audit Trail | Selesai | K-25, K-119 |
| Report Audit Trail | Belum | Ditunda (P13) |

### Fase 3: Gaji

| Item | Status | Catatan |
|---|---|---|
| `HRIS Payroll Schedule` | Selesai | K-105, K-106; ada di site kerja; 34 pemeriksaan skrip OK; uji browser belum. Penjaga penonaktifan jadwal diperbaiki 7 Nov (deb04ae): kini menghitung baris gaji berlaku milik karyawan Aktif |
| `HRIS Employee` (data karyawan lengkap) | Sebagian | K-116, K-126 (validasi, 8a16ade). Kode teruji dan gladi resik lulus di `hris-uji.local`. Di produksi tabel `HRIS Employee` belum ada (diagnosa 7 Nov); dibuat saat `migrate` produksi |
| Sinkron satu arah HRIS Employee ke Employee ERPNext (K-101) | Belum | Sesi 3c |
| Migrasi Employee ke HRIS Employee (K-102) | Sebagian | Kode di-push (7278bb7), teruji di site uji. Gladi resik `produksi_k102.sh` (`cadangan`, `siap`, `mulai`) lulus di `hris-uji.local`. Produksi belum dijalankan; menunggu waktu di luar jam kerja (lihat bagian 9) |
| Dokumen karyawan (KTP, kontrak, foto) | Belum | Perlu uji lampiran dengan role baca saja |
| `HRIS Employee Pay` (riwayat gaji, tanggal berlaku) | Sebagian | K-109, K-127. Dibuat dan teruji di `hris-uji.local` (701fc76, deb04ae): uji skrip OK 30 + OK 4 + OK 5, GAGAL 0; uji browser (form terkunci, tab Audit Trail, alasan wajib) lulus. K-129 (9 Nov, 913268f dan 4807cba): `write` untuk Payroll Manager dan Payroll Admin, Payroll Admin hanya melihat Jenis Gaji Harian di form baru; uji browser per peran lulus di site uji. Belum ada di produksi: tabel terbentuk saat `migrate` produksi. Sisa: uji dengan akun peran asli setelah migrasi |
| `HRIS Payroll Period` (periode, status Final) | Sebagian | K-108, K-128. Dibuat dan teruji di `hris-uji.local` (9c0648a, 0ebc487, 913268f, 4807cba): Draft, Ditinjau, Final, buka kembali dengan alasan, notifikasi in-app, dialog kesiapan lengkap; uji skrip kesiapan OK 18, Period OK 28, regresi OK 4; uji browser per peran lulus. Belum ada di produksi: tabel terbentuk saat `migrate` produksi. Sisa: orang yang menjadi HRIS Payroll Manager belum ditetapkan; syarat Department Rule (P10) dan `HRIS Absence` menyusul |
| Komponen gaji (dapat ditambah user) dan formula aman | Belum | P6; formula wajib dijalankan di lingkungan terbatas, bukan `eval` bebas (verifikasi dokumentasi Frappe) |
| `HRIS Payroll Slip` (termasuk Adjustment, K-111) | Sebagian | K-130: tahap pertama (DocType, layanan hitung, tombol Buat Slip, potongan absen dari klasifikasi K-131) di 2f483dc dan b11d89c; uji skrip OK 77 dan uji browser lulus di site uji (9 Nov); belum di produksi. Finalkan Periode tetap ditolak selama karyawan Hadir belum punya baris gaji (aturan K-128). Rancangan K-130: Pembuatan massal, per kelompok atau departemen, dan satu per satu; hitung ulang hanya slip Draft; Final terkunci. Tahap pertama tanpa BPJS dan PPh 21. Baris komponen Otomatis terkunci per baris (`f9a6601`, 10 Nov) |
| Aturan hitung bulanan, mingguan, harian (K-96, K-97, K-99, K-107) | Disetujui, belum dibuat | Dasar: `business/payroll-rancangan.md`; rumus tahap pertama di K-130 |
| Readiness Check sebelum Payroll Run (P10) | Belum | |
| Pro-rata (masuk/keluar di tengah periode), mutasi, final pay | Belum | Muncul tiap bulan |
| Pinjaman karyawan | Belum | P11 |
| Potongan dan pajak (BPJS, PPh 21, THR) | Sebagian | BPJS (K-133): angka tetap per program, Ketenagakerjaan satu angka atau rincian, dipotong sekali sebulan; kode `f6f837b`, teruji di site uji (skrip OK 68 dan OK 77, browser, izin per peran `aa87b66` OK 16); belum di produksi; dua butir menunggu konfirmasi HRD (keputusan-2026-11-10-bpjs.md bagian 8). PPh 21 (K-134, TER bulanan): rancangan disetujui 10 Nov, belum ada kode; tarif resmi, PTKP, dan NPWP menunggu HRD atau konsultan pajak. THR belum. Angka resmi diverifikasi HRD atau konsultan pajak |
| Slip gaji cetak (PDF) | Belum | Format perlu konfirmasi atasan |
| File transfer bank | Belum | Format menunggu dari HRD |
| Laporan gaji dan laporan wajib | Belum | Daftar menunggu dari HRD |
| Posting ke akuntansi ERPNext | Belum | Opsional; K-19 |
| Uji otomatis rumus dari slip lama | Belum | Slip lama jadi kasus uji |
| Akses data gaji hanya role khusus (K-110) | Sebagian | Penegakan per baris sudah teruji untuk `HRIS Employee Pay` di site uji (izin, daftar, Audit Trail, `Version`; Payroll Admin tidak melihat gaji Bulanan). Belum diuji dengan akun asli di produksi, dan untuk `HRIS Payroll Slip` teruji skrip di site uji (I1 sampai I3: Payroll Admin hanya melihat slip Harian, Payroll Manager semua, peran lain tidak); uji browser per peran belum |

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
| Uji browser per peran (tarik absensi, payroll, input karyawan, Kepala HRD, Direksi) | Belum | Dikerjakan setelah migrasi produksi, dengan akun uji khusus. Uji izin lewat skrip sudah ada untuk Employee dan Employee Pay |
| Dokumentasi pengguna HRD | Belum | Perlu menyebut merek final |
| SOP bulanan (closing absensi dan gaji) dan SOP mesin mati | Belum | |
| Pelatihan HRD | Belum | |
| Dokumen teknis: `requirements/`, `business/business-rules.md`, `operations/*` | Belum | Masih berupa stub (kurang dari 150 byte), kecuali `deployment.md` dan `migrasi-k102-checklist.md` |
| Sinkron `data-model.md`, `api.md`, `attendance-flow.md`, `CLAUDE.md` | Belum | Tertunda di `status.md` |

### Fase 6: Production dan cutover

| Item | Status | Catatan |
|---|---|---|
| `developer_mode` mati | Belum | Saat ini bernilai 1 di produksi (diagnosa 7 Nov). Setelah dimatikan, perubahan DocType hanya lewat git dan migrate |
| nginx dan HTTPS | Belum | K-56; estimasi singkat |
| supervisor atau service pengganti `honcho` di terminal | Belum | Restart sekarang manual: Ctrl+C lalu `bench start` |
| Satu atau dua bench | Belum diputuskan | Catatan 7 Nov: site uji dan produksi kini berbagi satu bench dan satu folder app, sehingga DocType baru (misalnya `HRIS Employee Pay`) ikut terbentuk di produksi saat `migrate` produksi |
| Scheduler dan email keluar aktif | Belum | `pause_scheduler` aktif; akun email keluar aktif = 0 |
| Backup terjadwal dan uji restore | Belum | Uji pulih, bukan hanya backup. `cadangan` dan `pulihkan` ada di runbook; cabang produksi pada `restore` belum terbukti |
| Prosedur update production (backup, pull, migrate, rollback) | Sebagian | Runbook ada di server (`/home/it/runbook_k102/`) dan diarsipkan di repo (`scripts/operations/k102/`, c7a0f52); checklist malam migrasi di `operations/migrasi-k102-checklist.md`; lulus gladi resik di site uji; `P mulai` di produksi belum terbukti |
| Rotasi token agen, `allowed_ips` | Belum | `architecture/agent-api.md` |
| Hardening (HTTPS, akses LAN, hak akses data sensitif) | Belum | |
| Site uji dibersihkan | Sebagian | K-117; data uji K-128 (periode, baris gaji, jadwal, dua user uji) dibersihkan 9 Nov; sisa site uji menunggu setelah migrasi aman |
| `migrate` di site kerja (role dan DocType baru) | Sebagian | Cadangan dan latihan di salinan (`hris-uji.local`) sudah lulus. Produksi belum; dijalankan lewat `produksi_k102.sh mulai`. Migrasi juga membuat tabel `HRIS Employee Pay` dan `HRIS Payroll Period` (kosong), serta memperbarui izin `HRIS Payroll Schedule` (K-129; verifikasi hasilnya) |
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
7. Migrasi produksi K-102: dikerjakan di luar jam kerja setelah lembur, saat pelaksana lelah. Mitigasi: runbook dengan konfirmasi berlapis, cadangan wajib maksimal 6 jam, diagnosa ulang sebelum mulai, dan `P pulihkan` untuk rollback.

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
| 2026-11-07 | Disinkronkan dengan hasil 6 sampai 7 Nov: K-126 dan K-102 di-push dan teruji; gladi resik `produksi_k102.sh` lulus di `hris-uji.local`; kondisi produksi (diagnosa 05:52 WIB); risiko 7 dan bagian 9 ditambahkan; runbook diarsipkan di repo (c7a0f52) |
| 2026-11-07 | Aturan lembur dirujuk ke K-38 (sudah diputuskan dan diterapkan 29 Okt); terverifikasi lewat kode `working_hour.py` dan nilai delapan Shift produksi (30 dan 240) |
| 2026-11-07 | `HRIS Employee Pay` (K-127) dibuat dan teruji di site uji (701fc76, deb04ae); penjaga penonaktifan jadwal gaji diperbaiki; selisih 1.078 vs 1.077 Employee tuntas; checklist malam migrasi ditambahkan; catatan bahwa `migrate` produksi ikut membuat tabel `HRIS Employee Pay` |
| 2026-11-09 | `HRIS Payroll Period` (K-128) dan hak akses K-129 dibuat dan teruji di site uji (9c0648a, 0ebc487, 913268f, 4807cba); data uji dibersihkan; keputusan di [keputusan-2026-11-09.md](../decisions/keputusan-2026-11-09.md) |
| 2026-11-09 | Rancangan `HRIS Payroll Slip` disetujui (K-130, belum ada kode); klasifikasi absen (K-131, 097a946) teruji skrip dan browser; aturan karyawan Harian (89f0c63) teruji skrip, browser menunggu baris gaji karyawan; keputusan di [keputusan-2026-11-09-payroll-slip.md](../decisions/keputusan-2026-11-09-payroll-slip.md) dan [keputusan-2026-11-09-absen.md](../decisions/keputusan-2026-11-09-absen.md) |
| 2026-11-10 | `HRIS Payroll Slip` tahap pertama dibuat dan teruji di site uji (2f483dc, b11d89c): uji skrip OK 77, uji browser lulus termasuk potongan absen Mangkir dan Sakit; slip uji dibersihkan; keputusan tetap di [keputusan-2026-11-09-payroll-slip.md](../decisions/keputusan-2026-11-09-payroll-slip.md) |
| 2026-11-10 | BPJS pada Payroll Slip (K-133, angka tetap) dibuat dan teruji di site uji (`f6f837b`, uji izin `aa87b66`): skrip OK 68, OK 77, izin OK 16, browser lulus; dokumen di [keputusan-2026-11-10-bpjs.md](../decisions/keputusan-2026-11-10-bpjs.md) |
| 2026-11-10 | Komponen Otomatis slip terkunci per baris (`f9a6601`, skrip OK 77, browser lulus); rancangan PPh 21 tahap 2a disetujui (K-134, belum ada kode), dokumen di [keputusan-2026-11-10-pph21.md](../decisions/keputusan-2026-11-10-pph21.md) |

## 9. Migrasi produksi K-102 (menunggu jadwal)

Tidak ada tanggal tetap. Dikerjakan saat Efendy diminta masuk di luar jam kerja (dihitung lembur). Efendy memberi tahu Claude sebelum mulai. Rincian langkah ada di `operations/deployment.md` dan versi satu halaman di `operations/migrasi-k102-checklist.md`; berikut ringkasannya.

| Langkah | Perintah atau tindakan (dari `/home/it/erp`, `P` = `bash /home/it/runbook_k102/produksi_k102.sh`) |
|---|---|
| 0 | Jalankan ulang diagnosa (`diag_db_k102.sh`); cocokkan jumlah Employee |
| 1 | `P cadangan` (cadangan lama ditolak bila lebih dari 6 jam) |
| 2 | Salin cadangan ke PC lewat PowerShell `scp`, verifikasi dengan `Get-FileHash` |
| 3 | `P siap` |
| 4 | `P mulai` (2 jawaban "ya", lalu ketik `MULAI PRODUKSI erp.ciptamebel.co.id`) |
| 5 | Restart: Ctrl+C di terminal `bench start`, jalankan `bench start` lagi, tunggu situs hidup, baru Enter |
| 6 | Uji asap (`deployment.md` bagian 9) |
| Rollback | `P pulihkan` (perlu password root MariaDB lewat prompt tersembunyi) |

Catatan: server mencetak waktu UTC (WIB = UTC+7). Tanpa `SITE_TARGET=hris-uji.local`, sasaran `produksi_k102.sh` adalah produksi. Migrasi juga membuat tabel `HRIS Employee Pay` (kosong).
