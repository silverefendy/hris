# Keputusan 11 November 2026: Department Rule (P8, K-135, rancangan)

Status: **rancangan, belum disetujui, belum ada kode.** Nomor K-135 dipakai karena K-134 terakhir; ubah bila perlu.

## 1. Latar

`go-live.md` (P8): aturan hitung (uang) menempel ke Department lewat DocType baru (nama kerja: Department Rule) dengan tanggal berlaku. Jadwal shift tetap di Employee Group, Rotation, dan Assignment; `HRIS Shift` tetap definisi jam dan pengukuran waktu.

## 2. Jawaban Efendy (11 Nov 2026, pagi)

| # | Hal | Jawaban |
|---|---|---|
| 1 | Aturan apa yang berbeda antar Department | Belum diketahui; ditanyakan ke HRD (permintaan-ke-hrd-2026-11-10.md bagian E) |
| 2 | Karyawan dipinjam dari Department M ke O | Seluruh biaya dan gaji hari itu mengikuti aturan Department tujuan (O) |
| 3 | Penyesuaian per karyawan | Harus bisa dipilih (kustomisasi per karyawan) |
| 4 | Tanggal berlaku (Effective From) | Perlu |

## 3. Usulan urutan prioritas aturan (belum disetujui)

1. Penggantian per karyawan yang masih berlaku
2. Aturan Department tujuan pada hari itu (bila dipinjam), selain itu Department asal
3. Tidak ada aturan: perilaku bawaan saat ini

## 4. Masalah terbuka

- Field "Dipinjam untuk Grup" di `HRIS Shift Assignment` merujuk Employee Group, bukan Department. Opsi: A) tambah field Dipinjam ke Department (mengubah DocType berjalan, perlu persetujuan); B) petakan Employee Group ke satu Department (hanya benar bila satu grup selalu satu Department); C) tunda penanganan pinjam.
- Isi aturan (jenis parameter) menunggu jawaban HRD (butir E1 dan E2).
- Cek reuse: apakah baris `HRIS Employee Pay` bisa dipakai untuk penggantian per karyawan, dan apakah ERPNext atau HRMS sudah punya konsep serupa.
