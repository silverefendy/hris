# Keputusan 11 November 2026: HRIS Department sebagai sumber utama (K-136, arah disetujui)

Status: **arah disetujui Efendy 11 Nov 2026 (09:12 WIB); desain rinci belum disetujui; belum ada kode.** Nomor K-136 dipakai karena K-135 terakhir; ubah bila perlu.

## 1. Keputusan

HRIS Department menjadi sumber utama data Department. Department ERPNext hanya salinan (satu arah), sama seperti HRIS Employee. Penempelan aturan (Department Rule, K-135) dan peminjaman karyawan (P9) menunjuk ke HRIS Department.

## 2. Temuan (baca-saja, 11 Nov 2026)

| Temuan | Arti |
|---|---|
| DocType HRIS Department belum ada | Dibuat baru |
| Department ERPNext berbentuk pohon; satu company; nama berakhiran " - CML"; sampai tingkat kru tukang | Pohon dan nama harus dipertahankan |
| Tabel HRIS Employee belum ada di erp (K-102 belum dijalankan) | HRIS Department bisa dibuat sebelum migrasi karyawan produksi |
| HRIS Shift Assignment: 0 baris di erp dan hris-uji.local | Mengganti field pinjam tidak berisiko data |
| Tempat yang menunjuk Link ke Department ERPNext: HRIS Employee, HRIS Employee Group, HRIS Working Hour (field, daftar, laporan), HRIS Payroll Slip, dialog Payroll Period, custom field di `setup/install.py` | Penggantian target Link dilakukan sendiri dan diuji |

## 3. Urutan aman (arah disetujui)

| Tahap | Isi |
|---|---|
| 1 | Buat DocType HRIS Department (tidak menyentuh yang berjalan) |
| 2 | Salin data Department ERPNext ke HRIS Department (mode COBA dulu) |
| 3 | Sinkron HRIS Department ke Department ERPNext |
| 4 | Ganti target Link di tempat-tempat pada bagian 2 (latihan restore, seperti K-102) |
| 5 | Department Rule (K-135) dan field Dipinjam ke Department |

## 4. Jawaban Efendy (11 Nov 2026, 09:35 WIB)

| # | Hal | Jawaban |
|---|---|---|
| 1 | Pewarisan aturan lewat pohon | Aturan Department berlaku untuk semua cabang; cabang yang punya setelan sendiri memakainya; bila tidak ada, ikut induk |
| 2 | Department bawaan ERPNext | Tidak disalin dulu (hindari salah hapus). Harus diperiksa dahulu bahwa tidak ada karyawan memakainya |
| 3 | Akhiran " - CML" | Dipertahankan (ikut saran Claude) |
| 4 | Siapa mengelola Department | HRD saja (HRD dan manajernya mengurus employee); peran Payroll tidak menulis. Hak baca untuk peran Payroll perlu dikonfirmasi dan diuji |
| 5 | Kru tukang | Department mirip Employee Group untuk kru; keduanya tetap ada |

## 5. Data awal (erp, 11 Nov 2026)

178 Department (160 daun, 18 induk, 1 company); 95 dipakai oleh 1078 karyawan; 3 karyawan tanpa Department. Custom field HRIS pada Department ERPNext: `hris_device_dept_id` (kegunaan menunggu pembacaan kode).

## 6. Hasil baca ke-4 (11 Nov 2026, 09:57 WIB)

| Temuan | Keputusan |
|---|---|
| `hris_device_dept_id` hanya didefinisikan di `setup/install.py`, tidak dipakai kode | Tidak dibawa ke HRIS Department; field di Department ERPNext dibiarkan |
| 13 Department bawaan ERPNext: 0 karyawan, 0 cabang | Tidak disalin (sesuai keputusan 11 Nov) |
| 59 Department daun tanpa karyawan (bukan bawaan) | Tetap disalin; dapat dinonaktifkan nanti |
| 482 karyawan menunjuk Department induk | HRIS Department tidak membatasi karyawan hanya ke daun |
| 3 karyawan Active tanpa Department (HR-EMP-00730, HR-EMP-00856, HR-EMP-00879) | HRD mengisi Department (permintaan E7); menurut P10 gaji mereka ditolak sampai terisi |

Salinan data tahap 2: 164 Department (178 dikurangi akar dan 13 bawaan), nama dipertahankan.

## 7. Tahap 1 (DocType HRIS Department)

DocType pohon di modul Employee Data: nama `{nama} - {singkatan company}`, akar otomatis sebagai induk, induk wajib Is Group, company wajib selain akar. Izin: menulis HRIS HR Admin dan HRIS Manager; hapus System Manager; baca peran Payroll, Direksi, dan Employee Admin. Belum ada: sinkron ke Department ERPNext (tahap 3) dan tab Audit Trail HRIS (pola menunggu dibaca). Uji: `uji_hris_department.py`.

## 8. Belum diputuskan

- Bentuk pewarisan: aturan cabang menggantikan seluruh aturan induk, atau hanya parameter yang diisi cabang (tahap 5).
- Hak baca peran Payroll pada HRIS Department: dibuat membaca saja; perlu diuji pada pemilih Department.
- Cara tab Audit Trail HRIS ditambahkan.
