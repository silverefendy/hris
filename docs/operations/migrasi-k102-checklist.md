# Checklist Malam Migrasi K-102 (produksi)

Diperbarui: 7 November 2026

Satu halaman untuk dibuka saat migrasi `HRIS Employee` di `erp.ciptamebel.co.id`. Penjelasan lengkap: [deployment.md](deployment.md) dan [../progress/go-live.md](../progress/go-live.md) bagian 9.

## Sebelum mulai
- [ ] Beri tahu Claude bahwa migrasi dimulai (opsional, untuk pendampingan).
- [ ] Buka dua terminal: SSH ke server dan PowerShell di PC.
- [ ] Siapkan password root MariaDB (hanya dipakai bila rollback).
- [ ] Semua perintah server dijalankan dari `/home/it/erp`.
- Catatan: `P` = `bash /home/it/runbook_k102/produksi_k102.sh`.
- Server mencetak waktu UTC (WIB = UTC+7).

## Langkah

| No | Langkah | Hasil yang diharapkan | Jika tidak cocok |
|---|---|---|---|
| 0 | `bash /home/it/runbook_k102/diag_db_k102.sh` | Employee Active sama dengan jumlah yang diharapkan (7 Nov 2026: 1078; angka dapat berubah bila HRD menambah karyawan) | **Berhenti.** Selidiki selisih sebelum lanjut |
| 1 | `P cadangan` | Berkas cadangan baru terbentuk (cadangan lebih dari 6 jam ditolak) | Berhenti bila gagal |
| 2 | Salin cadangan ke PC dengan `scp` (PowerShell), lalu `Get-FileHash` | Hash di PC sama dengan di server | Salin ulang; jangan lanjut tanpa salinan yang hash-nya cocok |
| 3 | `P siap` | Pemeriksaan lulus | Berhenti, simpan keluarannya |
| 4 | `P mulai`: jawab "ya" dua kali, lalu ketik `MULAI PRODUKSI erp.ciptamebel.co.id` | Migrasi berjalan sampai selesai | Bila berhenti dengan galat, jangan jalankan ulang; simpan keluarannya |
| 5 | Ctrl+C di terminal `bench start`, jalankan `bench start` lagi, tunggu situs hidup, baru tekan Enter di skrip | Situs terbuka normal | Tunggu lebih lama sebelum menyimpulkan gagal |
| 6 | Uji asap: [deployment.md](deployment.md) bagian 9 | Menu HRIS Employee muncul; tiga role baru ada (`HRIS Payroll Manager`, `HRIS Direksi`, `HRIS Employee Admin`) | Pertimbangkan rollback |

## Kapan berhenti dan kapan rollback
- **Berhenti (belum rollback):** langkah 0 sampai 3 tidak cocok. Produksi belum diubah.
- **Rollback:** langkah 4 atau 5 gagal, atau uji asap langkah 6 gagal. Jalankan `P pulihkan` (meminta password root MariaDB lewat prompt tersembunyi).
- Cabang produksi pada `restore` di `runbook_k102.sh` **belum terbukti**; jangan berasumsi rollback pasti mulus.

## Peringatan
- Tanpa `SITE_TARGET=hris-uji.local`, sasaran `produksi_k102.sh` adalah **produksi**. Untuk latihan, selalu isi `SITE_TARGET`.
- Cadangan 6 Nov 2026 hanya untuk gladi resik; migrasi memerlukan cadangan baru.
- Durasi tiap langkah di produksi belum diketahui (log gladi resik: `/home/it/runbook_k102/jalankan_*.txt`).
- `migrate` produksi juga membuat tabel `HRIS Employee Pay` (K-127, kosong) karena kodenya sudah ada di folder app yang sama. Ini tambahan murni; gladi resik K-102 dilakukan sebelum DocType ini ada. Setelah migrasi, role dan tabel baru ada di produksi.
- Bila ragu di tengah jalan, berhenti dan simpan keluaran terminal.

## Setelah migrasi
- [ ] Catat hasil (jumlah dibuat, jumlah berhasil, galat bila ada) di session log.
- [ ] Lanjut ke uji per peran, lihat [../progress/status.md](../progress/status.md) langkah berikutnya.
