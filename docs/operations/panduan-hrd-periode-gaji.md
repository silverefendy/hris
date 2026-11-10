# Panduan HRD: Urutan Kerja Tiap Periode Gaji (draf 11 November 2026)

Status: **draf**, disusun dari perilaku yang teruji di site uji (`hris-uji.local`). Belum berlaku di produksi dan belum ditinjau HRD. Nama tombol mengikuti tampilan site uji; bila berbeda di produksi, perbarui dokumen ini.

## 1. Urutan kerja

| Langkah | Di mana | Yang dilakukan | Catatan |
|---|---|---|---|
| 1 | HRIS Working Hour, tombol **Hitung Periode** | Hitung Working Hour untuk seluruh tanggal periode (pilih cakupan Semua, Karyawan, Departemen, atau Grup) | **Wajib sebelum membuat slip.** Slip tidak dibuat untuk minggu atau periode yang Working Hour-nya belum dihitung |
| 2 | HRIS Working Hour | Periksa baris **Tidak Lengkap** (hanya satu punch) dan perbaiki bila perlu | Baris Tidak Lengkap wajib berstatus Ditinjau sebelum Periode Final |
| 3 | HRIS Working Hour | Klasifikasi tiap **Tidak Hadir** yang bertanda Perlu Tinjauan: Mangkir, Cuti, Izin, Sakit (dengan atau tanpa surat dokter), atau Lainnya (catatan wajib) | Klasifikasi menentukan potongan gaji karyawan Bulanan. Karyawan Harian tanpa punch dianggap tidak masuk tanpa perlu klasifikasi |
| 4 | HRIS Payroll Period | Pastikan Periode berstatus **Draft** | Slip hanya dibuat atau dihitung ulang saat Periode Draft |
| 5 | HRIS Payroll Slip, tombol **Buat Slip** | Buat slip (cakupan Semua, Karyawan, Department, atau Grup) | Karyawan Hadir tanpa baris gaji dilewati dan dilaporkan; lengkapi **HRIS Employee Pay** lalu buat slip lagi |
| 6 | HRIS Payroll Slip | Periksa slip dan periksa catatan peringatan di slip | Slip bisa dihitung ulang dengan **Hitung Ulang** selama Draft |
| 7 | HRIS Payroll Period | **Tinjau** (Payroll Admin atau Payroll Manager) | Koreksi: **Kembalikan ke Draft** |
| 8 | HRIS Payroll Period | **Finalkan** (hanya Payroll Manager) | Slip terkunci setelah Final; membuka kembali memerlukan alasan |

## 2. Syarat Periode boleh Final

- Periode sudah berakhir.
- Tidak ada Working Hour berstatus Menunggu; Tidak Lengkap sudah Ditinjau.
- Tidak ada karyawan Hadir yang belum punya baris gaji berlaku.
- Tidak ada Tidak Hadir yang belum diklasifikasi (khusus yang mewajibkan klasifikasi).

## 3. Risiko yang perlu diperhatikan

| Risiko | Penyebab | Pencegahan |
|---|---|---|
| **PPh 21 bulan itu tidak terpotong** | PPh 21 dipotong pada slip terakhir bulan bayar. Bila slip terakhir dilewati karena Working Hour belum dihitung, tidak ada slip yang memotong pajak karyawan itu | Ikuti langkah 1 sebelum langkah 5; periksa peringatan "dilewati" pada hasil Buat Slip |
| Pajak terlalu kecil sementara | Slip lain bulan itu belum ada saat slip terakhir dihitung; pajak dihitung dari slip yang ada dan diperbarui setelah slip lain dibuat | Setelah semua slip bulan itu ada, lakukan **Hitung Ulang** pada slip terakhir (hasilnya idempoten) |
| BPJS terpotong dua kali atau tidak sama sekali | BPJS dipotong sekali sebulan pada slip pertama bulan itu | Jangan menambah baris BPJS manual; gunakan Hitung Ulang |

## 4. Belum berlaku atau menunggu konfirmasi

- Tarif TER, tabel PTKP, dan angka BPJS resmi belum diisi (menunggu HRD; lihat `permintaan-ke-hrd-2026-11-10.md`). Site uji memakai angka fiktif.
- Aturan potongan karyawan Harian multi-slip belum teruji pada data nyata.
- Aturan BPJS pada slip pertama bulan adalah ketentuan sementara; konfirmasi HRD diperlukan.
- Seluruh alur ini belum dijalankan di produksi (menunggu migrasi K-102).
