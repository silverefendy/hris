# Keputusan 14 Nov 2026: Tunjangan dan Potongan Komponen Masuk Payroll Slip (3b)

## 1. Ringkasan

K-139. Komponen aktif di `HRIS Pay Component` dihitung per karyawan lewat `hitung_tunjangan_karyawan` dan disisipkan ke `HRIS Payroll Slip` sebagai baris `Otomatis`, sebelum BPJS dan PPh 21. Kode: `hris/hris_payroll/services/tunjangan_slip.py` (baru), `payroll_slip.py` dan `payroll_pph21.py` (diubah). Commit `307f4c2` (3b) dan `e001a92` (K7).

## 2. Keputusan

| Butir | Isi |
|---|---|
| K1 | Saklar `hris_tunjangan_ikut_pajak` di `site_config.json`, bawaan mati. Saat mati, tunjangan `taxable = 0` dan tidak ikut bruto PPh 21. Saat hidup, `taxable` mengikuti `is_taxable` komponen. Nilai `1` atau `"1"` hidup, `0` atau `"0"` mati, kunci tidak ada berarti mati. `payroll_pph21` membaca `taxable` pada baris Otomatis dan komponen slip sendiri; daftar pengecualian PPh 21 tetap berlaku |
| K2 | Slip berstatus Final tidak disentuh: dilewati dengan pesan "berstatus Final (terkunci)" |
| K3 | Komponen berjenis Potongan masuk sebagai baris Potongan (`taxable = 0`) dan menambah `total_deduction` |
| K4 | Komponen yang dinonaktifkan: baris Otomatis hilang saat slip dihitung ulang dan total kembali ke dasar |
| K5 | Komponen janggal (status Berlaku tanpa nominal dan nilai dasar nol): slip tetap diperbarui, dihitung Rp0, dengan peringatan di `calc_notes`; slip ikut dalam notifikasi ringkasan |
| K6 | ISI MANUAL: rincian K6 tidak tersedia pada catatan sesi ini |
| K7 | Peringatan nama ganda: bila ada baris Manual dengan nama dan jenis sama (tanpa membedakan huruf besar dan kecil, spasi pinggir diabaikan) dengan komponen otomatis bernilai lebih dari 0, satu baris peringatan masuk `calc_notes` dan slip ikut dalam ringkasan. Tidak memblokir pembuatan slip. Alasan: mencegah bonus terbayar dua kali |
| D1 | Komponen galat: karyawan dilewati dengan pesan "Masalah: ..." yang menyebut komponen penyebabnya; slip lama tidak berubah |
| D2 | Satu notifikasi ringkasan per proses massal (slip yang perlu diperiksa dan karyawan yang dilewati) |
| D3 | ISI MANUAL: rincian D3 tidak tersedia pada catatan sesi ini |

## 3. Batasan dan konsekuensi

- Komponen berbasis **Per Hari Hadir** untuk karyawan Bulanan belum didukung (perlu keputusan). Mengaktifkannya membuat seluruh karyawan Bulanan dilewati. Saat go-live (K-102), aktifkan komponen Per Bulan atau Per Slip dulu.
- Baris Manual dan baris Otomatis boleh bernama sama; keduanya tidak saling menimpa. K7 hanya memperingatkan.
- Tidak ada perubahan struktur DocType yang sudah berjalan.
- Komponen yang diuji adalah data demo (`BONUS`, `POT_LAIN`, `TJ_MAKAN`). Nilai tunjangan sungguhan dan `is_taxable` menunggu HRD dan konsultan pajak.

## 4. Hasil uji (site uji `hris-uji.local`)

| Uji | Hasil |
|---|---|
| `uji_tunjangan_slip_integrasi` | OK 34, GAGAL 0, tanpa SKIP (M1-M4, U1-U8 termasuk U1b, U2e, U2f, U5b, dan Z1-Z4) |
| Regresi sebelum K7 | 40 uji SAMA dengan patokan |
| Regresi setelah K7 | 8 uji slip SAMA: `uji_payroll_slip` 77, `uji_slip_massal` 19, `uji_pph21_jadwal` 9, `uji_pph21_mingguan` 16, `uji_pph21_slip` 22, `uji_bpjs_slip` 68, `uji_department_rule_slip_utuh` 16, `uji_p9_slip` 6 |
| Sisa data | Z1-Z4 OK: normalisasi data uji di-rollback, tabel kunci kembali ke jumlah semula |

Catatan proses: tiga GAGAL pada putaran pertama (U1, U2, U5) berasal dari uji yang mencocokkan baris hanya berdasarkan nama, sehingga baris Manual ikut terhitung. Kode 3b benar; uji diperbaiki agar hanya menghitung baris `Otomatis`.

## 5. Belum teruji

- Kecepatan pada 1078 Employee Active dengan banyak komponen aktif.
- Data produksi (setelah K-102) dan nilai tunjangan nyata.
- Karyawan Harian dengan komponen Per Hari Hadir.
- Saklar `hris_tunjangan_ikut_pajak` di site kerja.
- Uji browser (hanya uji skrip yang dijalankan).
