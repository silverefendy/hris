# Matriks Role x Hak Akses

Berlaku per 28 Oktober 2026 (Device dan Raw Log terpasang). Role berawalan HRIS. Enam role sudah ada di kode; `HRIS Employee Admin` usulan (ditambah di modul Employee Data).

| Role | Fungsi |
|---|---|
| HRIS Attendance Operator | Mengelola mesin, melihat log |
| HRIS Attendance Supervisor | Hanya membaca |
| HRIS HR Admin | Meninjau dan mengubah log |
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

Catatan: Raw Log tidak dapat dihapus kecuali oleh System Manager (diterapkan di DocType). Report "HRIS Audit Trail": HR Admin dan Manager.
