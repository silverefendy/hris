# Keputusan 9 November 2026: rancangan HRIS Payroll Slip (K-130)

Dasar: [keputusan-2026-11-09.md](keputusan-2026-11-09.md) (K-128, K-129). Status: **rancangan disetujui Efendy, belum ada kode.**

## K-130 Rancangan HRIS Payroll Slip

| Aspek | Keputusan |
|---|---|
| Satuan | Satu slip = satu karyawan + satu `HRIS Payroll Period`. Kunci unik karyawan + periode |
| Penomoran | `PSL-YYMM-NNNN`, tanpa hash; tab Audit Trail HRIS |
| Status | Draft, Ditinjau, Final, mengikuti status periode. Slip Final terkunci; koreksi lewat buka kembali periode |
| Cara pembuatan | Massal (semua karyawan di jadwal periode), per kelompok atau departemen, dan satu per satu. Hitung ulang hanya untuk slip Draft |
| Snapshot | Slip menyalin tarif atau gaji pokok, jenis gaji, grup, departemen, basis hari kerja, dan aturan saat dihitung, sehingga slip lama tidak berubah bila tarif berubah |
| Komponen | Baris child table: kode, jenis (Pendapatan atau Potongan), jumlah, dasar hitung, sumber (Otomatis atau Manual, manual wajib alasan) |
| Cakupan tahap pertama | Pendapatan dan potongan dasar. BPJS dan PPh 21 di sesi terpisah |
| Lembur dan telat | Diambil dari `HRIS Working Hour` (lembur kelipatan 30 menit, potongan telat per blok jam, K-35 sampai K-41) |
| Pembulatan | Rupiah penuh per komponen |
| Desain | Dirancang dari awal, tanpa mengacu slip gaji lama (tidak ada contoh slip nyata) |

### Rumus tahap pertama

| Jenis Gaji | Pendapatan | Potongan |
|---|---|---|
| Harian | hari hadir x upah harian; lembur | Potongan telat per blok jam |
| Bulanan | Gaji pokok penuh; lembur | Absen tanpa alasan jelas: gaji pokok / hari kerja x jumlah hari absen (contoh 26 hari kerja, absen 2 hari: potong 2/26); potongan telat |

### Jawaban atas pertanyaan rancangan

| # | Keputusan |
|---|---|
| A | Semua absen yang tidak jelas dicek admin HRD. Admin HRD yang menentukan apakah itu cuti, sakit, mangkir, atau lainnya |
| B | Pembagi hari kerja = hari kerja nyata per periode (dari jadwal shift) |
| C | Karyawan masuk atau keluar di tengah periode dihitung per hari kerja |
| D | Karyawan berstatus Hadir tanpa baris gaji dilewati dan dilaporkan agar ditindaklanjuti; proses massal tidak berhenti |
| E | Pembulatan rupiah penuh per komponen |

## Temuan pemeriksaan kode (9 Nov 2026) yang memengaruhi pembuatan

| Temuan | Dampak |
|---|---|
| `HRIS Working Hour.employee` menaut ke `Employee` (ERPNext), sedangkan `HRIS Employee Pay.employee` menaut ke `HRIS Employee` | Slip perlu pemetaan karyawan yang jelas antara kedua jenis ID |
| `HRIS Working Hour` belum punya field klasifikasi absen (cuti, sakit, mangkir, lainnya); hanya ada status, status tinjauan, dan catatan tinjauan | Aturan A butuh tempat mencatat keputusan HRD. Menambah field di DocType yang sudah berjalan menunggu konfirmasi Efendy |
| `HRIS Absence` belum ada | Aturan sementara sampai DocType itu dibuat |

## Belum diputuskan
- Tempat pencatatan klasifikasi absen oleh HRD (field baru di `HRIS Working Hour` atau menunggu `HRIS Absence`).
- Klasifikasi mana yang dipotong pada gaji Bulanan (usul: hanya mangkir; cuti dan sakit belum ditentukan).
- Pemetaan `HRIS Employee` ke `Employee` pada slip.
- Siapa yang menjadi HRIS Payroll Manager (tetap ditunda).
