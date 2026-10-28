# Daftar Keputusan

Diperbarui: 28 Oktober 2026

## Sudah diputuskan
| No | Keputusan | Tanggal | Status |
|---|---|---|---|
| K-01 | Satu app `hris` untuk semua; lima modul terpisah (Core, Attendance, Employee Data, Payroll, Reports) | 2026-10-27 | Diterapkan |
| K-02 | Nama teknis `hris`; hindari `hrms`; nama merek menyusul | 2026-10-27 | Aktif |
| K-03 | `required_apps`: frappe, erpnext, hrms | 2026-10-27 | Diterapkan (perlu ditinjau ulang, lihat K-18) |
| K-04 | Aturan reuse HRMS: ada dan lengkap dipakai; tidak ada kustom; ada tapi kurang bridge + custom (data sinkron) | 2026-10-27 | Diganti sebagian oleh K-18 (absensi, shift, payroll) |
| K-05 | Komponen gaji custom, dikelola DocType HRIS sendiri | 2026-10-27 | Aktif |
| K-06 | Log absensi lebih lengkap dari HRMS (istirahat, pulang cepat, dll.); praktik "pinjam karyawan" antar bagian harus didukung | 2026-10-27 | Aktif |
| K-07 | Device diinput manual lewat form, tanpa hardcode | 2026-10-27 | Diterapkan (HRIS Device) |
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
| K-18 | HRIS mandiri: dari HRMS/ERPNext hanya `Employee` dan `Company`; shift, attendance, payroll, laporan dibuat di HRIS ([0002](0002-hris-mandiri-dan-bridge-keluar.md)) | 2026-10-28 | Aktif |
| K-19 | Bridge ke ERPNext/HRMS hanya arah HRIS ke ERPNext (mapping); integrasi langsung ke akun payroll/accounting ditunda | 2026-10-28 | Aktif |
| K-20 | Dokumen karyawan (perjanjian kerja, foto, KTP) dikelola di sisi HRIS; rancangan di modul Employee Data | 2026-10-28 | Aktif |
| K-21 | Log mentah satu baris per log; ditinjau HRD per baris lewat list view dengan filter dan aksi massal; tanpa DocType review tambahan | 2026-10-28 | Diterapkan |
| K-22 | ID karyawan sama di semua mesin; pencocokan lewat `Employee.attendance_device_id` (+ company, status Active) | 2026-10-28 | Diterapkan |
| K-23 | Status masuk/keluar dari mesin diabaikan; HRIS menentukan masuk/keluar, shift, dan waktu kerja | 2026-10-28 | Aktif (menunggu modul working hour) |
| K-24 | Punch ganda otomatis: masuk = tempelan paling awal, pulang = paling akhir; log lain diabaikan otomatis (tetap tersimpan); batas hari kerja ditentukan modul working hour | 2026-10-28 | Aktif (menunggu modul working hour) |
| K-25 | Data sumber log hanya boleh diubah HRIS HR Admin, HRIS Manager, atau System Manager dengan alasan baru setiap kali; audit trail dari Version, tab "Audit Trail HRIS" di form (report menyusul) | 2026-10-28 | Diterapkan |
| K-26 | `HRIS Device` lengkap: mode koneksi (Pull IP / Push ADMS), IP, port (default 4370), model, firmware; serial wajib dan unik; Comm Key per mesin | 2026-10-28 | Diterapkan |
| K-27 | Role tambahan untuk input data karyawan (nama usulan: `HRIS Employee Admin`) | 2026-10-28 | Disetujui, belum dibuat |
| K-28 | Zona waktu site kerja: Asia/Jakarta (WIB), agar audit trail berwaktu WIB | 2026-10-28 | Diterapkan |
| K-29 | `Department` tetap master ERPNext (modul Setup), dipakai lewat `Employee.department`; HRIS tidak membuat Department sendiri; field `department` di HRIS Employee Group opsional. Audit tab dipasang di semua DocType HRIS (Raw Log tetap). HRIS Holiday punya centang "Berlaku untuk Semua Company" | 2026-10-28 | Diterapkan |
| K-30 | Tidak ada penomoran hash di DocType HRIS; penomoran memuat YYMM dengan format `PREFIX-YYMM-NNNN`. Holiday `HOL-YYMM-NNNN` (4 digit), YYMM dari tanggal dibuat; data lama bernomor hash dihapus manual, tidak di-rename. Pengecualian: HRIS Raw Log (nama = kunci anti-duplikat), DocType bernama dari field nama, dan tabel anak | 2026-10-28 | Diterapkan (Holiday, 22126c0) |

## Belum diputuskan
- Nama merek dan lisensi final (implikasi GPLv3 ERPNext/HRMS perlu diverifikasi).
- Jalur data mesin (ADMS/push, agen Windows via SDK, pull lewat IP); diparkir sampai menu ADMS, model, dan firmware mesin dicek.
- Penentuan shift: HRIS Shift dan HRIS Employee Group (jadwal mingguan) sudah ada; rotasi dan Shift Assignment (Bagian B), jadwal per hari atau deteksi otomatis, serta shift lintas tengah malam untuk security 3 atau 4 shift belum.
- Cuti dan izin; aturan "pinjam karyawan"; aturan lembur dan insentif; komponen gaji spesifik.
- Akuntansi gaji: jurnal otomatis ke ERPNext atau cukup laporan.
- Apakah `hrms` tetap `required_apps` jika hanya Employee yang dipakai.
- Pemetaan `verify_mode` (jari/wajah) dan arti "no akun" dan "no induk" di Raw Log.
- Merek/model mesin untuk uji template wajah; prioritas 3 bulan.
- Satu atau dua bench untuk production; nasib site uji lama.
- Navigasi: Sidebar modul dan Dock (usulan), bukan Desktop Icon.

Templat keputusan rinci: [0001-template.md](0001-template.md). Keputusan rinci: [0002](0002-hris-mandiri-dan-bridge-keluar.md). Checklist DocType baru: [../development/doctype-checklist.md](../development/doctype-checklist.md).
