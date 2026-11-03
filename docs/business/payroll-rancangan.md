# Rancangan Payroll (Draf Fase 1)

Status: **disetujui sebagian (K-95 sampai K-99)**; A7 dan model data karyawan masih terbuka. Belum ada kode. Tanggal: 3 November 2026.

## 1. Prinsip
- Payroll mengubah fakta Working Hour menjadi uang per orang per periode.
- HRIS mandiri (K-18); bridge ke akuntansi ERPNext tidak dibuat di fase 1 (K-19).
- Gaji melekat pada **orang**, bukan departemen atau grup.
- Slip menyimpan salinan (snapshot) tarif dan aturan saat dihitung, sehingga perubahan di kemudian hari tidak mengubah riwayat (selaras K-35).
- Semua DocType memuat `company` dan awalan `HRIS`.

## 2. Ruang lingkup fase 1
| Termasuk | Ditunda ke fase 2 |
|---|---|
| Gaji pokok (bulanan, mingguan, harian) | BPJS |
| Potongan telat dan pulang cepat | PPh21 |
| Lembur | Tunjangan dan insentif khusus |
| Penyesuaian oleh HRD | Gaji per jam (disiapkan, belum diaktifkan) |
| Review Kepala HRD, lalu Final | Impor data gaji dari aplikasi lama |

Aturan BPJS dan PPh21 harus diverifikasi ke sumber resmi atau konsultan pajak sebelum dibuat.

## 3. Konsep
| Konsep | Arti | Contoh |
|---|---|---|
| Jenis gaji (`pay_type`) | Cara hitung | Bulanan, Mingguan, Harian, Per Jam (belum aktif) |
| Jadwal gaji | Frekuensi dan cut-off, dapat diatur | Bulanan cut-off tanggal 26; Mingguan Senin sampai Sabtu; Harian dibayar tiap N hari |
| Periode | Satu rentang tanggal dari satu jadwal gaji | Bulanan: 27 bulan lalu sampai 26 bulan ini (asumsi, perlu konfirmasi) |

Jenis gaji dan jadwal gaji dipisah: orang berupah harian bisa dibayar per minggu atau per 10 hari tanpa mengubah cara hitung.

## 4. Rumus (diusulkan)
Semua jam memakai `final_effective_hours` dan lembur dari HRIS Working Hour (K-37, K-38, K-42).

**Bulanan**
- Tarif per jam = gaji bulanan / jumlah jam terjadwal dalam periode.
- Gaji dibayar = tarif per jam x jam efektif final.
- Lembur = jam lembur x tarif per jam x pengali lembur (awal 1,0).

**Harian dan Mingguan**
- Upah pokok = jumlah hari Hadir x upah harian.
- Tarif per jam = upah harian / jam terjadwal hari itu.
- Telat dan pulang cepat = jam potongan x tarif per jam, dikurangkan.
- Lembur = jam lembur x tarif per jam x pengali lembur (awal 1,0).

Contoh bulanan: gaji 3.000.000, terjadwal 200 jam (tarif 15.000), efektif 190 jam, lembur 2 jam: 2.850.000 + 30.000 = 2.880.000.
Contoh harian: upah 100.000, 8 jam terjadwal, hadir 5 hari, potongan 1 jam, lembur 1 jam: 500.000 - 12.500 + 12.500 = 500.000.

## 5. Ketidakhadiran dan pengecekan HRD
- HRD memeriksa setiap hari berstatus Tidak Lengkap atau Tidak Hadir.
- **Periode tidak dapat difinalkan** selama masih ada hari seperti itu yang belum diselesaikan.
- Alasan ketidakhadiran dicatat di DocType baru `HRIS Absence` (karyawan, tanggal, jenis, dibayar atau tidak, lampiran, catatan). DocType Working Hour yang sudah berjalan tidak diubah.
- Aturan awal: bulanan sakit dengan surat dokter = dibayar (tidak dipotong). Jenis lain dan aturan harian atau mingguan menunggu HRD.
- Cuti dan izin: belum diputuskan.

## 6. Karyawan pindah atau dipinjam
- Gaji tetap milik orangnya. Peminjaman hanya dicatat (Shift Assignment, K-32; salinan di Working Hour, K-39).
- Laporan memuat rincian hari per grup atau departemen untuk alokasi biaya.
- Tunjangan atau insentif hari pinjam menunggu aturan HRD.

## 7. Entitas yang diusulkan
| DocType | Isi |
|---|---|
| `HRIS Payroll Schedule` | Jenis jadwal, hari awal, panjang periode atau tanggal cut-off |
| `HRIS Employee Pay` | Per orang: jenis gaji, nominal, jadwal gaji, berlaku dari, aktif. Terpisah dari Employee agar hak baca dibatasi pada role Payroll |
| `HRIS Payroll Period` | Jadwal, dari, sampai, status: Draft, Ditinjau, Final |
| `HRIS Payroll Slip` | Per orang per periode, salinan tarif, komponen, total |
| `HRIS Absence` | Lihat bagian 5 |
| Pengaturan | Pengali lembur (awal 1,0) |

Role: HRIS Payroll User (menyiapkan), HRIS Payroll Admin (mengelola), Kepala HRD (menyetujui). Data gaji hanya terbaca role Payroll. Fungsi server wajib cek role (pelajaran P5 repo lama).

## 8. Alur

Working Hour + HRIS Employee Pay + HRIS Absence
-> Payroll Period (Draft) -> Slip dihitung
-> HRD menyelesaikan hari bermasalah
-> Review Kepala HRD (Ditinjau) -> Final (terkunci)

Pembukaan kembali periode Final dengan alasan wajib dan tercatat di audit trail.

## 9. Asumsi yang perlu dikonfirmasi
| No | Asumsi |
|---|---|
| A1 | Periode bulanan = tanggal 27 sampai 26 |
| A2 | Pembagi tarif bulanan = jam terjadwal periode (bukan angka tetap), sehingga tarif per jam bisa berbeda antarbulan |
| A3 | Mingguan memakai upah harian x hari hadir, bukan nominal mingguan tetap |
| A4 | Sakit bersurat dokter pada harian atau mingguan: dibayar atau tidak |
| A5 | Pengali lembur 1,0 disetujui Kepala HRD dan sesuai aturan ketenagakerjaan |
| A6 | Hari libur nasional bagi harian dan mingguan: dibayar atau tidak |
| A7 | Satu karyawan hanya punya satu jadwal gaji pada satu waktu |

## 10. Risiko dari repo lama yang dihindari
Dua jenis komponen gaji yang tercampur (P2), endpoint tanpa cek role (P5), submit tanpa tahap review (P10), dan formula yang tidak diuji (P1).
