# Rangkuman: `docs/decisions`

Diperiksa: 27 November 2026. 34 berkas keputusan, K-01 sampai K-142.

## Indeks

| Berkas | Cakupan | Catatan |
|---|---|---|
| `README.md` (28 KB) | K-01 s/d K-77 dalam tabel + indeks berkas per periode | **Diperbarui 15 Nov**; K-127 ke atas belum masuk tabel utama (hanya sebagian di indeks). K-135 tidak muncul |
| `0001-template.md` | Templat | — |
| `0002-hris-mandiri-dan-bridge-keluar.md` | K-18/K-19: HRIS mandiri, bridge keluar | Acuan utama arsitektur |
| `0003-jalur-data-mesin.md` | K-46–K-56: dua jalur data mesin | Sesuai kode |
| `0004-pull-pyzk-dan-penamaan-raw-log.md` | K-57–K-61: penamaan Raw Log, `punch_key` | Sesuai kode |
| `keputusan-2026-11-01.md` | K-78–K-88 | — |
| `keputusan-2026-11-03.md` | K-89–K-94 (navigasi, `allowed_ips`) | Navigasi masih tertunda |
| `keputusan-2026-11-03-payroll.md` | K-95–K-99 rancangan payroll | Sudah diimplementasikan sebagian |
| `keputusan-2026-11-04.md` | K-100–K-117 (termasuk K-102 migrasi, K-105 jadwal) | — |
| `keputusan-2026-11-05.md` | K-118–K-121 (Audit Trail, izin, role) | — |
| `keputusan-2026-11-06.md` | K-126 + pelaksanaan K-102 | Produksi baru jalan 17 Nov |
| `keputusan-2026-11-07.md` | K-127 Employee Pay | — |
| `keputusan-2026-11-09.md` | K-128 Period, K-129 izin | — |
| `keputusan-2026-11-09-payroll-slip.md` | K-130 rancangan slip | **Status di berkas: "belum ada kode"** — padahal slip sudah jalan & teruji |
| `keputusan-2026-11-09-absen.md` | K-131 klasifikasi absen | Sesuai kode |
| `keputusan-2026-11-10-bpjs.md` | K-133 BPJS angka tetap (revisi di berkas) | Sesuai kode |
| `keputusan-2026-11-10-pph21.md` | K-134 PPh 21 TER | Sesuai kode; verifikasi pajak belum |
| `keputusan-2026-11-11-department-rule.md` | K-135 rancangan Department Rule | **"belum disetujui, belum ada kode"** — padahal DocType + uji + patch sudah ada |
| `keputusan-2026-11-11-hris-department.md` | K-136 HRIS Department | **"belum ada kode"** — padahal sudah diimplementasikan & disalin 164 baris |
| `keputusan-2026-11-12-peminjaman-aturan.md` | K-138 peminjaman karyawan tahap 1–3 | Sesuai kode |
| `keputusan-2026-11-12-pengali-per-tanggal.md` | K-137 pengali per tanggal + notifikasi | Sesuai kode |
| `keputusan-2026-11-13-laporan-biaya.md` | Laporan biaya tenaga kerja | Sesuai kode |
| `keputusan-2026-11-14-default-tidak-dapat.md` | K-140 HEC/HCA | Sesuai kode |
| `keputusan-2026-11-14-tunjangan-slip.md` | K-139 tunjangan masuk slip | Sesuai kode |
| `keputusan-2026-11-16-per-bulan.md` | K-141 komponen Per Bulan | Sesuai kode |
| `keputusan-2026-11-17-k142.md` | K-142 pengaturan & impor PPh 21 | Disusun dari pesan commit; sesi 1–2 tidak terdokumentasi |
| `keputusan-2026-11-19-absen-6a.md` | Working Hour kosong, potongan 6a, batas hari depan | Sesuai kode |
| `keputusan-2026-11-19-hapus-working-hour.md` | Hapus massal Working Hour 6b | Sesuai kode |

## Pola masalah yang berulang

1. **Status di berkas keputusan tidak diperbarui setelah kode dibuat.**
   Tiga berkas (K-130, K-135, K-136) masih menyatakan "belum ada kode".
   Pembaca yang percaya status itu akan salah menilai kesiapan sistem.
2. **Indeks tidak lengkap.** `README.md` berhenti di K-129 untuk tabel utama;
   K-130 sampai K-142 hanya ada di berkas per tanggal. K-135 paling mudah hilang.
3. **K-142 tidak lengkap sebagai catatan keputusan**: sesi 1 dan 2 hanya
   direkonstruksi dari pesan commit, bukan dari diskusi.

## Yang masih benar-benar "belum diputuskan"

Daftar di `README.md` masih relevan untuk: merek & lisensi final, arti status
`Terkirim` pada Raw Log, aturan cuti/izin, insentif, jurnal akuntansi gaji,
`hrms` di `required_apps`, pemetaan `verify_mode`, dan navigasi (sidebar/dock).
