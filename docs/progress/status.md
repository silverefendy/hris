# Status Proyek

Diperbarui: 28 Oktober 2026

## Kondisi terkini
- App `hris` terpasang di site kerja (Frappe 16.53.0, ERPNext 16.52.1, HRMS 16.52.0).
- Modul HRIS Attendance berisi DocType terpasang dan teruji: `HRIS Device`, `HRIS Raw Log`, `HRIS Shift`, `HRIS Employee Group` (+ tabel anak jadwal mingguan), dan `HRIS Holiday`. Custom Field dan hook validasi di `Employee` untuk grup karyawan.
- Tab "Audit Trail HRIS" ada di semua DocType HRIS; API `get_audit_trail` membaca perubahan field biasa dan tabel anak (ditambah, dihapus, diubah), teruji di v16.
- Arah arsitektur: HRIS mandiri; dari HRMS/ERPNext hanya `Employee` dan `Company` (K-18). Bridge hanya arah HRIS ke ERPNext, ditunda (K-19).
- `Department` memakai master ERPNext (K-29). Penomoran tanpa hash dengan YYMM (K-30).
- Zona waktu site kerja: Asia/Jakarta (K-28).
- Belum ada koneksi ke mesin; jalur data diparkir. Log hanya bisa masuk manual atau lewat skrip.
- Site kerja belum production.
- Kode terbaru sudah di-push ke `origin main` (fd1c1c2, 22126c0, 3efd73b).

## Selesai
| Item | Keterangan |
|---|---|
| Struktur modul, penamaan, enam role, `required_apps`, instal | Sesi 27 Okt (aa6c418, 853d504) |
| Analisis repo lama | `ANALISIS_REPO_LAMA.md` dan `ANALISIS_REPO_LAMA_TAMBAHAN.md` |
| Keputusan K-18 sampai K-30 | Lihat `decisions/README.md` |
| `HRIS Device` | 16 field, serial wajib dan unik, field koneksi, validasi IP/port, aturan Pull di controller |
| `HRIS Raw Log` | 25 field, nama anti-duplikat, pencocokan Employee, alasan ubah wajib, status tinjauan |
| `HRIS Shift` | Jam mulai/selesai, lintas tengah malam, durasi, toleransi, jendela, istirahat; detik dibulatkan ke menit (opsional, teruji) |
| `HRIS Employee Group` | Jadwal mingguan (tabel anak), department opsional, filter shift per company |
| `HRIS Holiday` | Jenis libur, centang "Berlaku untuk Semua Company", cegah tanggal dobel, penomoran `HOL-YYMM-NNNN` |
| Audit trail semua DocType HRIS | Tab di form; teruji skrip dan browser |
| Zona waktu | Asia/Jakarta |

## Belum teruji
- Pencocokan Employee dengan karyawan nyata.
- Pengguna non-editor (Operator): penguncian form.
- Log berstatus Terkirim terkunci di form.
- Hook validasi grup di `Employee` dengan data karyawan nyata.

## Tertunda
| Item | Catatan |
|---|---|
| Bagian B: rotasi dan Shift Assignment | Diskusi rancangan dulu (penomoran `SAS-YYMM-NNNN` direncanakan) |
| Data awal contoh (shift, grup, libur) | Menunggu input atau skrip |
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
1. Diskusi rancangan Bagian B: rotasi shift dan Shift Assignment (termasuk shift lintas tengah malam dan security 3 sampai 4 shift), tanpa kode.
2. Data awal contoh untuk shift, grup, dan libur.
3. Cek menu ADMS, model, dan firmware pada mesin (penentu jalur data).
4. Terapkan CI ke `main`; putuskan lisensi dan nama merek.
5. Opsional: Report "HRIS Audit Trail".
