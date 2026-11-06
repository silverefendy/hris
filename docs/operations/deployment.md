# Deployment Produksi dan Rollback

Diperbarui: 6 November 2026

Cakupan: runbook migrasi K-102 (Employee ke `HRIS Employee`) di `erp.ciptamebel.co.id`, disusun dari gladi resik di `hris-uji.local` (6 November 2026). Bagian umum produksi (nginx, supervisor atau service pengganti `honcho`, HTTPS, `developer_mode` mati) belum ditulis; daftarnya ada di [../progress/status.md](../progress/status.md) bagian "Sebelum produksi". Keputusan terkait: [../decisions/keputusan-2026-11-06.md](../decisions/keputusan-2026-11-06.md).

## 1. Konsep dasar

| Istilah | Arti |
|---|---|
| Folder kode dipakai bersama | Semua site di bench `/home/it/erp` memakai kode yang sama di `apps/`. `migrate` ke `erp` langsung mengaktifkan kode terbaru, termasuk `HRIS Employee` dan hook sinkron ke Employee |
| Site uji | `hris-uji.local`: salinan produksi dengan scheduler dan email dimatikan (K-117) |
| Migrasi K-102 | Membaca Employee, lalu membuat `HRIS Employee` satu per satu. Tabel `Employee` tidak diubah |
| Pola aman | Semua tahap sebelum `jalankan` hanya menambah struktur kosong. Selama `HRIS Employee` kosong, rollback cukup berhenti. Setelah `jalankan`, rollback = restore dari cadangan |
| Rollback | `restore` dari cadangan, lalu `migrate` supaya skema cocok dengan kode (seperti di gladi) |

Contoh: bila `migrate` gagal di tengah jalan, tabel `HRIS Employee` masih kosong dan data Employee utuh. Bila `jalankan` menulis 1.078 baris lalu hasil verifikasi tidak SAMA, cadangan dipulihkan dan `HRIS Employee` kembali 0.

## 2. Alat (ada di server, belum di repo)

Lokasi: `/home/it/runbook_k102/`. Log tiap perintah tersimpan di folder yang sama; cadangan disalin ke `/home/it/cadangan_k102/`.

| Skrip | Perintah | Fungsi | Menulis data? |
|---|---|---|---|
| `runbook_k102.sh` | `awal <site>` | Catat jumlah Employee, `MAX(modified)`, versi, disk | Tidak |
| | `cadangan <site>` | `bench backup --with-files`, salin, hitung sha256 | Hanya berkas cadangan |
| | `restore <site> <berkas>` | Menimpa database dari cadangan | **Ya** |
| | `skema <site>` | `bench migrate` | **Ya** (struktur) |
| | `maintenance <site> on\|off` | Mode maintenance | Tidak |
| | `cek <site>` | `dry_run` lalu `latih` (rollback) | Tidak |
| | `jalankan <site>` | `migrasi`, `verifikasi`, `verifikasi terapkan=1`, bandingkan tabel Employee | **Ya** |
| `gladi_k102.sh` | `fase1`, `fase2` | Gladi resik di site uji (langkah 1 sampai 5, lalu rollback) | Hanya site uji |
| `produksi_k102.sh` | `cadangan`, `siap`, `mulai`, `pulihkan` | Urutan produksi (bagian 4) | `mulai` dan `pulihkan` menulis |
| `diag_erp_k102.sh` | (tanpa perintah) | Diagnosa baca-saja kondisi site sebelum migrasi | Tidak |

Pengaman bawaan:
- Perintah yang menulis meminta ketikan persis, misalnya `RESET hris-uji.local`, `MIGRASI <site>`, `MIGRATE <site>`, `PULIHKAN <site> DARI CADANGAN`, `MULAI PRODUKSI <site>`. Salah ketik (misalnya titik di tempat strip) membatalkan perintah tanpa menulis apa pun.
- `restore` ke site selain uji lebih dulu membuat cadangan pengaman dan berhenti bila itu gagal.
- Password root MariaDB diminta lewat prompt tersembunyi dan tidak ditulis ke berkas atau log.
- `SITE_TARGET=hris-uji.local` pada `produksi_k102.sh` mengganti site sasaran, sehingga urutan produksi bisa dilatih di site uji. Tanpa variabel itu, sasarannya `erp.ciptamebel.co.id`.

Status: `runbook_k102.sh` dan `gladi_k102.sh` sudah dijalankan penuh di site uji (bagian 10). `produksi_k102.sh` diuji 6 Nov di `hris-uji.local` lewat `SITE_TARGET`: `cadangan`, `siap`, dan `mulai` lulus penuh. `pulihkan` hanya sampai sha256 dan prompt konfirmasi (dibatalkan); restore itu sendiri terbukti di gladi. `diag_erp_k102.sh` dijalankan di produksi 6 Nov 22:47 WIB: bagian git, versi, dan disk berfungsi; bagian database lewat `bench console` tidak mengeluarkan keluaran dan perlu diperbaiki.

## 3. Prasyarat

| No | Syarat | Cara memastikan |
|---|---|---|
| 1 | K-126 dan K-102 sudah di `origin main` (kini 7278bb7) | `git -C /home/it/erp/apps/hris log --oneline -3` |
| 2 | Gladi resik lulus di site uji, termasuk restore | Bagian 10 |
| 3 | Cadangan produksi baru, disalin ke mesin lain, sha256 cocok | Bagian 4 dan 7 |
| 4 | Di luar jam kerja HRD (belum ada jadwal tetap; kemungkinan saat lembur) dan HRD sudah diberi tahu | Konfirmasi manual |
| 5 | Tabel Employee produksi sama dengan saat cadangan (jumlah dan `MAX(modified)`) | Otomatis di `produksi_k102.sh siap` |
| 6 | Cara me-restart `erp` diketahui | Ya (6 Nov): Ctrl+C di terminal tempat `bench start` berjalan, lalu `bench start` lagi |
| 7 | Ruang disk minimal 5 GB | Otomatis di `siap` (per 6 Nov: 28 GB tersisa dari 48 GB) |
| 8 | Uji per peran | Dikerjakan setelah migrasi produksi, langsung di `erp.ciptamebel.co.id` (keputusan Efendy 6 Nov); bukan syarat sebelum produksi |

## 4. Prosedur produksi (disarankan)

Dari `/home/it/erp`. Ganti `produksi` dengan `bash /home/it/runbook_k102/produksi_k102.sh`.

| No | Perintah | Hasil yang benar |
|---|---|---|
| 1 | `produksi cadangan` | Kondisi Employee dicatat, cadangan dibuat, sha256 dan jalur berkas tercetak |
| 2 | Salin ke mesin lain (bagian 7) | Hash di mesin tujuan sama dengan sha256 di server |
| 3 | `produksi siap` | `SIAP: semua pemeriksaan lulus` |
| 4 | `produksi mulai` | Berakhir `SELESAI` (enam tahap di bawah) |
| 5 | Uji asap (bagian 9) | Sinkron berhasil |

Pemeriksaan `siap`: cabang `main`, semua commit hris sudah di-push, berkas cadangan ada dan sha256 cocok, cadangan berumur kurang dari 6 jam, tabel Employee sama dengan saat cadangan (jumlah dan `MAX(modified)`), ruang disk cukup.

Tahap `mulai` (berhenti dan menyisakan maintenance ON bila ada yang gagal):

| Tahap | Isi | Bukti berhasil |
|---|---|---|
| 1 | Maintenance ON | Pesan `Maintenance on` |
| 2 | `skema` (`migrate`) | Tanpa galat, HRIS Employee 0 |
| 3 | Restart `erp` | Anda restart manual lalu tekan Enter |
| 4 | `awal` dan `cek` | `CEK LULUS` (dry_run SIAP, latihan SAMA, rollback bersih) |
| 5 | `jalankan` | `MIGRASI LULUS` dan `SAMA: tabel Employee tidak berubah` |
| 6 | Maintenance OFF | Setelah Anda konfirmasi |

## 5. Prosedur manual (tanpa `produksi_k102.sh`)

Ganti `rb` dengan `bash /home/it/runbook_k102/runbook_k102.sh`, dan `S` dengan `erp.ciptamebel.co.id`.

| No | Perintah | Bukti berhasil |
|---|---|---|
| 1 | `rb awal S` | Jumlah dan `MAX(modified)` Employee dicatat |
| 2 | `rb cadangan S`, lalu salin ke mesin lain | sha256 cocok |
| 3 | `rb maintenance S on` | Maintenance on |
| 4 | `rb skema S` | Tanpa galat |
| 5 | Restart `erp` | Situs hidup |
| 6 | `rb cek S` | `CEK LULUS` |
| 7 | `rb jalankan S` | `MIGRASI LULUS` |
| 8 | `rb maintenance S off` | Maintenance off |

## 6. Hati-hati saat `migrate` ke `erp`

- `bench migrate` memigrasi **semua** app yang terpasang di site, termasuk `wms` pada branch `feat/wms-bag-transfer-partial-receipt` yang sedang aktif di disk. Hal yang sama terjadi di site uji (salinan produksi) dan lolos, tetapi perlu disadari.
- Server dev (`frappe serve`, `developer_mode`) memuat ulang kode Python otomatis, sehingga perubahan Python bisa aktif sebelum `migrate`.
- Setelah migrasi, Simpan pertama pada karyawan memicu sinkron ke Employee. Hanya satu Employee (`HR-EMP-01078`) yang namanya terpecah ulang (nama lengkap ke `first_name`); `employee_name` tetap sama.
- `migrate` membuat role `HRIS Payroll Manager`, `HRIS Direksi`, dan `HRIS Employee Admin` (lewat `after_migrate`). Uji per peran baru bisa dilakukan setelah itu; pakai akun uji khusus, karena menyimpan HRIS Employee memicu sinkron ke Employee ERPNext.

## 7. Salin cadangan ke mesin lain (dari PC Windows)

`scp` dari server ke jalur Windows (`D:\...`) gagal karena `D:` dibaca sebagai nama host. Tarik dari sisi Windows, di PowerShell (ganti nama berkas sesuai cadangan terbaru):

```powershell
scp "it@10.1.0.26:/home/it/cadangan_k102/<AWALAN>-erp_ciptamebel_co_id-*" "D:\Efendy\Temp\"
Get-FileHash "D:\Efendy\Temp\<AWALAN>-erp_ciptamebel_co_id-database.sql.gz" -Algorithm SHA256
```

Hash harus sama dengan sha256 yang dicetak `cadangan`. Terbukti 6 November 2026: cadangan `20261106_152714` tiba utuh dengan hash cocok. Alamat server diperiksa dengan `hostname -I`.

## 8. Rollback

| Gagal di | Tindakan |
|---|---|
| Tahap 1 sampai 5 (maintenance, skema, restart, cek) | Berhenti. Tabel `HRIS Employee` kosong, data Employee tidak tersentuh. Kirim log di `/home/it/runbook_k102/` |
| Tahap `jalankan` (tabel Employee berubah atau verifikasi tidak SAMA) | `produksi pulihkan` (cek sha256, restore, lalu tawaran `migrate`) |
| Setelah maintenance OFF | `produksi pulihkan`, lalu restart dan maintenance off manual |

`pulihkan` memakai berkas yang dicatat oleh `cadangan` dan menolak berjalan bila sha256 tidak cocok. Hasil rollback: `HRIS Employee` kosong, Employee utuh (sama seperti keadaan setelah `migrate`, sebelum `jalankan`).

## 9. Setelah migrasi (uji asap)

1. Buka tiga `HRIS Employee` (satu berstatus Lengkap, satu Perlu Dilengkapi, `HR-EMP-01078`): data benar, Audit Trail bersih.
2. Ubah telepon satu karyawan, Simpan, lalu cek di Employee: sinkron berhasil, status sinkron Berhasil.
3. `rb awal S` dan bandingkan dengan kondisi awal: `MAX(modified)` Employee berubah hanya bila Anda menyimpan karyawan pada langkah 2.

## 10. Hasil gladi resik di `hris-uji.local` (6 November 2026)

| Langkah | Hasil |
|---|---|
| Cadangan produksi | Database 2,8 MiB, sha256 tercetak, berkas disalin |
| Restore ke site uji | Berhasil, `migrate` jalan, HRIS Employee 0, kolom `data_status` dan `data_note` ada, scheduler mati |
| Kondisi awal | Employee 1.078 |
| `cek` | `CEK LULUS` |
| `jalankan` | `MIGRASI LULUS`: dibuat 1.078, verifikasi SAMA, status Berhasil 1.078, tabel Employee tidak berubah |
| Cek browser | Data benar, Audit Trail bersih |
| Rollback (restore berkas yang sama) | HRIS Employee kembali 0 |
| Salin cadangan ke PC | Utuh, sha256 cocok |
| Uji tampilan D1 sampai D4 | Lulus (bagian Kelengkapan Data tampil, perubahan tercatat di Audit Trail HRIS, filter daftar tampil) |

## 11. Belum diketahui atau belum terbukti

| Hal | Kondisi |
|---|---|
| Cara me-restart `erp` produksi | Ctrl+C lalu `bench start` (dari Efendy, 6 Nov); belum pernah dijalankan dalam urutan produksi. `produksi_k102.sh` menunggu Enter setelah restart manual |
| Kebutuhan password root MariaDB untuk `restore` | Diketik di prompt saat gladi. Skrip meneruskannya lewat argumen `--db-root-password`, sehingga sesaat terlihat di daftar proses (`ps`) bagi pengguna lain di server. Risiko kecil di server dengan satu admin; verifikasi opsi `bench restore` di dokumentasi Frappe |
| Jalur restore produksi di `runbook_k102.sh` | Hanya cabang site uji yang sudah dijalankan. Cabang produksi (cadangan pengaman, konfirmasi panjang) belum pernah dijalankan |
| `produksi_k102.sh` pada produksi | Teruji di site uji; belum pernah menyasar `erp.ciptamebel.co.id` |
| Diagnosa database produksi | `diag_erp_k102.sh` belum berhasil membaca database lewat `bench console`; perlu pendekatan lain |
| Skrip di repo | Skrip hanya ada di `/home/it/runbook_k102/` |
