# Session log 14 Nov 2026

- 3b (K-139) di-push: `307f4c2`. Uji baru OK 34 setelah perbaikan uji; regresi 40 uji SAMA.
- Tiga GAGAL awal (U1, U2, U5) adalah bug uji (pencocokan hanya berdasarkan nama, baris Manual "Bonus" ikut terhitung), bukan bug kode.
- Runner regresi awal melewatkan 13 uji (pola `^def jalankan` tidak menangkap uji yang berjalan saat di-import atau memakai alias); diperbaiki dengan pintu masuk dan berkas patokan yang sama.
- K7 (peringatan nama ganda) dipasang dan di-push: `e001a92`. Uji OK 34, 8 uji slip SAMA.
- Menjalankan ulang skrip patch yang sudah terpasang berhenti dengan aman pada pemeriksaan acuan (`ditemukan 0`); tidak ada berkas berubah.
- T2 dicatat: komponen Per Hari Hadir untuk karyawan Bulanan belum didukung; aktifkan Per Bulan atau Per Slip dulu saat go-live.
- Belum: aturan Bulanan + Per Hari Hadir, uji kecepatan 1078 karyawan, K-102, TER, PTKP, NPWP.

## K-140 (14 sampai 15 Nov 2026): default tidak dapat, HEC dan HCA
- Tahap A (`d7cb11c`): default tidak dapat dan Bulanan + Per Hari Hadir. Uji murni 18 OK, regresi hijau setelah 12 uji lama diubah dengan sengaja dan pemicu galat U7 diganti.
- Tahap B (`13407ee`): tombol massal HEC. Uji browser awal tidak menampilkan hasil karena karyawan Grup Security Malam belum punya data gaji dan akun Payroll Admin hanya berhak atas Harian.
- Perubahan arah: HRD ingin penetapan per Grup, bukan per karyawan. Rancangan HCA disetujui (6 butir), lalu E1 (`75b5b60`), E2 (`f2a122f`), E3 (`adf5ef1`), E4 (`0098966`), E4b (`b84f5c1`).
- Uji browser menemukan field `company` HCA (wajib dan hanya-baca, diisi server) memblokir simpan; diperbaiki di E4b.
- Uji 3b melewati bagian database saat ada komponen aktif (diaktifkan untuk uji browser); setelah dinonaktifkan semua hijau (3b OK 34).
- Pengukuran kecepatan: C (`f111a1f`) menyesatkan (2 karyawan ber-gaji); C2 (`47783d5`) dengan gaji sintetis: Payroll Summary 1078 baris sekitar 1,0 detik; slip sekitar 22 ms per karyawan (proyeksi 24 sampai 25 detik untuk 1078).
- Belum: W6, memasukkan HCA ke K-102, K6, D3, Per Bulan pada slip mingguan, TER, PTKP, NPWP.
