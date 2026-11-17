# K-142 Sesi 4: Impor CSV Tarif PPh 21 (TER dan Pasal 17)

Tanggal: 16 dan 17 November 2026. Site uji: `hris-uji.local`.

## 1. Keputusan

| Hal | Keputusan |
|---|---|
| DocType | `HRIS PPh21 TER Rate` dan `HRIS PPh21 Pasal17 Rate` memakai `allow_import` |
| Izin Import | Hanya **System Manager** |
| Mode impor | Data Import, Insert New Records |
| Commit | `d2f6916` (sudah di-push) |

Panduan pengguna ada di `panduan-impor-tarif.md` (bagian 6 memuat hasil uji).

## 2. Hasil Verifikasi

- Impor TER dan Pasal 17 berhasil; desimal `1,5` tersimpan 1,5%; penomoran terbentuk saat impor.
- Impor ulang berkas yang sama ditolak per baris (rentang bertumpang tindih). Baris valid tetap masuk bila sebagian baris bentrok.
- Data uji (`UJICSV`, 2030-01-01) sudah dibersihkan (sisa 0 dan 0).
- Regresi 16 November 2026: 27 modul sama dengan baseline, 0 berbeda. Modul pajak, BPJS, dan slip cocok dengan patokan.

## 3. Catatan untuk Produksi

Perubahan `allow_import` dan izin Import baru ada di `hris-uji.local`. Produksi memperolehnya saat K-102. Gladi `fase1` harus mencakup keduanya.

## 4. Temuan di Luar Lingkup K-142

Tidak ada yang menyentuh DocType TER atau Pasal 17. Perbaikan ditangani sebagai tugas terpisah.

| Uji | Hasil 16 November 2026 | Dugaan penyebab | Status bukti |
|---|---|---|---|
| `uji_hris_employee`, `uji_sinkron`, `uji_tampilan` | Berhenti dengan galat validasi | Uji lebih tua dari validasi K-122, K-123, K-126 | Dugaan |
| `uji_k102`, `uji_k126` | 2 gagal masing-masing | ID Finger 11356 kini dipegang `HRE-01097` (Aktif) | Dugaan kuat |
| `uji_bpjs_peserta` | 1 gagal (S10) | S10 menghitung enam centang termasuk PPh 21. Satu baris (HRE-00335) punya `pph21_enrolled` = 1, diubah 10 November 2026 16:54. Lima centang BPJS bernilai 0. Asal perubahan belum diketahui | Terbukti sebagian (barisnya), penyebab belum |
| `uji_izin` | 12 gagal | Bukan bug izin. Penjalan tidak memanggil `siapkan` (user uji tidak ada). Dengan `siapkan` lalu `periksa`: 15 OK, 0 GAGAL (17 November 2026) | Terbukti |

## 5. Catatan Teknis

- `bench execute` menampilkan `NameError: name 'hris' is not defined` ketika fungsi atau impor melempar galat. Itu hasil fallback `eval`; galat asli ada di atasnya.
- Beberapa berkas uji berbentuk skrip yang berjalan saat diimpor, tanpa fungsi `jalankan`.
- Jam server memakai UTC (WIB = UTC + 7).

## 6. Regresi v2 (17 November 2026)

- 67 modul uji terukur, 0 error, 0 beda. 59 modul lulus tanpa kegagalan dan disimpan sebagai patokan.
- 7 uji gagal yang sudah dikenal tetap pada angka yang sama.
- Berkas `uji_*.py` berbentuk beragam (`jalankan`, `periksa`, atau skrip). Penjalan menangani ketiganya. `uji_izin` perlu urutan `siapkan`, `periksa`, `bersihkan`.
