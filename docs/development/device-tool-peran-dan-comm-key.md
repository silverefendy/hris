# HRIS Device Tool: Catatan Tahap 3d sampai 0.6.2

Diperbarui: Selasa, 24 Nov 2026, 06:00 WIB
Lokasi kode: `tools/device_tool` (repo `silverefendy/hris`)
Kompilasi: `build.ps1` (csc .NET 4, C# 5, x86)

## 1. Riwayat Commit

| Commit | Versi | Isi |
|---|---|---|
| `2c8af74` | 0.5.1 (3d) | Catatan aktivitas per menu, Kelola salinan, sampah 14 hari |
| `2b907bb` | 0.6.0 (4a) | Peran dan login lima tingkat, Ganti sandi, pagar tombol |
| `4a836a9` | 0.6.0 | Peran ditambahkan ke format `Log()` di MainForm |
| `ef4b7e2` | 0.6.1 | Tombol Keluar akun, `Main` berulang |
| `d6cd56b` | 0.6.2 | Comm Key dienkripsi DPAPI, tanpa sandi aplikasi, migrasi berkas lama |

## 2. Peran dan Login (Tahap 4a)

Lima akun tetap. Nama akun sama dengan nama peran. Izin bersifat kumulatif.

| Peran | Level | Izin tambahan |
|---|---|---|
| user | 1 | Info, Pindai, Ringkas, Ekspor, Cek user, Daftar user, Bandingkan, Tarik log, Kelola salinan (ke sampah, pulihkan), Diagnostik, Panduan, Cek semua |
| supervisor | 2 | Tambah user uji, Picu, Selesai, Baca template |
| manager | 3 | Hapus permanen salinan, kosongkan sampah |
| direksi | 4 | Disiapkan untuk hapus user/log mesin (tahap 2f) |
| administrator | 5 | Tambah, Ubah, Hapus, Urut, Geser mesin; ganti sandi peran mana pun |

- Aksi yang belum terdaftar di `Peran.cs` otomatis butuh administrator.
- Sandi disimpan sebagai hash PBKDF2 (20000 iterasi) + salt di `data\pengguna.hdtusr`.
- Sandi bawaan: `<peran>123`. **Ganti sebelum dipakai orang lain.**
- Ganti sandi: peran biasa mengganti sandinya sendiri (wajib sandi lama); administrator dapat mengganti sandi peran mana pun. Minimal 4 karakter.
- Salah sandi: jeda 800 ms. Login, logout, dan penolakan aksi dicatat di `data\log\sistem\`.

### Keluar akun (0.6.1)

Tombol **Keluar akun** menutup jendela utama dan menampilkan dialog Masuk lagi. Tombol X menutup aplikasi. `Peran.Level` direset ke 0.

### Batas keamanan (jujur)

Ini pagar pengaman, bukan keamanan penuh.
- Menghapus `pengguna.hdtusr` mengembalikan sandi ke bawaan.
- Tombol **Buka folder data** dan **Bersihkan log** tidak dipagari.
- Repo harus private karena sandi bawaan ada di kode sumber.

## 3. Comm Key Tanpa Sandi Aplikasi (0.6.2)

| Hal | Isi |
|---|---|
| Enkripsi | DPAPI Windows (`CryptProtectData`), terikat akun Windows di PC ini |
| Berkas | `data\rahasia.hdtsec`, diawali penanda `HDT2` |
| Implementasi | `Dpapi.cs` memanggil `crypt32.dll` langsung (tanpa referensi `System.Security.dll`) |
| Per PC | Comm Key diisi sekali per PC, lalu diingat. Di PC lain diisi sekali lagi |
| Migrasi berkas lama (bersandi) | Sandi lama diminta sekali, isi dipindah ke DPAPI, salinan lama ke `data\cadangan\rahasia_sebelum_migrasi_*.hdtbak` |
| Lupa sandi lama | Berkas lama dicadangkan, Comm Key diisi ulang sekali |
| Berkas dari PC/akun lain | Dicadangkan (`rahasia_pc_lain_*.hdtbak`), Comm Key ditanyakan lagi |

Catatan: DPAPI melindungi dari penyalinan berkas ke PC atau akun lain. DPAPI tidak melindungi dari orang yang sedang login di akun Windows yang sama. Itu dibatasi pagar peran. Profil Windows yang dibuat ulang membuat berkas tidak terbaca (ditangani seperti kasus PC lain).

`Crypto.cs` masih dipakai hanya untuk membuka berkas format lama saat migrasi. Boleh dihapus setelah semua PC termigrasi.

## 4. Hasil Uji

| Fitur | Hasil |
|---|---|
| 3d Kelola salinan (uji 1-7) | Lulus |
| 4a Peran, login, ganti sandi (uji 1-9) | Lulus |
| 0.6.1 Keluar akun (uji 1-6) | Lulus |
| 0.6.2 Comm Key DPAPI (uji 1-6), berkas berawalan `HDT2` | Lulus |

## 5. Masalah Dikenal dan Catatan

| Hal | Keterangan |
|---|---|
| Akhir baris | `.gitignore`, `README.md`, `build.ps1`, `Crypto.cs` hanya beda LF/CRLF di PC rumah. Jangan di-add. Keputusan `.gitattributes` menunggu persetujuan |
| Build gagal `CS0016` | Exe masih terbuka. Tutup aplikasi sebelum build |
| Patch skrip PowerShell | Pakai jangkar satu baris, bungkus `if/else` dalam `& { ... }` |
| Dua PC | Jalankan skrip patch di satu PC saja, commit dan push dari situ, di PC lain `git pull` |

## 6. Langkah Berikutnya

1. Pemilih mesin bertabel (kolom No/Nama/IP/Port/Key, kotak cari, klik ganda) untuk Tarik log dan Bandingkan.
2. Impor CSV dan kirim log ke HRIS (perlu baca `punch_ingest.py`, Raw Log, `agent-api.md`; keputusan token).
3. Generator ID 5 digit lintas mesin dan aturan distribusi per department (menunggu jawaban pertanyaan terbuka 1 dan 2).
4. Tahap 2e/2f (ubah privilege, hapus user/log), sinkron jam, restart.
