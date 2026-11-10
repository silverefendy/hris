# Catatan Sesi 10 November 2026

Fokus: BPJS pada `HRIS Payroll Slip` (K-133), implementasi angka tetap, uji browser, uji izin per peran, perbaikan tampilan komponen Otomatis (lanjutan K-130), dan PPh 21 pada slip (K-134, langkah 1 sampai 4). Semua uji di `hris-uji.local`; belum ada di produksi.

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
| Dokumen K-133 | Commit `5be7572`: revisi `keputusan-2026-11-10-bpjs.md` (bagian 8), `status.md`, `go-live.md` |

## 2. Perbaikan tampilan komponen Otomatis (lanjutan K-130)

| Item | Hasil |
|---|---|
| JS awal | Commit `3498eef`: centang hapus baris Otomatis terkunci, tabel terkunci penuh bila slip bukan Draft. Uji browser: kolom baris Otomatis **belum** abu-abu (kolom inline grid dibuat malas, sehingga `toggle_editable` tidak berefek) |
| Celah server | `validate_komponen` tidak membandingkan kolom Alasan pada baris Otomatis, jadi Alasan di baris Otomatis bisa tersimpan (tercatat di Audit Trail) |
| Penjaga hapus | Uji T4b: menghapus baris Otomatis lewat centang header ditolak server dengan pesan "Komponen Otomatis tidak dapat diubah atau ditambah dengan tangan..." |
| Perbaikan | Commit `f9a6601`: `read_only_depends_on` (`eval:doc.source=='Otomatis'`) pada field komponen, jenis, jumlah, dasar, dan alasan di `HRIS Payroll Slip Item`; Sumber `read_only`; server ikut membandingkan Alasan; centang header dinonaktifkan. Hanya metadata DocType tanpa kolom baru; diterapkan di site uji lewat `reload-doc` |
| Uji | Regresi `uji_payroll_slip.py`: OK 77, GAGAL 0. Browser U1 sampai U7 lulus: semua kolom baris Otomatis abu-abu dan tidak bisa diketik, Hitung Ulang menghapus Alasan yang tersimpan sebelumnya, centang header terkunci, baris Manual tambah dan simpan dan hapus tanpa galat. Console hanya memuat galat `socket.io` 404 (polling lewat IP, K-67) dan peringatan ekstensi browser; tidak ada galat dari `hris_payroll_slip.js` |
| Jawaban pertanyaan lama | Pesan "Komponen Otomatis tidak dapat diubah..." muncul saat baris Otomatis diubah atau dihapus; menyimpan tanpa perubahan lolos (T5 dan T8). Perilaku normal, bukan bug |
| Belum tertutup | Tombol hapus di dalam form baris (dialog edit) pada slip Draft belum dikunci di tampilan; server tetap menolak saat Simpan. Event `before_components_remove` bisa dipakai bila perlu, perilakunya belum diverifikasi. Perubahan JSON baru aktif di produksi saat `migrate` K-102. Data uji slip tidak ada pembanding Harian (slip B tidak tersedia) |

## 3. Keputusan

| Hal | Keputusan |
|---|---|
| Cara hitung BPJS | Angka tetap, tanpa persen (Efendy, 12:01 WIB) |
| Ketenagakerjaan | Dua cara bisa dipilih per karyawan: satu angka atau rincian JHT, JP, JKK, JKM; tidak boleh keduanya |
| Slip pembawa potongan BPJS | Sementara mengikuti implementasi berjalan (slip pertama yang tanggal bayarnya jatuh di bulan itu) sampai ada perubahan; rancangan awal menyebut slip terakhir |
| Tampilan komponen Otomatis | Efendy mengikuti usulan (13:11 sampai 14:20 WIB): baris Otomatis abu-abu dan tidak bisa dicentang hapus, Manual tetap bisa diedit |
| PPh 21 tahap 2a | Lihat [keputusan-2026-11-10-pph21.md](../decisions/keputusan-2026-11-10-pph21.md) (K-134). Enam keputusan langkah 4 disetujui sesuai usul (bagian 5 di bawah) |

## 4. Belum dikerjakan atau belum terbukti

- Hitung Ulang slip Bulanan dan pindah total ke rincian di browser (terbukti unit test K40 sampai K42).
- Konfirmasi HRD atas dua butir sementara BPJS.
- Kunci tombol hapus di form baris (opsional).
- PPh 21 (K-134): uji izin per peran, verifikasi HRD atau pajak, tahap 2b, dan jembatan ke ERPNext (tahap 3); rincian di bagian 5.
- Merapikan sisa field rincian lama pada `validate_bpjs` (belum dicek DocType anak BPJS).
- Migrasi produksi K-102 tetap menunggu jadwal.

## 5. PPh 21 pada slip (K-134)

| Item | Hasil |
|---|---|
| Langkah 2 dan 3 | Commit `84b093c`: field PTKP dan Ikut PPh 21 di `HRIS Employee`, DocType tarif TER dan pengaturan. `uji_pph21_field.py` OK 13, `uji_pph21_rate.py` OK 32. Temuan: server tidak menegakkan wajib PTKP (validasi "Missing Fields" hanya di form) |
| Keputusan langkah 4 | Enam butir disetujui sesuai usul: rincian di Catatan Perhitungan; slip tidak lengkap dihitung dengan peringatan "N dari M slip"; data kurang melewati slip dengan pesan Masalah, Penyebab, Tindakan, Berwenang; pengaturan mati tanpa potongan dan dicatat; validasi server PTKP di `HRIS Employee`; karyawan tanpa slip terakhir di bulan itu belum terpotong (sampai tahap 2b) |
| Kode | Commit `9ad4fcf` (4 berkas, 465 tambah, 1 hapus): `services/payroll_pph21.py` (baru), patch `payroll_slip.py` (dipanggil setelah BPJS), `_cek_pph21` di controller `HRIS Employee`, `tests/uji_pph21_slip.py`. Tidak ada perubahan DocType |
| Uji skrip | `uji_pph21_slip.py` OK 22, GAGAL 0; regresi `uji_payroll_slip.py` OK 77, `uji_bpjs_slip.py` OK 68, `uji_pph21_field.py` OK 13, `uji_pph21_rate.py` OK 32 |
| Uji browser (16:39 sampai 16:42 WIB, tarif fiktif) | Hitung Ulang: PPh 21 36.250 (bruto 3.625.000, tarif 1%), gaji bersih 3.588.750. Kena Pajak satu baris Manual dimatikan: 33.000; dinyalakan lagi: 36.250. PTKP kosong: dialog Message berisi Masalah, Penyebab, Tindakan, Berwenang, slip tidak berubah. PTKP dipulihkan: 36.250. Audit Trail HRIS mencatat semua perubahan |
| Pembersihan | `bersihkan` dijalankan; setelah Hitung Ulang Slip, baris PPh 21 hilang dan angka kembali seperti sebelum uji |
| Belum terbukti | Jadwal Harian atau Mingguan dengan banyak slip pada data nyata (deteksi slip terakhir baru diuji pada satu Periode Bulanan); uji izin per peran untuk field PTKP dan Ikut PPh 21 |
| Verifikasi HRD atau pajak | Rumus TER (bruto x tarif; pemahaman Claude), tarif resmi, pemetaan PTKP, pengaruh NPWP, aturan harian atau mingguan |
