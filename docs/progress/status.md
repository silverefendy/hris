# Status Proyek

Diperbarui: 10 November 2026

Acuan utama kesiapan go-live: [go-live.md](go-live.md).

## Kondisi terkini
- App `hris` terpasang di site kerja `erp.ciptamebel.co.id` (Frappe 16.53.0, ERPNext 16.52.1, HRMS 16.52.0). Kode terakhir di `origin main` per 31 Okt 2026 (malam): `92027bf` (Pull Run, riwayat Status, kosmetik `depends_on`). Pembaruan setelahnya: lihat bagian 4 sampai 9 November di bawah.
- Modul HRIS Attendance berisi DocType terpasang: `HRIS Device`, `HRIS Raw Log`, `HRIS Shift`, `HRIS Employee Group` (+ tabel anak), `HRIS Holiday`, `HRIS Shift Rotation` (+ tabel anak), `HRIS Shift Assignment`, `HRIS Working Hour`, `HRIS Pull Run`, dan `HRIS Attendance Settings` (Single), serta Page `Konsol Mesin`. Custom Field dan hook validasi di `Employee` untuk grup karyawan (`hris_employee_group`).
- Service: `shift_schedule.py` (K-33), `working_hour.py` (K-35 sampai K-44), `working_hour_batch.py` (K-45), `audit_trail.py`, `employee_group.py`; jalur data mesin: `punch_ingest.py`, `agent_auth.py`, `pull_device.py`, `delete_raw_log.py`, `pull_run_log.py`, `raw_log_naming.py`; endpoint `integrations/agent_api.py` ([agent-api.md](../architecture/agent-api.md)).
- **Jalur data mesin (K-46 sampai K-77, [0003](../decisions/0003-jalur-data-mesin.md), [0004](../decisions/0004-pull-pyzk-dan-penamaan-raw-log.md)):** jalur agen (`push_punches`) teruji; jalur Pull pyzk sudah berjalan untuk mesin `PLTB 220`. Form Device dan Konsol Mesin memiliki dialog Tarik Log (Otomatis atau Rentang Tanggal, dengan Cek Dulu), Status (polling) dengan riwayat 10 terakhir, dan Hapus Raw Log. Tombol "Ambil Info dari Mesin" ada di form Device. Agen Windows sudah dibuat sebagai jendela manual dan teruji di satu PC (K-90 sampai K-93, [agen-windows.md](../development/agen-windows.md)).
- Tab "Audit Trail HRIS" ada di semua DocType HRIS.
- Arah arsitektur: HRIS mandiri; dari HRMS/ERPNext hanya `Employee` dan `Company` (K-18). Bridge hanya arah HRIS ke ERPNext, ditunda (K-19).
- Zona waktu site kerja: Asia/Jakarta (K-28). Jam OS server dan `logs/hris_agent.log` tampaknya UTC.
- Cara server berjalan: `bench start` (honcho) di terminal, `frappe serve --port 8000`, `developer_mode` menyala, tanpa nginx dan HTTPS (hanya LAN). Worker antrean aktif (1 worker, terbukti 31 Okt). Scheduler tidak aktif (`pause_scheduler` di konfigurasi). Site uji `hris-uji.local` dan produksi berbagi satu bench dan satu folder app.
- **Data nyata pertama:** 2.306 Raw Log `PLTB 220` untuk 25 sampai 31 Okt 2026 (sumber `Pull pyzk`, semua berstatus `Tidak Cocok`). Catatan lama "belum ada Employee Active" sudah usang untuk Employee ERPNext: per 7 Nov 2026 produksi memiliki 1078 Employee Active (lihat Pembaruan 7 Nov). Belum ada working hour nyata; semua uji working hour memakai karyawan sementara yang di-rollback. Sejak itu isi Raw Log berubah karena uji tarik dan hapus (31 Okt); lihat "Celah data tarikan" pada bagian Pembaruan 31 Okt.
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
| `HRIS Payroll Schedule` (K-105, K-106) | Ada di site kerja dan site uji (dicek 5 Nov); 34 pemeriksaan skrip OK |
| `HRIS Employee` (K-116, `HRE-#####`) | Diterapkan di site uji; 13 pemeriksaan skrip OK |
| Tab Audit Trail dan menu Data Karyawan (K-118) | Site uji (124ec41) |
| Audit Trail menyembunyikan nilai field ber-permlevel (K-119) | 1acccd5; teruji skrip dan browser |
| Izin per peran, role `HRIS Direksi` dan `HRIS Employee Admin` (K-120) | 2a604e7; 31 pemeriksaan skrip OK di site uji. Matriks di [security/permissions.md](../security/permissions.md) |
| Status di site kerja (`erp.ciptamebel.co.id`), dicek 5 Nov | `HRIS Payroll Schedule` ada; `HRIS Employee` belum ada; role `HRIS Payroll Manager`, `HRIS Direksi`, `HRIS Employee Admin` belum ada (enam role lama ada); 1078 Employee ERPNext. Server `frappe serve` memuat ulang kode otomatis (`developer_mode` aktif), jadi perubahan Python kemungkinan sudah aktif; perubahan JSON, izin, dan role menunggu `migrate`. `pause_scheduler` aktif |

## Pembaruan 6 Nov 2026 (K-126, K-102, runbook produksi)

| Item | Status |
|---|---|
| K-126 validasi `HRIS Employee` (V1, V1b, V2, V3) | Di-push 8a16ade; teruji skrip dan browser |
| K-102 migrasi Employee ke `HRIS Employee` | Di-push 7278bb7; teruji di `hris-uji.local` (dry_run, latih, gladi resik penuh, `jalankan`: 1078 dibuat, Berhasil 1078, tabel Employee tidak berubah). **Belum dijalankan di `erp.ciptamebel.co.id`** |
| Runbook produksi | [operations/deployment.md](../operations/deployment.md); skrip di `/home/it/runbook_k102/`. `produksi_k102.sh` teruji di site uji |
| Cadangan produksi `20261106_152714` | Tersalin ke PC; sha256 cocok. Hanya untuk gladi resik: skrip menolak cadangan lebih dari 6 jam, jadi migrasi produksi memerlukan cadangan baru |
| Restart `erp` produksi | Ctrl+C lalu `bench start` lagi |
| Jadwal produksi | Belum ada; kemungkinan saat lembur (di luar jam kerja HRD) |
| Uji per peran | Setelah migrasi produksi, langsung di `erp.ciptamebel.co.id` |
| Belum terbukti | Cabang produksi pada `restore` di `runbook_k102.sh`; kebutuhan password root MariaDB di produksi. Uji tampilan D1 sampai D4 lulus (D1 dan D2 dilaporkan 6 Nov 21:24 WIB pada HRE-00274 di `hris-uji.local`: bagian Kelengkapan Data tampil; perubahan status dan catatan tercatat di Audit Trail HRIS, lalu dikembalikan) |
| Keputusan | [decisions/keputusan-2026-11-06.md](../decisions/keputusan-2026-11-06.md); catatan sesi [session-log-2026-11-06.md](session-log-2026-11-06.md) |

## Pembaruan 7 Nov 2026 (diagnosa produksi, arsip runbook, aturan lembur, HRIS Employee Pay)

| Item | Status |
|---|---|
| Diagnosa baca-saja produksi `erp.ciptamebel.co.id` | Selesai lewat `diag_db_k102.sh` dan `bench --site ... mariadb`; bagian `bench console` pada `diag_erp_k102.sh` yang tidak berkeluaran tidak lagi dibutuhkan |
| Jumlah Employee produksi | 1078 Employee, semuanya Active, `attendance_device_id` terisi dan unik pada semuanya. 1077 dibuat pada impor 1 Nov 2026, satu lagi (`HR-EMP-01078`) pada 2 Nov 2026. Efendy mengonfirmasi 1078 adalah karyawan sungguhan; impor pertama sempat tanpa nama dan sudah diperbaiki. Selisih dengan angka rencana (1.077) tuntas: rencana belum memuat karyawan tambahan itu |
| Arsip skrip runbook di repo | `scripts/operations/k102/` (c7a0f52, oleh Efendy): enam skrip, `README.md`, `.gitignore`. Pemeriksaan: tidak ada rahasia tertanam; password root dibaca lewat `read -s`. Skrip yang dipakai tetap yang di `/home/it/runbook_k102/`; salinan di repo hanya arsip |
| Aturan lembur | Sudah diputuskan: K-38 (29 Okt). Terverifikasi di kode (`working_hour.py`) dan data produksi: delapan Shift semuanya `overtime_min_minutes` = 30 dan `window_after_min` = 240, yaitu lembur maksimal 4 jam per hari; punch di luar batas ditandai untuk HRD (K-36). Menaikkan `window_after_min` bila ada lembur di atas 4 jam adalah keputusan Efendy dan HRD |
| `go-live.md` dan checklist malam migrasi | Disinkronkan; checklist satu halaman: [operations/migrasi-k102-checklist.md](../operations/migrasi-k102-checklist.md) |
| `HRIS Employee Pay` (K-127) | **Dibuat dan teruji di `hris-uji.local`** (701fc76, deb04ae): `pay_type` Bulanan atau Harian, baris gaji dikunci dan baris lama ditutup otomatis, izin per baris (Payroll Admin hanya Harian), tab Audit Trail. Uji skrip OK 30 + OK 4 + OK 5, GAGAL 0; uji browser lulus. Rancangan: [decisions/keputusan-2026-11-07.md](../decisions/keputusan-2026-11-07.md). Belum ada di produksi; tabelnya (kosong) terbentuk saat `migrate` produksi |
| Perbaikan penjaga jadwal gaji (K-105) | `validate_deactivation` di `HRIS Payroll Schedule` dulu tidak pernah aktif karena memeriksa field `is_active` yang tidak ada di Employee Pay; kini menghitung baris gaji berlaku milik karyawan Aktif (deb04ae) |
| Pelajaran teknis | Frappe 16.53: hook `has_permission` harus mengembalikan `True` bila tidak menolak; `None` dianggap menolak |
| Migrasi produksi K-102 | **Belum dijalankan.** `HRIS Employee` dan role `HRIS Payroll Manager`, `HRIS Direksi`, `HRIS Employee Admin` belum ada di produksi karena dibuat oleh `bench migrate`; menu HRIS Employee belum muncul karena itu, bukan karena galat. Langkah migrasi: [go-live.md](go-live.md) bagian 9 |

## Pembaruan 9 Nov 2026 (HRIS Payroll Period K-128, hak akses K-129)

| Item | Status |
|---|---|
| `HRIS Payroll Period` (K-128) | Dibuat dan teruji di `hris-uji.local` (9c0648a, 0ebc487, 913268f, 4807cba): alur Draft, Ditinjau, Final; penguncian Working Hour dan baris Employee Pay setelah Final; notifikasi in-app; dialog Periksa Kesiapan menampilkan semua kekurangan dengan nama. Uji skrip kesiapan OK 18, Period OK 28, regresi Working Hour OK 4, Employee Pay OK 30/4/5, GAGAL 0; uji browser per peran lulus. Belum ada di produksi |
| Hak akses (K-129) | Payroll Manager: baca, tulis, buat Jadwal Gaji (tanpa hapus; hapus hanya System Manager). Payroll Manager dan Payroll Admin: `write` pada Employee Pay. Payroll Admin hanya melihat Jenis Gaji Harian di form baru. Teruji skrip (K13 sampai K16) dan browser |
| Pembersihan data uji K-128 | Dua periode, empat baris gaji, tiga jadwal uji, dua user uji, dan notifikasinya dihapus (9 Nov); cadangan site uji diambil sebelumnya |
| Dokumen | [decisions/keputusan-2026-11-09.md](../decisions/keputusan-2026-11-09.md); catatan sesi [session-log-2026-11-09.md](session-log-2026-11-09.md) |
| Pelajaran | Uji browser per peran wajib sebelum produksi: uji skrip yang hanya memeriksa izin `create` meloloskan form kosong |
| Belum diputuskan | Siapa HRIS Payroll Manager; kombinasi Jenis Gaji dan tipe jadwal belum diperiksa; indeks `decisions/README.md` belum memuat K-127 sampai K-129 |

## Pembaruan 9 Nov 2026, sore (K-130 rancangan Payroll Slip, K-131 klasifikasi absen)

| Item | Status |
|---|---|
| Rancangan `HRIS Payroll Slip` (K-130) | Disetujui Efendy; tahap pertama kode sudah ada (lihat Pembaruan 9 Nov malam). Pembuatan slip massal, per kelompok atau departemen, dan satu per satu memakai satu layanan hitung yang sama; hitung ulang hanya untuk slip Draft; slip Final terkunci dan koreksi lewat buka kembali periode (K-128). Struktur field `HRIS Working Hour`, `HRIS Employee Pay`, `HRIS Payroll Schedule`, `HRIS Payroll Period` dan `period_lock.py` sudah dibaca untuk menyusun DocType. Dokumen: [decisions/keputusan-2026-11-09-payroll-slip.md](../decisions/keputusan-2026-11-09-payroll-slip.md) |
| Klasifikasi Absen di `HRIS Working Hour` (K-131) | Di-push 097a946. Teruji skrip (OK 33, GAGAL 0) dan browser di `hris-uji.local`, termasuk langkah 6b (Lainnya dengan catatan, Dipotong Gaji manual; 9 Nov 16:45 WIB). Hari Tidak Hadir karyawan Bulanan kini ditandai Perlu Tinjauan dan menghalangi Final sampai diklasifikasi (K-128). Belum ada di produksi |
| Aturan karyawan Harian (K-131) | Tidak Hadir karyawan Harian tidak ditandai dan tidak menghalangi Final; Tidak Lengkap tetap ditandai. Jenis gaji dibaca dari `HRIS Employee Pay` lewat `services/pay_type.py` (`pay_type_on`). Di-push 89f0c63; uji skrip OK 11, regresi klasifikasi OK 33, GAGAL 0. **Uji browser belum**: site uji belum punya baris gaji karyawan. Tanpa baris gaji, karyawan diperlakukan seperti Bulanan (ditandai) |
| Dokumen | [decisions/keputusan-2026-11-09-absen.md](../decisions/keputusan-2026-11-09-absen.md) |
| Belum diputuskan | K-132 (usul): memindahkan tautan Working Hour, Raw Log, dan Shift Assignment ke `HRIS Employee`; rancangan `HRIS Absence`; perlakuan hari Tidak Lengkap pada gaji Bulanan; pemetaan `HRIS Employee` ke `Employee` pada slip |

## Pembaruan 9 Nov 2026, malam (HRIS Payroll Slip tahap pertama)

| Item | Status |
|---|---|
| `HRIS Payroll Slip` dan `HRIS Payroll Slip Item` (K-130) | Kode di `2f483dc` (DocType, layanan hitung, tombol Buat Slip); perbaikan di `b11d89c` (kolom Alasan tampil di grid; komponen Otomatis diurutkan dulu lalu baris dinomori ulang 1..n). Uji skrip `uji_payroll_slip.py`: OK 77, GAGAL 0. Belum di produksi |
| Uji browser di `hris-uji.local` (Administrator) | Lulus: Buat Slip dua kali memperbarui, tidak menggandakan; Gaji Pokok 3.000.000 dan tarif per jam 61.855,67; kolom otomatis tidak bisa diedit; komponen Manual wajib beralasan, menambah Gaji Bersih, dan bertahan setelah Hitung Ulang; Tinjau dan Kembalikan ke Draft; slip Ditinjau terkunci; Periode yang punya slip tidak bisa dihapus |
| Potongan absen (K-131 ke slip) | Terbukti di browser: 1 hari Mangkir menghasilkan Potongan Absen Rp 500.000 (3.000.000 / 6 hari kerja x 1 hari); diubah ke Sakit dengan surat dokter, potongan hilang; hari Tidak Hadir yang belum diklasifikasi tidak dipotong dan dicatat di Catatan Perhitungan |
| Perilaku yang disengaja | Buat Slip hanya saat Periode Draft. Finalkan Periode ditolak selama ada karyawan Hadir tanpa baris gaji (aturan kesiapan K-128 berlaku global; di site uji 285 karyawan) |
| Pembersihan data uji | Slip uji dihapus lewat skrip sekali pakai (mode COBA lalu TERAPKAN, slip tersisa 0); klasifikasi absen Working Hour uji dibiarkan di site uji |
| Belum | Cakupan pembuatan slip massal, per kelompok, dan per departemen belum diuji; uji browser per peran untuk slip belum; Catatan Audit Hitung Ulang masih mencatat "baris dihapus lalu ditambah" untuk komponen yang nilainya sama (hanya bising); BPJS dan PPh 21 menyusul. Catatan sesi: [session-log-2026-11-09.md](session-log-2026-11-09.md) |

## Langkah berikutnya
1. Migrasi produksi K-102 lewat `produksi_k102.sh` saat Efendy diminta masuk di luar jam kerja (cadangan baru, `siap`, `mulai`, restart, uji asap; latihan sudah lulus di site uji). Ulangi diagnosa `diag_db_k102.sh` tepat sebelum mulai karena jumlah Employee dapat berubah. Migrasi juga membuat tabel `HRIS Employee Pay` dan `HRIS Payroll Period` (kosong); izin baru `HRIS Payroll Schedule` (K-129) perlu diverifikasi hasilnya di produksi.
2. Setelah migrasi produksi: uji browser per peran (`HRIS Employee Admin`, `HRIS Payroll Manager`, `HRIS Direksi`, petugas tarik absensi, Kepala HRD) dan tarikan nyata oleh Operator.
3. `HRIS Payroll Slip` tahap pertama selesai dan teruji (9 Nov malam); berikutnya pembuatan slip massal, per kelompok, dan per departemen, lalu `Department Rule` (P8), BPJS dan PPh 21: satu fitur per sesi, dimulai dari diskusi rancangan. `HRIS Payroll Period` sudah dibuat dan teruji (K-128, 9 Nov).
4. Fitur Dokumen Karyawan: rancangan, dan uji apakah lampiran bawaan Employee dapat dibuka role yang hanya boleh membaca dokumen (belum terbukti).
5. Pembersihan site uji (hapus setelah migrasi aman, K-117; data gaji, periode, jadwal, dan user uji K-128 sudah dibersihkan 9 Nov; sisa site uji dibersihkan setelah migrasi aman) dan penghentian server dev port 8001 bila masih berjalan.
6. Sebelum produksi: daftar di agent-api.md. Butir daftar 31 Oktober yang belum dilaporkan selesai (tarik celah data, perapian kecil, agen Windows, uji browser 5c-1) tetap berlaku.
7. Permintaan ke HRD yang belum dikirim: slip contoh, format bank, daftar laporan, aturan cut-off, potongan, cuti, saldo awal; konfirmasi Kepala HRD soal lembur x1,0 (K-98).
