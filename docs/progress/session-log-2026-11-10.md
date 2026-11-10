# Catatan Sesi 10 November 2026

Fokus: BPJS pada `HRIS Payroll Slip` (K-133), implementasi angka tetap, uji browser, dan uji izin per peran. Semua uji di `hris-uji.local`; belum ada di produksi.

## 1. Yang dikerjakan

| Item | Hasil |
|---|---|
| Rancangan K-133 | Disetujui Efendy (06:53 WIB). Rancangan awal memakai persentase; implementasi akhir memakai **angka tetap** per program (lihat bagian 8 [keputusan-2026-11-10-bpjs.md](../decisions/keputusan-2026-11-10-bpjs.md)) |
| Kode | Commit `f6f837b`: `hris_employee.json`, `payroll_bpjs.py`, `uji_bpjs_slip.py` (204 tambah, 27 hapus) |
| Uji skrip | OK 68 dan OK 77, GAGAL 0 |
| Uji browser slip (10:56 sampai 11:02 WIB) | Slip Bulanan: dua potongan (Kesehatan dan Ketenagakerjaan satu angka), rincian 2 baris. Slip Harian pertama: rincian 5 baris, JKK dan JKM bernilai 0 tanpa potongan. Slip Harian berikutnya pada bulan bayar yang sama: tanpa potongan BPJS dan catatan "tidak dipotong pada slip ini". Tabel Rincian BPJS tidak bisa diedit |
| Hitung Ulang (slip Harian) | Tanpa perubahan data: baris tidak berlipat. Setelah JHT, JP, JKK, JKM dinonaktifkan: potongan tersisa Kesehatan 30.000, gaji bersih 225.455 menjadi 315.455 |
| Pembersihan | `bersihkan`: sisa jadwal uji 0; nilai BPJS karyawan uji dikembalikan |
| Uji izin per peran | `uji_izin_bpjs.py` (commit `aa87b66`): HASIL OK 16, GAGAL 0. HR Admin boleh membaca dan menulis field BPJS; Payroll Admin hanya membaca dan percobaan simpan ditolak |

## 2. Keputusan

| Hal | Keputusan |
|---|---|
| Cara hitung | Angka tetap, tanpa persen (Efendy, 12:01 WIB) |
| Ketenagakerjaan | Dua cara bisa dipilih per karyawan: satu angka atau rincian JHT, JP, JKK, JKM; tidak boleh keduanya |
| Slip pembawa potongan | Sementara mengikuti implementasi berjalan (slip pertama yang tanggal bayarnya jatuh di bulan itu) sampai ada perubahan; rancangan awal menyebut slip terakhir |
| Pesan "Komponen Otomatis tidak dapat diubah..." | Berasal dari guard K-130, bukan K-133. Efendy mengikuti usulan: perbaikan tampilan (baris Otomatis abu-abu) dikerjakan sebagai fitur terpisah setelah K-133. Belum dipastikan apakah pesan muncul tanpa perubahan data |

## 3. Belum dikerjakan atau belum terbukti

- Hitung Ulang slip Bulanan dan pindah total ke rincian di browser (terbukti unit test K40 sampai K42).
- Konfirmasi HRD atas dua butir sementara.
- PPh 21 dan jembatan ke ERPNext (tahap 2 dan 3).
- Migrasi produksi K-102 tetap menunggu jadwal.
