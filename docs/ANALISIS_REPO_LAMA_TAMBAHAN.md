# Analisis Repo Lama: Tambahan

Tanggal: 27 Oktober 2026. Melengkapi [ANALISIS_REPO_LAMA.md](ANALISIS_REPO_LAMA.md).

> **Catatan metode:** temuan berasal dari membaca kode, bukan menjalankannya. Uji sebelum memperbaiki.

## 1. Tambahan temuan `hr_app`

Penomoran di dokumen utama memakai H7 untuk "tidak ada scheduler". Temuan berikut diberi nomor baru agar tidak bentrok.

| # | Temuan | Prioritas |
|---|---|---|
| H8 | `Attendance Device Operation Log` tidak punya `company`. Cakupan jenis operasi "Delete Attendance Logs" belum diperiksa. | Sedang |

## 2. Tambahan temuan `hr_payroll`

| # | Temuan | Prioritas |
|---|---|---|
| N1 | `Payroll Run.employee_group` menaut ke `Employee Group` standar, sedangkan `Payroll Policy Assignment.employee_group` menaut ke `Payroll Employee Group` kustom. Dua konsep grup berbeda. | Tinggi |
| N2 | Role `HR Payroll User` tidak ada di role `hr_app`. | Sedang |
| N3 | Permission mencampur role HRMS standar dan role kustom. | Sedang |

Pembuktian P1 dan P12 dilakukan lewat unit test di app baru.

## 3. Inventaris HRMS v16 (yang sudah ada)

| Area | Ada di HRMS | Padanan kode lama |
|---|---|---|
| Log absensi | `Employee Checkin` (`employee` wajib; log_type, time, device_id; tanpa jenis verifikasi, link perangkat, atau company) | `Attendance Raw Log` |
| Shift | `Shift Type` (toleransi, jendela check-in/out, Holiday List) | `Payroll Shift*` |
| Lembur | `Overtime Type` | `Payroll Overtime Type` |
| Gaji | `Salary Component`, `Salary Structure`, `Salary Structure Assignment`, `Salary Slip`, `Payroll Entry`, `Payroll Period`, `Additional Salary` | `Payroll Salary Component`, `Payroll Formula`, `Payroll Run` |
| Pajak | `Income Tax Slab` (kecocokan dengan PPh21/TER belum diverifikasi) | `tax_service.py` |
| Biometrik | Tidak ada | `Attendance Device` dan terkait |

**Belum diverifikasi:** validasi duplikat `Employee Checkin`, lembur bertingkat, perilaku `Salary Slip.validate` HRMS (apakah menimpa baris hitungan kita), keberadaan `Shift Schedule`/`Overtime Slip` di v16, field `attendance_device_id` di `Employee`. Sebagian dapat dicek langsung karena HRMS 16.52.0 terpasang di site kerja.

## 4. Draf rancangan fondasi (belum disetujui final)

- **Bridge absensi:** Mesin -> Raw Log HRIS (termasuk ID tak dikenal) -> Log Absensi HRIS -> `Employee Checkin`/`Attendance` HRMS. Alasan: `employee` wajib di `Employee Checkin`.
- **Penugasan Sementara** (nama sementara, untuk "pinjam karyawan"): karyawan, bagian asal, bagian tujuan, periode, jenis perlakuan; dibaca engine gaji.
- **Komponen gaji:** DocType HRIS sebagai master, dipetakan ke satu `Salary Component` HRMS tipis; perhitungan tetap di HRIS. **Risiko:** `Salary Slip` HRMS dapat menghitung ulang baris saat disimpan; wajib diuji.
- **Urutan sesi kode:** (1) kerangka app, Core, role [selesai]; (2) perangkat dan log mentah; (3) log lengkap, shift, penugasan sementara, bridge; (4) komponen gaji dan formula; (5) Payroll Run dan bridge Salary Slip; (6) laporan, lalu biometrik.
- **Navigasi:** Sidebar modul dan Dock (format Frappe 16), bukan Desktop Icon.

## 5. Catatan teknis

- Pemeriksaan `table_exists("tabX")` pada kode lama kemungkinan salah (Frappe menambah awalan `tab` sendiri). Verifikasi di source Frappe.
- Data biometrik tergolong data pribadi spesifik (UU No. 27 Tahun 2022; verifikasi ke sumber resmi): enkripsi, akses terbatas, log akses, persetujuan karyawan.
