# Keputusan 9 November 2026 (pembaruan K-128, K-129)

Dasar: [keputusan-2026-11-07.md](keputusan-2026-11-07.md) (K-127, K-128).

| No | Keputusan | Tanggal | Status |
|---|---|---|---|
| K-128 (pembaruan) | `HRIS Payroll Period` dibuat sesuai rancangan 7 November, dengan keputusan kode berikut. **Aturan kesiapan campuran (pilihan Efendy):** Tidak Lengkap wajib Sudah Ditinjau; baris Menunggu menghalangi apa pun statusnya; Tidak Hadir berstatus Tidak Perlu tidak menghalangi; aturan ini hanya menghitung karyawan yang punya baris `HRIS Employee Pay` di jadwal periode itu. **Koreksi syarat gaji:** pemeriksaan karyawan Hadir tanpa baris gaji berlaku bersifat global, tidak dibatasi jadwal periode. **Final hanya setelah akhir periode lewat.** **Buka kembali** (Final ke Draft, alasan wajib dan tercatat) dan tombol **Kembalikan ke Draft** (Ditinjau ke Draft, oleh Payroll Admin atau Payroll Manager). **Notifikasi in-app:** Tinjau memberi tahu Payroll Manager; Kembalikan, Final, dan Buka Kembali memberi tahu Payroll Admin; tidak dikirim ke Administrator atau orang yang bertindak; kegagalan notifikasi tidak membatalkan perpindahan status; email keluar nonaktif. **Pesan penolakan** memakai pola Masalah, Penyebab, Tindakan, Berwenang. **Dialog Periksa Kesiapan** menampilkan semua kekurangan (batas 1500 baris) dengan nama karyawan dan tautan ke dokumen | 2026-11-09 | **Dibuat dan teruji** di `hris-uji.local` (9c0648a, 0ebc487, 913268f, 4807cba): uji skrip kesiapan OK 18, Period OK 28, regresi Working Hour OK 4, Employee Pay OK 30/4/5, GAGAL 0; uji browser per peran (Payroll Admin, Payroll Manager, Administrator) lulus untuk tinjau, kembalikan, penolakan Final, notifikasi, dan dialog kesiapan. Belum ada di produksi; tabel terbentuk saat `bench migrate` produksi (K-102) |
| K-129 | **Hak akses Jadwal Gaji dan Employee Pay.** `HRIS Payroll Schedule`: Payroll Manager baca, tulis, buat, ekspor; Payroll Admin tetap baca, tulis, buat; hapus hanya System Manager (jadwal yang sudah dipakai tetap terkunci parameternya dan tidak bisa dinonaktifkan). `HRIS Employee Pay`: Payroll Manager dan Payroll Admin mendapat `write` agar form tampil, sementara baris tersimpan tetap terkunci oleh controller dan JS, dan Payroll Admin tetap dibatasi baris Harian oleh hook izin (K-127). Pada form baru, pengguna yang bukan Payroll Manager atau System Manager hanya melihat Jenis Gaji Harian | 2026-11-09 | **Dibuat dan teruji** (913268f, 4807cba): K13 sampai K16 OK; browser: Payroll Admin hanya melihat Harian dan bisa menyimpan baris Harian, Payroll Manager murni bisa memilih jadwal, membuat dan mengubah Jadwal Gaji tanpa menu Hapus |

## Catatan
- Pelajaran: uji skrip yang hanya memeriksa izin `create` meloloskan form kosong untuk Manager dan Admin (izin `write` kurang). Uji browser per peran wajib sebelum produksi.
- Pelajaran teknis: `bench console` tidak andal untuk skrip multibaris; pakai Python non-interaktif dari folder `sites`. `reload_doc` dengan reset izin memuat izin dari JSON.
- Izin Payroll Schedule (Manager baca, tulis, buat) perlu diverifikasi pada hari migrasi produksi (K-102), karena tabelnya kemungkinan sudah ada di sana.
- Kombinasi Jenis Gaji dan tipe jadwal (misalnya Bulanan dengan jadwal Mingguan): belum diperiksa apakah sistem menolaknya.

## Belum diputuskan
- Siapa yang menjadi HRIS Payroll Manager (K-110: Kepala HRD sementara memakai peran Payroll Admin).
- Nasib komponen gaji lain (tunjangan, potongan) di fase 2, bersama BPJS dan PPh21.
