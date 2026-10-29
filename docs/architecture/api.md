# API

Diperbarui: 29 Oktober 2026. Daftar fungsi `@frappe.whitelist()` yang diekspos app `hris`, beserta cek akses.

| Fungsi | Lokasi | Parameter | Cek akses | Catatan |
|---|---|---|---|---|
| `get_audit_trail` | `hris.hris_attendance.services.audit_trail` | DocType, nama dokumen | Izin baca dokumen; hanya DocType berawalan `HRIS ` | Dipakai tab "Audit Trail HRIS"; membaca field biasa dan tabel anak |
| `get_employee_schedule` | `hris.hris_attendance.services.shift_schedule` | `employee`, `from_date`, `to_date` | `frappe.has_permission("Employee", "read", doc=employee, throw=True)` | Satu entri per hari; rentang maksimal 62 hari; tanggal sampai tidak boleh sebelum dari |
| `recalculate_working_hours` | `hris.hris_attendance.services.working_hour_batch` | `from_date`, `to_date`, `scope` (Semua, Karyawan, Department, Grup), `employee`, `department`, `employee_group`, `company`, `skip_reviewed` | Role HRIS HR Admin, HRIS Manager, atau System Manager | Maks 31 hari; sampai kemarin; hanya karyawan Active; sampai 300 karyawan-hari langsung (mode `sync`), di atasnya job background (mode `background`, mengembalikan `run_id`); ditolak bila ada proses lain aktif (K-45) |
| `get_recalc_status` | `hris.hris_attendance.services.working_hour_batch` | `run_id` (opsional; kosong = proses terakhir pengguna) | Role yang sama | Status dari cache Redis (TTL 1 jam); menyertakan `warning` bila Antre lebih dari 60 detik atau tanpa kemajuan lebih dari 120 detik |

## Hasil `get_employee_schedule` (per hari)

| Kunci | Arti |
|---|---|
| `date`, `employee`, `group` | Tanggal, karyawan, grup karyawan |
| `source` | `Shift Assignment`, `Rotasi`, `Jadwal Mingguan`, atau `Tidak ada` (K-33) |
| `shift`, `shift_detail` | Nama shift; jam mulai, jam selesai, lintas tengah malam |
| `is_off`, `is_required` | Hari libur rotasi; wajib hadir |
| `rotation`, `day_number` | Rotasi dan hari ke-n dalam siklus (bila dari rotasi) |
| `assignment`, `borrowed_for_group` | Shift Assignment pemenang dan grup peminjam (bila ada) |
| `is_holiday`, `holiday_name` | Hari libur HRIS Holiday untuk company karyawan |
| `works` | 1 bila ada shift dan (sumbernya Shift Assignment atau bukan hari libur) |

`get_schedule_for_date(employee, date)` adalah fungsi internal (tanpa cek izin) untuk satu hari; dipakai fungsi di atas dan modul working hour.

## Hasil `recalculate_working_hours`

| Kunci | Arti |
|---|---|
| `mode` | `sync` (hasil langsung) atau `background` (pantau lewat `get_recalc_status`) |
| `run_id` | Pengenal proses |
| `total`, `ok`, `failed` | Total karyawan-hari, berhasil dihitung, gagal |
| `skipped_reviewed` | Dilewati karena sudah ditinjau atau disesuaikan HRD |
| `skipped_joining` | Dilewati karena sebelum tanggal masuk karyawan |
| `errors` | Hingga 20 pesan gagal (karyawan, tanggal, alasan); detail lengkap di Error Log |

Status `get_recalc_status`: `Antre`, `Berjalan`, `Selesai`, `Gagal`, `Tidak Ada`.

## Fungsi internal (bukan whitelisted)

| Fungsi | Lokasi | Catatan |
|---|---|---|
| `calculate_working_hour(employee, day)` | `services/working_hour.py` | Hitung dan simpan satu baris `HRIS Working Hour`; idempoten lewat `unique_key` |
| `compute_day` | `services/working_hour.py` | Perhitungan murni (K-43) |
| `run_batch(run_id, params)` | `services/working_hour_batch.py` | Dijalankan worker antrean `long` |
| `ping_job(token)` | `services/working_hour_batch.py` | Uji kesehatan worker |

## Aturan
- Setiap fungsi whitelisted wajib mengecek izin dan membatasi rentang (pelajaran dari `hr_payroll`, temuan P5).
- Fungsi baru dicatat di tabel ini pada sesi yang sama.
