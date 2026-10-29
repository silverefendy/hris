# Status Proyek

Diperbarui: 29 Oktober 2026

## Kondisi terkini
- App `hris` terpasang di site kerja `erp.ciptamebel.co.id` (Frappe 16.53.0, ERPNext 16.52.1, HRMS 16.52.0). Kode terakhir di `origin main`: `523d70e` (5c-1).
- Modul HRIS Attendance berisi DocType terpasang dan teruji: `HRIS Device`, `HRIS Raw Log`, `HRIS Shift`, `HRIS Employee Group` (+ tabel anak), `HRIS Holiday`, `HRIS Shift Rotation` (+ tabel anak), `HRIS Shift Assignment`, dan `HRIS Working Hour`. Custom Field dan hook validasi di `Employee` untuk grup karyawan (`hris_employee_group`).
- Service: `shift_schedule.py` (jadwal per hari, K-33), `working_hour.py` (perhitungan, K-35 sampai K-44), `working_hour_batch.py` (hitung ulang per cakupan, status, job background, K-45), `audit_trail.py`, `employee_group.py`.
- Tab "Audit Trail HRIS" ada di semua DocType HRIS.
- Arah arsitektur: HRIS mandiri; dari HRMS/ERPNext hanya `Employee` dan `Company` (K-18). Bridge hanya arah HRIS ke ERPNext, ditunda (K-19).
- Zona waktu site kerja: Asia/Jakarta (K-28). Catatan: jam OS server tampaknya UTC.
- Belum ada koneksi ke mesin; jalur data diparkir. Log hanya bisa masuk manual atau lewat skrip.
- **Site kerja belum punya Employee Active dan Raw Log nyata.** Semua uji working hour memakai karyawan sementara yang di-rollback.
- Data di site: 1 Company, 8 HRIS Shift aktif (Kantor, Lapangan, Security Pagi dan Malam; lihat `data-model.md`), grup nyata `Lapangan Harian` (jadwal mingguan Senin sampai Sabtu), sebagian sisa uji lama (lihat Tertunda).

## Selesai
| Item | Keterangan |
|---|---|
| Struktur modul, penamaan, enam role, `required_apps`, instal | Sesi 27 Okt (aa6c418, 853d504) |
| Analisis repo lama | `ANALISIS_REPO_LAMA.md` dan `ANALISIS_REPO_LAMA_TAMBAHAN.md` |
| Keputusan K-18 sampai K-45 | Lihat `decisions/README.md` |
| `HRIS Device`, `HRIS Raw Log` | Teruji skrip dan browser |
| `HRIS Shift` | Termasuk field aturan working hour (e1cd6f7): batas terlambat, jarak minimum masuk ke pulang, lembur minimal/kelipatan, blok dan jam potongan, istirahat |
| `HRIS Employee Group`, `HRIS Holiday`, `HRIS Shift Rotation`, `HRIS Shift Assignment` | Teruji skrip dan browser; Shift Assignment 20 pemeriksaan skrip dan langkah 1 sampai 7 di browser |
| Service `shift_schedule` | `get_schedule_for_date`, `get_employee_schedule` (whitelisted, maks 62 hari) |
| Perbaikan temuan kode (efd88fa) | Lihat bagian Temuan |
| 5a: DocType `HRIS Working Hour` (f607a0b, f582aff) | 72 field, `unique_key` unik di database (terverifikasi), penjaga controller (K-42), tab Audit Trail |
| 5b: service perhitungan (5230691) | `calculate_working_hour` dan `compute_day`; 25 pemeriksaan skrip semua OK, di-rollback |
| 5c-1: hitung ulang per cakupan (523d70e) | `working_hour_batch.py`, `hris_working_hour_list.js` (tombol Hitung Periode dan Status Hitung), tombol Hitung Ulang di form. Uji skrip T1 sampai T9 semua OK (cakupan Karyawan, Semua, Department, Grup; lewati baris HRD; validasi dan role; kegagalan satu baris dibatalkan bersih dengan savepoint; status Antre ke Selesai; kunci proses ganda; peringatan macet) dan ping worker `long` merespons dalam 1 detik |
| Dugaan teknis terjawab (29 Okt) | `frappe.cache` di v16 berbentuk `RedisWrapper` dengan `set_value`/`get_value`/`delete_value`; `frappe.db.savepoint` dan `rollback(save_point=...)` bekerja; antrean `long` dan worker hidup |

## Belum teruji
- **Tampilan browser 5c-1**: tombol Hitung Periode dan Status Hitung di list view, dialog (`depends_on` per cakupan), tombol Hitung Ulang di form. Diputuskan dicek saat data nyata ada; sisi server sudah teruji skrip.
- **Job background sungguhan** (di atas 300 karyawan-hari lewat antrean): `run_batch` baru diuji dipanggil langsung; ping worker hanya membuktikan worker hidup.
- Hari `Libur` (libur nasional dan rotasi libur) dan karyawan dengan grup pada working hour: kode ada, belum diuji dengan data.
- Shift lintas tengah malam (Security) pada data nyata; tumpang tindih jendela antar shift.
- Pencocokan Employee dan hook grup dengan karyawan nyata.
- Pengguna non-editor (Operator): penguncian form. Log Terkirim terkunci di form.
- Tampilan form `HRIS Shift` di browser setelah field baru.

## Temuan dari pembacaan kode (28 Okt) dan penyelesaiannya (29 Okt)
| # | Temuan | Penyelesaian |
|---|---|---|
| 1 | `hris_employee_group.json` memakai fieldname `schedule_section` dua kali | Selesai (efd88fa): `schedule_type_section` dan `weekly_section` |
| 2 | Deskripsi `weekly_schedule` usang soal rotasi | Selesai (efd88fa) |
| 3 | Dua pencarian shift mingguan | Selesai (efd88fa): `get_shift_for_weekday` dihapus |
| 4 | Service tidak mengecek rotasi nonaktif | Selesai: K-34 (efd88fa) dan patch service melewati rotasi nonaktif |

Catatan: field `early_leave_limit_min` dihapus dari DocType `HRIS Shift` tetapi kolomnya masih ada di tabel (Frappe tidak menghapus kolom otomatis); tidak berbahaya.

## Tertunda
| Item | Catatan |
|---|---|
| 5c-2 | Warna list view working hour dan Report ringkasan per karyawan per periode; rancangan dibahas lebih dulu |
| Data nyata | Employee Active, `attendance_device_id`, Raw Log asli; jalur data mesin (cek menu ADMS, model dan firmware) |
| Pembersihan sisa uji lama (manual) | Holiday "Merdeka" bernomor hash lama (input ulang agar bernomor `HOL-YYMM-NNNN`), grup "Uji Rotasi", rotasi "Rotasi Baru". Urutan hapus: grup, rotasi, Holiday. Cek dulu apakah masih ada |
| Istirahat Security | Security Pagi dan Malam masih 0 menit; menunggu aturan |
| Konfirmasi asumsi working hour | Lihat "Belum diputuskan" di `decisions/README.md` |
| Report "HRIS Audit Trail" | Ditunda atas permintaan Efendy |
| Pemetaan `verify_mode` | Menunggu jalur data dan uji mesin |
| Role `HRIS Employee Admin` | Disetujui (K-27), belum dibuat |
| CI | Pemicu `ci.yml` diubah ke `main` (K-15), belum diterapkan |
| Lisensi final, pre-commit, judul app | `license.txt` placeholder (MIT sementara); hook pre-commit belum aktif; "HRIS CML" masih di README, `hooks.py`, `pyproject.toml` |
| Navigasi | Sidebar modul dan Dock menunggu keputusan |
| Isu ikon desk | Diparkir (lihat `operations/environment.md`) |
| `docs/architecture/attendance-flow.md` dan `CLAUDE.md` | Perlu dicek dan diperbarui terhadap working hour dan K-18 |
| Penomoran | Counter `HR-EMP-` kembali ke 0 setelah data contoh dihapus (belum diverifikasi di kode Frappe); penomoran `SAS` tidak tampil di `tabSeries`, penyebab belum diketahui |

## Langkah berikutnya
1. 5c-2: rancangan warna list view dan Report ringkasan (tanpa kode dulu), lalu skrip.
2. Data nyata: input Employee Active dan `attendance_device_id`, lalu Raw Log asli; cek menu ADMS, model, dan firmware mesin.
3. Uji browser 5c-1 dan job background sungguhan setelah data nyata ada.
4. Hapus manual sisa uji lama; putuskan istirahat Security.
5. Terapkan CI ke `main`; putuskan lisensi dan nama merek.
