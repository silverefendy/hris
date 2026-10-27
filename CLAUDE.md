# CLAUDE.md — Panduan untuk AI

Baca file ini lebih dulu setiap sesi.

## Urutan baca
1. `docs/progress/status.md` — kondisi terkini + langkah berikutnya
2. `docs/decisions/README.md` — keputusan yang sudah diambil
3. `docs/progress/session-log.md` — catatan sesi terakhir
4. `docs/development/ai-workflow.md` — aturan kerja detail

## Aturan kerja (ringkas)
- Platform: custom app Frappe/ERPNext v16, berdampingan dengan HRMS. Jangan ubah core ERPNext/HRMS; pakai hooks, custom field, atau override aman.
- Claude hanya boleh push file `.md`. File lain (`.py`, `.js`, `.json`, `.html`) diberikan sebagai skrip bash heredoc; Efendy yang menjalankan dan push.
- Setiap skrip: tujuan, lokasi file, cara menjalankan, cara verifikasi.
- Jangan ubah struktur DocType yang sudah berjalan tanpa penjelasan risiko dan konfirmasi.
- Cek dulu apakah fitur sudah ada di HRMS sebelum membuat yang baru (ada dan lengkap = pakai; tidak ada = kustom; kurang = bridge + custom).
- Satu modul/fitur per sesi. Alur: diskusi rancangan, persetujuan, skrip, uji, perbaikan, catat di docs.
- Bahasa Indonesia; istilah teknis tetap Inggris; timestamp WIB di awal jawaban.
- Jangan menulis IP atau nama mesin internal ke dokumen.
- Akhir sesi: perbarui `docs/progress/status.md` dan `session-log.md`.
