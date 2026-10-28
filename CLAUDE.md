# CLAUDE.md — Panduan untuk AI

Baca file ini lebih dulu setiap sesi.

## Urutan baca
1. `docs/progress/status.md` — kondisi terkini + langkah berikutnya
2. `docs/decisions/README.md` — keputusan yang sudah diambil
3. `docs/progress/session-log.md` — catatan sesi terakhir
4. `docs/development/ai-workflow.md` — aturan kerja detail

## Aturan kerja (ringkas)
- Platform: custom app Frappe/ERPNext v16. HRIS mandiri (K-18): dari ERPNext/HRMS hanya `Employee` dan `Company` yang dipakai; shift, attendance, payroll, dan laporan dibuat di HRIS. Bridge hanya arah HRIS ke ERPNext (K-19), ditunda. Jangan ubah core ERPNext/HRMS; pakai hooks, custom field (berawalan `hris_`), atau override aman.
- Claude hanya boleh push file `.md`. File lain (`.py`, `.js`, `.json`, `.html`) diberikan sebagai skrip bash heredoc; Efendy yang menjalankan dan push. Sebelum Claude push `.md`, Efendy `git pull origin main` (K-17); setelah Claude push, Efendy pull lagi sebelum push berikutnya.
- Setiap skrip: tujuan, lokasi file, cara menjalankan, cara verifikasi.
- Jangan ubah struktur DocType yang sudah berjalan tanpa penjelasan risiko dan konfirmasi.
- Semua DocType, child table, dan role berawalan `HRIS ` (K-10). Penomoran `PREFIX-YYMM-NNNN`, tanpa hash (K-30).
- DocType baru mengikuti `docs/development/doctype-checklist.md`. Uji lewat skrip tidak cukup; uji juga di browser.
- Satu modul/fitur per sesi. Alur: diskusi rancangan, persetujuan, skrip, uji, perbaikan, catat di docs.
- Bahasa Indonesia; istilah teknis tetap Inggris; timestamp WIB di awal jawaban.
- Jangan menulis IP atau nama mesin internal ke dokumen.
- Akhir sesi: perbarui `docs/progress/status.md` dan `session-log.md`.
