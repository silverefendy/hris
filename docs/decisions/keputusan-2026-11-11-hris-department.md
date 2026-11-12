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

## 13. Patch aturan akar dan keputusan tahap 4b (11 Nov 2026)

| Hal | Keputusan / hasil | Commit |
|---|---|---|
| Patch aturan akar | `hris/patches/v1_0/buat_aturan_akar_department.py`, terdaftar di `[post_model_sync]`. Membuat satu aturan di akar: pengali lembur 1.0, berlaku 2000-01-01. Idempoten. Di hris-uji.local: DR-2611-0006, `resolve` dari daun mengembalikan 1.0 | f2445f0 |
| Karyawan tanpa Department (4b) | Memakai aturan akar | |
| `period_end` kosong (4b) | Slip dilewati dengan pesan jelas | |
| Titik sambung 4b | Satu pemanggil produksi `hitung_komponen` di `payroll_slip.py` baris 220; nilai pengali dihitung sekali dan dipakai juga di baris 261 (salinan ke slip) | |
| Urutan malam K-102 | Migrate (patch akar ikut jalan), lalu kode 4b aktif | |
| Belum diuji | Migrate kedua tanpa duplikasi; nomor DR- lintas bulan; penyambungan 4b | |

## 14. Department Rule pindah modul dan tab Audit Trail (11 Nov 2026)

| Hal | Keputusan / hasil |
|---|---|
| Modul | HRIS Department Rule dipindah dari HRIS Payroll ke HRIS Employee Data (folder `hris_employee_data/doctype/hris_department_rule`). Layanan `department_rule.py` dan uji tetap di `hris_payroll` |
| Audit Trail | Field `audit_trail_tab` dan `audit_trail_html` ditambah; JS form memanggil `hris.audit.render(frm)` |
| Catatan teknis | Perubahan DocType di JSON perlu menaikkan `modified`, kalau tidak sinkron migrate bisa melewatkannya |
| Cek browser form (sebelum pindah) | Daftar dan form OK; pesan "Isi minimal satu parameter" dan "duplikat aktif" tampil benar |
| Cek browser Audit Trail (12 Nov 2026) | Lulus di hris-uji.local: tab tampil; baris "(dokumen dibuat)" tercatat; ubah Pengali Lembur 1 → 1,50 → 1 tercatat 2 baris; nilai dikembalikan ke 1,00. Activity bawaan Frappe mencatat perubahan yang sama |

## 15. Tahap 4b: pengali lembur dari Department Rule (12 Nov 2026)

| Hal | Keputusan / hasil |
|---|---|
| Pilihan | A: kode toleran. Bila tabel `HRIS Department Rule` belum ada, memakai konstanta `PENGALI_LEMBUR` (1.0); bila ada, membaca Department Rule |
| Fungsi | `_pengali_lembur(department, period_end)` di `hris/hris_payroll/services/payroll_slip.py`; mengembalikan `(nilai, None)` atau `(None, pesan)` |
| Aturan | Tanpa Department memakai akar "All Departments"; `period_end` kosong membuat slip dilewati; `resolve` gagal membuat slip dilewati dengan pesan (tidak diam-diam 1.0) |
| Titik sambung | Dihitung sekali sebelum `hitung_komponen`, dipakai juga untuk salinan `overtime_multiplier` ke slip |
| Uji | `hris/hris_payroll/tests/uji_department_rule_slip.py` (site uji, data uji dihapus sesudahnya) |
| Alasan Pilihan A | Folder kode dipakai bersama erp; erp belum punya tabel Department Rule sampai K-102, jadi kode wajib tahan terhadap ketiadaan tabel |
| Tindak lanjut | Setelah K-102 selesai dan stabil, cabang "tabel tidak ada" boleh dihapus. Belum diuji: migrate kedua tanpa duplikasi aturan akar, nomor DR- lintas bulan, perilaku untuk Department yang tidak ada di HRIS Department |

## 16. Koreksi tahap 4b (12 Nov 2026)

| Hal | Hasil |
|---|---|
| Temuan | Uji `uji_department_rule_slip.py` pada commit 5d0f06a: S0, T4, T6, T7a-d lulus; T1, T2, T3 GAGAL (nilai 0.0, seharusnya 1.0 / 1.5 / 1.0); T5 (Department tidak dikenal) melempar TypeError. Penyebab dugaan: nilai balik `resolve` bukan angka, sedangkan helper memakai `flt(...)` yang mengubah nilai non-angka menjadi 0.0 tanpa galat |
| Status | ~~4b belum benar~~ (kedaluwarsa; diperbaiki di 66b4825, hasil akhir di bagian 17). Bagian 15 di atas menggambarkan rancangan, bukan hasil yang sudah terbukti |
| Aman | erp: tabel Department Rule belum ada, `_pengali_lembur` mengembalikan (1.0, None), terbukti 12 Nov 2026. Regresi di hris-uji.local: department_rule 13 OK, payroll_slip 77 OK, slip_massal 19 OK (belum tentu memeriksa nilai pengali pada slip utuh) |
| Larangan | (dicabut, lihat bagian 17) Jangan migrasi K-102 sebelum 4b diperbaiki dan seluruh uji baru lulus |
| Perbaikan | Baca isi `resolve`, sesuaikan helper, tolak nilai kosong atau tidak positif dengan pesan, periksa Department ada sebelum `resolve`, tambah uji; lalu perbarui bagian ini |

## 17. Hasil akhir tahap 4b dan langkah Department di runbook (12 Nov 2026)

| Hal | Hasil | Commit |
|---|---|---|
| Perbaikan 4b | `_pengali_lembur` membaca dict hasil `resolve`, menolak nilai tidak valid dan Department tidak dikenal. `uji_department_rule_slip.py` OK 15 GAGAL 0 | 66b4825 |
| Uji slip utuh | `uji_department_rule_slip_utuh.py` OK 16 GAGAL 0 di hris-uji: pengali slip 1.0 (hanya aturan akar), 1.0 (aturan 2099 belum berlaku), 1.75, 2.0 (setelah hitung ulang); komponen Lembur sesuai tarif jam x 2 jam x pengali (selisih di bawah 1 rupiah, pembulatan) | 297dc6a |
| Patch aturan akar | Idempoten; migrate kedua tidak menggandakan aturan (8 uji OK) | 7020e37 |
| Risiko urutan (terbukti di gladi) | `migrate` pada database tanpa pohon Department membuat patch aturan akar "dilewati" dan Patch Log tetap mencatatnya selesai, sehingga aturan akar tidak terbentuk lewat migrate | |
| Penanganan (opsi B) | `migrasi_department.py` memanggil `execute()` patch dalam transaksi yang sama dengan salinan; hasil harus tepat 1 aturan akar aktif, kalau tidak rollback total | dd3c1ea |
| Runbook (di luar repo, `/home/it/runbook_k102/`) | Perintah `department <site> coba\|salin`; langkah 2b di `produksi_k102.sh` dan `gladi_k102.sh` | tidak di repo |
| Gladi di hris-uji (cadangan produksi pra-migrate) | Langkah 2b: salin 164 Department, aturan akar 1, commit. Lalu cek SAMA, migrasi 1078 HRIS Employee, Employee ERPNext tidak berubah; Audit Trail 3 HRIS Employee bersih (browser, dilaporkan Efendy); restore mengembalikan ke 0 | |

Urutan malam K-102: maintenance ON, migrate, **2b (department coba lalu salin)**, restart, kondisi awal dan cek, jalankan migrasi, maintenance OFF.

Belum terbukti: langkah 2b di erp sungguhan (hanya di hris-uji dengan cadangan erp); waktu proses slip massal untuk 1078 karyawan; uji browser dengan akun Operator/Supervisor; nomor DR- lintas bulan (Desember); jawaban HRD untuk E1, E2, E7, E8 dan pengali 1.0.
