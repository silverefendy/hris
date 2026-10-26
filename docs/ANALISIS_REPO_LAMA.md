# Analisis Repo Lama: `hr_app` dan `hr_payroll`

Tanggal analisis: 27 Oktober 2026
Sumber: pembacaan kode repo `silverefendy/hr_app` (branch `master`) dan `silverefendy/hr_payroll` (branch `main`).

> **Catatan metode:** seluruh temuan berasal dari **membaca kode, bukan menjalankan aplikasi**. Setiap temuan perlu diuji sebelum diperbaiki. Bagian yang belum terbaca dicantumkan di akhir dokumen.

---

## 1. Tujuan Repo Baru

Repo `hris` akan menjadi **satu aplikasi HRIS** (Frappe/ERPNext v16) yang menggabungkan:

- penarikan absensi dari mesin (ZKTeco dan Solution),
- data karyawan (memakai Employee ERPNext/HRMS),
- penggajian berbasis absensi,
- laporan HRD.

Latar belakang: aplikasi HR pihak ketiga yang dipakai saat ini dinilai kurang nyaman dari sisi UX oleh tim HRD. Target awal internal, kemungkinan dijual ke publik.

---

## 2. Gambaran Dua Repo Lama

| Aspek | `hr_app` | `hr_payroll` |
|---|---|---|
| Fungsi | Tarik log absensi mesin ZKTeco (TCP port 4370) | Hitung gaji dari absensi, isi Salary Slip |
| Cara kerja | Manual: Test Connection dan Pull Logs | Hook `Salary Slip.validate`, Payroll Run batch, scheduler harian |
| DocType utama | Attendance Device, Attendance Raw Log, Operation Log | 15 DocType (Payroll Run, Formula Profile, Shift, Policy, dan lain-lain) |
| Dokumentasi | README ringkas + 3 file `docs/` | README lengkap + situs docs di `www/hr-payroll-docs` |
| Test | Belum terbaca | 15 file test |

**Alur gabungan:**

```
Mesin absensi -> Attendance Raw Log
              -> konteks absensi (hadir, telat, lembur)
              -> BPJS + PPh21
              -> Formula Profile
              -> Salary Slip
```

---

## 3. Temuan

### 3.1 `hr_app`

| # | Temuan | Prioritas |
|---|---|---|
| H1 | Data khusus perusahaan ter-hardcode (nama dan IP mesin) di `install.py`, fixtures `hooks.py`, dan dokumen troubleshooting. Wajib dihapus sebelum dibagikan atau dijual. | Tinggi |
| H2 | `Attendance Device` tidak punya field `company` dan jenis mesin (ZKTeco atau Solution). | Tinggi |
| H3 | Password mesin hanya satu, dari `site_config` (`zkteco_default_password`). | Sedang |
| H4 | Belum ada unduh template sidik jari/wajah, dan belum ada ekspor log. | Fitur baru |
| H5 | Pengecekan duplikat satu query per baris log. Pull selalu membaca semua log di mesin. | Sedang |
| H6 | Pemetaan kode verifikasi (misalnya 15 = Face) adalah asumsi. Verifikasi pada mesin nyata. | Sedang |
| H7 | Tidak ada scheduler (`scheduler_events = {}`), semua manual. | Info |

### 3.2 `hr_payroll`

| # | Temuan | Prioritas |
|---|---|---|
| P1 | **Dugaan bug `SafeFormulaEngine._eval_binop`:** semua operator dihitung sekaligus saat membuat kamus. `x + 0` dapat memicu `ZeroDivisionError`, dan perkalian float besar (misalnya `4.0 * 50000.0`) dapat memicu `OverflowError`. Test yang ada tidak mencakup kasus ini. | Tinggi, uji dulu |
| P2 | **Dua jenis Salary Component tercampur.** `Payroll Formula.salary_component` menaut ke `Payroll Salary Component` (kustom), tetapi engine mencari tipe di `Salary Component` ERPNext. Jika tidak ada padanan, tipe default menjadi `Earning`, sehingga potongan bisa tercatat sebagai pendapatan. | Tinggi |
| P3 | **Pemilihan Formula Profile** hanya berdasarkan `company` dan `is_active`; `employee_group` dan `effective_from` diabaikan. | Tinggi |
| P4 | **`PolicyService` hanyalah placeholder** (`return []`). DocType Payroll Policy, Rule, dan Assignment belum ikut menghitung gaji. | Tinggi |
| P5 | **Endpoint `@frappe.whitelist()` tanpa cek role** (`api/attendance.py`, `api/payroll.py`, `api/formula.py`). User yang login dapat meminta konteks gaji karyawan mana pun. | Tinggi (keamanan) |
| P6 | Aturan jendela absensi: check-in valid hanya +/-2 jam dari mulai shift, check-out hanya 0 sampai 4 jam setelah akhir shift. Terlambat lebih dari 2 jam atau pulang lebih awal dihitung absen. Cocokkan dengan aturan HRD. | Sedang |
| P7 | Menit telat dihitung dari jam mulai shift (bukan setelah toleransi) begitu melewati toleransi. Mungkin disengaja. | Sedang |
| P8 | `StatutoryService` mencari `base_salary` atau `gross_pay`, sedangkan konteks memakai `basic_salary` dan `gaji_pokok`. | Sedang |
| P9 | **PPh21** hanya estimator tarif datar 5% di atas PTKP bulanan. Plafon BPJS JP di-hardcode. Verifikasi ke regulasi terbaru dan konsultan pajak. | Sedang |
| P10 | Payroll Run langsung men-submit Salary Slip tanpa tahap review draft. | Sedang |
| P11 | `enqueue_pending_payroll_runs()` adalah stub (`return None`). | Rendah |
| P12 | Job `refresh_attendance_context_cache` memanggil `table_exists("tabAttendance Raw Log")`. Frappe menambahkan awalan `tab` sendiri, sehingga job kemungkinan langsung berhenti. Docstring menyebut "bulan lalu" tetapi kode memakai bulan berjalan. Verifikasi di bench console. | Sedang |
| P13 | `hooks.py` tidak mencantumkan `required_apps`, padahal bergantung pada `hr_app` dan HRMS. | Sedang |
| P14 | Query per karyawan dapat lambat pada jumlah besar. | Rendah |
| P15 | README salah memanggil `AttendanceContextService.build_for_employee(...)` seperti classmethod, dan menjanjikan resolusi dependensi komponen otomatis (`GAJI_POKOK * 0.02`). Docs di `www/` sudah benar memakai variabel konteks. | Rendah |
| P16 | `search_fields` di `Payroll Formula` dan `Payroll Policy Rule` merujuk field yang tidak ada. | Rendah |
| P17 | Workspace dibangun ulang di setiap `migrate`, dan `Payroll Run` tidak ada di daftar shortcut. | Rendah |
| P18 | Halaman di `www/` biasanya publik tanpa login di Frappe. Verifikasi apakah `/hr-payroll-docs` memang boleh publik. | Perlu dicek |

### Hal yang sudah baik

- Formula engine berbasis AST dengan whitelist, tanpa function call, dengan batas kompleksitas.
- Payroll Run matang: lock Redis, antrean, idempotensi per slip, snapshot, log event, commit per karyawan.
- Dokumentasi situs `hr-payroll-docs` akurat dan jujur soal keterbatasan.
- Versi yang diuji (menurut docs): Frappe 16.14.0, ERPNext 16.13.3, HRMS 16.4.8.

---

## 4. Kesiapan terhadap Tujuan

| Tujuan | Kondisi |
|---|---|
| Tarik absensi | Ada, perlu uji ulang |
| Multi-perusahaan | Payroll sebagian, mesin belum |
| ZKTeco dan Solution | Belum ada pembeda jenis mesin |
| Unduh sidik jari dan wajah | Belum ada |
| Ekspor log dan laporan HRD | Belum ada |
| Data karyawan | Memakai Employee ERPNext |
| Siap dijual | Belum: perlu pembersihan, lisensi, perbaikan keamanan |

---

## 5. Pertimbangan Khusus

- **Data biometrik** (sidik jari, wajah) sangat sensitif. UU Pelindungan Data Pribadi (UU No. 27 Tahun 2022), setahu saya, memasukkannya ke data pribadi spesifik. Verifikasi ke sumber resmi atau konsultan hukum. Praktik minimal: enkripsi, akses terbatas, log akses, persetujuan karyawan.
- **Template wajah** tidak selalu bisa diunduh lewat protokol ZK, tergantung model dan firmware. Uji pada mesin nyata sebelum menjanjikan fitur.
- **Lisensi**: ERPNext dan HRMS memakai GPLv3. Implikasi untuk menjual aplikasi yang bergantung padanya perlu dikonfirmasi ke dokumentasi lisensi Frappe atau konsultan hukum.
- **Nama aplikasi**: hindari `hrms` (nama aplikasi resmi Frappe HR).

---

## 6. Usulan Struktur Aplikasi Gabungan

```
hris/
  hris/
    attendance_device/   mesin, sidik jari/wajah, raw log
    employee_data/       tambahan data karyawan di atas HRMS
    payroll/             formula, shift, lembur, kebijakan
    reports/             laporan HRD
```

---

## 7. Urutan Kerja yang Diusulkan

1. Uji dugaan P1 dan P12 di bench console.
2. Putuskan model komponen gaji (P2): pakai Salary Component ERPNext saja, atau pemetaan eksplisit.
3. Rancang penggabungan app (fase diskusi, tanpa kode, sesuai alur kerja).
4. Bersihkan data hardcode (H1), tambah `company` dan jenis mesin (H2).
5. Perbaiki engine dan keamanan API (P1, P3, P5).
6. Sambungkan Policy ke perhitungan (P4).
7. Fitur baru: template sidik jari/wajah, ekspor log, laporan.
8. Tulis ulang README dan dokumentasi sesuai kondisi kode.

---

## 8. Yang Belum Terbaca

- 14 dari 15 file test `hr_payroll`, tiga laporan, sub-halaman docs lain.
- JSON `Payroll Run` dan `Payroll Policy Assignment`, patch `v1_0`, `fixtures/`, `config/`, `utils/`.
- Di `hr_app`: JS halaman console, workspace, `docs/INSTALL_UBUNTU.md`, `docs/TESTING.md`.
