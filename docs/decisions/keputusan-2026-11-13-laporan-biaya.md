# Keputusan 13 Nov 2026: Laporan Biaya Tenaga Kerja

## 1. Ringkasan

Script Report `HRIS Biaya Tenaga Kerja` (modul HRIS Payroll, `hris/hris_payroll/report/hris_biaya_tenaga_kerja/`) menampilkan biaya tenaga kerja per Department atau Employee Group, seperti cost center. Hanya membaca data; slip tidak diubah.

## 2. Keputusan

| Butir | Isi |
|---|---|
| Akses | HRIS Payroll Manager, HRIS Direksi, System Manager |
| Filter | Payroll Period (wajib), pengelompokan, Department induk (mencakup anak lewat lft/rgt), status slip |
| Biaya | Bruto = Pendapatan slip (`total_earning`). Tanpa potongan, tanpa BPJS |
| Status | Semua status slip; porsi Draft ditampilkan di kolom Perkiraan (Draft) |
| Hari pinjam (Department) | Dibebankan ke Department tujuan (`rule_department`) |
| Hari pinjam (Grup) | Dibebankan ke Grup tujuan (`borrowed_for_group`) |
| Cara realokasi (cara A) | Total slip dipakai, lalu porsi hari pinjam dipindah. Bulanan: gaji / working_days per hari, lembur jam x gaji / jam terjadwal total x pengali. Harian: gaji per hari Hadir, lembur jam x gaji / jam terjadwal hari itu x pengali |
| Rekonsiliasi | Total laporan dibandingkan jumlah `total_earning`; selisih tampil sebagai PERINGATAN |

## 3. BPJS perusahaan (ditunda)

Angka BPJS di HRIS Employee (K-133) masuk slip sebagai Potongan (iuran karyawan). Porsi perusahaan tidak tersimpan di mana pun, jadi tidak ditampilkan. Aturan yang disepakati untuk tahap berikutnya: bila dipinjam penuh satu periode penggajian ke satu tujuan, BPJS dibebankan ke tujuan; bila ada hari bolong atau dua tujuan, ke asal. Butuh keputusan dan data porsi perusahaan lebih dulu (mengubah DocType, perlu konfirmasi).

## 4. Batasan

- Potongan (telat, pulang cepat, absen) dan komponen manual tidak direalokasi; tetap di asal.
- Bila porsi pinjam melebihi bruto slip, porsi diskalakan turun dan laporan memberi peringatan.
- Angka di pesan rekonsiliasi belum berformat ribuan.

## 5. Hasil uji

| Uji | Hasil |
|---|---|
| Jalur tanpa pinjaman (HPP-01107, di browser dan skrip) | Lulus, 3.625.000 cocok |
| `uji_biaya_laporan` (realokasi Bulanan, Department dan Grup, rollback) | OK 8, GAGAL 0 |

## 6. Belum teruji

Lembur hari pinjam, jalur Harian, filter Department induk dengan banyak Department, hak akses per peran (M4, M5), data produksi setelah K-102.
