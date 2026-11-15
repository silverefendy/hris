# Keputusan 14 sampai 15 November 2026: default tidak dapat, penetapan per karyawan (HEC) dan per Grup atau Department (HCA)

Nomor: K-140. Status: diterapkan dan teruji di `hris-uji.local`. Belum dimigrasi ke site kerja (K-102).

## 1. Konteks

Sebelum K-140, komponen gaji yang nilai dasarnya lebih dari 0 otomatis dibayar ke semua karyawan di Department atau Grup itu. HRD ingin sebaliknya: **komponen tidak dibayar kecuali ada penetapan**. Penetapan harus bisa dibuat per karyawan, dan juga sekali untuk seluruh Grup atau Department.

## 2. Keputusan

| No | Keputusan |
|---|---|
| R1 | Default tidak dapat: komponen dibayar hanya bila ada penetapan Berlaku yang mencakup hari atau periode itu. Tanpa penetapan = Rp0, untuk semua jenis komponen |
| R2 | Penetapan per karyawan tetap memakai `HRIS Employee Component` (HEC). Struktur HEC tidak diubah |
| R3 | Tombol massal "Terapkan ke Department atau Grup" di list HEC tetap ada. Ia membuat HEC per karyawan. Karyawan yang sudah punya HEC aktif pada rentang itu dilewati dan dilaporkan, tidak ditimpa |
| R4 | Mengeluarkan satu orang: HEC dengan Status Tidak Berlaku |
| R5 | Karyawan Bulanan dengan komponen Per Hari Hadir dihitung hari Hadir x nilai per hari, sama dengan Harian |
| R6 | Pengaman janggal tetap (Berlaku tanpa nominal dan nilai dasar nol ditandai dan masuk notifikasi) |
| HCA | **Perubahan arah 14 Nov:** input per Grup atau Department menghasilkan **satu penetapan milik Grup atau Department**, bukan baris per karyawan. Dibuat DocType baru `HRIS Component Assignment` (HCA). HEC tidak diubah |

Aturan HCA yang disetujui Efendy (6 butir):

| No | Aturan |
|---|---|
| 1 | DocType baru HCA, HEC tidak diubah |
| 2 | Prioritas: HEC karyawan, lalu HCA tingkat terdekat, lalu HCA tingkat lebih jauh, lalu Rp0 |
| 3 | Department atau Grup mengikuti `rule_follow` karyawan. Grup yang punya HCA untuk komponen itu dipakai; selain itu jatuh ke Department. Departemen induk ikut hanya bila `include_children` aktif; anak menang atas induk |
| 4 | Anggota baru Grup atau Department otomatis menerima komponen (konsekuensi diterima) |
| 5 | HCA hanya untuk `System Manager`, `HRIS Payroll Manager` (buat, ubah), dan `HRIS Direksi` (baca). `HRIS Payroll Admin` tidak punya akses, karena dibatasi pada karyawan Harian (K-110) sedangkan Grup bisa memuat Bulanan |
| 6 | Tombol massal HEC dibiarkan |

Keputusan tambahan yang diambil tanpa dikoreksi Efendy:

| Hal | Keputusan |
|---|---|
| Per Bulan, penetapan hanya mencakup sebagian periode | Nilai per periode dibayar **penuh** disertai peringatan di `calc_notes` dan notifikasi ringkasan, sejalan dengan aturan lama |
| Hari yang dihitung pada Per Hari Hadir | Hanya hari berstatus Hadir. Tidak Lengkap dan Absen tidak |
| Periode Final | HCA **tidak** diperiksa terhadap periode Final (tidak seperti HEC, K-128): slip Final tidak dihitung ulang (K2), jadi HCA yang disimpan belakangan tidak mengubah slip Final |
| Pratinjau | Form HCA punya tombol "Lihat karyawan terkena" (menerima, ikut Department, tertutup HCA Grup, punya HEC sendiri) |

## 3. Cara kerja

Contoh: Uang Makan Rp20.000 per hari, Grup Security Malam 14 orang, 2 orang tidak dapat.
1. Satu HCA Grup Security Malam, Berlaku. Nilai dasar di aturan Grup.
2. Dua HEC Tidak Berlaku untuk dua orang itu.
3. Slip: 12 orang dihitung, 2 orang Rp0. Karyawan ke-15 yang masuk Grup besok otomatis dihitung.

Penggabungan dilakukan di `services/cakupan_komponen.py`: rentang HCA dikurangi rentang HEC karyawan (HEC menang), lalu hasilnya diberikan ke `hitung_tunjangan()`. Disambung di `hitung_tunjangan_karyawan` (slip) dan `payroll_summary.ambil_data` (pemuatan massal). Bila tabel HCA belum ada (site belum dimigrasi), semua fungsi HCA mengembalikan kosong.

## 4. Konsekuensi yang perlu diketahui HRD

| Hal | Akibat |
|---|---|
| Anggota baru Grup atau Department | Otomatis dapat. Untuk menahan, buat HEC Tidak Berlaku |
| Karyawan pindah Grup atau Department | Haknya berubah sendiri mengikuti Grup atau Department sekarang |
| Riwayat | HCA punya Audit Trail sendiri; tidak ada catatan "si A menerima sejak kapan" |
| Per Bulan pada slip mingguan | Per Bulan dan Per Slip diperlakukan sama (satu nilai per slip), jadi karyawan slip mingguan menerimanya di setiap slip. Dari pembacaan kode, belum diuji. Aman untuk karyawan Bulanan |

## 5. Hasil uji (hris-uji.local)

| Uji | Hasil |
|---|---|
| `uji_default_tidak_dapat` (murni) / `_db` | 18 OK / 4 OK |
| `uji_tunjangan_slip` | 30 OK |
| `uji_hec_massal` | 18 OK |
| `uji_cakupan_komponen` (murni) | 18 OK |
| `uji_hca` (DocType) | 16 OK |
| `uji_hca_slip` | 13 OK |
| `uji_hca_pratinjau` | 10 OK |
| Regresi: `uji_payroll_summary` 19, `uji_komponen_karyawan` 27, `uji_pengecualian` 25, 3b 34, `uji_payroll_slip` 77 | OK |
| Uji browser HCA: simpan (W1), pratinjau 18 karyawan (W2), indikator (W3), nonaktif (W4), akun Payroll Admin tidak melihat menu (W5) | Lulus |

Kecepatan (data sintetis di-rollback, mesin uji):

| Jalur | Hasil |
|---|---|
| Payroll Summary, 1078 baris | sekitar 1,0 detik, 2,2 sampai 2,4 query per baris |
| Slip, 300 karyawan x 6 komponen | 22 sampai 23 ms per karyawan, 60 query per karyawan, proyeksi 1078 karyawan sekitar 24 sampai 25 detik |
| Tambahan karena baris HCA dan HEC | sekitar 1 ms per karyawan, tanpa query tambahan |

Bila hitung massal terasa lambat, opsi optimasi: cache per Department dalam satu proses hitung massal (bukan antar proses, agar tidak menyimpan HCA lama).

## 6. Commit

| Tahap | Commit |
|---|---|
| A (aturan default tidak dapat, Bulanan Per Hari Hadir) | `d7cb11c` |
| B (tombol massal HEC) | `13407ee` |
| E1 (fungsi murni penggabungan) | `75b5b60` |
| E2 (DocType HCA) | `f2a122f` |
| E3 (sambung ke slip dan Payroll Summary) | `adf5ef1` |
| E4 dan E4b (pratinjau, indikator, company diisi otomatis) | `0098966`, `b84f5c1` |
| E5 (penomoran HCA mengikuti K-30, tab audit) | lihat `git log` |
| C dan C2 (alat ukur) | `f111a1f`, `47783d5` |

## 7. Pelajaran

| Pelajaran | Keterangan |
|---|---|
| Field wajib hanya-baca yang diisi server lolos uji skrip tetapi gagal di browser | Browser memeriksa kewajiban sebelum mengirim. DocType baru harus diuji di browser sekali. `company` HCA dibuat tidak wajib di browser, controller tetap menolak bila kosong, dan form mengisinya saat Department atau Grup dipilih |
| Uji yang mengaktifkan komponen untuk pengujian browser mengganggu uji 3b | 3b menolak bagian database bila ada komponen aktif. Nonaktifkan lagi setelah uji browser |
| Pengukuran dengan sampel kecil menyesatkan | Pengukuran pertama (2 karyawan ber-gaji) menunjukkan tambahan 14 ms yang ternyata derau. Pengukuran kedua memakai gaji sintetis ber-rollback |
| Penomoran HCA tidak memuat YYMM (misalnya `HCA-02213`) | Melanggar butir 2 checklist DocType (K-30). Diperbaiki di E5 menjadi `HCA-YYMM-NNNN`; tab Audit Trail juga diberi `depends_on` (butir 4). Ditemukan saat membaca checklist, bukan oleh uji |

## 8. Tertunda

| Hal | Keterangan |
|---|---|
| **K-102** | DocType HCA harus ikut dimigrasi ke site kerja (`bench migrate`), termasuk izin. Perubahan kode ikut berlaku di site kerja setelah restart; fungsi HCA aman bila tabel belum ada, tetapi aturan "default tidak dapat" langsung berlaku. Semua komponen masih nonaktif |
| W6 | Uji Payroll Summary lewat browser dengan komponen aktif, setelah restart proses web. Logikanya sudah teruji lewat `uji_hca_slip` D4 |
| Pemeriksaan periode Final untuk HCA | Belum ada (keputusan: tidak perlu sekarang) |
| Kolom "sumber" Payroll Summary | Baris HCA tampil sebagai "Pengecualian HCA-xxxxx"; teks bisa dibedakan nanti |
| Per Bulan pada slip mingguan | Lihat bagian 4 |
| Tombol di list HCA | Tombol massal HEC tetap membuat HEC per karyawan; belum ada tombol "buat HCA" khusus (HCA dibuat lewat form biasa) |
