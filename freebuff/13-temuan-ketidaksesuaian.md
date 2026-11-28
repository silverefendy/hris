# Temuan: Sudah Sesuai atau Belum

Diperiksa: 27 November 2026. Hasil pemeriksaan silang dokumen `.md` ↔ kode ↔
skrip ↔ aplikasi C#. Diurutkan dari yang paling berdampak.

## A. Dokumen yang bertentangan dengan kode/keadaan (perlu diperbaiki)

| # | Berkas | Isi dokumen | Kenyataan | Dampak |
|---|---|---|---|---|
| A1 | `scripts/operations/k102/README.md` | "Status (12 Nov 2026): migrasi produksi K-102 BELUM dijalankan" | Selesai 17 Nov 2026, `cek_pasca` SEMUA OK | Tinggi — pembaca bisa mengira produksi belum dimigrasi |
| A2 | `docs/decisions/keputusan-2026-11-09-payroll-slip.md` | "belum ada kode" | Slip + item + layanan hitung sudah ada & teruji (OK 77) | Tinggi — status kesiapan salah |
| A3 | `docs/decisions/keputusan-2026-11-11-department-rule.md` | "rancangan, belum disetujui, belum ada kode" | `HRIS Department Rule` + layanan + patch + uji sudah ada | Tinggi |
| A4 | `docs/decisions/keputusan-2026-11-11-hris-department.md` | "belum ada kode" | `HRIS Department` ada, 164 baris disalin ke produksi | Tinggi |
| A5 | `docs/development/testing.md` | "Unit test per modul belum ditulis" | ±80 berkas uji di `tests/` dan akar modul | Sedang |
| A6 | `tools/device_tool/README.md` | "Status: tahap 2"; "Comm Key … kata sandi aplikasi" | Versi 0.8.0; Comm Key memakai DPAPI tanpa sandi | Sedang |
| A7 | `docs/progress/status.md` | Header "Diperbarui: 17 November 2026" | Ada entri 21 Nov 2026 | Rendah |
| A8 | `docs/progress/roadmap.md` | Roadmap 28 Okt | Tidak lagi mencerminkan pekerjaan Nov | Rendah |
| A9 | `docs/security/permissions.md` | Berlaku 5 Nov | Ada 4 role + izin baru setelahnya (K-129, K-140, K-142) | Sedang |
| A10 | `docs/architecture/api.md`, `data-model.md` | Per 29 Okt | Banyak DocType/endpoint baru tidak tercatat | Sedang |
| A11 | `docs/progress/c1-c4-tinjauan-koreksi.md` | "C4 tahap 1 … belum di produksi" | C4 tahap 5 live 21 Nov | Rendah |
| A12 | `CLAUDE.md` | Menyebut `docs/architecture/attendance-flow.md` | Berkas ada di `docs/business/process-flows/` | Rendah |

## B. Dokumen yang masih kosong (kerangka tanpa isi)

`docs/architecture/architecture.md`, `docs/architecture/integration.md`,
`docs/business/business-rules.md`, `docs/development/coding-standards.md`,
`docs/development/contribution.md`, `docs/development/development.md`,
`docs/operations/configuration.md`, `docs/operations/installation.md`,
`docs/operations/troubleshooting.md`, `docs/overview/project-overview.md`,
`docs/requirements/requirements.md`,
`docs/requirements/functional-requirements.md` (hanya header),
`docs/requirements/non-functional-requirements.md` (hanya header).

Tiga belas berkas. Yang paling merugikan: `project-overview.md` (tidak ada
ringkasan proyek) dan `functional-requirements.md` (tidak ada daftar kebutuhan).

## C. Kode yang tidak konsisten dengan dirinya sendiri

| # | Letak | Temuan | Saran |
|---|---|---|---|
| C1 | `hris/modules.txt` | `HRIS Reports` terdaftar tetapi modulnya kosong | Isi atau hapus dari `modules.txt` |
| C2 | `hris/setup/install.py` vs `hris/setup/roles.py` | Dua daftar role terpisah (6 + 4) | Satukan, `izin.py` memanggil satu sumber |
| C3 | `hris/hris_attendance/` | Tiga uji (`uji_device_user`, `uji_kirim_agen`, `uji_perbandingan`) di akar modul; uji lain di `tests/` | Pindahkan ke `tests/` |
| C4 | `hris/hooks.py` | `app_title`/`app_license` masih "HRIS CML"/"mit" | Putuskan merek & lisensi (butir tertunda) |
| C5 | `hris_attendance/services/working_hour.py` | Query punch per karyawan, bukan per mesin | Ukur dulu; ubah hanya bila terbukti lambat |
| C6 | `hris_attendance/services/punch_ingest.py` | Docstring masih menyebut nama dokumen sebagai penjaga duplikat | Rapikan ke `punch_key` |

## D. Temuan di `tools/device_tool` (rinci di [15](15-checklist-device-tool.md))

| # | Temuan | Bukti |
|---|---|---|
| D1 | Template jari ditulis **tanpa enkripsi** ke `data\cadangan` saat "Baca template" | `Dev.ReadTemplates` memakai `File.WriteAllText`; berkas `bin/data/cadangan/tmpl_*.hdttmpl` ada di disk |
| D2 | `InfoMesin` membuang sebagian baris info yang sudah dibaca `Dev.InfoRows` | `Peta` tidak memuat "Nama perangkat", "Vendor", "Password terdaftar", "Catatan operasi", "Sisa jari/user/log", "Angka 22" |
| D3 | Tombol "Buka folder panduan" menuju folder yang tidak ada | `MainForm.OnPanduan` mencari `docs\`; folder itu belum dibuat |
| D4 | Versi aplikasi hanya konstanta di `MainForm.cs` | Tidak ada assembly/file version, ikon, atau cap build |
| D5 | Tidak ada uji untuk `KirimHris`, `BacaCsv`, `Salinan`, `Brankas`, `Peran` | Folder `uji_sqlite` hanya menguji lapisan database |
| D6 | Kata sandi bawaan (`user123` … `administrator123`) masih berlaku, tanpa paksaan ganti | `Peran.Akun.Bawaan`; dokumen 0.7.2 mencatat "ganti sandi bawaan" sebagai tertunda |
| D7 | Login tanpa batas percobaan (hanya `Thread.Sleep(800)`) | `Akun.Masuk` |
| D8 | `GetStrCardNumber(out k)` dipanggil tanpa indeks mesin | `Dev.ListUsersLengkap` — bergantung pada user terakhir yang dibaca |

## E. Yang sudah sesuai (tidak perlu diubah)

- Kontrak `push_punches` di `agent-api.md` cocok dengan `punch_ingest.py` dan
  `KirimHris.cs` (batch 500, WIB, hasil per baris).
- `cek_pasca.sh` memeriksa hal yang sama dengan yang dicatat `status.md`
  (DocType, role, `allow_import`, komponen aktif, kunci pohon kerja).
- `.gitignore` dan `build.ps1` Device Tool benar-benar menolak data pribadi
  masuk Git (sudah diperiksa isinya).
- `docs/development/doctype-checklist.md`, `ai-workflow.md`,
  `device-tool-0.7.2-catatan.md`, `process-flows/hapus-working-hour.md` sesuai
  kode.
- Semua aset yang dirujuk `hooks.py` (`public/js/*`, `css`, `images/hris-logo.svg`)
  benar-benar ada.

## F. Urutan perbaikan yang disarankan

1. A1–A4 (status keputusan & runbook) — satu berkas masing-masing, cepat,
   mencegah salah paham.
2. D1 (template jari terenkripsi) — menyangkut data biometrik.
3. D2 (info mesin) dan D3 (folder panduan) — perbaikan kecil, terasa langsung.
4. B (dokumen kosong) — isi minimal `project-overview` dan
   `functional-requirements`, sisanya menyusul.
5. C1–C3 (kerapian kode) — sekali jalan saat ada sesi perapian.
6. A5–A10 — sinkronisasi dokumen teknis dengan kode.
