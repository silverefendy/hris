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

## 4. Aturan yang sudah ada di go-live.md

| Kode | Isi |
|---|---|
| P9 | Pinjam karyawan dihitung per hari: hari dipinjam memakai aturan Department peminjam; hari lain memakai Department asal. Department yang dipakai tiap hari disimpan sebagai snapshot di Working Hour |
| P10 | Department tanpa rule pada tanggal terkait: hitungan gaji ditolak dan ada notifikasi; Readiness Check mendaftar semua kekurangan sekaligus |

## 5. Keputusan Efendy (11 Nov 2026, 06:51 WIB)

Peminjaman harus menempel ke **HRIS Department** (sumber utama), bukan ke Employee Group dan bukan ke Employee Group atau Department milik ERPNext atau HRMS. Di ERPNext hanya salinan dari HRIS Department, sama seperti HRIS Employee. Field `borrowed_for_group` (Dipinjam untuk Grup) di `HRIS Shift Assignment` kemungkinan catatan lama.

## 6. Rencana (belum disetujui, belum ada kode)

| Langkah | Isi |
|---|---|
| 1 | Tambah field Dipinjam ke Department (Link HRIS Department) di `HRIS Shift Assignment`; field lama tidak dihapus |
| 2 | Field lama disembunyikan setelah terbukti kosong dan tidak dipakai kode |
| 3 | Field lama dihapus pada perubahan terpisah |

Syarat awal: DocType HRIS Department harus ada; bila belum, dibuat lebih dulu dan keputusannya dibahas terpisah.

## 7. Masalah terbuka

- Isi aturan (jenis parameter) menunggu jawaban HRD (permintaan-ke-hrd-2026-11-10.md butir E1 dan E2).
- Cek reuse: apakah baris `HRIS Employee Pay` bisa dipakai untuk penggantian per karyawan, dan apakah ERPNext atau HRMS sudah punya konsep serupa (cek cepat di `hrms/payroll` menemukan field department pada beberapa DocType gaji, belum cukup untuk menyimpulkan).
