# Session log 14 Nov 2026

- 3b (K-139) di-push: `307f4c2`. Uji baru OK 34 setelah perbaikan uji; regresi 40 uji SAMA.
- Tiga GAGAL awal (U1, U2, U5) adalah bug uji (pencocokan hanya berdasarkan nama, baris Manual "Bonus" ikut terhitung), bukan bug kode.
- Runner regresi awal melewatkan 13 uji (pola `^def jalankan` tidak menangkap uji yang berjalan saat di-import atau memakai alias); diperbaiki dengan pintu masuk dan berkas patokan yang sama.
- K7 (peringatan nama ganda) dipasang dan di-push: `e001a92`. Uji OK 34, 8 uji slip SAMA.
- Menjalankan ulang skrip patch yang sudah terpasang berhenti dengan aman pada pemeriksaan acuan (`ditemukan 0`); tidak ada berkas berubah.
- T2 dicatat: komponen Per Hari Hadir untuk karyawan Bulanan belum didukung; aktifkan Per Bulan atau Per Slip dulu saat go-live.
- Belum: aturan Bulanan + Per Hari Hadir, uji kecepatan 1078 karyawan, K-102, TER, PTKP, NPWP.
