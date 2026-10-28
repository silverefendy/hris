# Batas Platform vs Kode Sendiri

Berlaku sejak keputusan K-18 (lihat decisions/0002, 28 Oktober 2026). Prinsip: HRIS mandiri; dari HRMS/ERPNext hanya Employee dan Company yang dipakai. Core tidak dimodifikasi.

| Area | HRMS/ERPNext | HRIS |
|---|---|---|
| Data karyawan | Pakai `Employee` (termasuk `attendance_device_id`) | Tambahan lewat Custom Field berawalan `hris_` (contoh: `hris_employee_group`) |
| Perusahaan | Pakai `Company` | Semua DocType HRIS punya `company` |
| Department | Pakai master `Department` (K-29) | Hanya ditautkan (opsional) di Employee Group |
| Role dan izin | Mekanisme Frappe | Enam role HRIS yang ada, ditambah `HRIS Employee Admin` (usulan) |
| Mesin absensi | Tidak dipakai | `HRIS Device` |
| Log mentah dan tinjauan | Tidak dipakai | `HRIS Raw Log` |
| Shift, grup, rotasi, penugasan sementara | Tidak dipakai | `HRIS Shift`, `HRIS Employee Group`, `HRIS Shift Rotation`, `HRIS Shift Assignment`, service `shift_schedule` |
| Hari libur | Tidak dipakai | `HRIS Holiday` |
| Attendance | Tidak dipakai | `HRIS Attendance` (menyusul) |
| Payroll | Tidak dipakai | Modul HRIS Payroll |
| Cuti dan izin | Belum diputuskan | Belum diputuskan |
| Dokumen karyawan | Lampiran Employee (private file) | Rancangan di modul Employee Data |
| Akuntansi, biaya, modul non-HRD | ERPNext | Bridge arah HRIS ke ERPNext (mapping), ditunda |
| Audit trail | Version (`track_changes`) | Tab dan Report "HRIS Audit Trail" |

## Aturan
- Tidak memodifikasi core ERPNext/HRMS; pakai hooks, custom field, atau override yang aman saat upgrade.
- Bridge hanya arah HRIS ke ERPNext/HRMS; tidak ada sinkronisasi balik ke HRIS.
- Nama objek HRIS berawalan `HRIS`; field tambahan di DocType non-HRIS berawalan `hris_`.

## Belum diverifikasi
- Apakah `hrms` masih perlu masuk `required_apps` jika hanya Employee yang dipakai.
