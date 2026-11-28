# Rangkuman: Requirements, Overview, Security, Analisis Repo Lama

Diperiksa: 27 November 2026.

## `docs/requirements/`

| Berkas | Ukuran | Isi | Status |
|---|---|---|---|
| `functional-requirements.md` | 120 B | Tabel ID/Kebutuhan/Prioritas/Status | **Hanya header** — tidak ada satu pun baris kebutuhan |
| `non-functional-requirements.md` | 107 B | Tabel ID/Kebutuhan/Status | **Hanya header** |
| `requirements.md` | 128 B | "Kerangka — belum diisi" | **Kosong** |

Ini kelemahan dokumentasi yang paling struktural: tidak ada daftar kebutuhan
yang bisa dipakai untuk mengukur "selesai" selain `status.md` dan keputusan.
Praktiknya, kebutuhan hidup sebagai keputusan K-01 sampai K-142.

## `docs/overview/`

| Berkas | Ukuran | Isi | Status |
|---|---|---|---|
| `glossary.md` | 1,7 KB | Istilah: Working Hour, Raw Log, Punch, Shift, dsb. | Berguna, tetapi belum memuat istilah payroll baru (HEC, HCA, TER, Pasal 17) |
| `project-overview.md` | 250 B | "Kerangka — belum diisi" | **Kosong** — tidak ada ringkasan proyek untuk pembaca baru |

## `docs/security/`

| Berkas | Ukuran | Isi | Status |
|---|---|---|---|
| `permissions.md` | 7,3 KB | Matriks Role × Hak Akses, berlaku 5 Nov (K-118–K-121) | **Perlu ditambah** peran & izin setelah 5 Nov: Payroll Manager (K-129), Employee Admin (K-120), izin HCA/HEC (K-140), impor tarif (K-142) |

## Analisis repo lama

| Berkas | Ukuran | Isi |
|---|---|---|
| `ANALISIS_REPO_LAMA.md` | 8,3 KB | Analisis `hr_app` dan `hr_payroll` (27 Okt): struktur, tabel, temuan, keputusan tulis ulang |
| `ANALISIS_REPO_LAMA_TAMBAHAN.md` | 3,4 KB | Tambahan analisis |

Keduanya dokumen historis; keputusan turunannya ada di K-08 (tulis ulang, tidak
membawa patch lama).

## Temuan

1. `project-overview.md` kosong padahal `CLAUDE.md` menyuruh membaca dokumen
   status lebih dulu. Pembaca baru tidak punya ringkasan "ini apa".
2. `functional-requirements.md` kosong membuat tidak ada dasar formal untuk
   menyatakan sebuah fitur "selesai"; yang dipakai adalah hasil uji.
3. `permissions.md` tertinggal sekitar tiga minggu dari kode — berisiko bila
   dipakai sebagai acuan uji per peran di produksi.
