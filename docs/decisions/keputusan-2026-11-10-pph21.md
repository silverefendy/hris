# Keputusan 10 November 2026: PPh 21 pada HRIS Payroll Slip (K-134, disetujui)

Status: **disetujui 10 Nov 2026; langkah 1 sampai 4 selesai, lulus uji skrip dan uji browser di site uji (commit 84b093c dan 9ad4fcf). Verifikasi tarif, NPWP, dan aturan harian atau mingguan oleh HRD atau konsultan pajak masih tertunda. Uji jadwal Bulanan dan Mingguan selesai (10 Nov malam, bagian 12).** Jawaban Efendy 10 Nov 2026 (13:11 dan 13:25 WIB) sudah dimasukkan. Nomor K-134 dipakai karena K-133 sudah BPJS; ubah bila perlu.

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

## Rancangan teknis langkah 1 (disetujui 10 Nov 2026)

| Hal | Keputusan |
|---|---|
| DocType | `HRIS PPh21 Settings` (Single), `HRIS PPh21 TER Rate`, tabel anak `HRIS PPh21 PTKP Map` dan `HRIS PPh21 Exempt Item` |
| Cakupan pengaturan | Satu untuk semua company (tarif TER aturan nasional); tidak ada field `company` |
| Pengisi | HRIS HR Admin dan System Manager menulis; Payroll Manager, Payroll Admin, dan Direksi hanya membaca; hapus baris tarif hanya System Manager (HR Admin menonaktifkan lewat centang Aktif) |
| Tarif | Memakai Berlaku Sejak; set dengan tanggal berlaku terbaru (<= tanggal pajak) menggantikan seluruh set lama untuk kategori itu |
| Rentang | Dari dan Sampai inklusif; atas terbuka lewat centang Tanpa Batas Atas; tumpang tindih ditolak per kategori dan Berlaku Sejak |
| Pembulatan | Ke bawah ke rupiah (bawaan), bisa diubah di pengaturan |
| Aktif | Bawaan mati sampai HRD selesai mengisi dan memverifikasi tarif |
| Kode | `services/pph21_rate.py` (`find_rate`, `pesan`); tidak ada fungsi `@frappe.whitelist()` |
| Uji | `tests/uji_pph21_rate.py` dengan tarif fiktif; tarif resmi hanya diisi HRD di produksi setelah diverifikasi |

## 9. Rancangan teknis langkah 4: PPh 21 pada slip (disetujui 10 Nov 2026)

Enam keputusan, semua disetujui sesuai usul:

| # | Keputusan |
|---|---|
| 1 | Rincian (bruto, jumlah slip, kategori, tarif, pengali) hanya di Catatan Perhitungan; tidak ada tabel rincian baru seperti BPJS |
| 2 | Slip lain bulan itu belum lengkap: dihitung dari slip yang ada, dengan peringatan "N dari M slip" (M dari jadwal gaji); tidak menolak |
| 3 | Data kurang (PTKP kosong atau belum dipetakan): slip dilewati dengan pesan Masalah, Penyebab, Tindakan, Berwenang pada **semua** slip bulan itu; tarif tidak ketemu hanya diperiksa di slip terakhir |
| 4 | Pengaturan mati tetapi karyawan dicentang: tidak dipotong, catatan menyebutnya jelas |
| 5 | Validasi server di `HRIS Employee`: bila Ikut PPh 21 dicentang, Status PTKP wajib (sebelumnya hanya validasi form di browser, sehingga data bisa tersimpan lewat API atau impor) |
| 6 | Keterbatasan diterima sampai tahap 2b: karyawan yang tidak punya slip terakhir di bulan itu (misalnya berhenti di tengah bulan) tidak terpotong |

Perilaku yang diterapkan:

| Hal | Isi |
|---|---|
| Berkas | `services/payroll_pph21.py` (baru, fungsi `hitung_pph21_slip`), patch kecil `payroll_slip.py` (dipanggil setelah BPJS), metode `_cek_pph21` di controller `HRIS Employee`, `tests/uji_pph21_slip.py` |
| Struktur DocType | Tidak ada perubahan JSON atau DocType pada langkah ini |
| Bruto | Komponen Otomatis kena pajak (kecuali daftar bebas pajak, tidak peka huruf besar-kecil) ditambah baris Manual yang tercentang Kena Pajak, ditambah slip lain karyawan itu di bulan yang sama |
| Slip bukan terakhir | Tanpa potongan; catatan menyebut pajak dipotong pada slip terakhir. Bila slip terakhir sudah memuat PPh 21, slip ini diberi peringatan agar slip terakhir dihitung ulang |
| Tarif 0% | Tidak membuat baris potongan; tertulis di catatan |
| Peringatan lain | Jumlah slip kurang dari jadwal; gaji bersih negatif |

## 10. Hasil pengujian (10 Nov 2026, site uji)

| Uji | Hasil |
|---|---|
| `uji_pph21_slip.py` (tarif fiktif) | OK 22, GAGAL 0 (U1 sampai U14, deteksi slip terakhir pada Periode yang ada, E1 sampai E3 validasi server) |
| Regresi | `uji_payroll_slip.py` OK 77, `uji_bpjs_slip.py` OK 68, `uji_pph21_field.py` OK 13, `uji_pph21_rate.py` OK 32 (GAGAL 0) |
| Browser: Hitung Ulang | PPh 21 tampil sebagai Potongan Otomatis; bruto 3.625.000 dengan tarif fiktif 1% menghasilkan 36.250 dan gaji bersih 3.588.750 |
| Browser: Kena Pajak | Mematikan centang Kena Pajak pada satu baris Manual menurunkan bruto menjadi 3.300.000 dan pajak 33.000; menyalakannya kembali mengembalikan 36.250 |
| Browser: PTKP kosong | Hitung Ulang menampilkan dialog Message berisi Masalah, Penyebab, Tindakan, Berwenang; slip tidak berubah |
| Browser: PTKP dipulihkan | Hitung Ulang kembali menghasilkan 36.250 |
| Audit Trail HRIS | Semua perubahan baris komponen, catatan, total, dan gaji bersih tercatat |

**Keterbatasan pengujian:** deteksi slip terakhir baru diuji pada satu Periode nyata (jadwal Bulanan, satu slip per bulan). Jadwal Harian atau Mingguan dengan banyak slip belum diuji pada data nyata; uji skrip memakai data pengganti.

## 11. Tertunda

- Uji izin per peran untuk field PTKP dan Ikut PPh 21 (seperti K-133).
- Verifikasi HRD atau konsultan pajak: rumus TER (bruto x tarif, dasar bruto penuh; ini pemahaman Claude), tarif resmi, pemetaan PTKP, pengaruh NPWP, aturan harian atau mingguan.
- Tahap 2b (rekonsiliasi, THR, pengurang BPJS per program) dan migrasi produksi K-102.

## 12. Uji jadwal dan multi-slip (10 Nov 2026, malam)

Semua uji berjalan di `hris-uji.local` dengan tarif fiktif; data di-rollback.

| Uji | Hasil | Commit |
|---|---|---|
| `uji_slip_massal.py` (cakupan Semua, Department, Grup, Karyawan, mode background, idempotensi, Periode Ditinjau menolak) | OK 19, GAGAL 0 | `d645b00` |
| `uji_pph21_jadwal.py` bagian J (enam jenis jadwal, tiap bulan 2026 tepat satu slip pertama dan satu terakhir) | OK 9, GAGAL 0 | `e5c22e0` |
| `uji_pph21_mingguan.py` (jadwal Mingguan Senin offset 10; slip terakhir dibuat dulu, lalu slip lain, lalu hitung ulang) | OK 16, GAGAL 0 | `705fc4e` |

Temuan:

- Bagian P pada `uji_pph21_jadwal.py` dilewati (tidak ada karyawan Hadir di empat minggu berturut-turut: data Working Hour ber-Hadir hanya di minggu 28 Sep, 12 Okt, dan 26 Okt). Cakupannya dipenuhi oleh `uji_pph21_mingguan.py`.
- Pajak slip terakhir = tarif x bruto slip yang ada: 1 slip (345.768) dengan peringatan "1 dari 4", lalu 2 slip (545.768) dengan catatan "2 dari 4". Hitung ulang idempoten; slip bukan terakhir tidak memuat baris PPh 21 dan memuat peringatan.
- Minggu tanpa data Working Hour dilewati dengan alasan "Tidak ada data Working Hour pada periode ini (belum dihitung)".

Risiko operasional: bila slip terakhir bulan bayar dilewati karena Working Hour belum dihitung, tidak ada slip yang memotong PPh 21 untuk karyawan itu pada bulan tersebut. Urutan kerja HRD: hitung Working Hour, lalu buat slip. Perlu masuk panduan HRD.

Belum teruji: jadwal Harian multi-slip pada data nyata; izin per peran untuk field PTKP dan Ikut PPh 21; rumus TER dan tarif resmi (menunggu HRD atau konsultan pajak).
