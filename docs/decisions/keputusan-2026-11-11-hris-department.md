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

## 4. Belum diputuskan

- Pewarisan aturan lewat pohon Department (induk ke cabang).
- Department bawaan ERPNext ikut disalin atau tidak.
- Akhiran " - CML" dipertahankan atau tidak.
- Siapa yang mengelola Department (usul: HRIS HR Admin).
- Apakah kru tukang memang Department atau sebenarnya Employee Group.
