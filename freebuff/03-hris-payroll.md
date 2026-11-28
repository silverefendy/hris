# Rangkuman: Modul `hris_payroll`

Diperiksa: 27 November 2026. Modul terbesar dari sisi jumlah berkas
(±19 DocType, 18 layanan, ±60 berkas uji).

## DocType

| DocType | Isi |
|---|---|
| `HRIS Payroll Schedule` (+ `_cutoff`) | Jadwal gaji: periode, tanggal bayar, cut-off |
| `HRIS Payroll Period` | Periode gaji: Draft → Ditinjau → Final, kunci WH dan baris gaji |
| `HRIS Payroll Slip` (+ `_item`, `_bpjs`) | Slip gaji: komponen Otomatis/Manual, BPJS, PPh 21, potongan absen |
| `HRIS Employee Pay` | Gaji per karyawan: Bulanan/Harian, baris gaji berlaku, izin per baris |
| `HRIS Employee Component` (HEC) | Penetapan komponen per karyawan |
| `HRIS Component Assignment` (HCA) | Penetapan komponen per Grup/Department + pratinjau |
| `HRIS Pay Component` | Katalog komponen: jenis, Waktu Bayar (Per Bulan/Per Hari Hadir), kena pajak |
| `HRIS BPJS Rate` | Angka tetap iuran BPJS per program |
| `HRIS PPh21 Settings` | Saklar aktif, PTKP nominal, biaya jabatan, pemetaan kategori |
| `HRIS PPh21 TER Rate` | Tarif TER per kategori (impor CSV) |
| `HRIS PPh21 Pasal17 Rate` | Tarif Pasal 17 (`P17-YYMM-NNNN`, terpisah) |
| `HRIS PPh21 PTKP Map`, `HRIS PPh21 Exempt Item` | Pemetaan PTKP, pengecualian |

## Layanan

| Berkas | Baris | Fungsi |
|---|---|---|
| `payroll_slip.py` | 614 | Mesin hitung slip: gaji pokok, absen, lembur, komponen, BPJS, PPh 21 |
| `payroll_summary.py` | 302 | Ringkasan payroll per periode (dipakai Page Payroll Summary) |
| `payroll_pph21.py` | 253 | PPh 21: TER bulanan, bruto, NPWP/NIK, potongan sekali sebulan (slip terakhir) |
| `komponen_slip.py` | 206 | Penyisipan komponen ke slip |
| `pengecualian.py` | 175 | Komponen pengecualian |
| `cakupan_komponen.py` | 166 | Penentuan cakupan HEC/HCA |
| `hec_massal.py` | 159 | Tombol massal HEC |
| `tunjangan_slip.py` | 146 | Tunjangan/potongan masuk slip sebelum BPJS dan PPh 21 |
| `payroll_bpjs.py` | 125 | BPJS angka tetap, dipotong sekali sebulan |
| `department_rule_notify.py` | 101 | Notifikasi slip Draft saat Department Rule berubah |
| `payroll_schedule.py` | 92 | Enam jenis jadwal, giliran slip pertama/terakhir |
| `hca_pratinjau.py` | 81 | Pratinjau penerima HCA |
| `period_lock.py` | 77 | Kunci periode |
| `pph21_rate.py` | 72 | Pembacaan tarif TER/Pasal 17 |
| `department_komponen.py` | 59 | Nilai komponen per Department |
| `department_rule.py` | 58 | Pewarisan aturan Department |
| `giliran_bulan.py` | 32 | Penentuan slip pertama/terakhir bulan bayar |
| `pay_type.py` | 31 | `pay_type_on`: Bulanan/Harian dari Employee Pay |

## Page dan report

| Berkas | Isi |
|---|---|
| `page/payroll_summary/payroll_summary.js` (268) | Payroll Summary per periode, dialog penerima HCA |
| `report/hris_biaya_tenaga_kerja` (208) | Laporan biaya tenaga kerja per Department/Grup, hari pinjam dibebankan ke tujuan |

## Uji (ringkas)

Kelompok besar: `uji_payroll_slip`, `uji_pph21_slip` (215), `uji_bpjs_slip` (454),
`uji_slip_massal`, `uji_payroll_period`, `uji_employee_pay`, `uji_tunjangan_slip_integrasi` (296),
`uji_pph21_jadwal`, `uji_pph21_mingguan`, `uji_department_rule_slip_utuh`,
`uji_wh_hapus_*` (4 berkas), `uji_jam_koreksi_*` (5 berkas), `uji_e1_*`, `uji_hca*`.
Semua uji berada di `tests/` kecuali `bandingkan_slip.py` dan `siapkan_data_uji_hapus_ui.py`.

## Kondisi

- Semua fitur payroll ada di site uji dan sudah di-push; produksi mengikuti
  `migrate` (K-102 sudah jalan 17 Nov, tabel kosong terbentuk).
- **Produksi: `HRIS PPh21 TER Rate` masih 0 baris dan Settings nonaktif** —
  PPh 21 belum boleh diaktifkan sebelum tarif resmi diimpor.
- Belum diverifikasi HRD/konsultan pajak: rumus TER, tarif resmi, pemetaan PTKP,
  NPWP, aturan harian/mingguan, premi BPJS bagian perusahaan.
- Slip Harian dengan data nyata dan pengaruh pajak Potongan Absen masih terbuka.
