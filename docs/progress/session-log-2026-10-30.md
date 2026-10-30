# Session Log: 30 Oktober 2026 (jalur data mesin, Sesi 1 sampai 2B)

Catatan: entri ini dipisah dari `session-log.md` agar tidak menimpa riwayat; gabungkan bila diinginkan.

## Ringkasan
- Arah jalur data diputuskan (29 sampai 30 Okt): semua mesin lewat middleware seperti mesin Solution, Pull pyzk tetap diimplementasikan, satu mesin boleh lebih dari satu jalur. Rinci di [0003](../decisions/0003-jalur-data-mesin.md) (K-46 sampai K-56).
- Sesi 1: field jalur data di `HRIS Device` dan `HRIS Raw Log`, validasi IP/port wajib bersyarat. Uji console lulus.
- Sesi 2A: `punch_ingest.save_punches` dan endpoint `push_punches`. Uji console lulus.
- Sesi 2B (d773aeb): token buatan sendiri di `HRIS Attendance Settings`, `agent_auth.py`, izin role agen dicabut. Uji console lulus.
- Uji HTTP, `curl`, dan browser lulus (ringkasan di [agent-api.md](../architecture/agent-api.md)). Data uji dihapus.

## Kendala dan pelajaran
- Uji PowerShell pertama gagal: skrip ber-`Read-Host` ditempel ke konsol dan baris berikutnya tertelan. Solusi: file `.ps1` lewat here-string.
- Uji kedua gagal 13 dari 13: `-Base` memakai alamat mesin absensi, bukan server ERP. Skrip versi 2 memeriksa `/api/method/ping` lebih dulu.
- Uji ketiga 10 lulus, 4 gagal: urutan di browser tidak sesuai (saklar belum tersimpan, Allowed IPs dan rotasi belum tersimpan saat Enter ditekan). Log `hris_agent.log` menunjukkan `saklar mati` dan `diblokir`, bukan kesalahan token. Pembatas 10 kegagalan per 10 menit ikut memblokir IP PC saat uji beruntun.
- Pemeriksaan status lewat skrip baca-saja (`agent_enabled`, prefix, `modified`) membedakan "saklar tidak tersimpan" dari "token salah".
- Blok heredoc panjang yang ditempel kehilangan baris `cat > ... <<'EOF'`, sehingga isi Python dijalankan sebagai perintah bash. Pecah menjadi langkah pendek.
- Token sempat tampil di chat (diketik di teks prompt `read -p`, dan ditempel di chat). Token dirotasi setelah uji.
- Temuan teknis: `mandatory_depends_on` hanya dievaluasi di browser; `set_only_once` ditegakkan server; `modified` JSON harus dinaikkan agar `migrate` mengenali perubahan; mencabut izin dilakukan dengan menghapus entri dan menaikkan `modified`.
- Server berjalan dengan `bench start` (tanpa nginx dan HTTPS); web dimuat ulang otomatis, worker tidak.

## Belum
- Sesi 3 (Pull pyzk), Sesi 4 (agen Windows), data nyata, perbaikan kecil Settings, sinkronisasi `data-model.md` dan `api.md`.
