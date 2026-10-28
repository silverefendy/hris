# Aturan Kerja dengan AI

- Claude hanya push file `.md`; kode lain lewat skrip bash heredoc yang dijalankan Efendy.
- Git (K-17): Efendy `git pull origin main` sebelum Claude push `.md`, dan pull lagi setelahnya sebelum push berikutnya.
- Alur per fitur: diskusi rancangan, persetujuan, skrip, uji (skrip dan browser), perbaikan, dokumentasi.
- Satu modul per sesi; ringkasan progres di akhir sesi.
- Jangan ubah DocType berjalan tanpa konfirmasi; jangan modifikasi core.
- Arah platform (K-18): HRIS mandiri; dari ERPNext/HRMS hanya `Employee` dan `Company`. Aturan lama "cek HRMS dulu, ada dan lengkap = pakai" (K-04) sudah diganti. Lihat [../architecture/platform-boundaries.md](../architecture/platform-boundaries.md).
- Skrip heredoc: tulis dengan spasi; `.py` boleh dikonversi ke tab (gaya Frappe) dengan `sed` setelah file dibuat. Kode uji di `bench console` dijalankan lewat `exec(open(file).read(), {"frappe": frappe})` dan diakhiri rollback.
- Perubahan JSON DocType: ubah `modified`, lalu backup, `migrate`, dan `clear-cache` dalam satu blok.
