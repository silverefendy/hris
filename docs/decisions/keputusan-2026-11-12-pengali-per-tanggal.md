# K-137: Pengali lembur per tanggal berlaku dan notifikasi slip Draft

Tanggal: 12 Nov 2026. Lanjutan K-136 (HRIS Department Rule). Menjawab pertanyaan E8.

## 1. Latar

Bila pengali lembur sebuah Department berubah di tengah periode gaji, apakah satu slip memakai satu pengali atau dipecah menurut tanggal.

## 2. Keputusan (Efendy, 12 Nov 2026)

| Hal | Keputusan |
|---|---|
| Pemecahan | Opsi B: pengali dicari **per tanggal lembur**, mengikuti tanggal berlaku aturan |
| Slip Ditinjau atau Final | Tidak disentuh |
| Slip Draft | Tidak berubah sendiri; pengguna menekan Hitung Ulang bila ingin pengali baru |
| Pemberitahuan | Pesan di layar penyimpan Rule dan notifikasi in-app ke HRIS Payroll Manager dan HRIS Payroll Admin |
| Karyawan tanpa Department (E7) | Ikut aturan akar |
| Pengali lembur | 1.0 untuk semua lembur (aturan akar) |

## 3. Cara kerja

| Bagian | Perilaku |
|---|---|
| Pencarian | `resolve(department, tanggal)` dipanggil sekali per tanggal yang punya lembur; nilai kosong atau 0 mengikuti Department induk sampai akar (per parameter) |
| Bulanan | Menit lembur dikelompokkan per pengali; Catatan Perhitungan merinci per rentang tanggal bila pengali berubah |
| Harian | Pengali dipakai per hari lembur |
| Tersimpan di slip | Satu angka: pengali pada tanggal akhir periode (tidak ada perubahan DocType) |
| Gagal mencari aturan | Slip dilewati dengan pesan, tidak memakai nilai bawaan diam-diam |

Contoh (Bulanan, tarif 100.000 per jam): 10 jam x 1.0 untuk 15 sampai 19 Okt dan 18 jam x 1.5 untuk 20 sampai 28 Okt.

## 4. Notifikasi

Dipicu saat HRIS Department Rule baru atau Department, tanggal berlaku, status aktif, atau pengali berubah. Dihitung slip Draft pada Department itu dan cabangnya dengan akhir periode sama atau setelah tanggal berlaku **dan punya lembur**. Jumlah nol: tidak ada pesan. Kegagalan notifikasi dicatat di Error Log dan tidak membatalkan penyimpanan Rule.

## 5. Batasan

- Jumlah slip bersifat perkiraan: bila cabang punya aturan sendiri, slip di cabang itu sebenarnya tidak berubah.
- Department diambil dari HRIS Employee, bukan snapshot per hari di Working Hour. Peminjaman karyawan (P9) belum tersambung.
- Tanggal lembur sebelum aturan akar berlaku membuat slip dilewati dengan pesan.

## 6. Uji

| Uji | Hasil |
|---|---|
| uji_pengali_tanggal.py | OK 14, GAGAL 0 |
| uji_notif_department_rule.py | OK 10, GAGAL 0 |
| uji_notif_alur.py (alur penyimpanan Rule, rollback penuh) | OK 5, GAGAL 0 |
| Regresi uji_payroll_slip dan uji_slip_massal | OK 77 dan OK 19, GAGAL 0 |

Commit: bbbb27d (pengali per tanggal), 8eb5c8e (notifikasi).
