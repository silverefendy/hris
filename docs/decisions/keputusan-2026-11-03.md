# Keputusan 3 November 2026 (K-90 sampai K-93)

K-89 dipesan untuk icon aplikasi, dashboard Workspace, dan grup "Belum Dikelompokkan"; dicatat terpisah setelah pekerjaannya di-commit. Rincian teknis agen ada di [agen-windows.md](../development/agen-windows.md).

## Sudah diputuskan
| No | Keputusan | Tanggal | Status |
|---|---|---|---|
| K-90 | Agen Windows berupa jendela dengan penarikan **manual**; tidak ada penarikan terjadwal (Task Scheduler) karena PC agen tidak menyala terus. Jalur utama: **Tarik + Kirim**, log dibaca dari mesin, disimpan di memori, lalu dikirim hanya yang baru (sejak titik terakhir terkirim dikurangi satu hari). Tanpa CSV di tengah. Pengiriman batch 500, titik terakhir maju hanya bila semua permintaan sukses dan tanpa baris error. Penarikan tidak menghapus log di mesin | 2026-11-03 | Diterapkan, teruji di satu PC (log baru masuk, duplikat ditolak, error 0) |
| K-91 | Token agen dan kunci komunikasi mesin disimpan terenkripsi DPAPI di PC agen (hanya terbuka oleh pengguna Windows yang sama di PC itu) dan tidak pernah ditulis ke log. Folder agen tetap `C:\HRIS_Agen` dengan hak akses dibatasi untuk akun agen dan SYSTEM. Alamat server berupa dropdown yang bisa diketik; pengaturan non-rahasia di `config.json` | 2026-11-03 | Diterapkan, teruji (simpan, buka ulang, label "tersimpan") |
| K-92 | Data harus bisa dibedakan menurut asalnya. Setiap punch dari agen membawa objek di `raw_payload` (agen, pc, ditarik, via, dan untuk CSV `csv_sha256`), tanpa field baru. Nilai `via`: `langsung`, `csv`, `csv-diubah`. CSV tetap ada **hanya sebagai jalur cadangan** (Tarik ke CSV, Kirim dari CSV); hash dicatat saat penarikan dan dibandingkan saat kirim, bila beda muncul peringatan dan data ditandai `csv-diubah`. CSV berpassword tidak dipakai karena kuncinya harus ikut tersimpan di PC yang sama (perlindungan semu). Filter lewat `raw_payload` operator *like*. Tanda dikirim klien sehingga hanya jejak, bukan penjaga; penjaga adalah token, `allowed_ips`, dan pembandingan dengan mesin | 2026-11-03 | Diterapkan. Terbukti: `via: langsung` tersimpan dan terfilter di server; peringatan CSV tidak cocok muncul sebelum pengiriman |
| K-93 | SDK `zkemkeeper` hanya dijalankan dari proses 32-bit (x86). Semua DLL pendukung (`comms`, `rscagent`, `rscomm`, `tcpcomm`, `usbcomm`) harus satu generasi dengan `zkemkeeper.dll`; sebelum menyalin paket ke PC yang pernah memasang SDK lama, cadangkan lalu buang atribut ReadOnly dengan hak administrator, dan verifikasi hash kelimanya sama dengan paket | 2026-11-03 | Diterapkan. Terbukti: x64 gagal dan x86 berhasil; PC dengan paket bercampur gagal terhubung, setelah kelima DLL sama dengan paket koneksi berhasil |

## Belum diputuskan
- Field khusus `via` di Raw Log (perubahan struktur DocType; filter `raw_payload` dipakai dulu).
- Tanda tangan per kiriman (HMAC), butuh perubahan kode server.
- Tombol pembanding jumlah log mesin dengan HRIS, butuh endpoint baca baru di server.
- Isi `allowed_ips` untuk semua PC agen, setelah PC kedua lulus uji.
- Rotasi token dan penggantian kunci komunikasi mesin sebelum produksi.
- Lokasi skrip agen di repo dan cara memasangnya ke PC lain.
