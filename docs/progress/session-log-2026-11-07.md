# Catatan Sesi 7 November 2026

## Selesai
| Item | Hasil |
|---|---|
| Aturan lembur | Terverifikasi: K-38, kode `working_hour.py`, dan delapan Shift produksi (30 dan 240). Dua koreksi atas jawaban sebelumnya dicatat di `go-live.md` |
| Arsip runbook K-102 | Enam skrip diarsipkan di `scripts/operations/k102/` (c7a0f52); bersih dari rahasia tertanam |
| Diagnosa produksi dan selisih Employee | 1078 Employee Active, `attendance_device_id` terisi dan unik. 1077 dari impor 1 Nov, satu dari 2 Nov; dikonfirmasi karyawan sungguhan. Selisih dengan 1.077 tuntas |
| Checklist malam migrasi | `operations/migrasi-k102-checklist.md` (ab0cb1f, c739e1f) |
| `HRIS Employee Pay` (K-127) | Dibuat dan teruji di `hris-uji.local` (701fc76, deb04ae); uji skrip OK 30 + 4 + 5, GAGAL 0; uji browser lulus |
| Perbaikan penjaga jadwal gaji | `validate_deactivation` kini menghitung baris gaji berlaku milik karyawan Aktif (deb04ae) |
| Sinkron dokumen | `status.md` (491694b), `go-live.md` (c5c52f7), `keputusan-2026-11-07.md` (435e91a) |

## Temuan dan pelajaran
- Frappe 16.53: hook `has_permission` yang mengembalikan `None` dianggap menolak; harus mengembalikan `True` bila tidak menolak.
- Penjaga jadwal gaji lama tidak pernah aktif karena memeriksa field yang tidak ada di `HRIS Employee Pay`.
- Site uji dan produksi berbagi satu bench dan satu folder app. DocType baru ikut terbentuk di produksi saat `migrate` produksi; sudah dicatat di checklist dan `go-live.md`.
- Site uji memuat data gaji uji dengan nama karyawan sungguhan; masuk daftar pembersihan K-117.

## Tertunda
| Item | Catatan |
|---|---|
| Migrasi produksi K-102 | Menunggu jadwal lembur; ikut membuat tabel `HRIS Employee Pay` |
| Uji per peran dengan akun asli di produksi | Setelah migrasi produksi |
| Konfirmasi Kepala HRD soal lembur x1,0 (K-98) | Belum |
| Permintaan data ke HRD (slip contoh, format bank, daftar laporan, cut-off, potongan, cuti, saldo awal) | Belum |
| Indeks `decisions/README.md` belum memuat K-127 | Berkas besar; rapikan terpisah |
| Pembersihan site uji (K-117), Audit Trail report, K-122 sampai K-125 tidak ada di repo | Belum |

## Langkah berikutnya
1. `HRIS Payroll Period` (K-108): diskusi rancangan lebih dulu, tanpa kode.
2. Migrasi produksi K-102 saat jadwal lembur ada (ikuti checklist).
3. Setelah migrasi: uji browser per peran, lalu Payroll Slip.
