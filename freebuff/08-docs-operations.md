# Rangkuman: `docs/operations`

Diperiksa: 27 November 2026.

## Berkas

| Berkas | Ukuran | Isi | Status |
|---|---|---|---|
| `deployment.md` | 11 KB | Deployment produksi + rollback (diperbarui 6 Nov) | Perlu ditambah hasil migrasi K-102 17 Nov dan migrate 20/21 Nov |
| `migrasi-k102-checklist.md` | 4,7 KB | Checklist satu halaman malam migrasi | Sudah dilaksanakan 17 Nov; belum ditandai selesai |
| `environment.md` | 2,9 KB | Lingkungan kerja: bench, site, zona waktu, tanpa IP | Sesuai |
| `panduan-hrd-periode-gaji.md` | 3,5 KB | Urutan kerja HRD tiap periode gaji (draf 11 Nov) | **Draf**, belum ditinjau HRD, belum berlaku di produksi |
| `permintaan-ke-hrd-2026-11-10.md` | 6,2 KB | Daftar data & konfirmasi ke HRD | Belum dikirim (masih tercatat di `status.md`) |
| `impor-tarif/catatan-k142-sesi4.md` | 2,9 KB | Impor CSV tarif TER & Pasal 17 | Sesuai kode |
| `impor-tarif/panduan-impor-tarif.md` | 3,0 KB | Panduan impor tarif | Sesuai, tetapi di produksi tarif masih 0 baris |
| `troubleshooting.md` | 91 B | Tabel gejala/penyebab/solusi | **Kosong** (hanya header) |
| `configuration.md` | 62 B | "Kerangka — belum diisi" | **Kosong** |
| `installation.md` | 91 B | "Kerangka — belum diisi" | **Kosong** |

## Temuan

1. Tiga dokumen operasi paling dasar (instalasi, konfigurasi, troubleshooting)
   masih kosong, padahal instalasi sudah pernah gagal sekali
   (`No module named hris.hris_cml`) dan penyebabnya belum terbukti — bahan
   troubleshooting yang bagus belum ditulis.
2. Dokumen deployment berhenti di 6 Nov; kejadian nyata sesudahnya (K-102 17 Nov,
   migrate 20 Nov, C4 21 Nov, restart bench) hanya ada di `status.md`.
3. Checklist migrasi K-102 tidak diberi penanda "selesai 17 Nov 19:50 WIB";
   orang baru bisa salah mengira migrasi belum jalan.
4. `panduan-hrd-periode-gaji.md` adalah satu-satunya dokumen untuk pengguna HRD
   dan masih berstatus draf — ini yang paling dibutuhkan saat go-live.
