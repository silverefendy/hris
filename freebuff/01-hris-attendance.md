# Rangkuman: Modul `hris_attendance`

Diperiksa: 27 November 2026. Modul terbesar: mesin absensi, log mentah,
shift, Working Hour, dan konsol mesin.

## DocType (16)

| DocType | Berkas | Isi |
|---|---|---|
| `HRIS Device` | `hris_device.py/.js/.json` | Mesin absensi: IP, port, Comm Key, `use_agent`, `use_pull`, `device_code`, serial unik, `last_agent_at`, `last_pull_at` |
| `HRIS Device User` | `hris_device_user.py` | Baris anak: snapshot user mesin yang dikirim ke HRIS |
| `HRIS Raw Log` | `hris_raw_log.py/.js` + `_list.js` (369 baris) | Log mentah per punch, `punch_key` unik, status tinjauan, aksi massal di list view |
| `HRIS Shift` | `hris_shift.py/.js` | Jam shift, jendela punch, aturan telat/lembur, aturan working hour |
| `HRIS Shift Rotation` (+ `_day`) | `hris_shift_rotation.py/.js` | Siklus rotasi; hari ke-n = (tanggal - mulai) mod panjang siklus |
| `HRIS Shift Assignment` | `hris_shift_assignment.py/.js` | Penimpaan jadwal per karyawan per rentang; memicu hitung ulang aturan Department |
| `HRIS Employee Group` (+ `_day`, `_component`) | `hris_employee_group.py/.js` | Jadwal mingguan atau rotasi, Department, komponen grup |
| `HRIS Holiday` | `hris_holiday.py/.js` | Libur, opsi "berlaku semua Company" |
| `HRIS Working Hour` | `hris_working_hour.py` (240) + `_list.js` (416) | Hasil per karyawan per hari: 72 field, `unique_key`, penjaga field (K-42), dialog hitung ulang |
| `HRIS Pull Run` | `hris_pull_run.py` | Riwayat tarik (`PR-`) dan hapus (`DR-`), read-only |
| `HRIS Hapus WH Log` | `hris_hapus_wh_log.py` | Jejak hapus massal Working Hour |
| `HRIS Attendance Settings` | Single | Saklar `hris_hapus_wh_aktif`, `hris_skip_hari_kosong`, dsb. |

## Layanan (`services/`, 19 berkas)

| Berkas | Baris | Fungsi |
|---|---|---|
| `pull_device.py` | 478 | Pull pyzk: koneksi, baca log, riwayat, cek koneksi, enqueue |
| `working_hour.py` | 377 | `compute_day`: jadwal, jendela punch, potongan, lembur, status |
| `working_hour_batch.py` | 321 | Hitung ulang per cakupan (Semua/Karyawan/Department/Grup), status Redis, job |
| `working_hour_hapus.py` | 246 | Cek Dulu hapus massal: blokir/peringatan/info |
| `working_hour_hapus_job.py` | 223 | Job hapus per batch + `on_trash` guard |
| `delete_raw_log.py` | 197 | Hapus Raw Log per mesin/rentang, syarat persetujuan/WH |
| `pull_run_log.py` | 163 | Penulisan `HRIS Pull Run` yang aman-gagal |
| `rematch_raw_log.py` | 162 | "Cocokkan Ulang" Raw Log `Tidak Cocok` ke Employee |
| `audit_trail.py` | 152 | API `get_audit_trail` (Version + tabel anak) |
| `punch_ingest.py` | 146 | Penyimpanan punch dari agen, idempoten via `punch_key` |
| `shift_schedule.py` | 145 | `get_schedule_for_date`, `get_employee_schedule` (maks 62 hari) |
| `department_aturan.py` | 124 | Hitung ulang baris WH saat Shift Assignment berubah |
| `jam_koreksi.py` | 102 | Mesin hitung jam koreksi (C4) |
| `agent_auth.py` | 99 | Token agen, `allowed_ips`, batas gagal |
| `device_user_ingest.py` | 87 | Penerimaan snapshot user mesin (`push_device_users`) |
| `raw_log_naming.py` | 48 | Penamaan `{device_code}-{ID}-{YYMMDD}-{NNNNN}` |
| `absence_rule.py` | 23 | Aturan absen (Tidak Hadir, Tidak Lengkap) |
| `department_tujuan.py` | 19 | Department tujuan saat karyawan dipinjam |
| `employee_group.py` | 16 | Hook validasi grup di `Employee` |

## Page, report, number card, workspace

| Berkas | Isi |
|---|---|
| `page/konsol_mesin/konsol_mesin.js` (130) | Konsol Mesin: daftar mesin, Tarik Log, Cek Koneksi, Status |
| `report/hris_working_hour_ringkasan` | Ringkasan Working Hour (97 baris Python) |
| `report/perbandingan_user_mesin_dan_employee` (182) | Bandingkan user di mesin vs Employee |
| `number_card/hris_raw_log_menunggu`, `hris_perlu_tinjauan`, `hris_tidak_lengkap`, `hris_karyawan_tanpa_grup` | Kartu angka dashboard |
| `workspace/hris`, `workspace_sidebar/hris` | Workspace modul |
| `desktop_icon/hris` | Ikon desk (isu diparkir, K-16) |

## Integrasi

| Berkas | Isi |
|---|---|
| `integrations/agent_api.py` (22) | Endpoint `push_punches` |
| `integrations/device_user_api.py` (18) | Endpoint `push_device_users` |
| `public/js/hris_device_actions.js` (351) | Dialog Tarik Log/Status/Cek Dulu bersama |
| `public/js/hris_audit_trail.js` (48) | Tab Audit Trail di semua DocType HRIS |

## Uji

`uji_device_user.py`, `uji_kirim_agen.py`, `uji_perbandingan.py` berada di **akar
modul**, sedangkan folder `tests/` hanya berisi `__init__.py`. Modul payroll
menaruh uji di `tests/`. Ini ketidakseragaman struktur, bukan bug.

## Catatan

- Semua field yang dirujuk `hooks.py` (`hris_employee_group` di Employee,
  `doc_events` Shift Assignment) ada di modul ini.
- `working_hour.py` masih menyimpan query punch per karyawan (tercatat sebagai
  "perlu dibaca utuh" di `status.md`).
- DocType `HRIS Device User` belum tercantum di `data-model.md`.
