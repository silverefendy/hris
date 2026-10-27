# Status Proyek

Diperbarui: 27 Oktober 2026

## Kondisi terkini
- App `hris` terpasang di site kerja (Frappe 16.53.0, ERPNext 16.52.1, HRMS 16.52.0).
- Lima modul: HRIS Core, HRIS Attendance, HRIS Employee Data, HRIS Payroll, HRIS Reports. Modul bawaan `hris_cml` sudah dihapus.
- Enam role HRIS dibuat otomatis lewat `after_install` dan `after_migrate` (idempoten).
- `hooks.py` memuat `required_apps = [frappe, erpnext, hrms]`.
- Belum ada DocType milik HRIS. `HRIS Settings` menyusul bersama kebutuhan nyata pertama.
- Site kerja belum production dan belum berisi data.

## Selesai
| Item | Keterangan |
|---|---|
| Struktur modul | Lima modul, `hris_cml` dihapus (commit 853d504) |
| Aturan penamaan | Semua DocType dan role wajib berawalan `HRIS ` |
| Role HRIS | Enam role, dibuat saat install/migrate (commit aa6c418) |
| `required_apps` | frappe, erpnext, hrms |
| Instal ke site kerja | Terverifikasi: enam role dan lima Module Def ada |
| Analisis repo lama | `ANALISIS_REPO_LAMA.md` dan `ANALISIS_REPO_LAMA_TAMBAHAN.md` |

## Tertunda
| Item | Catatan |
|---|---|
| CI | Diputuskan: pemicu `ci.yml` diubah dari `version-16` ke `main`. Belum diterapkan |
| Lisensi final | `license.txt` masih placeholder `[year] [fullname]`; MIT sementara |
| Pre-commit | Konfigurasi ada, hook git belum aktif |
| Navigasi | Sidebar modul dan Dock (format Frappe 16) menunggu DocType pertama |
| Judul app | "HRIS CML" masih di README, `hooks.py`, `pyproject.toml`; nama merek belum diputuskan |
| Isu ikon desk | Diparkir (lihat `operations/environment.md`) |

## Langkah berikutnya
1. Terapkan perubahan CI ke `main`.
2. Sesi kode 2: modul Attendance, mulai dari tahap diskusi `HRIS Device` dan log mentah.
3. Putuskan lisensi final dan nama merek sebelum ada kode berarti.
