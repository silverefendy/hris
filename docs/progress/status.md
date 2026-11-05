# Status Proyek

Diperbarui: 5 November 2026

## Kondisi terkini
- App `hris` terpasang di site kerja `erp.ciptamebel.co.id` (Frappe 16.53.0, ERPNext 16.52.1, HRMS 16.52.0). Kode terakhir di `origin main` per 31 Okt 2026 (malam): `92027bf` (Pull Run, riwayat Status, kosmetik `depends_on`).
- Modul HRIS Attendance berisi DocType terpasang: `HRIS Device`, `HRIS Raw Log`, `HRIS Shift`, `HRIS Employee Group` (+ tabel anak), `HRIS Holiday`, `HRIS Shift Rotation` (+ tabel anak), `HRIS Shift Assignment`, `HRIS Working Hour`, `HRIS Pull Run`, dan `HRIS Attendance Settings` (Single), serta Page `Konsol Mesin`. Custom Field dan hook validasi di `Employee` untuk grup karyawan (`hris_employee_group`).
- Service: `shift_schedule.py` (K-33), `working_hour.py` (K-35 sampai K-44), `working_hour_batch.py` (K-45), `audit_trail.py`, `employee_group.py`; jalur data mesin: `punch_ingest.py`, `agent_auth.py`, `pull_device.py`, `delete_raw_log.py`, `pull_run_log.py`, `raw_log_naming.py`; endpoint `integrations/agent_api.py` ([agent-api.md](../architecture/agent-api.md)).
- **Jalur data mesin (K-46 sampai K-77, [0003](../decisions/0003-jalur-data-mesin.md), [0004](../decisions/0004-pull-pyzk-dan-penamaan-raw-log.md)):** jalur agen (`push_punches`) teruji; jalur Pull pyzk sudah berjalan untuk mesin `PLTB 220`. Form Device dan Konsol Mesin memiliki dialog Tarik Log (Otomatis atau Rentang Tanggal, dengan Cek Dulu), Status (polling) dengan riwayat 10 terakhir, dan Hapus Raw Log. Tombol "Ambil Info dari Mesin" ada di form Device. Agen Windows sudah dibuat sebagai jendela manual dan teruji di satu PC (K-90 sampai K-93, [agen-windows.md](../development/agen-windows.md)).
- Tab "Audit Trail HRIS" ada di semua DocType HRIS.
- Arah arsitektur: HRIS mandiri; dari HRMS/ERPNext hanya `Employee` dan `Company` (K-18). Bridge hanya arah HRIS ke ERPNext, ditunda (K-19).
- Zona waktu site kerja: Asia/Jakarta (K-28). Jam OS server dan `logs/hris_agent.log` tampaknya UTC.
- Cara server berjalan: `bench start` (honcho) di terminal, `frappe serve --port 8000`, `developer_mode` menyala, tanpa nginx dan HTTPS (hanya LAN). Worker antrean aktif (1 worker, terbukti 31 Okt). Scheduler tidak aktif (`pause_scheduler` di konfigurasi).
- **Data nyata pertama:** 2.306 Raw Log `PLTB 220` untuk 25 sampai 31 Okt 2026 (sumber `Pull pyzk`, semua berstatus `Tidak Cocok`). **Belum ada Employee Active**, sehingga belum ada punch yang cocok dan belum ada working hour nyata. Semua uji working hour memakai karyawan sementara yang di-rollback. Sejak itu isi Raw Log berubah karena uji tarik dan hapus (31 Okt); lihat "Celah data tarikan" pada bagian Pembaruan 31 Okt.
- Data di site: 1 Company, 8 HRIS Shift aktif (Kantor, Lapangan, Security Pagi dan Malam; lihat `data-model.md`), grup nyata `Lapangan Harian` (jadwal mingguan Senin sampai Sabtu), sebagian sisa uji lama (lihat Tertunda).

## Selesai
| Item | Keterangan |
|---|---|
| Struktur modul, penamaan, enam role, `required_apps`, instal | Sesi 27 Okt (aa6c418, 853d504) |
| Analisis repo lama | `ANALISIS_REPO_LAMA.md` dan `ANALISIS_REPO_LAMA_TAMBAHAN.md` |
| Keputusan K-18 sampai K-77 | Lihat `decisions/README.md` |
| `HRIS Device`, `HRIS Raw Log` | Teruji skrip dan browser |
| `HRIS Shift` | Termasuk field aturan working hour (e1cd6f7) |
| `HRIS Employee Group`, `HRIS Holiday`, `HRIS Shift Rotation`, `HRIS Shift Assignment` | Teruji skrip dan browser |
| Service `shift_schedule` | `get_schedule_for_date`, `get_employee_schedule` (whitelisted, maks 62 hari) |
| Perbaikan temuan kode (efd88fa) | Lihat bagian Temuan |
| 5a: DocType `HRIS Working Hour` (f607a0b, f582aff) | 72 field, `unique_key` unik di database, penjaga controller (K-42), tab Audit Trail |
| 5b: service perhitungan (5230691) | 25 pemeriksaan skrip semua OK, di-rollback |
| 5c-1: hitung ulang per cakupan (523d70e) | Uji skrip T1 sampai T9 OK; tampilan browser belum diuji |
| Sesi 1 sampai 2B (30 Okt, d773aeb) | Field jalur data, penyimpan punch, endpoint agen, token agen; teruji console, PowerShell, `curl`, browser |
| Patch `normalize_allowed_ips` (057251c) | Lulus 3 dari 3 |
| Dependensi `pyzk>=0.9` (6e36db0) | Terpasang di env bench |
| Pull pyzk: `pull_device.py` dan tombol "Ambil Info dari Mesin" (00eba4d) | Teruji ke PLTB 220 (TCP, jam mesin sama dengan WIB) |
| Penamaan Raw Log, `punch_key`, rentang tanggal (009ff78) | K-57 sampai K-61; uji: tarikan ulang tidak menggandakan data, jalur agen menolak duplikat |
| Tarikan satu minggu PLTB 220 | 2.306 baris, 7 tanggal, nama dan `punch_key` valid; job antrean dikerjakan worker; tarikan ulang baru 0 |

## Belum teruji
- **Tampilan browser 5c-1**: tombol Hitung Periode dan Status Hitung di list view, dialog, tombol Hitung Ulang di form. Sekarang sudah ada data Raw Log, tetapi menunggu Employee.
- **Job background working hour** (di atas 300 karyawan-hari lewat antrean). Catatan: job antrean Pull terbukti jalan, tetapi itu job lain.
- Hari `Libur` dan karyawan dengan grup pada working hour: kode ada, belum diuji dengan data.
- Shift lintas tengah malam (Security) pada data nyata; tumpang tindih jendela antar shift.
- Pencocokan Employee dan hook grup dengan karyawan nyata.
- Pengguna non-editor (Operator): penguncian form. Log Terkirim terkunci di form.
- Tampilan form `HRIS Shift` di browser setelah field baru.
- Jalur agen: Raw Payload di form belum terkonfirmasi di screenshot; batch lebih dari 500 baris dan `punches` bukan daftar baru lewat console; perilaku IP/port wajib saat "Via Pull" dicentang di browser.
- Pull pyzk: waktu baca penuh log mesin belum diukur; mesin selain PLTB 220 belum dicoba.

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
| **Data Employee** | Input karyawan Active dengan `attendance_device_id`; prasyarat pencocokan 2.306 punch. Rancangan dibahas lebih dulu |
| "Cocokkan Ulang" (jalan 3) | Sesi tersendiri; mencocokkan Raw Log `Tidak Cocok` dengan Employee |
| Penjadwalan tarikan rutin | `pause_scheduler` aktif; K-55 menetapkan manual dulu |
| `device_record_no` | Ditunda (K-59); data tetap di `raw_payload` |
| Mesin `WP 221` | `pyzk` gagal "Can't connect" (kelas kode 6001); dijangkau lewat agen Windows (K-72), sesi tersendiri |
| Perilaku mesin saat penuh | Cek manual MB460; perkiraan penuh dalam 5 sampai 6 bulan (kasar) |
| Sesi 4: agen Windows | 4a uji baca SDK dan 4b skrip agen selesai (K-90 sampai K-93); 4c Scheduled Task ditunda karena penarikan dibuat manual |
| Sesi 5: scheduler, hitung ulang malam, impor file | Opsional; sekarang semuanya manual (K-55) |
| Perbaikan kecil Settings | Refresh form setelah Generate Token (form basi membuat Simpan berikutnya tidak berlaku) |
| Sebelum produksi | `developer_mode` mati, nginx, supervisor atau service pengganti `honcho` di terminal, HTTPS, rotasi token (lihat agent-api.md) |
| `data-model.md` dan `api.md` | Belum memuat field jalur data, `punch_key`, `HRIS Attendance Settings`, `push_punches`, `HRIS Pull Run`, fungsi `riwayat`, dan endpoint tarik/hapus; perlu disinkronkan |
| Docstring `punch_ingest.py` | Masih menyebut nama dokumen sebagai penjaga duplikat; perlu dirapikan |
| Cek `working_hour.py` | Query punch tampaknya per karyawan, bukan per mesin; perlu dibaca utuh |
| Status commit `hris_shift.json` dan `hris_shift.py` | Revisi 29 Okt; cek `git log` |
| 5c-2 | Warna list view working hour dan Report ringkasan; rancangan dibahas lebih dulu |
| Pembersihan sisa uji lama (manual) | Holiday "Merdeka" bernomor hash lama, grup "Uji Rotasi", rotasi "Rotasi Baru". Urutan hapus: grup, rotasi, Holiday. Cek dulu apakah masih ada |
| Istirahat Security | Security Pagi dan Malam masih 0 menit; menunggu aturan |
| Konfirmasi asumsi working hour | Lihat "Belum diputuskan" di `decisions/README.md` |
| Report "HRIS Audit Trail" | Ditunda atas permintaan Efendy |
| Pemetaan `verify_mode` | Menunggu data mesin nyata |
| Role `HRIS Employee Admin` | Dibuat di kode (K-120); di site kerja menunggu `migrate` |
| CI | Pemicu `ci.yml` diubah ke `main` (K-15), belum diterapkan |
| Lisensi final, pre-commit, judul app | `license.txt` placeholder (MIT sementara); hook pre-commit belum aktif; "HRIS CML" masih di README, `hooks.py`, `pyproject.toml` |
| Navigasi | Sidebar modul dan Dock menunggu keputusan |
| Isu ikon desk | Diparkir (lihat `operations/environment.md`) |
| `docs/architecture/attendance-flow.md` dan `CLAUDE.md` | Perlu dicek dan diperbarui terhadap working hour, K-18, jalur data mesin, dan penamaan Raw Log |
| Penomoran | Counter `HR-EMP-` kembali ke 0 setelah data contoh dihapus (belum diverifikasi di kode Frappe); penomoran `SAS` tidak tampil di `tabSeries`, penyebab belum diketahui |

## Pembaruan 31 Okt 2026 (Tarik Log, Hapus Raw Log, Konsol Mesin, Pull Run)

| Item | Status |
|---|---|
| Status tarikan polling, perlindungan autofill Comm Key | Selesai, teruji (K-67, K-68) |
| Hapus Raw Log per rentang | Selesai, teruji (K-69) |
| Dialog bersama `hris_device_actions.js` dan Konsol Mesin | Selesai, teruji (K-70, K-71). Ini juga menyelesaikan butir 3c (dialog tanggal dan tombol tarik) |
| DocType `HRIS Pull Run` (Sesi A) | Selesai, ter-push, teruji (K-73, K-74) |
| Pencatatan riwayat di `pull_device.py` dan `delete_raw_log.py` (Sesi B) | Selesai, ter-push, teruji di browser (tarik, tarik ulang, hapus) |
| Sesi C: riwayat 10 terakhir di dialog Status, penanda "tidak responsif" (K-76) | Selesai, ter-push (0d0d669), tampilan teruji. Link ke form dan "Lihat semua" serta uji akun HRIS HR Admin masih dicek |
| Kosmetik `HRIS Pull Run`: `depends_on` per jenis (K-77) | Di-commit (92027bf); tampilan di browser belum dilaporkan. Cek: `PR-2610-0008` tanpa "Jumlah Dihapus", `DR-2610-0010` hanya "Jumlah Dihapus" |
| Celah data tarikan | Tanggal 2 Okt (535 baris dihapus saat uji) belum ditarik ulang; rentang 4 s/d 19 Okt dan 21 s/d 23 Okt belum ditarik. Gunakan Cek Dulu mode Rentang Tanggal |
| Agen Windows untuk satu mesin Solution (K-72) | Selesai dan teruji di satu PC (K-90 sampai K-93). Sisa: uji PC kedua, `allowed_ips`, rotasi token, mesin Solution lain |
| Hak baca HRIS HR Admin atas HRIS Device di Konsol Mesin | Belum diverifikasi; Konsol memuat daftar mesin lewat `frappe.client.get_list`. Bila kosong untuk HR Admin, buat fungsi server khusus |
| Hak HRIS HR Admin pada status terkini | `pull_status` mensyaratkan hak write pada HRIS Device; HR Admin mungkin melihat riwayat tetapi status terkini ditolak. Belum terbukti; perbaikan satu baris bila terbukti, ubah hanya setelah konfirmasi Efendy |
| Teks "Tidak ada Raw Log di mesin dan rentang ini" | Membingungkan; ganti ke "untuk mesin dan rentang ini" saat perapian |
| Catatan penomoran | Counter Pull Run dipakai bersama (K-74); nomor mulai tidak dari 0001 karena percobaan uji |

## Pembaruan 4 sampai 5 Nov 2026 (HRIS Employee, Payroll Schedule, izin role)

Catatan: ringkasan 1 sampai 3 November (K-78 sampai K-99) belum dimasukkan ke bagian ini; lihat [decisions/README.md](../decisions/README.md).

| Item | Status |
|---|---|
| `HRIS Payroll Schedule` (K-105, K-106) | Diterapkan di site uji; 34 pemeriksaan skrip OK |
| `HRIS Employee` (K-116, `HRE-#####`) | Diterapkan di site uji; 13 pemeriksaan skrip OK |
| Tab Audit Trail dan menu Data Karyawan (K-118) | Site uji (124ec41) |
| Audit Trail menyembunyikan nilai field ber-permlevel (K-119) | 1acccd5; teruji skrip dan browser |
| Izin per peran, role `HRIS Direksi` dan `HRIS Employee Admin` (K-120) | 2a604e7; 31 pemeriksaan skrip OK di site uji. Matriks di [security/permissions.md](../security/permissions.md) |
| Status di site kerja (`erp.ciptamebel.co.id`) | Perubahan Python kemungkinan sudah aktif (folder kode sama); perubahan JSON, izin, dan role menunggu `migrate`. Belum diverifikasi |

## Langkah berikutnya
1. Periksa kondisi site kerja (DocType `HRIS Employee` dan `HRIS Payroll Schedule`, role HRIS, cara server berjalan), lalu jadwalkan `migrate`: cadangan, latihan di salinan segar, baru site kerja.
2. Uji browser per peran (petugas tarik absensi, payroll, input karyawan, Kepala HRD, Direksi) dan tarikan nyata oleh Operator.
3. Sesi 3c: sinkron `HRIS Employee` ke Employee ERPNext satu arah (K-101), lalu migrasi 1.077 Employee (K-102) diuji di site uji.
4. Fitur Dokumen Karyawan: rancangan, dan uji apakah lampiran bawaan Employee dapat dibuka role yang hanya boleh membaca dokumen (belum terbukti).
5. `HRIS Employee Pay` dan `HRIS Payroll Period` (K-108, K-109), lalu Payroll Slip.
6. Pembersihan site uji (hapus setelah migrasi aman, K-117) dan penghentian server dev port 8001 bila masih berjalan.
7. Sebelum produksi: daftar di agent-api.md. Butir daftar 31 Oktober yang belum dilaporkan selesai (tarik celah data, perapian kecil, rancangan data Employee, agen Windows, uji browser 5c-1) tetap berlaku.
