# Status Proyek

Diperbarui: 28 Oktober 2026

## Kondisi terkini
- App `hris` terpasang di site kerja (Frappe 16.53.0, ERPNext 16.52.1, HRMS 16.52.0).
- Modul HRIS Attendance berisi dua DocType terpasang dan teruji: `HRIS Device` dan `HRIS Raw Log`, ditambah API audit trail dan tab "Audit Trail HRIS" di form Raw Log.
- Arah arsitektur: HRIS mandiri; dari HRMS/ERPNext hanya `Employee` dan `Company` (K-18). Bridge hanya arah HRIS ke ERPNext, ditunda (K-19).
- Zona waktu site kerja: Asia/Jakarta (K-28).
- Belum ada koneksi ke mesin; jalur data diparkir. Log hanya bisa masuk manual atau lewat skrip.
- Site kerja belum production; data uji sudah dihapus.
- Kode Device dan Raw Log ada di server kerja; commit dan push oleh Efendy (cek `git status`).

## Selesai
| Item | Keterangan |
|---|---|
| Struktur modul, penamaan, enam role, `required_apps`, instal | Sesi 27 Okt (aa6c418, 853d504) |
| Analisis repo lama | `ANALISIS_REPO_LAMA.md` dan `ANALISIS_REPO_LAMA_TAMBAHAN.md` |
| Keputusan K-18 sampai K-28 | Lihat `decisions/README.md` |
| `HRIS Device` | 16 field, serial wajib dan unik, field koneksi, validasi IP/port, aturan Pull di controller; uji skrip lolos |
| `HRIS Raw Log` | 25 field, nama anti-duplikat, pencocokan Employee, alasan ubah wajib, status tinjauan, `fetch_from` company; uji skrip dan UI lolos |
| Audit trail | `hris.hris_attendance.services.audit_trail.get_audit_trail` dan tab di form; teruji skrip dan UI |
| Warna list view Raw Log | Teruji di UI dengan data contoh (sudah dihapus) |
| Zona waktu | Asia/Jakarta |

## Belum teruji
- Pencocokan Employee dengan karyawan nyata.
- Pengguna non-editor (Operator): penguncian form.
- Log berstatus Terkirim terkunci di form.
- Baris audit untuk perubahan Review Status (belum terlihat di hasil uji).

## Tertunda
| Item | Catatan |
|---|---|
| Report "HRIS Audit Trail" | Ditunda atas permintaan Efendy |
| Jalur data mesin | Cek menu ADMS dan model/firmware mesin lebih dulu |
| Pemetaan `verify_mode` | Menunggu jalur data dan uji mesin |
| CI | Pemicu `ci.yml` diubah ke `main` (K-15), belum diterapkan |
| Lisensi final | `license.txt` masih placeholder; MIT sementara |
| Pre-commit | Konfigurasi ada, hook git belum aktif |
| Navigasi | Sidebar modul dan Dock menunggu keputusan |
| Judul app | "HRIS CML" masih di README, `hooks.py`, `pyproject.toml` |
| Isu ikon desk | Diparkir (lihat `operations/environment.md`) |

## Langkah berikutnya
1. Efendy: commit dan push kode Device, Raw Log, audit trail, dan JS.
2. Cek menu ADMS, model, dan firmware pada mesin (penentu jalur data).
3. Sesi working hour/shift: diskusi rancangan tanpa kode (jadwal per hari atau deteksi otomatis; security 3 sampai 4 shift; shift lintas tengah malam; model grup karyawan).
4. Terapkan CI ke `main`; putuskan lisensi dan nama merek.
5. Opsional: Report "HRIS Audit Trail".
