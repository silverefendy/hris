# Rangkuman Repo HRIS — Folder `freebuff`

Diperiksa: 27 November 2026 (WIB). HEAD saat pemeriksaan: `8a695d1`
("Device Tool 0.8.0: info mesin di database, simpan template terenkripsi").

Folder ini adalah hasil pembacaan ulang seluruh berkas `.md`, kode app `hris`,
skrip operasi, dan aplikasi C# `tools/device_tool`. Tujuannya: satu tempat
untuk melihat isi tiap bagian, menandai yang sudah sesuai dan yang belum,
serta memberi alur kerja dari dokumen dan skrip.

## Daftar berkas rangkuman

| Berkas | Cakupan |
|---|---|
| [01-hris-attendance.md](01-hris-attendance.md) | Modul `hris_attendance`: DocType, layanan, page, report, JS |
| [02-hris-employee-data.md](02-hris-employee-data.md) | Modul `hris_employee_data`: Employee, Department, Department Rule, migrasi |
| [03-hris-payroll.md](03-hris-payroll.md) | Modul `hris_payroll`: slip, BPJS, PPh 21, komponen, period, laporan |
| [04-hris-core-setup-public-api.md](04-hris-core-setup-public-api.md) | `hris_core`, `hris_reports`, `setup/`, `patches/`, `public/`, `hooks.py`, `api/` |
| [05-docs-architecture-business.md](05-docs-architecture-business.md) | `docs/architecture/*`, `docs/business/*` |
| [06-docs-decisions.md](06-docs-decisions.md) | `docs/decisions/*` per berkas |
| [07-docs-development.md](07-docs-development.md) | `docs/development/*` |
| [08-docs-operations.md](08-docs-operations.md) | `docs/operations/*` |
| [09-docs-progress.md](09-docs-progress.md) | `docs/progress/*` |
| [10-docs-requirements-overview-security.md](10-docs-requirements-overview-security.md) | requirements, overview, security, analisis repo lama |
| [11-tools-device-tool.md](11-tools-device-tool.md) | Aplikasi C# `tools/device_tool` per berkas |
| [12-skrip-operasi.md](12-skrip-operasi.md) | `scripts/operations/k102/*` |
| [13-temuan-ketidaksesuaian.md](13-temuan-ketidaksesuaian.md) | Hasil cek "sudah sesuai atau belum" + prioritas |
| [14-alur-sistem.md](14-alur-sistem.md) | Alur absensi, payroll, Device Tool, migrasi, alur dokumen |
| [15-checklist-device-tool.md](15-checklist-device-tool.md) | Yang kurang / perlu di-upgrade di aplikasi C# |

## Ringkasan eksekutif (10 baris)

1. App `hris` adalah app Frappe v16 mandiri; dari ERPNext/HRMS hanya `Employee`
   dan `Company` yang dipakai (K-18). Empat modul berisi kode, satu kosong.
2. Absensi sudah lengkap dari mesin sampai Working Hour: dua jalur data
   (agen Windows + Pull pyzk), penjaga duplikat `punch_key`, hitung ulang
   per cakupan, hapus massal Working Hour.
3. Karyawan: `HRIS Employee` (K-116) sudah dimigrasi ke produksi lewat K-102
   (17 Nov 2026, 1.078 baris, `cek_pasca` SEMUA OK).
4. Payroll: slip Bulanan/Harian, BPJS angka tetap, PPh 21 TER + Pasal 17,
   komponen HEC/HCA, aturan per Department, kunci periode.
5. Dokumen `.md` sangat banyak (90 berkas) tetapi 9 berkas masih kerangka kosong
   dan beberapa keputusan masih berstatus "belum ada kode" padahal kodenya ada.
6. `README.md` root dan `hooks.py` masih memakai nama/lisensi placeholder
   ("HRIS CML", "mit") — sudah tercatat sebagai tertunda, belum dikerjakan.
7. Device Tool sudah sampai 0.8.0 (2026-11-26/27): tarik log, kelola salinan,
   kirim ke HRIS, snapshot user, info mesin, template jari terenkripsi.
8. Celah Device Tool yang paling perlu ditutup: template jari ditulis **tanpa
   enkripsi** ke `data\cadangan` saat "Baca template", folder `docs\` yang
   dirujuk tombol Bantuan belum ada, `README.md` Device Tool masih versi lama,
   dan `InfoMesin` membuang sebagian baris info yang dibaca dari mesin.
9. Tiga berkas `tools/device_tool` tampak "modified" di `git status`, tetapi
   `git diff` kosong: hanya perbedaan akhir baris (LF/CRLF).
10. Tidak ada perubahan kode yang dilakukan dalam pemeriksaan ini; semua hasil
    berbentuk dokumen di folder ini.

## Cara memakai folder ini

- Mulai dari [13-temuan-ketidaksesuaian.md](13-temuan-ketidaksesuaian.md) bila
  yang dicari adalah "apa yang harus diperbaiki".
- Mulai dari [14-alur-sistem.md](14-alur-sistem.md) bila yang dicari adalah
  "bagaimana sistem bekerja dari ujung ke ujung".
- Berkas 01–12 adalah rangkuman per bagian, disusun per berkas agar mudah
  dicocokkan dengan kode aslinya.
