# Data Model

Status per 28 Oktober 2026 (malam): `HRIS Device`, `HRIS Raw Log`, `HRIS Shift`, `HRIS Employee Group`, `HRIS Shift Rotation`, `HRIS Holiday`, dan `HRIS Shift Assignment` terpasang di site kerja dan teruji skrip. Form Shift Assignment belum diuji di browser. DocType lain masih rancangan.

Aturan: semua DocType HRIS berawalan `HRIS`, punya `company`, dan memakai `track_changes`. Dari ERPNext hanya `Employee` dan `Company` yang ditautkan (`Department` lewat Employee, K-29).

## Peta modul

| Modul | DocType / objek | Status |
|---|---|---|
| HRIS Attendance | `HRIS Device` | Terpasang |
| HRIS Attendance | `HRIS Raw Log` | Terpasang |
| HRIS Attendance | `HRIS Shift`, `HRIS Employee Group` (+ `HRIS Employee Group Day`), `HRIS Holiday` | Terpasang |
| HRIS Attendance | `HRIS Shift Rotation` (+ `HRIS Shift Rotation Day`), `HRIS Shift Assignment` | Terpasang |
| HRIS Attendance | Working hour, `HRIS Attendance` | Berikutnya |
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

Aturan punch ganda (otomatis, bukan pilihan HRD): jika satu karyawan punya beberapa tempelan dalam satu hari kerja, masuk = paling awal, pulang = paling akhir. Log lain ditandai diabaikan otomatis dan tidak dihapus. HRD dapat mengoreksi dengan alasan wajib. Batas "hari kerja" ditentukan modul working hour; sebelum modul itu ada, log hanya ditandai. Shift lintas tengah malam belum diputuskan untuk Raw Log.

Anti-duplikat: nama dokumen dari mesin + ID user + waktu asli (teruji: duplikat ditolak).

## HRIS Shift

Nama dokumen = `shift_name` (unik, boleh di-rename).

| Field | Tipe | Catatan |
|---|---|---|
| `shift_name` | Data | Wajib, unik |
| `company` | Link Company | Wajib |
| `is_active` | Check | Default aktif |
| `start_time`, `end_time` | Time | Wajib; detik dibulatkan ke menit |
| `crosses_midnight` | Check | Read-only, dihitung otomatis (selesai lebih awal dari mulai) |
| `duration_minutes` | Int | Read-only, dihitung otomatis |
| `late_tolerance_min`, `early_leave_tolerance_min` | Int | Toleransi telat dan pulang cepat; default 0 |
| `window_before_min` | Int | Jendela tempel masuk sebelum jam mulai; default 120 |
| `window_after_min` | Int | Jendela tempel pulang sesudah jam selesai, sekaligus batas lembur; default 240 |
| `break_minutes` | Int | Istirahat; default 0 |

## HRIS Employee Group

Nama dokumen = `group_name` (unik, boleh di-rename). Anggota ditentukan lewat Custom Field `hris_employee_group` (Link) di `Employee`, dengan hook validasi.

| Field | Tipe | Catatan |
|---|---|---|
| `group_name` | Data | Wajib, unik |
| `company` | Link Company | Wajib |
| `department` | Link Department | Opsional; harus satu company dengan grup |
| `is_active` | Check | Grup nonaktif tidak menghasilkan jadwal |
| `schedule_type` | Select | `Jadwal Mingguan` (default) atau `Rotasi`; tidak bercampur (K-31) |
| `rotation` | Link HRIS Shift Rotation | Wajib bila Rotasi; harus aktif dan satu company; dikosongkan bila Jadwal Mingguan |
| `rotation_start_date` | Date | Wajib bila Rotasi; tanggal hari ke-1 siklus |
| `weekly_schedule` | Tabel `HRIS Employee Group Day` | Dikosongkan bila Rotasi |

Tabel anak `HRIS Employee Group Day`: `day_from`, `day_to`, `shift`, `is_required`. Aturan: satu baris untuk satu hari atau rentang; rentang tidak boleh melewati hari Minggu (pisahkan jadi dua baris); tidak boleh ada hari ganda antarbaris; shift harus aktif dan satu company; baris tanpa shift otomatis `is_required` = 0; hari yang tidak terdaftar dianggap libur.

## HRIS Shift Rotation

Nama dokumen = `rotation_name` (unik, boleh di-rename).

| Field | Tipe | Catatan |
|---|---|---|
| `rotation_name` | Data | Wajib, unik |
| `company` | Link Company | Wajib |
| `is_active` | Check | Default aktif |
| `cycle_days` | Int | Read-only; jumlah baris pola |
| `description` | Small Text | Opsional |
| `pattern` | Tabel `HRIS Shift Rotation Day` | Wajib |

Tabel anak `HRIS Shift Rotation Day`: `day_number` (otomatis), `is_off` (Libur), `shift`. Aturan: baris libur mengosongkan shift; baris non-libur wajib shift dan satu company dengan rotasi; pola tidak boleh libur semua. **Pola dan company dikunci bila rotasi sudah dipakai grup**; ubah dengan membuat rotasi baru lalu memindahkan grupnya (jadwal lama tidak boleh ikut bergeser).

Contoh siklus security tiga shift: Pagi, Malam, Libur (panjang siklus 3). Hari ke-n = (tanggal - tanggal mulai) mod 3, dihitung dari 0.

## HRIS Holiday

Penomoran `HOL-YYMM-NNNN` (K-30).

| Field | Tipe | Catatan |
|---|---|---|
| `holiday_date` | Date | Wajib; tanggal ganda dicegah |
| `holiday_name` | Data | Wajib |
| `holiday_type` | Select | Nasional, Cuti Bersama, Khusus Perusahaan |
| `applies_to_all_companies` | Check | Default aktif; matikan untuk libur satu company |
| `company` | Link Company | Diisi hanya bila tidak berlaku untuk semua company |

## HRIS Shift Assignment

Penomoran `SAS-YYMM-NNNN` (K-30, K-32). Tanpa approval. Dibatalkan dengan mematikan centang Aktif.

| Field | Tipe | Catatan |
|---|---|---|
| `employee` | Link Employee | Wajib; harus Active |
| `employee_name`, `company` | Data, Link Company | Read-only; diisi dari Employee di server |
| `is_active` | Check | Default aktif |
| `from_date`, `to_date` | Date | Wajib; tanggal sampai tidak sebelum dari; tanggal sampai terisi otomatis di form |
| `shift` | Link HRIS Shift | Wajib; aktif dan satu company dengan karyawan |
| `reason` | Small Text | Wajib (di-trim) |
| `borrowed_for_group` | Link HRIS Employee Group | Opsional; grup harus aktif |

Anti tumpang tindih: karyawan yang sama tidak boleh punya dua Assignment aktif yang rentang tanggalnya beririsan.

## Penentuan shift per hari (service `shift_schedule`)

Jawaban untuk "karyawan X pada tanggal Y masuk shift apa" (K-33). Dihitung saat dibutuhkan, tidak disimpan per hari.

| Urutan | Sumber | Catatan |
|---|---|---|
| 1 | Shift Assignment aktif | Menang atas semuanya |
| 2 | Rotasi grup | Hari ke-n = (tanggal - tanggal mulai) mod panjang siklus; sebelum tanggal mulai belum berlaku |
| 3 | Jadwal Mingguan grup | Berdasarkan hari dalam minggu |
| 4 | Tidak ada | Bukan hari kerja |

Hari libur (HRIS Holiday, yang berlaku untuk semua company atau company karyawan) ditandai terpisah: dari Assignment dianggap masuk kerja, dari rotasi atau jadwal mingguan dianggap tidak masuk. Fungsi dan hasilnya: lihat [api.md](api.md).

## Audit trail
- Sumber: Version (`track_changes`): waktu, pengguna, field, nilai lama dan baru.
- Tampilan: tab "Audit Trail HRIS" di form (terpasang di semua DocType HRIS) dan Report "HRIS Audit Trail" (menyusul). Waktu ditampilkan dalam WIB; `time_zone` site = `Asia/Jakarta`.

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

## Catatan shift lintas tengah malam

`HRIS Shift` menandai shift lintas tengah malam (`crosses_midnight`) dan service jadwal meneruskan penanda itu. Yang belum diputuskan: batas "hari kerja" untuk mengelompokkan tempelan Raw Log pada shift malam (security 3 atau 4 shift), diputuskan di modul working hour.
