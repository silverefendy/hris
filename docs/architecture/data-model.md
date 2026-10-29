# Data Model

Status per 29 Oktober 2026: `HRIS Device`, `HRIS Raw Log`, `HRIS Shift`, `HRIS Employee Group`, `HRIS Shift Rotation`, `HRIS Holiday`, `HRIS Shift Assignment`, dan `HRIS Working Hour` terpasang di site kerja dan teruji skrip. Tampilan browser tombol hitung ulang Working Hour belum diuji.

Aturan: semua DocType HRIS berawalan `HRIS`, punya `company`, dan memakai `track_changes`. Dari ERPNext hanya `Employee` dan `Company` yang ditautkan (`Department` lewat Employee, K-29).

## Peta modul

| Modul | DocType / objek | Status |
|---|---|---|
| HRIS Attendance | `HRIS Device` | Terpasang |
| HRIS Attendance | `HRIS Raw Log` | Terpasang |
| HRIS Attendance | `HRIS Shift`, `HRIS Employee Group` (+ `HRIS Employee Group Day`), `HRIS Holiday` | Terpasang |
| HRIS Attendance | `HRIS Shift Rotation` (+ `HRIS Shift Rotation Day`), `HRIS Shift Assignment` | Terpasang |
| HRIS Attendance | `HRIS Working Hour` | Terpasang (5a, 5b, 5c-1) |
| HRIS Employee Data | Tambahan Employee, dokumen karyawan | Belum dirancang |
| HRIS Payroll | Komponen, formula, Payroll Run | Belum dirancang |
| HRIS Reports | Report "HRIS Audit Trail", ringkasan Working Hour, laporan HRD | Belum dirancang |

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

Belum ada koneksi ke mesin; jalur data masih diparkir.

## HRIS Raw Log (terpasang)

Satu baris = satu log. Semua informasi ada di baris itu.

| Kelompok | Field | Catatan |
|---|---|---|
| Sumber | `company` (dari Device), `device`, `device_user_id` (no akun/ID user di mesin), `punch_time`, `verify_mode` (jari/wajah/dll), `punch_status_raw` | Tidak dipakai untuk logika IN/OUT |
| Karyawan | `employee`, nomor induk (diambil dari Employee) | Dicocokkan lewat `Employee.attendance_device_id`; kosong = Tidak Cocok. Arti "no akun" dan "no induk" perlu dikonfirmasi |
| Tinjauan | `review_status` (Menunggu, Tidak Cocok, Disetujui, Ditolak, Terkirim), peninjau, waktu tinjau, catatan | Per baris |
| Peran punch | `punch_role` (Masuk, Pulang, Diabaikan Otomatis) | Read-only, bukan field sumber; ditulis layanan working hour lewat `frappe.db.set_value` tanpa Version (K-44) |
| Perubahan | `change_reason` | Wajib saat field sumber diubah |

Anti-duplikat: nama dokumen dari mesin + ID user + waktu asli (teruji: duplikat ditolak).

Log yang dihitung working hour: Menunggu, Disetujui, Terkirim. Ditolak dan Tidak Cocok tidak dihitung (K-44).

## HRIS Shift

Nama dokumen = `shift_name` (unik, boleh di-rename).

| Field | Tipe | Catatan |
|---|---|---|
| `shift_name` | Data | Wajib, unik |
| `company` | Link Company | Wajib |
| `is_active` | Check | Default aktif |
| `start_time`, `end_time` | Time | Wajib; detik dibulatkan ke menit |
| `crosses_midnight` | Check | Read-only, dihitung otomatis |
| `duration_minutes` | Int | Read-only, dihitung otomatis |
| `break_minutes` | Int | Istirahat; default 0 |
| `late_tolerance_min`, `early_leave_tolerance_min` | Int | Toleransi telat dan pulang cepat; default 0 |
| `window_before_min` | Int | Jendela masuk sebelum jam mulai; default 120 |
| `late_limit_min` | Int | Batas terlambat setelah jam mulai (jendela masuk berakhir); 240 (K-36) |
| `min_out_after_in_min` | Int | Jarak minimum masuk ke pulang; 60 |
| `window_after_min` | Int | Batas pulang sesudah jam selesai, sekaligus batas lembur; 240 |
| `overtime_min_minutes` | Int | Lembur minimal sekaligus kelipatan; 30 (K-38) |
| `deduction_block_min`, `deduction_hours_per_block` | Int | Blok potongan telat dan pulang cepat; 60 menit dan 1 jam (K-37) |

Validasi: jarak minimum lebih kecil dari durasi; lembur minimal tidak melebihi jendela sesudah selesai; blok potongan lebih dari 0; angka tidak negatif.

Data nyata (8 shift): Kantor Senin - Kamis (08:00 sampai 17:00, istirahat 60), Kantor Jumat (08:00 sampai 17:30, 90), Kantor Sabtu (08:00 sampai 15:00, 60), Lapangan Senin - Kamis (07:45 sampai 17:00, 60), Lapangan Jumat (07:45 sampai 17:30, 90), Lapangan Sabtu (07:45 sampai 16:00, 60), Security Pagi (08:00 sampai 20:00, 0), Security Malam (20:00 sampai 08:00, lintas tengah malam, 0).

Catatan: kolom lama `early_leave_limit_min` masih ada di tabel walau field sudah dihapus dari DocType; tidak berbahaya.

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
| `is_active` | Check | Default aktif; tidak boleh dinonaktifkan selama dipakai grup aktif (K-34) |
| `cycle_days` | Int | Read-only; jumlah baris pola |
| `description` | Small Text | Opsional |
| `pattern` | Tabel `HRIS Shift Rotation Day` | Wajib |

Tabel anak `HRIS Shift Rotation Day`: `day_number` (otomatis), `is_off` (Libur), `shift`. Aturan: baris libur mengosongkan shift; baris non-libur wajib shift dan satu company dengan rotasi; pola tidak boleh libur semua. **Pola dan company dikunci bila rotasi sudah dipakai grup**; ubah dengan membuat rotasi baru lalu memindahkan grupnya.

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
| `from_date`, `to_date` | Date | Wajib; tanggal sampai tidak sebelum dari |
| `shift` | Link HRIS Shift | Wajib; aktif dan satu company dengan karyawan |
| `reason` | Small Text | Wajib (di-trim) |
| `borrowed_for_group` | Link HRIS Employee Group | Opsional; grup harus aktif |

Anti tumpang tindih: karyawan yang sama tidak boleh punya dua Assignment aktif yang rentang tanggalnya beririsan.

## HRIS Working Hour

Satu baris hasil per karyawan per hari kerja (K-35). Nama `WH-YYMMDD-NNNN` dari tanggal kerja (K-40). Kunci unik di database: `unique_key` = `<employee>|<tanggal kerja>` (tersembunyi). Total 72 field; daftar nama field lengkap ada di `hris_working_hour.json` (sumber kebenaran), tabel di bawah hanya mencatat kelompok dan field yang sudah dikonfirmasi.

| Kelompok | Isi | Catatan |
|---|---|---|
| Identitas | `employee`, `work_date`, `unique_key`, nama dan company | Karyawan dan tanggal kerja tidak bisa diubah (K-42) |
| Salinan karyawan | Grup, department, "Dipinjam untuk Grup" | Snapshot pada hari itu (K-39) |
| Jadwal | Shift, sumber jadwal, penanda libur dan wajib hadir | Dari `get_schedule_for_date` (K-33) |
| Salinan aturan shift | Jam mulai dan selesai, durasi, istirahat, batas dan blok | Snapshot saat dihitung (K-35) |
| Punch | Masuk, pulang, jumlah punch diabaikan | Raw Log: Menunggu, Disetujui, Terkirim (K-44) |
| Hasil hitung | `status`, menit telat dan pulang cepat, potongan, lembur dan `overtime_type`, `effective_hours` | Hanya layanan yang mengubah (`flags.from_calculation`) |
| Tinjauan HRD | `review_status`, `review_note`, `reviewed_by`, `reviewed_on` | `review_status`: Tidak Perlu, Menunggu, Sudah Ditinjau |
| Penyesuaian HRD | `adjustment_hours`, `adjustment_reason`, `final_effective_hours` | `final = max(0, effective + adjustment)`; alasan wajib bila ada penyesuaian |
| Jejak | Waktu hitung dan sumber | |
| Audit | Tab "Audit Trail HRIS" | |

`status`: Hadir, Tidak Lengkap, Tidak Hadir, Libur, Tidak Terjadwal (K-41). `overtime_type`: Hari Kerja atau Hari Libur.

Hak: buat dan hapus hanya System Manager; ubah `review_status`, `review_note`, `adjustment_hours`, `adjustment_reason` oleh HRIS HR Admin, HRIS Manager, System Manager (K-42). Baris dibuat layanan dengan `ignore_permissions`.

Hitung ulang: idempoten; penyesuaian dan catatan HRD dipertahankan; "Sudah Ditinjau" dipertahankan bila masuk, pulang, dan status tidak berubah, selain itu kembali ke Menunggu (K-43). Hitung ulang massal lewat K-45 dan [api.md](api.md).

Catatan penting: nama field di kelompok Hasil hitung, Punch, dan Jejak belum disalin satu per satu ke dokumen ini; verifikasi dari JSON sebelum dipakai oleh Report 5c-2.

## Penentuan shift per hari (service `shift_schedule`)

Jawaban untuk "karyawan X pada tanggal Y masuk shift apa" (K-33). Dihitung saat dibutuhkan, tidak disimpan per hari.

| Urutan | Sumber | Catatan |
|---|---|---|
| 1 | Shift Assignment aktif | Menang atas semuanya |
| 2 | Rotasi grup | Hari ke-n = (tanggal - tanggal mulai) mod panjang siklus; sebelum tanggal mulai belum berlaku; rotasi nonaktif dilewati |
| 3 | Jadwal Mingguan grup | Berdasarkan hari dalam minggu |
| 4 | Tidak ada | Bukan hari kerja |

Hari libur (HRIS Holiday, yang berlaku untuk semua company atau company karyawan) ditandai terpisah: dari Assignment dianggap masuk kerja, dari rotasi atau jadwal mingguan dianggap tidak masuk. Fungsi dan hasilnya: lihat [api.md](api.md).

## Audit trail
- Sumber: Version (`track_changes`): waktu, pengguna, field, nilai lama dan baru.
- Tampilan: tab "Audit Trail HRIS" di form (terpasang di semua DocType HRIS) dan Report "HRIS Audit Trail" (menyusul). Waktu ditampilkan dalam WIB; `time_zone` site = `Asia/Jakarta`.
- Perubahan lewat `frappe.db.set_value` (mis. `punch_role`, perapian data) tidak tercatat di Version.

Alur data: lihat `business/process-flows/attendance-flow.md`.

## Keputusan implementasi Raw Log

- Nama dokumen dibuat dari mesin + ID user + waktu punch (script); duplikat ditolak database (teruji).
- `verify_mode` disimpan apa adanya (kode mentah). Pemetaan jari/wajah menyusul setelah jalur data dan mesin diuji.
- Employee dicocokkan lewat `company` + `attendance_device_id` + status Active; jika tidak tepat satu, status Tidak Cocok.
- Mengubah field sumber hanya oleh HRIS HR Admin, HRIS Manager, atau System Manager, dengan alasan baru setiap kali. Setelah diubah, status kembali ke Menunggu/Tidak Cocok.
- Log berstatus Terkirim tidak dapat diubah.
- Operator hanya membaca dan membuat; tidak dapat mengubah log yang sudah ada.
- `company` disalin dari Device di server dan lewat `fetch_from` di form (field wajib, read-only).
- Tab "Audit Trail HRIS" di form memanggil `hris.hris_attendance.services.audit_trail.get_audit_trail`; Report audit trail menyusul.

## Catatan shift lintas tengah malam

`HRIS Shift` menandai shift lintas tengah malam (`crosses_midnight`) dan service jadwal meneruskan penanda itu. Hari kerja shift lintas tengah malam dihitung ke tanggal shift dimulai (K-35). Belum diuji dengan data nyata; tumpang tindih jendela antar shift (malam hari ini dan pagi esok) menunggu data nyata.
