# Matriks Role x Hak Akses

Berlaku per 28 Oktober 2026 (Device, Raw Log, Shift, Grup, Rotasi, Holiday, dan Shift Assignment terpasang). Role berawalan HRIS. Enam role sudah ada di kode; `HRIS Employee Admin` usulan (ditambah di modul Employee Data).

| Role | Fungsi |
|---|---|
| HRIS Attendance Operator | Mengelola mesin, melihat log dan jadwal |
| HRIS Attendance Supervisor | Hanya membaca |
| HRIS HR Admin | Meninjau dan mengubah log; mengelola jadwal (tanpa hapus) |
| HRIS Manager | Seperti HR Admin, plus hapus |
| HRIS Payroll User / Payroll Admin | Payroll (belum dirancang) |
| HRIS Employee Admin (usulan) | Input dan ubah data karyawan, tanpa hak tinjau atau gaji |

| DocType | Role | Read | Write | Create | Delete |
|---|---|---|---|---|---|
| HRIS Device | Attendance Operator | ya | ya | ya | tidak |
| HRIS Device | HR Admin | ya | ya | tidak | tidak |
| HRIS Device | Attendance Supervisor | ya | tidak | tidak | tidak |
| HRIS Device | Manager | ya | ya | ya | ya |
| HRIS Raw Log | Attendance Operator | ya | tidak | ya | tidak |
| HRIS Raw Log | HR Admin | ya | ya (alasan wajib) | tidak | tidak |
| HRIS Raw Log | Attendance Supervisor | ya | tidak | tidak | tidak |
| HRIS Raw Log | Manager | ya | ya (alasan wajib) | tidak | tidak |
| HRIS Shift, Employee Group, Shift Rotation, Holiday, Shift Assignment | HR Admin | ya | ya | ya | tidak |
| (lima DocType yang sama) | Manager, System Manager | ya | ya | ya | ya |
| (lima DocType yang sama) | Attendance Supervisor | ya | tidak | tidak | tidak |
| (lima DocType yang sama) | Attendance Operator | ya | tidak | tidak | tidak |

Catatan:
- Raw Log tidak dapat dihapus kecuali oleh System Manager (diterapkan di DocType). Report "HRIS Audit Trail": HR Admin dan Manager.
- Shift Assignment: HR Admin tidak punya hak hapus; pembatalan dengan mematikan centang Aktif sehingga riwayat tetap ada (K-32). Hak dasar kelima DocType jadwal disalin dari `HRIS Shift` dan dibaca dari file JSON, belum diuji dengan pengguna non-editor.
- Fungsi `get_employee_schedule` mengikuti izin baca Employee (lihat [../architecture/api.md](../architecture/api.md)).
