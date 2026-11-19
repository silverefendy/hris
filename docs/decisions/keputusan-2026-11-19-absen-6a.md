# Keputusan 19 Nov 2026: Working Hour kosong, potongan absen (6a), batas hari depan

## Keputusan

| Hal | Keputusan |
|---|---|
| Dokumen Working Hour kosong | Libur dan Tidak Terjadwal tanpa punch tidak dibuat. Satu tap tetap diproses (Tidak Lengkap). Hari terjadwal tanpa punch tetap dibuat (Tidak Hadir), karena dasar potongan Bulanan. Dokumen kosong lama dibiarkan, dibersihkan lewat 6b. Saklar `hris_skip_hari_kosong` (bawaan aktif). |
| Bulanan, Tidak Hadir belum diklasifikasi | Dipotong sementara sampai HRD mengklasifikasi. Saklar `hris_absen_belum_klas_dipotong` (bawaan mati). Tampilan opsi A: slip memotong dengan catatan yang menyebut tanggal; dokumen Working Hour tetap menampilkan "Dipotong Gaji: tidak". |
| Harian, Tidak Hadir | Tidak digaji dan dokumen tidak dibuat. Saklar `hris_skip_harian_absen` (bawaan mati). |
| Harian tanpa hari kerja | Opsi A: slip dilewati dengan pesan jelas, tidak ada slip upah nol. |
| Hari ini dan setelahnya | Tidak dihitung di hitung massal. Saklar `hris_batasi_hari_depan` (bawaan aktif). Tombol Hitung Ulang pada dokumen hari ini juga tidak menghitung (jalur sama). |
| `device_code` HRIS Device | Field baru, otomatis tetapi bisa diedit, unik. Dipakai untuk Raw Log baru; Raw Log lama tidak di-rename. |
| Hak tulis PTKP | Direksi boleh (disengaja). Patokan `uji_izin_pph21` menjadi 29. |
| Letak `ptkp_status` | Opsi B: tepat setelah `pph21_enrolled` di HRIS Employee. |

## Bukti uji (site `hris-uji.local`)

- `uji_absen_6a`: 9 OK (fungsi hitung, tanpa database).
- Perbandingan slip periode HPP-01107, saklar mati lalu hidup: dua slip Bulanan berubah sesuai hitungan manual (17 hari x 3.000.000 / 25 = 2.040.000; 25 hari x 3.000.000 / 25 = 3.000.000). Selisih net pay sama dengan potongan. Tiga hari Tidak Lengkap tetap tidak dipotong.
- Regresi setelah perbaikan: SAMA 63, BEDA 3 (semuanya dijelaskan, gagal 0), ERROR 0. Patokan disimpan ulang (70 modul).

## Belum terbukti

- Slip Harian pada data nyata (hanya unit test fungsi hitung).
- Pengaruh Potongan Absen (`taxable: 1`) terhadap PPh 21; PPh21 Settings belum aktif di site uji.
- Perilaku produksi bila data mesin belum ditarik: karyawan Bulanan tampak Tidak Hadir dan slip Draft terpotong sementara.
- Produksi belum disentuh: `migrate` belum dijalankan, saklar `hris_skip_hari_kosong` dan `hris_batasi_hari_depan` sudah diset 0.
