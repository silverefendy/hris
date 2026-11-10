# Permintaan Data dan Konfirmasi ke HRD (10 November 2026)

Tujuan: mengumpulkan angka dan aturan resmi yang dibutuhkan sebelum data produksi payroll HRIS diisi.
Semua tarif dan angka di HRIS hanya **konfigurasi**; kode tidak berisi angka pajak atau BPJS.
Catatan: contoh nilai di kolom "Petunjuk" berasal dari pengetahuan umum dan **wajib diverifikasi** HRD atau konsultan pajak terhadap peraturan yang berlaku.

Cara pakai: HRD mengisi kolom "Jawaban HRD", lalu mengembalikan dokumen ini. Kolom "Fitur tertahan" menunjukkan pekerjaan yang menunggu butir tersebut.

## A. PPh 21 (K-134)

| # | Pertanyaan | Mengapa dibutuhkan | Fitur tertahan | Jawaban HRD |
|---|---|---|---|---|
| A1 | Tabel tarif TER resmi yang berlaku (kategori dan lapisan penghasilan bruto bulanan beserta persentasenya) | Mengisi `HRIS PPh 21 TER Rate`; saat ini hanya tarif fiktif untuk uji | Pengisian data produksi | |
| A2 | Pemetaan status PTKP ke kategori TER (misalnya TK/0, K/1 masuk kategori mana) | Menentukan kategori tarif dari field Status PTKP karyawan | Pengisian data produksi | |
| A3 | Daftar status PTKP yang dipakai perusahaan dan nilai PTKP tahunan tiap status | Validasi pilihan Status PTKP dan tahap 2b | Tahap 2b | |
| A4 | Apakah NPWP memengaruhi tarif? Jika ya, berapa pengali bila karyawan tidak punya NPWP | Menentukan apakah field NPWP ikut dalam perhitungan | Tahap 2b | |
| A5 | Bagaimana perhitungan bulan terakhir tahun pajak (Desember) dan karyawan yang keluar di tengah tahun: dihitung ulang dengan tarif progresif atau tetap TER? | Rekonsiliasi akhir tahun | Tahap 2b | |
| A6 | Komponen mana yang masuk penghasilan bruto untuk PPh 21 (gaji pokok, tunjangan, lembur, bonus, THR) dan apakah iuran BPJS karyawan (Kesehatan, JHT, JP) mengurangi bruto | Penanda Kena Pajak per komponen dan pengurang per program BPJS | Tahap 2b | |
| A7 | Aturan PPh 21 untuk karyawan Harian dan Mingguan (ambang penghasilan harian, kapan dipotong, apakah memakai TER bulanan atau tarif harian) | Saat ini Harian dan Mingguan dihitung dengan TER bulanan atas bruto semua slip dalam bulan bayar | Jadwal Harian dan Mingguan di produksi | |

## B. BPJS (K-133)

| # | Pertanyaan | Mengapa dibutuhkan | Fitur tertahan | Jawaban HRD |
|---|---|---|---|---|
| B1 | Angka iuran per program (Kesehatan, JHT, JP, JKK, JKM) bagian perusahaan dan bagian karyawan | Mengisi `HRIS BPJS Rate` (angka tetap per program) | Pengisian data produksi | |
| B2 | Batas upah (plafon) untuk BPJS Kesehatan dan JP, beserta tanggal berlakunya | Angka tetap perlu diperbarui bila batas berubah | Pengisian data produksi | |
| B3 | Kelas risiko JKK perusahaan (per bagian jika berbeda) | Menentukan besaran JKK | Pengisian data produksi | |
| B4 | Dasar upah BPJS karyawan Harian: total gaji sebulan versi final atau versi penuh, dan siapa saja yang memakai versi mana | Dasar perhitungan per karyawan | Pengisian data produksi | |
| B5 | Dua butir sementara pada `keputusan-2026-11-10-bpjs.md` bagian 8 | Perlu konfirmasi sebelum produksi | Produksi BPJS | |

## C. Penggajian umum

| # | Pertanyaan | Mengapa dibutuhkan | Fitur tertahan | Jawaban HRD |
|---|---|---|---|---|
| C1 | Tanggal cut-off dan tanggal bayar tiap jenis jadwal gaji (Bulanan, Mingguan, Harian) | Memeriksa `HRIS Payroll Schedule` terhadap kebiasaan nyata | Produksi | |
| C2 | Format data bank untuk transfer gaji (nama bank, format berkas yang diminta bank) | Laporan transfer gaji | Laporan | |
| C3 | Daftar potongan lain di luar absen, BPJS, PPh 21 (pinjaman, koperasi, denda) dan cara perhitungannya | Komponen Manual atau Otomatis tambahan | Tahap berikutnya | |
| C4 | Aturan THR: dasar hitung, masa kerja minimum, kapan dibayar | Rancangan THR | THR | |
| C5 | Saldo awal cuti per karyawan dan aturan cuti tahunan | Potongan absen (cuti tahunan habis dipotong) | HRIS Absence | |
| C6 | Daftar laporan yang dibutuhkan HRD tiap periode (rekap gaji, slip, rekap BPJS, rekap pajak) | Prioritas modul Reports | Reports | |

## D. Konfirmasi keputusan

| # | Pertanyaan | Mengapa dibutuhkan | Jawaban HRD |
|---|---|---|---|
| D1 | Konfirmasi lembur dikalikan 1,0 jam aktual (K-98), atau ada pengali lain per jenis hari | Rumus lembur pada slip | |
| D2 | Siapa yang menjadi HRIS Payroll Manager (yang boleh Finalkan dan Buka Kembali periode) | Hak akses K-128 | |
| D3 | Urutan kerja HRD tiap periode: hitung Working Hour lebih dulu, baru buat slip. Apakah HRD menyetujui urutan ini | Bila slip terakhir bulan bayar dilewati, PPh 21 bulan itu tidak terpotong | |

## Catatan

- Selama jawaban belum ada, HRIS tetap memakai tarif fiktif di site uji dan **tidak boleh** dipakai untuk slip produksi.
- Setiap jawaban akan dicatat sebagai keputusan baru di `docs/decisions/` sebelum kode atau data diubah.
