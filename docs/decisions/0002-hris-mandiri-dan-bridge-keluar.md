# 0002 — HRIS mandiri, HRMS hanya untuk Employee, bridge keluar ke ERPNext

- Tanggal: 28 Oktober 2026
- Status: disetujui (lisan oleh Efendy). Dicatat sebagai K-18, K-19, dan K-20 di [README](README.md).

## Konteks
Rencana awal memakai Shift Type, Attendance, dan Salary Slip HRMS lewat bridge dari HRMS ke HRIS (aturan reuse K-04). Setelah diskusi, dipilih HRIS yang mandiri agar kendali dan kelengkapan fitur ada di tangan sendiri. Site kerja belum production dan belum berisi data, sehingga tidak ada migrasi.

## Keputusan
- **K-18:** HRIS satu untuk semua. Dari HRMS/ERPNext hanya `Employee` dan `Company` yang dipakai. Shift/working hour, attendance, payroll, dan laporan dibuat di HRIS. Konsep bridge HRMS ke HRIS dan Custom Field `hris_` di Employee Checkin tidak dipakai. K-04 tetap berlaku untuk hal di luar absensi, shift, dan payroll.
- **K-19:** Hubungan ke modul di luar HRD (gaji, biaya, akuntansi) lewat bridge **arah HRIS ke HRMS/ERPNext**, berupa mapping. Kemungkinan integrasi langsung ke akun payroll/accounting ditunda sampai modul Payroll.
- **K-20:** Dokumen karyawan (perjanjian kerja, foto, KTP) dikelola di sisi HRIS; rancangan rinci (penyimpanan privat, akses terbatas, audit) di modul Employee Data.

## Alternatif yang dipertimbangkan
- Memakai HRMS penuh dengan bridge: beban kerja lebih ringan, tetapi terikat perilaku dan validasi HRMS.
- Hibrida (HRIS menentukan masuk/keluar lalu menulis ke Attendance HRMS): masih bergantung pada validasi HRMS.

## Konsekuensi
- Beban kerja lebih besar: cuti, izin, hari libur, gaji, dan pajak dibuat sendiri (cuti dan hari libur belum diputuskan).
- Tanpa Salary Slip HRMS, tidak ada jurnal gaji otomatis; keputusan akuntansi ditunda.
- Apakah `hrms` tetap menjadi `required_apps` perlu diverifikasi sebelum modul Employee Data.
- Data biometrik dan dokumen karyawan termasuk data pribadi; verifikasi ke UU PDP atau konsultan hukum sebelum modul Employee Data dan biometrik.
