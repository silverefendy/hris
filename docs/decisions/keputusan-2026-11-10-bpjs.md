# Keputusan 10 November 2026: BPJS pada HRIS Payroll Slip (K-133, rancangan)

Status: **disetujui Efendy (10 Nov 2026, 06:53 WIB, "lanjutkan semuanya"); diterapkan bertahap dalam empat langkah: (1) HRIS BPJS Rate, (2) field peserta di HRIS Employee, (3) tabel informasi dan perhitungan pada slip, (4) uji browser per peran dan sinkron dokumen.**
Nomor K-133 dipakai karena K-132 sudah menjadi usulan di `status.md`; ubah bila perlu.

## 1. Konteks

`HRIS Payroll Slip` tahap pertama (K-130) sudah teruji di site uji dan belum memuat BPJS maupun PPh 21. Dokumen ini merancang BPJS (tahap 1). PPh 21 (tahap 2) dan jembatan ke ERPNext (tahap 3) dibahas setelahnya.

## 2. Hasil pengecekan fitur bawaan (10 Nov 2026)

| Pemeriksaan | Hasil |
|---|---|
| `apps/hrms/hrms/regional` | Hanya `india` dan `united_arab_emirates` |
| Pencarian `pph 21`, `bpjs`, `ptkp` pada `.py` dan `.json` di `hrms/hrms` dan `erpnext/erpnext` | Tidak ada berkas |
| Kesimpulan | Tidak ada fitur Indonesia bawaan. HRIS membuat sendiri (K-18), tanpa mengubah HRMS atau ERPNext |

## 3. Sudah diputuskan (Efendy, 10 Nov 2026)

| Hal | Keputusan |
|---|---|
| Tahapan | Tahap 1 BPJS; tahap 2 PPh 21 (TER); tahap 3 jembatan ke ERPNext (data karyawan dan slip Final ke Salary Slip) |
| Tarif | Dapat diubah lewat pengaturan karena peraturan bisa berubah; ada bagian karyawan dan bagian perusahaan |
| Dasar upah | Gaji Pokok |
| Karyawan Harian | Dasar = total gaji satu bulan; dipilih per karyawan: versi final (setelah potongan absensi) atau versi penuh (tanpa potongan absensi) |
| Peserta | Dipilih per karyawan (sebagian Harian dan Mingguan ikut, sebagian tidak) |
| Tempat pilihan | `HRIS Employee` |
| Pembanding | Tidak ada slip lama; uji memakai hitungan tangan dan tarif contoh |
| Sumber tarif resmi | Diverifikasi HRD, BPJS, atau konsultan pajak. Dokumen ini tidak memuat angka resmi |
| Waktu potong | BPJS dipotong sekali satu bulan, juga untuk karyawan Harian dan Mingguan (Efendy, 10 Nov 06:36 WIB) |
| Slip pembawa potongan | Slip terakhir yang tanggal bayarnya jatuh di bulan itu; bulan dihitung dari tanggal bayar (Efendy, 10 Nov 06:53 WIB, opsi A) |
| Pilihan peserta | Per program: BPJS Kesehatan, JHT, JP, JKK, JKM |
| Yang mengisi pilihan peserta | HRD (HRIS HR Admin dan HRIS Employee Admin); HRIS Payroll Admin hanya baca |
| Gaji Penuh karyawan Harian | Upah harian x jumlah hari kerja terjadwal, tanpa memotong ketidakhadiran (dikonfirmasi) |

## 4. Rancangan tahap 1

### 4.1 DocType baru `HRIS BPJS Rate` (modul HRIS Payroll)

Satu baris = satu program pada satu tanggal berlaku.

| Field | Tipe | Keterangan |
|---|---|---|
| `company` | Link Company | wajib |
| `program` | Select | BPJS Kesehatan, JHT, JP, JKK, JKM; wajib |
| `risk_class` | Data | hanya untuk JKK (tarif JKK bergantung kelas risiko); kosong untuk program lain |
| `employee_rate` | Percent | bagian karyawan |
| `company_rate` | Percent | bagian perusahaan |
| `wage_cap` | Currency | batas upah tertinggi; kosong atau 0 = tanpa batas |
| `effective_from` | Date | wajib |
| `is_active` | Check | |
| `notes` | Small Text | sumber peraturan |
| `unique_key` | Data tersembunyi, unik | `company|program|risk_class|effective_from` |

Penomoran `BPR-YYMM-NNNN` (K-30). Tab Audit Trail wajib. Izin: HRIS Payroll Manager baca, tulis, buat; HRIS Payroll Admin baca; hapus hanya System Manager.
Validasi: tarif 0 sampai 100; JKK wajib kelas risiko; program lain tanpa kelas risiko; tidak ada kunci ganda.

### 4.2 Field baru di `HRIS Employee` (bagian Data Sensitif, `permlevel` 1)

| Field | Tipe | Keterangan |
|---|---|---|
| `bpjs_kes_enrolled` | Check | Ikut BPJS Kesehatan |
| `bpjs_jht_enrolled` | Check | Ikut JHT |
| `bpjs_jp_enrolled` | Check | Ikut JP |
| `bpjs_jkk_enrolled` | Check | Ikut JKK |
| `bpjs_jkm_enrolled` | Check | Ikut JKM |
| `pph21_enrolled` | Check | Ikut PPh 21 (disiapkan; dipakai tahap 2) |
| `bpjs_jkk_risk_class` | Data | Kelas risiko JKK karyawan |
| `bpjs_wage_basis` | Select | Gaji Final atau Gaji Penuh; berlaku untuk karyawan Harian; bawaan Gaji Final |

Semua centang bawaan **mati**, sehingga tidak ada potongan sampai HRD mengisinya. Hanya penambahan kolom; data lama tidak berubah. Paling aman ditambahkan **sebelum** migrasi produksi K-102.

### 4.3 Perhitungan pada slip

| Aturan | Isi |
|---|---|
| Waktu | Setelah komponen yang ada (Gaji Pokok, telat, pulang cepat, absen, lembur) dihitung |
| Dasar Bulanan | Gaji Pokok penuh |
| Dasar Harian | Dihitung untuk satu bulan: Gaji Penuh = upah harian x jumlah hari kerja terjadwal bulan itu, tanpa memotong ketidakhadiran; Gaji Final = jumlah komponen Upah Harian pada slip karyawan itu di bulan tersebut (hari Hadir x upah) |
| Waktu potong | Sekali sebulan, pada slip terakhir yang tanggal bayarnya jatuh di bulan itu (bulan dari tanggal bayar). Untuk Gaji Final Harian, dasar = jumlah Upah Harian seluruh slip karyawan itu pada bulan tersebut. Bila slip lain di bulan itu belum ada atau dihitung ulang, slip terakhir ikut dihitung ulang dan catatan hitung memberi peringatan |
| Batas upah | Dasar = nilai terkecil antara dasar dan `wage_cap` bila diisi |
| Iuran karyawan | Dasar x tarif karyawan, dibulatkan rupiah penuh per komponen (sejalan K-130). Muncul sebagai komponen Potongan per program (mis. BPJS Kesehatan, JHT, JP). Program dengan tarif karyawan nol tidak membuat baris potongan |
| Bagian perusahaan | Tidak mengurangi gaji. Disimpan sebagai informasi pada tabel anak baru `HRIS Payroll Slip BPJS` (program, dasar, tarif karyawan, tarif perusahaan, iuran karyawan, iuran perusahaan) sebagai snapshot |
| Tarif yang dipakai | Baris aktif dengan `effective_from` terbesar yang tidak melewati tanggal akhir periode (usulan) |
| Tidak ikut | Tidak ada komponen dan tidak ada baris informasi |
| Ikut tetapi tarif tidak ada | Slip dilewati dengan pesan jelas (pola "dilewati" yang sudah ada) |
| Slip | Hitung Ulang hanya saat Draft (K-130); Final terkunci |

## 5. Rencana pengujian

- Skrip uji baru dengan tarif **contoh fiktif** (bukan tarif resmi): hitung benar, pembulatan, batas upah, tidak ikut, kelas risiko tidak ada, tarif tidak ada, Harian Final dan Penuh, slip Final tidak berubah, izin per peran.
- Regresi: `uji_payroll_slip.py` tetap OK 77.
- Browser: Payroll Manager mengubah tarif; Payroll Admin hanya melihat; HRD mengisi centang peserta.
- Data uji dibersihkan. Tarif resmi diisi HRD hanya di produksi, setelah verifikasi.

## 6. Risiko

| Risiko | Mitigasi |
|---|---|
| Menambah field di DocType yang berjalan | Hanya penambahan; dilakukan sebelum migrasi produksi |
| Mengubah hasil slip yang sudah teruji | BPJS dihitung di akhir; regresi 77 pemeriksaan |
| Tarif salah | Tanggal berlaku, Audit Trail, verifikasi HRD sebelum parallel run |
| 1.078 karyawan harus diisi centang pesertanya | Pengeditan massal di list view atau impor file (fitur terpisah) |

## 7. Belum diputuskan

1. (Terjawab) Opsi A: potongan pada slip terakhir yang tanggal bayarnya jatuh di bulan itu; bulan dari tanggal bayar.
2. (Terjawab) Gaji Penuh Harian = upah harian x hari kerja terjadwal, tanpa memotong ketidakhadiran.
3. (Terjawab) Pilihan peserta per program.
4. (Terjawab) HR Admin dan Employee Admin; Payroll Admin hanya baca.
5. Tanggal acuan tarif berlaku (akhir periode, usulan).
6. Tahap 2: pengaruh iuran karyawan pada dasar pajak, jumlah tanggungan (PTKP), tabel TER, rekonsiliasi Desember, THR dan lembur.
7. Tahap 3: field NPWP dan BPJS ke Employee ERPNext; slip Final ke Salary Slip. Perlu dicek dulu apakah submit Salary Slip membuat jurnal (K-19 menunda posting akuntansi).
