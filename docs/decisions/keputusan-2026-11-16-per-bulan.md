# K-141 — Komponen Per Bulan dibayar sekali sebulan

- Tanggal: 16 November 2026
- Status: disetujui; diterapkan dan teruji di `hris-uji.local` (produksi menyusul lewat K-102)

## Konteks

Katalog `HRIS Pay Component` punya tiga cara pembayaran (field Dibayar): Per Slip, Per Bulan, Per Hari Hadir. Deskripsi Per Bulan menjanjikan "sekali di slip pertama bulan itu", tetapi kode memperlakukannya sama dengan Per Slip. Akibatnya karyawan dengan slip mingguan (4 atau 5 slip per bulan) akan menerima tunjangan Per Bulan di setiap slip.

Saat ini belum ada karyawan mingguan yang menerima tunjangan bulanan (keterangan Efendy), tetapi perilakunya harus benar sebelum kasus itu muncul. Efendy meminta agar bisa diatur: tiap slip atau sekali sebulan, di awal atau di akhir bulan, supaya bila karyawan tidak masuk pada minggu ke-2 sampai ke-4 tunjangannya masih sempat dihapus.

## Keputusan

| Dibayar | Waktu Bayar | Perilaku |
|---|---|---|
| Per Slip | tidak ada | Tiap slip (tidak berubah) |
| Per Bulan | Slip Pertama (bawaan) | Dibayar di slip pertama yang tanggal bayarnya jatuh di bulan itu; slip lain Rp0 dengan catatan |
| Per Bulan | Slip Terakhir | Dibayar di slip terakhir yang tanggal bayarnya jatuh di bulan itu; slip lain Rp0 dengan catatan |
| Per Hari Hadir | tidak ada | Tidak berubah |

1. Bulan ditentukan dari **tanggal bayar** slip, sama dengan BPJS dan PPh 21. Penentu slip pertama (BPJS) dan slip terakhir (PPh 21) dipakai ulang di `giliran_bulan.py`.
2. Karyawan yang hanya punya satu slip per bulan (jadwal Bulanan): slip itu pertama sekaligus terakhir, sehingga selalu dibayar.
3. Pengaturan per komponen di katalog: field `monthly_timing` (Waktu Bayar), bawaan Slip Pertama, tampil hanya bila Dibayar = Per Bulan.
4. Pengecualian (HEC Tidak Berlaku) dinilai pada periode slip yang menjadi gilirannya. Pada Slip Terakhir, pengecualian di minggu terakhir menghapus tunjangan bulan itu.
5. Slip yang bukan giliran mendapat satu catatan ("dibayar sekali sebulan ... bukan slip ini"). Catatan ini usulan Claude dan tidak menandai slip sebagai perlu diperiksa.
6. Payroll Summary tampilan Per Periode memakai giliran periode itu. Tampilan Per Tanggal tidak punya periode, sehingga tetap berperilaku lama.
7. Bila giliran gagal dihitung, komponen dihitung tiap slip seperti perilaku lama dan galat dicatat di Error Log.

## Alternatif yang dipertimbangkan

| Alternatif | Hasil |
|---|---|
| Override per penetapan (HEC atau HCA) | Ditunda: mengubah dua DocType berjalan dan belum ada kasusnya. Bila dibuat, prioritasnya HEC > HCA > katalog |
| Dibagi rata sesuai jumlah slip | Ditolak: nominal per slip berubah-ubah |
| Dibiarkan; karyawan mingguan memakai Per Slip atau Per Hari Hadir | Tidak memenuhi permintaan pengaturan yang fleksibel |

## Konsekuensi

- Bila slip pertama (atau terakhir) bulan itu dilewati karena Working Hour belum dihitung, tunjangan Per Bulan bulan itu tidak terbayar. Sama dengan batasan BPJS dan PPh 21. Penanganannya: hitung ulang slip atau baris Manual.
- Field `monthly_timing` baru ada di produksi setelah `migrate` K-102.
- Payroll Summary Per Periode di browser belum diuji; menunggu restart `bench start` (bagian dari W6 dan K-102).
- Uji browser form katalog (Waktu Bayar muncul hanya saat Per Bulan) belum dilaporkan.

## Pengujian (`hris-uji.local`)

| Uji | OK | Cakupan |
|---|---|---|
| `uji_per_bulan` | 16 | Aturan murni di `hitung_tunjangan` |
| `uji_per_bulan_slip` | 8 | Giliran tersambung ke slip dan Payroll Summary |
| `uji_per_bulan_mingguan` | 9 | Jadwal Mingguan sintetis: bulan bayar 4, 4, dan 5 slip |
| Regresi | 13 uji lain dan `uji_payroll_slip` (77) | Semua hijau |

Commit: `4a37e60` (field dan aturan), `51a6fc7` (penyambungan), `2120cdb` (uji Mingguan).
