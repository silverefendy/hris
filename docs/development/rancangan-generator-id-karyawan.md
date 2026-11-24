# Rancangan: Generator ID Karyawan Baru (ID Finger)

Status: rancangan, belum ada kode. Tanggal: 24 Nov 2026.

## 1. Latar Belakang

ID Finger (`attendance_device_id`) dipakai di tiga tempat dan dicocokkan sebagai **teks**: mesin absensi, Employee, dan `device_user_id` di HRIS Raw Log. `123` dan `00123` adalah dua ID berbeda, sehingga mengubah ID lama memutus pencocokan.

## 2. Fakta (dari produksi, 24 Nov 2026)

| Panjang | Jumlah | Rentang |
|---|---|---|
| 1 digit | 3 | 1 - 4 |
| 2 digit | 10 | 12 - 76 |
| 3 digit | 38 | 145 - 968 |
| 4 digit | 454 | 1111 - 9988 |
| 5 digit | 573 | 10000 - 12196 |

Total 1.078 karyawan. ID terbesar: 12196. Sebagian besar karyawan sudah ber-ID 5 digit dan sistem berjalan dengan panjang campuran.

## 3. Keputusan

| Hal | Keputusan | Sumber |
|---|---|---|
| ID lama (1-5 digit) | Tidak diubah | Efendy, 24 Nov 2026 |
| ID karyawan baru | Terbesar + 1 (bukan lebar tetap 5 digit) | Efendy, 24 Nov 2026 |
| `99901`, `99902`, `99903` | ID uji, bukan acuan produksi | Catatan sebelumnya |

## 4. Usulan (belum disetujui)

| # | Usulan | Alasan |
|---|---|---|
| U1 | Nilai terbesar dihitung dari gabungan: Employee ERPNext, HRIS Employee, dan `device_user_id` HRIS Raw Log (hanya yang murni angka), semua status karyawan termasuk resign | ID di mesin bisa lebih besar dari yang terdaftar. ID resign tidak boleh dipakai ulang (K-126 V2) |
| U2 | ID dibuat lewat tombol di form HRIS Employee baru, bukan otomatis saat simpan | Pemakai tetap melihat dan bisa menolak nomor sebelum didaftarkan ke mesin |
| U3 | Hanya HRIS Employee Admin, HRIS HR Admin, dan System Manager | Sejalan dengan siapa yang menginput karyawan baru |
| U4 | Pengambilan nomor dikunci (satu proses sekali jalan) dan tetap dicek unik saat simpan | Mencegah dua orang mengambil nomor yang sama |
| U5 | Celah angka (misalnya setelah 9988) tidak diisi ulang | Menghindari bentrok dengan ID lama di mesin |
| U6 | ID bukan angka diabaikan saat menghitung terbesar, tetapi dilaporkan jumlahnya | Hasil `cast` teks menjadi 0 menyembunyikannya |
| U7 | Setelah nomor dibuat, tampil pengingat: daftarkan ID ini di mesin | Pendaftaran di mesin tetap manual |

## 5. Pertanyaan Terbuka

1. Apakah ada ID non-angka di Employee atau di mesin? (Belum dicek.)
2. Apakah ada ID di Raw Log yang lebih besar dari 12196? (Belum dicek.)
3. Setuju U2 (tombol) atau lebih suka otomatis?
4. Nama field ID Finger di HRIS Employee perlu dibaca dari kode sebelum implementasi.

## 6. Rencana Uji (setelah disetujui)

| # | Uji | Hasil benar |
|---|---|---|
| 1 | Nomor pertama | 12197 bila data tidak berubah |
| 2 | Dua permintaan beruntun | Nomor berbeda |
| 3 | ID resign terbesar | Tetap dihitung, tidak dipakai ulang |
| 4 | ID non-angka | Diabaikan, jumlahnya dilaporkan |
| 5 | Role di luar U3 | Ditolak dengan pesan jelas |
| 6 | Regresi: ID lama 1-4 digit | Tidak berubah, pencocokan Raw Log utuh |
