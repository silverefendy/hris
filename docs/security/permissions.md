# Matriks Role x Hak Akses

Berlaku per 5 November 2026 (K-118 sampai K-121). Menggambarkan kondisi **di kode** (`main`, commit 2a604e7), teruji di site uji. Site kerja baru mengikutinya setelah `migrate` (lihat "Penerapan"). Role berawalan HRIS.

## Peran dan fungsi
| Role | Fungsi | Dipegang oleh (fungsi, bukan nama) |
|---|---|---|
| HRIS Attendance Operator | Mengelola mesin, menarik log, melihat jadwal dan log | Petugas tarik absensi |
| HRIS Attendance Supervisor | Hanya membaca | Belum dipetakan |
| HRIS HR Admin | Meninjau dan mengubah log, mengelola jadwal (tanpa hapus), mengubah Data Karyawan termasuk Data Sensitif | Belum dipetakan |
| HRIS Manager | Hak penuh absensi dan jadwal, mengubah Data Karyawan, membaca Data Sensitif | Kepala HRD |
| HRIS Payroll Admin | Mengelola jadwal gaji; membaca Data Karyawan, Data Sensitif, jadwal, absensi, dan laporan Working Hour | Petugas payroll |
| HRIS Payroll Manager | Membaca Data Karyawan dan Data Sensitif (payroll belum dirancang) | Belum dipetakan |
| HRIS Payroll User | Membaca Payroll Schedule | Belum dipetakan |
| HRIS Employee Admin | Input dan ubah Data Karyawan termasuk Data Sensitif; tanpa jadwal, absensi, atau gaji | Petugas input karyawan |
| HRIS Direksi | Hanya membaca semua DocType HRIS termasuk Data Sensitif; tanpa Konsol Mesin dan Attendance Settings | Direksi |
| System Manager | Semua | IT (sementara juga memegang semua role HRIS) |
| HR Manager, HR User (bawaan ERPNext/HRMS) | HR Manager menulis Data Karyawan dan Data Sensitif; HR User menulis Data Karyawan tanpa Data Sensitif | Jangan diberikan ke staf umum, terutama HR Manager |
| Petugas dokumen karyawan | Belum ada role; dibuat bersama fitur Dokumen Karyawan (K-20) | Petugas dokumen |

## Tiga lapis izin
Satu tindakan harus lolos ketiga lapis. Contoh: petugas tarik absensi menekan "Tarik Log" butuh lapis 1 (tulis `HRIS Device`), lapis 2 (membuka Konsol Mesin), dan lapis 3 (daftar `PULL_ROLES` di kode).

| Lapis | Apa yang dicek | Di mana diatur | Tersinkron lewat `migrate` |
|---|---|---|---|
| 1. Izin DocType | Baca, tulis, buat, hapus per role dan per permlevel | `permissions` di JSON DocType | Ya |
| 2. Role Page dan Report | Boleh membuka halaman atau laporan | JSON Page dan Report | Page ya; **Report tidak** (ditambahkan fungsi `after_migrate` di `hris/setup/izin.py`) |
| 3. Cek role di kode | Fungsi menolak bila role tidak ada di daftar | Set role di berkas Python | Ikut kode |

Menu sidebar tidak punya aturan sendiri: item tersembunyi bila role tidak punya hak baca DocType-nya (K-121).

## Lapis 1: izin DocType
R = baca, W = tulis, C = buat, D = hapus. SM = System Manager.

| DocType | Hak per role |
|---|---|
| HRIS Attendance Settings (Single) | SM RW; Manager RW |
| HRIS Device | SM RWCD; Manager RWCD; Operator RWC; HR Admin RW; Supervisor R; Direksi R |
| HRIS Raw Log | SM RWCD; Manager RW; HR Admin RW (alasan wajib); Operator RC; Supervisor R; Direksi R |
| HRIS Pull Run | SM RD; Manager R; HR Admin R; Operator R; Direksi R |
| HRIS Shift, HRIS Shift Rotation, HRIS Shift Assignment | SM RWCD; Manager RWCD; HR Admin RWC; Supervisor R; Operator R; Payroll Admin R; Direksi R |
| HRIS Employee Group | Sama dengan baris di atas, ditambah Employee Admin R |
| HRIS Holiday | SM RWCD; Manager RWCD; HR Admin RWC; Supervisor R; Operator R; Payroll Admin R; Direksi R |
| HRIS Working Hour | SM RWCD; Manager RW; HR Admin RW; Supervisor R; Operator R; Payroll Admin R; Direksi R |
| HRIS Employee, level 0 (data biasa) | SM RWCD; HR Manager RWC; HR Admin RWC; HR User RWC; Manager RWC; Employee Admin RWC; Payroll Admin R; Payroll Manager R; Direksi R |
| HRIS Employee, level 1 (Data Sensitif) | SM RW; HR Manager RW; HR Admin RW; Employee Admin RW; Manager R; Payroll Admin R; Payroll Manager R; Direksi R |
| HRIS Payroll Schedule | SM RWCD; Payroll Admin RWC; Payroll User R; HR Admin R; Manager R; Direksi R |

Catatan:
- Data Sensitif (level 1): nomor KTP, rekening, BPJS, NPWP (K-114, K-116). Level 1 tidak bisa dibuat/dihapus terpisah; `create` dan `delete` mengikuti level 0.
- Raw Log hanya dapat dihapus lewat fungsi Hapus Raw Log (K-69); Pull Run dibuat oleh sistem (K-73).
- Shift Assignment: pembatalan dengan mematikan centang Aktif, bukan hapus (K-32).

## Lapis 2: Page dan Report
| Objek | Role |
|---|---|
| Page `konsol-mesin` | HRIS HR Admin, HRIS Manager, System Manager, HRIS Attendance Operator |
| Report `HRIS Working Hour Ringkasan` | HRIS HR Admin, HRIS Manager, System Manager (JSON); HRIS Payroll Admin, HRIS Direksi (fungsi `after_migrate`) |
| Workspace HRIS dan desktop icon | Tanpa batasan role; item menu disaring lewat Lapis 1 |

## Lapis 3: cek role di kode
| Berkas | Fungsi | Role yang diizinkan |
|---|---|---|
| `services/pull_device.py` (`PULL_ROLES`) | Info mesin, cek dan jalankan tarikan, status, riwayat; tarikan juga butuh hak tulis `HRIS Device` | HR Admin, Manager, Operator, SM |
| Laporan Working Hour Ringkasan (`ALLOWED_ROLES`) | Membuka laporan | HR Admin, Manager, Payroll Admin, Direksi, SM |
| `hris_raw_log.py` (`EDIT_ROLES`) | Mengubah, menyetujui, menolak log | HR Admin, Manager, SM |
| `hris_working_hour.py` (`EDIT_ROLES`) | Tinjauan dan penyesuaian | HR Admin, Manager, SM |
| `services/working_hour_batch.py` | Hitung ulang working hour | HR Admin, Manager, SM |
| `services/rematch_raw_log.py` | Pencocokan ulang Raw Log | HR Admin, Manager, SM |
| `services/delete_raw_log.py` (`DELETE_ROLES`) | Hapus Raw Log (K-69) | Belum dibaca ulang untuk dokumen ini; K-69: SM dan Manager |
| `hris_attendance_settings.py` (`MANAGE_ROLES`) | Mengelola pengaturan dan token agen | Belum dibaca untuk dokumen ini |

## Audit Trail dan Data Sensitif
- Tab Audit Trail menyaring nilai berdasarkan permlevel pemanggil (K-119): pemanggil tanpa hak baca level 1 melihat `(disembunyikan)` pada nilai lama dan baru field Data Sensitif.
- Pembatasan mengikuti hak baca level 1, jadi Payroll Admin, Payroll Manager, Manager, HR Admin, Employee Admin, HR Manager, dan Direksi melihat nilainya.

## Penerapan dan pengujian
- Perubahan JSON dan role berlaku di sebuah site hanya setelah `bench --site <nama> migrate`. Perubahan Python berlaku bagi semua site pada bench yang sama setelah proses web dimuat ulang.
- Role dibuat otomatis lewat `hris/setup/roles.py` dan `hris/setup/izin.py` (hook `after_migrate`, aman diulang).
- Pengujian: `hris_employee_data/tests/uji_tampilan.py` (permlevel dan audit trail) dan `uji_izin.py` (izin tiga lapis); keduanya hanya untuk site uji.
- Custom DocPerm (izin hasil edit UI yang dapat menimpa JSON) kosong di site uji dan site kerja per 5 November 2026.

## Belum terbukti atau belum diputuskan
- Uji browser per peran dan tarikan nyata oleh Operator.
- Lampiran bawaan form Employee tidak mengikuti permlevel (dugaan): role yang hanya boleh membaca dokumen dapat membuka lampirannya. Ditinjau bersama fitur Dokumen Karyawan.
- Field Link (Company, Department, Branch) pada form Employee untuk role yang hanya punya HRIS Employee Admin: belum diuji.
- Hak `HRIS Direksi` pada Attendance Settings; hak role `HRIS Payroll Manager` pada Payroll Schedule.
- Daftar role tersebar di beberapa berkas Python; pemusatan dijadwalkan terpisah.
