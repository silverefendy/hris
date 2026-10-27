# Daftar Keputusan

Diperbarui: 27 Oktober 2026

## Sudah diputuskan
| No | Keputusan | Tanggal | Status |
|---|---|---|---|
| K-01 | Satu app `hris` untuk semua; lima modul terpisah (Core, Attendance, Employee Data, Payroll, Reports) | 2026-10-27 | Diterapkan |
| K-02 | Nama teknis `hris`; hindari `hrms`; nama merek menyusul | 2026-10-27 | Aktif |
| K-03 | `required_apps`: frappe, erpnext, hrms | 2026-10-27 | Diterapkan |
| K-04 | Aturan reuse HRMS: ada dan lengkap dipakai; tidak ada kustom; ada tapi kurang bridge + custom (data sinkron) | 2026-10-27 | Aktif |
| K-05 | Komponen gaji custom, dikelola DocType HRIS sendiri | 2026-10-27 | Aktif |
| K-06 | Log absensi lebih lengkap dari HRMS (istirahat, pulang cepat, dll.); praktik "pinjam karyawan" antar bagian harus didukung | 2026-10-27 | Aktif |
| K-07 | Device diinput manual lewat form, tanpa hardcode | 2026-10-27 | Aktif |
| K-08 | Kode lama (`hr_app`, `hr_payroll`) ditulis ulang; hanya referensi, patch lama tidak dibawa | 2026-10-27 | Aktif |
| K-09 | Layout standar Frappe (bukan `src/`); services dan integrations sebagai sub-package dalam modul | 2026-10-27 | Aktif |
| K-10 | Semua DocType, child table, dan role milik app wajib memuat awalan `HRIS ` | 2026-10-27 | Aktif |
| K-11 | Enam role: HRIS Attendance Operator, HRIS Attendance Supervisor, HRIS HR Admin, HRIS Payroll User, HRIS Payroll Admin, HRIS Manager | 2026-10-27 | Diterapkan |
| K-12 | Modul bawaan `hris_cml` dihapus | 2026-10-27 | Diterapkan (853d504) |
| K-13 | HRIS Core tahap awal hanya role; `HRIS Settings` menyusul bersama kebutuhan nyata pertama | 2026-10-27 | Aktif |
| K-14 | Lisensi MIT sementara | 2026-10-27 | Sementara |
| K-15 | Pemicu CI diubah dari `version-16` ke `main` | 2026-10-27 | Belum diterapkan |
| K-16 | Isu ikon desk bawaan ERPNext dibiarkan/diparkir | 2026-10-27 | Diparkir |
| K-17 | Alur git: Efendy push ke `origin main`; Claude hanya push `.md` setelah Efendy `git pull origin main` | 2026-10-27 | Aktif |

## Belum diputuskan
- Nama merek dan lisensi final (implikasi GPLv3 ERPNext/HRMS perlu diverifikasi).
- Cara bridge absensi final; model grup karyawan (N1); aturan "pinjam karyawan"; aturan lembur dan insentif; komponen gaji spesifik.
- Merek/model mesin untuk uji template wajah; prioritas 3 bulan.
- Satu atau dua bench untuk production; nasib site uji lama.
- Navigasi: Sidebar modul dan Dock (usulan), bukan Desktop Icon.

Templat keputusan rinci: [0001-template.md](0001-template.md).
