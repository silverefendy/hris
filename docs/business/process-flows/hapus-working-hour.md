# Alur: Hapus Massal Working Hour

- Aktor: System Manager atau HRIS Direksi (dicek di server, bukan hanya di tampilan)
- Pemicu: data Working Hour salah atau tidak diperlukan (misalnya hasil hitung untuk karyawan tanpa baris gaji) dan perlu dibuang per rentang tanggal
- Syarat: saklar site `hris_hapus_wh_aktif` bernilai 1 (bawaan 0)

## Langkah
1. Buka list HRIS Working Hour, menu **Hapus > Hapus Massal**.
2. Isi **Dari Tanggal** dan **Sampai Tanggal** (wajib). Filter opsional: karyawan (satu pilihan), status, dan "Hanya karyawan tanpa baris gaji berlaku".
3. Klik **Cek Dulu**. Tahap ini hanya membaca: menampilkan jumlah dokumen, rincian per status, blokir, peringatan, dan info.
4. Bila tidak ada blokir, tombol berubah menjadi **Hapus**. Centang semua peringatan yang muncul, lalu ketik jumlah dokumen persis seperti yang ditampilkan.
5. Server memvalidasi ulang, lalu mengantre job (queue `long`). Hanya satu proses hapus boleh berjalan sekaligus.
6. Job menghapus per batch 1000 dokumen. Tiap batch: cek ulang blokir, hapus dokumen, bersihkan Version dan Comment terkait, commit.
7. Pantau lewat **Hapus > Status Hapus** (polling 2 detik). Catatan permanen ada di DocType **HRIS Hapus WH Log**.

## Aturan penghalang

| Jenis | Kondisi | Akibat |
|---|---|---|
| Blokir | Dokumen berada di bawah slip berstatus Final, atau di bawah Payroll Period Final | Tidak bisa dihapus. Buka kembali atau hapus slip terkait lebih dulu |
| Blokir | Karyawan punya baris gaji berlaku pada tanggal itu dan jadwalnya punya Payroll Period Final yang memuat tanggal tersebut (kunci periode, sama dengan `period_lock`), walaupun tidak ada slip | Tidak bisa dihapus |
| Peringatan | Di bawah slip Draft atau Ditinjau | Boleh lanjut dengan konfirmasi. Hitung ulang slip setelahnya |
| Peringatan | Menunggu atau Tidak Lengkap belum ditinjau, milik karyawan ber-gaji | Boleh lanjut dengan konfirmasi |
| Peringatan | Memuat input manual HR (klasifikasi, tinjauan, koreksi jam) | Boleh lanjut dengan konfirmasi. Data ini tidak bisa dihitung ulang dari Raw Log |
| Info | Hadir tanpa baris gaji berlaku; Raw Log tidak ikut terhapus | Hanya informasi |

## Jalur hapus bawaan Frappe
Hapus lewat form (menu Hapus) atau list (centang baris, Actions > Delete) tidak memakai dialog di atas. Guard `on_trash` pada controller menolak penghapusan dokumen yang terkunci (slip Final atau periode Final). Hak delete bawaan DocType hanya dimiliki System Manager.

## Pengecualian
- Dokumen baru muncul selama job berjalan: job berhenti bila jumlah putaran melebihi perkiraan.
- Dokumen menjadi terkunci saat job berjalan: job berhenti pada batch itu, dan jumlah yang sudah terhapus dicatat di log.
- Job gagal: transaksi batch berjalan di-rollback, status `Gagal` dan pesan error tercatat di HRIS Hapus WH Log dan Error Log.
- Raw Log tidak ikut terhapus. Hapus lewat fitur Hapus Raw Log bila perlu.
