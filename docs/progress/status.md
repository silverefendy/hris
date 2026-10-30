# Status Proyek

Diperbarui: 30 Oktober 2026

## Kondisi terkini
- App `hris` terpasang di site kerja `erp.ciptamebel.co.id` (Frappe 16.53.0, ERPNext 16.52.1, HRMS 16.52.0). Kode terakhir di `origin main`: `d773aeb` (Sesi 2B, jalur agen).
- Modul HRIS Attendance berisi DocType terpasang dan teruji: `HRIS Device`, `HRIS Raw Log`, `HRIS Shift`, `HRIS Employee Group` (+ tabel anak), `HRIS Holiday`, `HRIS Shift Rotation` (+ tabel anak), `HRIS Shift Assignment`, `HRIS Working Hour`, dan `HRIS Attendance Settings` (Single, baru). Custom Field dan hook validasi di `Employee` untuk grup karyawan (`hris_employee_group`).
- Service: `shift_schedule.py` (K-33), `working_hour.py` (K-35 sampai K-44), `working_hour_batch.py` (K-45), `audit_trail.py`, `employee_group.py`, serta jalur data mesin: `punch_ingest.py` dan `agent_auth.py`; endpoint `integrations/agent_api.py` ([agent-api.md](../architecture/agent-api.md)).
- **Jalur data mesin sudah diputuskan (K-46 sampai K-56, [0003](../decisions/0003-jalur-data-mesin.md)):** mesin yang tidak bisa ditarik langsung memakai agen Windows lewat endpoint `push_punches` (teruji lewat console, PowerShell, `curl`, dan browser); mesin lain akan memakai Pull pyzk (Sesi 3, belum dibuat). Agen Windows itu sendiri belum dibuat (Sesi 4).
- Tab "Audit Trail HRIS" ada di semua DocType HRIS.
- Arah arsitektur: HRIS mandiri; dari HRMS/ERPNext hanya `Employee` dan `Company` (K-18). Bridge hanya arah HRIS ke ERPNext, ditunda (K-19).
- Zona waktu site kerja: Asia/Jakarta (K-28). Catatan: jam OS server dan `logs/hris_agent.log` tampaknya UTC.
- Cara server berjalan: `bench start` (honcho) dengan `frappe serve --port 8000`, `developer_mode` menyala, tanpa nginx dan HTTPS (hanya LAN). Lihat "Sebelum produksi" di [agent-api.md](../architecture/agent-api.md).
- **Site kerja belum punya Employee Active dan Raw Log nyata.** Data uji jalur agen sudah dihapus. Semua uji working hour memakai karyawan sementara yang di-rollback.
- Data di site: 1 Company, 8 HRIS Shift aktif (Kantor, Lapangan, Security Pagi dan Malam; lihat `data-model.md`), grup nyata `Lapangan Harian` (jadwal mingguan Senin sampai Sabtu), sebagian sisa uji lama (lihat Tertunda).

## Selesai
| Item | Keterangan |
|---|---|
| Struktur modul, penamaan, enam role, `required_apps`, instal | Sesi 27 Okt (aa6c418, 853d504) |
| Analisis repo lama | `ANALISIS_REPO_LAMA.md` dan `ANALISIS_REPO_LAMA_TAMBAHAN.md` |
| Keputusan K-18 sampai K-56 | Lihat `decisions/README.md` |
| `HRIS Device`, `HRIS Raw Log` | Teruji skrip dan browser |
| `HRIS Shift` | Termasuk field aturan working hour (e1cd6f7) |
| `HRIS Employee Group`, `HRIS Holiday`, `HRIS Shift Rotation`, `HRIS Shift Assignment` | Teruji skrip dan browser |
| Service `shift_schedule` | `get_schedule_for_date`, `get_employee_schedule` (whitelisted, maks 62 hari) |
| Perbaikan temuan kode (efd88fa) | Lihat bagian Temuan |
| 5a: DocType `HRIS Working Hour` (f607a0b, f582aff) | 72 field, `unique_key` unik di database, penjaga controller (K-42), tab Audit Trail |
| 5b: service perhitungan (5230691) | 25 pemeriksaan skrip semua OK, di-rollback |
| 5c-1: hitung ulang per cakupan (523d70e) | Uji skrip T1 sampai T9 OK; tampilan browser belum diuji |
| Dugaan teknis terjawab (29 Okt) | `frappe.cache` v16 `RedisWrapper`; `frappe.db.savepoint`; antrean `long` dan worker hidup |
| Sesi 1 (30 Okt): field jalur data | Device: `use_agent`, `use_pull`, `last_agent_at`, `last_pull_at`, section Data Channels, validasi IP/port wajib (server dan browser). Raw Log: `source`, `raw_payload` (`set_only_once`). Uji console lulus |
| Sesi 2A (30 Okt): penyimpan punch dan endpoint agen | `punch_ingest.save_punches`, `agent_api.push_punches`. Uji console lulus |
| Sesi 2B (30 Okt, d773aeb): token agen | `HRIS Attendance Settings`, `agent_auth.py`, izin role agen dicabut. Uji console, PowerShell (token, saklar, GET, detak, 417, baris rusak, valid, duplikat), `curl` (daftar IP, rotasi token), dan browser (Last Agent Sync, `source`, Owner `Guest`) lulus |

## Belum teruji
- **Tampilan browser 5c-1**: tombol Hitung Periode dan Status Hitung di list view, dialog, tombol Hitung Ulang di form. Menunggu data nyata.
- **Job background sungguhan** (di atas 300 karyawan-hari lewat antrean).
- Hari `Libur` dan karyawan dengan grup pada working hour: kode ada, belum diuji dengan data.
- Shift lintas tengah malam (Security) pada data nyata; tumpang tindih jendela antar shift.
- Pencocokan Employee dan hook grup dengan karyawan nyata.
- Pengguna non-editor (Operator): penguncian form. Log Terkirim terkunci di form.
- Tampilan form `HRIS Shift` di browser setelah field baru.
- Jalur agen: Raw Payload di form belum terkonfirmasi di screenshot; batch lebih dari 500 baris dan `punches` bukan daftar baru lewat console; perilaku IP/port wajib saat "Via Pull" dicentang di browser.

## Temuan dari pembacaan kode (28 Okt) dan penyelesaiannya (29 Okt)
| # | Temuan | Penyelesaian |
|---|---|---|
| 1 | `hris_employee_group.json` memakai fieldname `schedule_section` dua kali | Selesai (efd88fa) |
| 2 | Deskripsi `weekly_schedule` usang soal rotasi | Selesai (efd88fa) |
| 3 | Dua pencarian shift mingguan | Selesai (efd88fa) |
| 4 | Service tidak mengecek rotasi nonaktif | Selesai: K-34 dan patch service |

Catatan: field `early_leave_limit_min` dihapus dari DocType `HRIS Shift` tetapi kolomnya masih ada di tabel; tidak berbahaya.

## Tertunda
| Item | Catatan |
|---|---|
| **Sesi 3: tarik log Pull pyzk** | Rancangan dibahas lebih dulu; butuh persetujuan memasang `pyzk` dan membaca `pyproject.toml` |
| Sesi 4: agen Windows | Dipecah 4a uji baca SDK, 4b skrip agen, 4c Scheduled Task; butuh endpoint konfigurasi agen |
| Sesi 5: scheduler, hitung ulang malam, impor file | Opsional; sekarang semuanya manual (K-55) |
| Perbaikan kecil Settings | `normalize_allowed_ips` hanya menimpa bila hasil berbeda; refresh form setelah Generate Token (form basi membuat Simpan berikutnya tidak berlaku); Device Model dan Firmware belum diisi di device uji |
| Sebelum produksi | `developer_mode` mati, nginx, supervisor, HTTPS, rotasi token (lihat agent-api.md) |
| `data-model.md` dan `api.md` | Belum memuat field jalur data, `HRIS Attendance Settings`, dan `push_punches`; perlu disinkronkan |
| 5c-2 | Warna list view working hour dan Report ringkasan; rancangan dibahas lebih dulu |
| Data nyata | Employee Active, `attendance_device_id`, Raw Log asli |
| Pembersihan sisa uji lama (manual) | Holiday "Merdeka" bernomor hash lama, grup "Uji Rotasi", rotasi "Rotasi Baru". Urutan hapus: grup, rotasi, Holiday. Cek dulu apakah masih ada |
| Istirahat Security | Security Pagi dan Malam masih 0 menit; menunggu aturan |
| Konfirmasi asumsi working hour | Lihat "Belum diputuskan" di `decisions/README.md` |
| Report "HRIS Audit Trail" | Ditunda atas permintaan Efendy |
| Pemetaan `verify_mode` | Menunggu data mesin nyata |
| Role `HRIS Employee Admin` | Disetujui (K-27), belum dibuat |
| CI | Pemicu `ci.yml` diubah ke `main` (K-15), belum diterapkan |
| Lisensi final, pre-commit, judul app | `license.txt` placeholder (MIT sementara); hook pre-commit belum aktif; "HRIS CML" masih di README, `hooks.py`, `pyproject.toml` |
| Navigasi | Sidebar modul dan Dock menunggu keputusan |
| Isu ikon desk | Diparkir (lihat `operations/environment.md`) |
| `docs/architecture/attendance-flow.md` dan `CLAUDE.md` | Perlu dicek dan diperbarui terhadap working hour, K-18, dan jalur data mesin |
| Penomoran | Counter `HR-EMP-` kembali ke 0 setelah data contoh dihapus (belum diverifikasi di kode Frappe); penomoran `SAS` tidak tampil di `tabSeries`, penyebab belum diketahui |

## Langkah berikutnya
1. Sesi 3: rancangan tombol "Tarik Log Sekarang" (background job, `save_punches(..., "Pull pyzk")`), lalu skrip setelah disetujui.
2. Perbaikan kecil Settings (lihat Tertunda).
3. Sesi 4: agen Windows.
4. Data nyata: Employee Active dan `attendance_device_id`, lalu Raw Log asli dari tarikan mesin; setelah itu uji browser 5c-1.
5. Sebelum produksi: lihat daftar di agent-api.md.
