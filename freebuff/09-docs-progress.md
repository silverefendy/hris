# Rangkuman: `docs/progress`

Diperiksa: 27 November 2026. Berisi status, catatan sesi, serah terima, dan
rencana go-live.

## Berkas

| Berkas | Ukuran | Isi | Status |
|---|---|---|---|
| `status.md` | 44 KB | Kondisi terkini + riwayat pembaruan 31 Okt – 21 Nov, "Belum teruji", "Tertunda", langkah berikutnya | **Sumber utama**, tetapi header masih "Diperbarui: 17 November 2026" padahal ada entri 21 Nov |
| `session-log.md` | 30 KB | Catatan sesi 27 Okt – 21 Nov | Berhenti 21 Nov; commit Device Tool 22–27 Nov tidak tercatat |
| `session-log-2026-11-01.md` … `-11-14.md` (9 berkas) | 0,3–7,6 KB | Catatan sesi per tanggal | Lengkap untuk rentangnya; **tidak ada** untuk 15–18 Nov (15 Nov ada di handoff) |
| `serah-terima-17nov2026.md` | 8,3 KB | Serah terima K-142 + perbaikan uji + alat regresi | Acuan terakhir sesi app |
| `handoff-2026-11-15.md` | 11 KB | Serah terima K-140 | — |
| `handoff-2026-10-31.md` | 7,2 KB | Serah terima sesi A/B/C | — |
| `go-live.md` | 27 KB | Rencana go-live + checklist malam migrasi | Diperbarui 10 Nov; bagian 9 sudah dilaksanakan |
| `c1-c4-tinjauan-koreksi.md` | 2,9 KB | C1 hari Tidak Lengkap, C4 tinjauan | C1 live; catatan menyebut C4 tahap 1 belum produksi (sudah usang) |
| `c4-tahap5-tampilan.md` | 2,5 KB | C4 tahap 5 (mesin hitung, tampilan) | Live di produksi 21 Nov |
| `roadmap.md` | 1,1 KB | Roadmap 28 Okt | **Usang** (belum diperbarui sejak Oktober) |

## Temuan

1. **`status.md` adalah dokumen paling padat dan paling penting**, tetapi
   bagian "Belum teruji" dan "Tertunda" sudah diberi catatan sendiri bahwa
   isinya belum diverifikasi butir demi butir sejak akhir Oktober. Jadi kondisi
   kesiapan tidak bisa dibaca langsung dari tabel itu.
2. **Dokumentasi berhenti di 21 Nov.** Commit 22–27 Nov (Device Tool 0.7.2,
   0.7.3, 0.8.0) tidak punya entri `session-log`. Yang ada hanya
   `docs/development/device-tool-0.7.2-catatan.md` (24 Nov).
3. `roadmap.md` tidak lagi mencerminkan kenyataan; semua arah sekarang ada di
   `status.md` bagian "Langkah berikutnya terkini".
4. `go-live.md` (27 KB) adalah dokumen terbesar; bagian 9 sudah dieksekusi
   tetapi belum diberi tanda hasil.

## Angka penting dari `status.md`

| Hal | Nilai |
|---|---|
| Employee produksi | 1.078 (semua Active, `attendance_device_id` terisi) |
| HRIS Employee setelah K-102 | 1.078 (17 Nov 2026) |
| Department disalin | 164 + akar |
| Raw Log pertama | 2.306 baris `PLTB 220` (25–31 Okt) |
| Regresi terakhir | SAMA 82, BEDA 0, ERROR 0 (21 Nov) |
| Patokan modul uji | 82 modul |
