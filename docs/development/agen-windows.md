# Agen Windows untuk mesin Solution

Dokumen ini mencatat agen Windows yang menarik log dari mesin absensi Solution lewat SDK `zkemkeeper`, lalu mengirimnya ke HRIS. Kontrak endpoint ada di [agent-api.md](../architecture/agent-api.md) dan tidak diulang di sini.

**Status (3 November 2026):** teruji pada satu mesin dan dua PC (satu PC lulus penuh, satu PC lagi menunggu uji). Penarikan dilakukan **manual** lewat jendela; tidak ada jadwal otomatis.

## 1. Mengapa agen Windows

Mesin Solution jenis ini tidak bisa ditarik dengan `pyzk` (gagal terhubung). SDK vendor berbentuk COM (`zkemkeeper`) yang hanya berjalan di Windows. Agen berada di PC Windows yang bisa menjangkau mesin dan server HRIS, membaca log lewat SDK, lalu mengirim ke endpoint `push_punches`.

## 2. Aturan teknis yang terbukti

| Aturan | Bukti |
|---|---|
| SDK hanya bisa terhubung dari proses **32-bit (x86)** | Dari PowerShell x64 objek COM berhasil dibuat tetapi `Connect_Net` gagal (kode -7); dari x86 berhasil |
| Semua DLL pendukung SDK harus **satu generasi** dengan `zkemkeeper.dll` | PC dengan `zkemkeeper.dll` 2024 dan lima DLL komunikasi 2010 gagal terhubung (kode -307 lalu -2); setelah kelima DLL diganti paket yang sama, koneksi berhasil |
| Metode baca yang dipakai: `ReadAllGLogData` lalu `SSR_GetGeneralLogData` | Jumlah log terbaca sama dengan jumlah di mesin |
| Penarikan tidak menghapus log di mesin | Skrip tidak memanggil perintah hapus; jumlah log sebelum dan sesudah konsisten |
| Waktu punch dikirim sebagai waktu mesin (WIB, tanpa zona) | Endpoint menolak zona dan waktu lebih dari satu hari ke depan. Jangan pakai jam OS server (UTC) |

Makna kode error SDK (-7, -307, -2) **belum diverifikasi** terhadap dokumentasi vendor. Tabel di atas hanya mencatat apa yang teramati.

### Lima DLL yang perlu disamakan

`comms.dll`, `rscagent.dll`, `rscomm.dll`, `tcpcomm.dll`, `usbcomm.dll` di folder sistem 32-bit (`SysWOW64`). Pada PC yang pernah memasang SDK lama, kelimanya berstatus ReadOnly dan bertanggal 2010, sehingga penyalinan paket baru ditolak ("Access is denied") dan hasilnya paket bercampur. Perbaikan: cadangkan kelimanya, buang atribut ReadOnly dengan hak administrator, salin dari paket, bandingkan hash, lalu daftarkan ulang `zkemkeeper.dll` dengan `regsvr32` 32-bit. Cek selesai bila hash kelimanya sama dengan paket.

Peringatan: DLL ini bersifat global di PC. Aplikasi absensi lain yang memakainya ikut terpengaruh; simpan cadangan untuk jalan mundur.

## 3. Cara kerja jendela agen

Skrip PowerShell x86 dengan jendela Windows Forms, dipasang di folder tetap pada PC agen. Isinya:

| Elemen | Fungsi |
|---|---|
| Pengaturan | Alamat server (dropdown yang bisa diketik dan bertambah otomatis), nama site, nama Device, IP dan port mesin |
| Token dan kunci komunikasi mesin | Disimpan terenkripsi DPAPI per pengguna Windows di PC itu; tidak pernah ditulis ke log |
| Tarik + Kirim | Membaca mesin, menyimpan di memori, mengirim hanya log baru (sejak titik terakhir terkirim dikurangi satu hari). Tanpa CSV di tengah |
| Tarik ke CSV | Jalur cadangan: menulis CSV dan mencatat hash SHA-256 |
| Kirim dari CSV | Jalur cadangan: bila hash tidak cocok dengan catatan, muncul peringatan dan data ditandai `csv-diubah` |

Berkas pendukung di folder agen: `config.json` (non-rahasia), `state.json` (titik terakhir terkirim dan daftar hash CSV), `agen.log` (dibatasi 1 MB), serta folder `cadangan` untuk CSV. Hak akses folder dibatasi untuk akun Windows agen dan SYSTEM.

Konfirmasi hanya muncul pada kiriman pertama, kiriman lebih dari 500 baris, dan setiap kiriman dari CSV. Pengiriman memakai batch 500 punch. State hanya maju bila seluruh permintaan sukses dan tidak ada baris error; kegagalan di tengah aman diulang karena duplikat ditolak.

## 4. Tanda asal data

Setiap punch dari agen membawa objek di `raw_payload` (field yang sudah ada, tanpa perubahan struktur):

| Kunci | Isi |
|---|---|
| `agen` | Versi skrip |
| `pc` | Nama komputer pengirim |
| `ditarik` | Waktu tarik di PC (menit) |
| `via` | `langsung`, `csv`, atau `csv-diubah` |
| `csv_sha256` | Hash file, hanya untuk jalur CSV |

Filter di List View HRIS Raw Log: field `raw_payload`, operator *like*, nilai misalnya `%csv-diubah%`. Terbukti di server untuk `via: langsung`.

Batas: tanda dikirim oleh sisi klien, jadi hanya jejak, bukan penjaga. Orang yang memegang token tetap bisa mengirim data langsung tanpa agen. Penjaga yang sebenarnya adalah token, daftar IP yang diizinkan, dan pembandingan jumlah log mesin dengan HRIS. Raw Log yang masuk sebelum fitur tanda ini ada tidak memiliki `raw_payload`.

## 5. Hasil uji

| Uji | Hasil |
|---|---|
| Endpoint dengan `curl`: token salah, heartbeat, satu punch, kirim ulang | 401; 200; created 1; duplicate 1. Data uji dihapus dan jumlah Raw Log kembali semula |
| SDK dari x64 dan x86 | x64 gagal, x86 berhasil (jumlah log, user, versi firmware terbaca) |
| Kirim penuh dari CSV pertama | Sembilan permintaan, created sesuai jumlah log, error 0 |
| Tarik + Kirim langsung dari PC kedua | created hanya punch baru, sisanya duplicate, error 0; Raw Log di server sama dengan jumlah log mesin |
| Tanda `raw_payload` di server | Terlihat `via: langsung`, versi agen, nama PC, waktu tarik |
| Kirim dari CSV tidak cocok catatan | Peringatan muncul sebelum pengiriman |

## 6. Belum dikerjakan

| Item | Catatan |
|---|---|
| Uji di PC kedua yang belum menyala | Termasuk pembandingan hash DLL |
| Isi daftar IP yang diizinkan | Saat ini kosong; isi dengan IP semua PC agen sebelum produksi |
| Rotasi token dan penggantian kunci komunikasi mesin | Nilai lama pernah tampil di layar atau percakapan; ganti sebelum produksi |
| Tombol pembanding jumlah log mesin dengan HRIS | Butuh endpoint baca baru di server |
| Tanda tangan per kiriman (HMAC) | Perubahan kode server; belum diputuskan |
| Field khusus `via` di Raw Log | Perubahan struktur DocType; belum diputuskan, filter `raw_payload` dipakai dulu |
| Penarikan terjadwal (Task Scheduler) | Ditunda; PC agen tidak menyala terus |
| Skrip agen belum masuk repo | Keputusan lokasi dan pemasangan ke PC lain menyusul |
| Mesin Solution lain pada jalur Pull | Belum diuji; perlu dibuktikan satu mesin dulu |
