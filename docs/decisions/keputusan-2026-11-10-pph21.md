# Keputusan 10 November 2026: PPh 21 pada HRIS Payroll Slip (K-134, rancangan)

Status: **rancangan; belum disetujui akhir dan belum ada kode.** Jawaban Efendy 10 Nov 2026 (13:11 dan 13:25 WIB) sudah dimasukkan. Nomor K-134 dipakai karena K-133 sudah BPJS; ubah bila perlu.

**Peringatan:** dokumen ini tidak memuat tarif, kategori, atau aturan pajak resmi. Semua angka dan aturan wajib diverifikasi HRD atau konsultan pajak dari peraturan resmi (DJP atau PMK tentang PPh 21 dengan tarif efektif rata-rata, TER). Bagian yang berasal dari pemahaman Claude dan belum terverifikasi ditandai "verifikasi".

## 1. Konteks

BPJS (K-133) sudah ada di slip. Tahap 2 adalah PPh 21. Pengecekan 10 Nov 2026 menunjukkan HRMS dan ERPNext tidak punya fitur PPh 21 Indonesia (lihat [keputusan-2026-11-10-bpjs.md](keputusan-2026-11-10-bpjs.md) bagian 2), jadi dibuat sendiri di HRIS tanpa mengubah HRMS atau ERPNext (K-18).

## 2. Sudah diputuskan (Efendy, 10 Nov 2026)

| Hal | Keputusan |
|---|---|
| Cakupan tahap 2a | TER bulanan. Rekonsiliasi Desember, THR, dan pengurang BPJS per program ditunda ke tahap 2b |
| Status PTKP | Diinput lewat field di `HRIS Employee` |
| Ikut PPh 21 | Centang per karyawan, berlaku untuk Bulanan, Harian, dan Mingguan. Karyawan yang tidak kena pajak tidak dicentang |
| Penanggung pajak | Dipotong dari gaji karyawan |
| Waktu potong | Di akhir bulan: pada slip **terakhir** yang tanggal bayarnya jatuh di bulan itu (bulan dari tanggal bayar). Dasar adalah penghasilan bruto satu bulan |
| Penghasilan di bawah PTKP | Tidak kena pajak (pada tabel TER biasanya tampak sebagai baris tarif 0%; verifikasi) |
| NPWP | Diduga memengaruhi persentase pajak (Efendy tidak yakin). Dibuat sebagai **pengaturan** (verifikasi) |
| Tarif TER | Diisi HRD dari sumber resmi sebagai pengaturan, bukan di kode |
| Penanda kena pajak pada komponen | Disetujui (cara pada bagian 3) |
| Pengurang BPJS per program (Kesehatan 1% tidak mengurangi, JHT 2% mengurangi, menurut sumber yang Efendy kutip) | Ditunda ke tahap 2b; belum diverifikasi, perlakuan JP belum jelas |

## 3. Rancangan tahap 2a

| Bagian | Isi |
|---|---|
| Field di `HRIS Employee` | Status PTKP (pilihan) dan centang Ikut PPh 21, di bagian data sensitif (`permlevel` 1) seperti NPWP. Periksa dulu apakah field serupa sudah ada. NPWP, status pernikahan sudah ada |
| DocType tarif TER | Kategori, penghasilan dari, penghasilan sampai, persentase, tanggal berlaku, aktif. Diisi HRD |
| Pemetaan PTKP ke kategori TER | Tabel pengaturan, bukan di kode |
| Pengali bila NPWP kosong | Pengaturan yang diisi HRD; nilai satu berarti tidak berpengaruh |
| Penanda kena pajak | Daftar komponen **tidak** kena pajak di pengaturan; komponen lain Pendapatan dianggap kena pajak. Baris Manual diberi centang "Kena pajak" (bawaan aktif); itu menambah satu field pada `HRIS Payroll Slip Item` dan perlu konfirmasi |
| Hasil di slip | Satu komponen Potongan "PPh 21" berjenis Otomatis, plus catatan dasar bruto, kategori, dan tarif yang dipakai (snapshot) |

## 4. Aturan hitung (rancangan)

| Aturan | Isi |
|---|---|
| Karyawan yang dihitung | Hanya yang dicentang Ikut PPh 21 |
| Slip pembawa | Slip terakhir menurut jadwal yang tanggal bayarnya jatuh di bulan itu. Penentunya kebalikan dari `pertama_bulan_murni` pada `payroll_bpjs.py` (periode berikutnya dibayar di bulan lain). Karyawan Bulanan: satu-satunya slip bulan itu |
| Dasar bruto | Jumlah komponen Pendapatan kena pajak pada **semua slip** karyawan itu dengan tanggal bayar di bulan tersebut, termasuk slip yang masih Draft |
| Tarif | Baris aktif untuk kategori dan rentang penghasilan dengan tanggal berlaku terbesar yang tidak melewati tanggal akhir periode slip pembawa |
| Rumus | Pajak = bruto x tarif x pengali NPWP (bila NPWP kosong), dibulatkan rupiah penuh. Tarif 0 tidak membuat baris potongan |
| Data kurang | Ikut PPh 21 tetapi status PTKP kosong atau tarif tidak ada: slip dilewati dengan pesan pola Masalah, Penyebab, Tindakan, Berwenang |
| Slip lain bulan itu belum ada atau dihitung ulang | Catatan peringatan di slip pembawa, seperti pada BPJS |
| Slip Final | Terkunci; Hitung Ulang hanya saat Draft (K-130) |

Contoh dengan angka fiktif (bukan tarif resmi): bruto bulan itu Rp 5.700.000, tarif contoh 2%, NPWP ada: pajak Rp 114.000 sebagai potongan Otomatis pada slip terakhir bulan itu.

## 5. Belum diputuskan atau perlu verifikasi

| # | Hal | Catatan |
|---|---|---|
| 1 | Tarif TER resmi dan pemetaan PTKP ke kategori | HRD atau konsultan pajak |
| 2 | Pengaruh NPWP terhadap tarif dan besar pengalinya | Verifikasi aturan terbaru |
| 3 | Aturan PPh 21 untuk penghasilan harian dan mingguan | Verifikasi; centang per karyawan membatasi risikonya |
| 4 | Daftar pilihan status PTKP di field | Mengikuti peraturan; verifikasi |
| 5 | Letak pengaturan (satu DocType Single baru atau beberapa) | Dibahas saat rancangan teknis |
| 6 | Penambahan field "Kena pajak" pada `HRIS Payroll Slip Item` | Mengubah DocType yang berjalan; konfirmasi Efendy |
| 7 | Tahap 2b: pengurang BPJS per program, rekonsiliasi Desember, THR | Rancangan terpisah |
| 8 | Tahap 3: jembatan ke ERPNext (NPWP dan BPJS ke Employee, slip Final ke Salary Slip) | Cek dulu apakah submit Salary Slip membuat jurnal (K-19) |

## 6. Risiko

| Risiko | Mitigasi |
|---|---|
| Menambah field di DocType yang berjalan (`HRIS Employee`, `HRIS Payroll Slip Item`) | Hanya penambahan; dikerjakan sebelum migrasi produksi K-102; dijelaskan dan dikonfirmasi dulu |
| Aturan atau tarif pajak salah | Tarif sebagai pengaturan dengan tanggal berlaku dan Audit Trail; verifikasi HRD atau konsultan pajak; parallel run |
| Data sensitif (NPWP, status PTKP) | `permlevel` 1; uji izin per peran seperti pada K-133 |
| Slip bulan itu belum lengkap saat slip terakhir dihitung | Peringatan di catatan; hitung ulang setelah slip lain lengkap |

## 7. Rencana pengujian

- Skrip uji dengan tarif **fiktif**: karyawan Bulanan satu slip; Harian dengan beberapa slip dalam satu bulan; tidak dicentang; NPWP kosong; PTKP kosong; tarif tidak ada; bruto di baris 0%; komponen tidak kena pajak; slip Final tidak berubah; Hitung Ulang tidak melipatgandakan baris.
- Regresi: `uji_payroll_slip.py` (OK 77) dan `uji_bpjs_slip.py` tetap lulus.
- Uji izin per peran dan uji browser sebelum produksi.

## 8. Langkah implementasi (setelah rancangan disetujui)

1. DocType tarif TER dan pengaturan.
2. Field PTKP dan Ikut PPh 21 di `HRIS Employee`.
3. Penanda kena pajak pada komponen.
4. Perhitungan pada slip dan skrip uji.
5. Uji browser per peran, lalu sinkron dokumen.
