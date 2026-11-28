# Checklist Device Tool: Yang Kurang / Perlu Di-upgrade

Diperiksa: 27 November 2026, versi kode 0.8.0. Daftar ini hasil membaca
seluruh `src/*.cs` dan membandingkannya dengan `README.md` serta catatan
0.7.0/0.7.2. Tidak ada perubahan kode yang dilakukan.

## 1. Harus diperbaiki (risiko nyata)

| # | Hal | Letak | Kenapa penting | Usul perbaikan |
|---|---|---|---|---|
| 1 | Template jari disimpan **plaintext** saat "Baca template" | `Dev.ReadTemplates` → `File.WriteAllText(path, tmp)` ke `data\cadangan` | Data biometrik bisa dibaca siapa pun yang membuka folder; bertentangan dengan `TemplateStore` yang sengaja dienkripsi | Tulis lewat `TemplateStore`/`Crypto`, atau hapus berkas setelah dibaca; paling tidak beri opsi "jangan simpan ke disk" |
| 2 | Info mesin tidak lengkap tersimpan | `InfoMesin.Peta` vs `Dev.InfoRows` | Enam baris yang dibaca (Nama perangkat, Vendor, Password terdaftar, Catatan operasi, Sisa jari/user/log, Angka 22) hilang saat disimpan | Tambah kolom di skema v4 + masukkan ke `Peta` |
| 3 | Tombol panduan menuju folder yang tidak ada | `MainForm.OnPanduan`, tab Bantuan | Pengguna mendapat pesan "Folder panduan belum ada" | Buat `tools/device_tool/docs/` (panduan pengguna + pemulihan) atau buka `docs/development/device-tool-*.md` |
| 4 | Kata sandi bawaan masih aktif | `Akun.Bawaan`, `Akun.Masuk` | Siapa pun yang punya exe bisa masuk sebagai administrator | Paksa ganti sandi saat login pertama; simpan penanda di `pengguna.hdtusr` |
| 5 | Login tanpa batas percobaan | `Akun.Masuk` (hanya `Sleep(800)`) | Tebakan sandi tak terbatas | Kunci 5 menit setelah 5 kegagalan, catat di `AuditLog` |
| 6 | `GetStrCardNumber` tanpa indeks mesin | `Dev.ListUsersLengkap` | Nomor kartu bisa milik user sebelumnya bila SDK berperilaku lain | Baca kartu per user lewat API yang eksplisit, atau beri catatan risiko di dokumentasi |

## 2. Perlu di-upgrade (kualitas & kesesuaian dokumen)

| # | Hal | Usul |
|---|---|---|
| 7 | `README.md` masih "tahap 2" dan menyebut Comm Key bersandi aplikasi | Tulis ulang: versi 0.8.0, daftar fitur nyata, DPAPI, isi `docs\` |
| 8 | Versi hanya konstanta `Versi` di `MainForm.cs` | Tambah `AssemblyFileVersion`/ikon di `build.ps1` (`/win32icon`, `/optimize+`) dan tampilkan dari assembly |
| 9 | Tidak ada uji untuk `KirimHris`, `BacaCsv`, `Salinan`, `Brankas`, `Peran` | Tambah uji konsol di `uji_sqlite/`: parsing CSV, batch 500, penandaan `.hdtman`, buka/tutup kunci |
| 10 | `Salinan` hanya menandai "terkirim" bila `Error == 0` | Simpan hasil per batch di `.hdtman` agar kirim ulang bisa dilanjutkan dari batch gagal |
| 11 | `KirimHris` berhenti total pada satu kegagalan jaringan | Tambah 1 percobaan ulang dengan jeda untuk timeout/5xx (bukan 401) |
| 12 | `BacaCsv` mengandalkan urutan kolom dan hanya melewati header bila diawali `device_user_id` | Validasi header/kolom wajib, beri pesan jelas bila format berubah |
| 13 | `DatabaseForm` tidak bisa melihat `template_jari` dan `kunci_template` | Tambah hitungan template per mesin (tanpa membuka isi) agar bisa dicocokkan dengan Info mesin |
| 14 | `SnapshotUser` menghapus seluruh snapshot mesin lalu mengisi ulang | Sudah aman dalam transaksi, tetapi tidak menyimpan riwayat; pertimbangkan tabel `user_mesin_riwayat` bila ingin melacak perubahan |
| 15 | Kolom `jumlah_wajah` di `user_mesin` tidak pernah diisi | Isi dari `St(21)` per user bila memungkinkan, atau hapus kolomnya di skema berikut |
| 16 | Status strip (`pnlStrip`) bertumpuk area tombol pada lebar minimum | Uji pada 1200×720 dan DPI 125/150%, rapikan `Anchor` |
| 17 | `KirimUser` masih memakai `ComboBox`, sedangkan dialog lain memakai `MesinPicker` | Samakan agar pencarian mesin konsisten |
| 18 | Tidak ada pemilih profil server (uji vs produksi) | Satu `UrlHris` saja; tambahkan profil bernama agar tidak salah kirim ke produksi (tercatat di 0.7.2 sebagai tertunda) |
| 19 | Tidak ada daftar "mesin belum terkirim" | Rencana 0.7.3 yang belum dikerjakan: ringkasan per mesin + tombol kirim semua yang belum |
| 20 | `pindai_jejak.txt` dan log bertumpuk tanpa rotasi | Tambah rotasi/berkas per bulan untuk `data\log` |

## 3. Yang sudah baik (jangan diubah tanpa alasan)

- Pemisahan tegas: data (`data\`), pustaka (`lib\`), hasil build (`bin\`),
  dan penolakan build bila data terdaftar di Git.
- `TemplateStore`: AES-256-CBC + HMAC-SHA256 terikat `mesin|id|jari`, dengan
  verifikasi baca-balik dan pembatalan seluruh transaksi bila satu gagal.
- `KelolaSalinan`: hash SHA-256 sebagai penjaga integritas sebelum kirim,
  tempat sampah 14 hari, konfirmasi bila ada salinan belum terkirim.
- `Peran`: pagar bertingkat dengan penolakan yang tercatat di `AuditLog`, dan
  aksi yang belum terdaftar otomatis butuh administrator (default aman).
- `Cek data` dan `DatabaseForm` tidak pernah menampilkan data pribadi pada
  mode ringkas.
- Konfirmasi berlapis untuk aksi merusak (hapus permanen, kosongkan sampah).

## 4. Urutan kerja yang disarankan

1. Butir 1 dan 2 (keamanan data + data hilang) — satu sesi kecil.
2. Butir 3 dan 7 (panduan + README) — dokumentasi, tanpa risiko kode.
3. Butir 4 dan 5 (sandi & batas login) — perlu keputusan Efendy soal kebijakan.
4. Butir 9 dan 10 (uji + kelanjutan kirim) — menaikkan kepercayaan sebelum
   dipakai di banyak PC.
5. Sisanya (6, 8, 11–20) sesuai kebutuhan.
