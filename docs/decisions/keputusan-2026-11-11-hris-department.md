# Keputusan 11 November 2026: HRIS Department sebagai sumber utama (K-136, arah disetujui)

Status: **arah disetujui Efendy 11 Nov 2026 (09:12 WIB); desain rinci belum disetujui; belum ada kode.** Nomor K-136 dipakai karena K-135 terakhir; ubah bila perlu.

## 1. Keputusan

HRIS Department menjadi sumber utama data Department. Department ERPNext hanya salinan (satu arah), sama seperti HRIS Employee. Penempelan aturan (Department Rule, K-135) dan peminjaman karyawan (P9) menunjuk ke HRIS Department.

## 2. Temuan (baca-saja, 11 Nov 2026)

| Temuan | Arti |
|---|---|
| DocType HRIS Department belum ada | Dibuat baru |
| Department ERPNext berbentuk pohon; satu company; nama berakhiran " - CML"; sampai tingkat kru tukang | Pohon dan nama harus dipertahankan |
| Tabel HRIS Employee belum ada di erp (K-102 belum dijalankan) | HRIS Department bisa dibuat sebelum migrasi karyawan produksi |
| HRIS Shift Assignment: 0 baris di erp dan hris-uji.local | Mengganti field pinjam tidak berisiko data |
| Tempat yang menunjuk Link ke Department ERPNext: HRIS Employee, HRIS Employee Group, HRIS Working Hour (field, daftar, laporan), HRIS Payroll Slip, dialog Payroll Period, custom field di `setup/install.py` | Penggantian target Link dilakukan sendiri dan diuji |

## 3. Urutan aman (arah disetujui)

| Tahap | Isi |
|---|---|
| 1 | Buat DocType HRIS Department (tidak menyentuh yang berjalan) |
| 2 | Salin data Department ERPNext ke HRIS Department (mode COBA dulu) |
| 3 | Sinkron HRIS Department ke Department ERPNext |
| 4 | Ganti target Link di tempat-tempat pada bagian 2 (latihan restore, seperti K-102) |
| 5 | Department Rule (K-135) dan field Dipinjam ke Department |

## 4. Jawaban Efendy (11 Nov 2026, 09:35 WIB)

| # | Hal | Jawaban |
|---|---|---|
| 1 | Pewarisan aturan lewat pohon | Aturan Department berlaku untuk semua cabang; cabang yang punya setelan sendiri memakainya; bila tidak ada, ikut induk |
| 2 | Department bawaan ERPNext | Tidak disalin dulu (hindari salah hapus). Harus diperiksa dahulu bahwa tidak ada karyawan memakainya |
| 3 | Akhiran " - CML" | Dipertahankan (ikut saran Claude) |
| 4 | Siapa mengelola Department | HRD saja (HRD dan manajernya mengurus employee); peran Payroll tidak menulis. Hak baca untuk peran Payroll perlu dikonfirmasi dan diuji |
| 5 | Kru tukang | Department mirip Employee Group untuk kru; keduanya tetap ada |

## 5. Data awal (erp, 11 Nov 2026)

178 Department (160 daun, 18 induk, 1 company); 95 dipakai oleh 1078 karyawan; 3 karyawan tanpa Department. Custom field HRIS pada Department ERPNext: `hris_device_dept_id` (kegunaan menunggu pembacaan kode).

## 6. Hasil baca ke-4 (11 Nov 2026, 09:57 WIB)

| Temuan | Keputusan |
|---|---|
| `hris_device_dept_id` hanya didefinisikan di `setup/install.py`, tidak dipakai kode | Tidak dibawa ke HRIS Department; field di Department ERPNext dibiarkan |
| 13 Department bawaan ERPNext: 0 karyawan, 0 cabang | Tidak disalin (sesuai keputusan 11 Nov) |
| 59 Department daun tanpa karyawan (bukan bawaan) | Tetap disalin; dapat dinonaktifkan nanti |
| 482 karyawan menunjuk Department induk | HRIS Department tidak membatasi karyawan hanya ke daun |
| 3 karyawan Active tanpa Department (HR-EMP-00730, HR-EMP-00856, HR-EMP-00879) | HRD mengisi Department (permintaan E7); menurut P10 gaji mereka ditolak sampai terisi |

Salinan data tahap 2: 164 Department (178 dikurangi akar dan 13 bawaan), nama dipertahankan.

## 7. Tahap 1 (DocType HRIS Department)

DocType pohon di modul Employee Data: nama `{nama} - {singkatan company}`, akar otomatis sebagai induk, induk wajib Is Group, company wajib selain akar. Izin: menulis HRIS HR Admin dan HRIS Manager; hapus System Manager; baca peran Payroll, Direksi, dan Employee Admin. Belum ada: sinkron ke Department ERPNext (tahap 3) dan tab Audit Trail HRIS (pola menunggu dibaca). Uji: `uji_hris_department.py`.

## 8. Belum diputuskan

- Bentuk pewarisan: aturan cabang menggantikan seluruh aturan induk, atau hanya parameter yang diisi cabang (tahap 5).
- Hak baca peran Payroll pada HRIS Department: dibuat membaca saja; perlu diuji pada pemilih Department.
- Cara tab Audit Trail HRIS ditambahkan.

## 9. Hasil tahap 1 sampai 3 (11 Nov 2026, hris-uji.local)

| Tahap | Hasil | Commit |
|---|---|---|
| 1 DocType HRIS Department | Uji OK 15 GAGAL 0. Sempat rusak karena karakter Tab hilang saat paste ke terminal; diperbaiki dengan spasi | 68e4955, 2187a5b, 8ce82c6 |
| 2 Salin Department dan akar | COBA lalu salin OK: 164 Department ditambah akar "All Departments", 13 bawaan dilewati, nama sama semua | ebb9339 |
| 3 Sinkron ke Department ERPNext, adopsi, tab Audit Trail | Adopsi 165 dari 165; uji OK 13 GAGAL 0 | 5c57a8c |

Keputusan tambahan (Efendy, 11 Nov): nama dan Company tidak boleh diubah setelah tersinkron; nonaktif di HRIS menonaktifkan Department ERPNext; 164 Department yang sudah ada diadopsi, bukan dibuat ulang. Belum teruji: tab Audit Trail di browser.

## 10. Inventaris tahap 4 (ganti Link Department)

- Link JSON ke Department: 5 tempat; 4 diganti (Employee, Payroll Slip, Working Hour, Employee Group), `erpnext_department` dibiarkan.
- Data site uji: HRIS Employee 1075, Payroll Slip 1, Working Hour 5559 punya Department dan semuanya ada di HRIS Department.
- Kode yang merujuk Department: `employee_group.py`, dialog `hris_payroll_period.js`, filter laporan Working Hour Ringkasan (js dan py), dialog `hris_working_hour_list.js`.
- Risiko: folder kode dipakai bersama site erp. Ganti JSON tidak berdampak di erp sampai migrate; ganti kode py/js langsung berdampak. Maka tahap 4a (JSON) dikerjakan lebih dulu; 4b (kode) menunggu keputusan: ditunda sampai migrasi K-102 atau dibuat toleran.
- HRMS: hanya `hooks.py` (required_apps) dan `setup/install.py` yang menyebut HRMS; tidak ada Link JSON ke DocType HRMS.

## 11. Izin baca dan arah Department Rule (11 Nov 2026)

| Hal | Keputusan / hasil | Commit |
|---|---|---|
| Izin baca HRIS Department | Ditambah untuk HRIS Attendance Operator dan HRIS Attendance Supervisor (read dan report). Terverifikasi di database hris-uji.local (9 peran, tanpa Custom DocPerm). Dropdown dan nilai Department tampil di Employee Group dan Working Hour. Uji browser dengan akun yang hanya berperan Operator/Supervisor belum dilakukan | ad21bb5 |
| Pewarisan Department Rule | Per parameter: kosong ikut induk, terisi menimpa |  |
| Parameter pertama | `overtime_multiplier` (pengganti konstanta `PENGALI_LEMBUR` di `payroll_slip.py`). Nilai bawaan di Department akar |  |
| PPh 21 | Tetap global (HRIS PPh21 Settings), tidak masuk Department Rule |  |
| Parameter Shift | Tidak digandakan di Department Rule sampai jawaban HRD E1/E2 |  |
| Pengganti konstanta di kode | Menyentuh kode py, jadi masuk tahap 4b / migrasi K-102 |  |

Peta parameter aturan hitung saat ini: HRIS Shift (toleransi, blok potongan, batas lembur), konstanta kode (`PENGALI_LEMBUR`), HRIS PPh21 Settings (pajak). HRIS Attendance Settings hanya berisi pengaturan agent.

## 12. Department Rule tahap 5a (11 Nov 2026)

| Hal | Keputusan / hasil | Commit |
|---|---|---|
| DocType HRIS Department Rule | Modul HRIS Payroll. Kolom: department, effective_from, is_active, overtime_multiplier. Nama `DR-YYMM-####` dengan nomor lanjut (autoname di kode, penghitung kunci `DR-`). Aturan unik: tidak ada dua aturan aktif dengan Department dan tanggal berlaku sama | 49de98d |
| Layanan `resolve` | `services/department_rule.py`: pewarisan per parameter naik ke akar; tanpa nilai sampai akar = error (P10). Uji OK 13 GAGAL 0 | 49de98d |
| Nilai konstanta | `PENGALI_LEMBUR = 1.0` (K-98), hanya dipakai di `payroll_slip.py` (baris 20, 48, 261). Slip menyimpan salinan `overtime_multiplier` (read-only) | |
| Aturan akar | Satu aturan `overtime_multiplier = 1.0` di akar, dibuat lewat patch idempoten (site uji dan erp K-102) | |
| Tanggal acuan slip | `period_end`. Aturan baru di tengah periode berlaku untuk seluruh slip periode itu | |
| Pengali 1.0 | Ditanyakan ke HRD bersama E1/E2; pertanyaan baru E8: perlu pemecahan per hari bila aturan berubah di tengah periode? | |
| Belum diuji | Nomor DR- lanjut lintas bulan (cek Desember); nilai 0 di database sebagai "ikut induk"; penyambungan ke `payroll_slip.py` (tahap 4b) | |
