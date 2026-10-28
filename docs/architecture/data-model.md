# Data Model

Status per 28 Oktober 2026: `HRIS Device` dan `HRIS Raw Log` terpasang di site kerja dan teruji; DocType lain masih rancangan.

Aturan: semua DocType HRIS berawalan `HRIS`, punya `company`, dan memakai `track_changes`. Dari ERPNext hanya `Employee` dan `Company` yang ditautkan.

## Peta modul

| Modul | DocType / objek | Status |
|---|---|---|
| HRIS Attendance | `HRIS Device` | Terpasang |
| HRIS Attendance | `HRIS Raw Log` | Terpasang |
| HRIS Attendance | Working hour/shift per kelompok, `HRIS Attendance` | Setelah Raw Log |
| HRIS Employee Data | Tambahan Employee, dokumen karyawan | Belum dirancang |
| HRIS Payroll | Komponen, formula, Payroll Run | Belum dirancang |
| HRIS Reports | Report "HRIS Audit Trail" dan laporan HRD | Belum dirancang |

## HRIS Device

| Field | Tipe | Catatan |
|---|---|---|
| `company` | Link Company | Wajib |
| `device_name` | Data | Wajib, unik, dipakai sebagai nama dokumen |
| `location` | Data | |
| `device_type` | Select | ZKTeco / Solution, wajib |
| `serial_number` | Data | Wajib dan unik (identitas mesin; kunci jalur ADMS) |
| `is_active` | Check | Default aktif |
| `comm_key` | Password | Per mesin, tersimpan terenkripsi |
| `connection_mode` | Select | Kosong (belum ditentukan), Pull (IP), Push (ADMS) |
| `ip_address` | Data | IP atau hostname; wajib jika mode Pull; format divalidasi |
| `port` | Int | Default 4370; wajib jika mode Pull; 1 sampai 65535 |
| `device_model` | Data | Opsional |
| `firmware_version` | Data | Opsional |

Field koneksi ditambahkan 28 Oktober 2026 karena mesin lama mungkin tetap memakai IP. Belum ada koneksi ke mesin; jalur data masih diparkir.

## HRIS Raw Log (terpasang)

Satu baris = satu log. Semua informasi ada di baris itu.

| Kelompok | Field | Catatan |
|---|---|---|
| Sumber | `company` (dari Device), `device`, `device_user_id` (no akun/ID user di mesin), `punch_time`, `verify_mode` (jari/wajah/dll), `punch_status_raw` | Tidak dipakai untuk logika IN/OUT |
| Karyawan | `employee`, nomor induk (diambil dari Employee) | Dicocokkan lewat `Employee.attendance_device_id`; kosong = Tidak Cocok. Arti "no akun" dan "no induk" perlu dikonfirmasi |
| Tinjauan | `review_status` (Menunggu, Tidak Cocok, Disetujui, Ditolak, Terkirim), peninjau, waktu tinjau, catatan | Per baris |
| Penanda | punch ganda (diabaikan otomatis), ID tidak dikenal, tidak cocok; telat, lembur, di luar jam shift (menyusul) | Diwarnai di list view |
| Perubahan | `change_reason` | Wajib saat field diubah |

Aturan punch ganda (otomatis, bukan pilihan HRD): jika satu karyawan punya beberapa tempelan dalam satu hari kerja, masuk = paling awal, pulang = paling akhir. Log lain ditandai diabaikan otomatis dan tidak dihapus. HRD dapat mengoreksi dengan alasan wajib. Batas "hari kerja" ditentukan modul working hour; sebelum modul itu ada, log hanya ditandai. Shift lintas tengah malam belum diputuskan.

Anti-duplikat: nama dokumen dari mesin + ID user + waktu asli (teruji: duplikat ditolak).

## Audit trail
- Sumber: Version (`track_changes`): waktu, pengguna, field, nilai lama dan baru.
- Tampilan: tab "Audit Trail HRIS" di form (terpasang) dan Report "HRIS Audit Trail" (menyusul). Waktu ditampilkan dalam WIB; `time_zone` site = `Asia/Jakarta`.

Alur data: lihat `business/process-flows/attendance-flow.md`.

## Keputusan implementasi Raw Log

- Nama dokumen dibuat dari mesin + ID user + waktu punch (script); duplikat ditolak database (teruji).
- `verify_mode` disimpan apa adanya (kode mentah). Pemetaan jari/wajah menyusul setelah jalur data dan mesin diuji.
- `punch_role` (Masuk/Pulang/Diabaikan Otomatis) dibiarkan kosong sampai modul working hour ada.
- Employee dicocokkan lewat `company` + `attendance_device_id` + status Active; jika tidak tepat satu, status Tidak Cocok.
- Mengubah field sumber hanya oleh HRIS HR Admin, HRIS Manager, atau System Manager, dengan alasan baru setiap kali. Setelah diubah, status kembali ke Menunggu/Tidak Cocok.
- Log berstatus Terkirim tidak dapat diubah.
- Operator hanya membaca dan membuat; tidak dapat mengubah log yang sudah ada.
- `company` disalin dari Device di server dan lewat `fetch_from` di form (field wajib, read-only).
- Tab "Audit Trail HRIS" di form memanggil `hris.hris_attendance.services.audit_trail.get_audit_trail`; Report audit trail menyusul.

## Catatan shift (28 Oktober 2026)

Ada shift yang melewati tengah malam, dan security punya 3 atau 4 shift. Penentuan hari kerja, jadwal per hari atau deteksi otomatis, diputuskan di modul working hour.
