# API

Diperbarui: 28 Oktober 2026. Daftar fungsi `@frappe.whitelist()` yang diekspos app `hris`, beserta cek akses.

| Fungsi | Lokasi | Parameter | Cek akses | Catatan |
|---|---|---|---|---|
| `get_audit_trail` | `hris.hris_attendance.services.audit_trail` | DocType, nama dokumen | Izin baca dokumen; hanya DocType berawalan `HRIS ` | Dipakai tab "Audit Trail HRIS"; membaca field biasa dan tabel anak |
| `get_employee_schedule` | `hris.hris_attendance.services.shift_schedule` | `employee`, `from_date`, `to_date` | `frappe.has_permission("Employee", "read", doc=employee, throw=True)` | Satu entri per hari; rentang maksimal 62 hari; tanggal sampai tidak boleh sebelum dari |

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

`get_schedule_for_date(employee, date)` adalah fungsi internal (tanpa cek izin) untuk satu hari; dipakai fungsi di atas dan modul working hour nanti.

## Aturan
- Setiap fungsi whitelisted wajib mengecek izin dan membatasi rentang (pelajaran dari `hr_payroll`, temuan P5).
- Fungsi baru dicatat di tabel ini pada sesi yang sama.
