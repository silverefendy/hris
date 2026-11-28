# Rangkuman: `tools/device_tool` (aplikasi C# WinForms)

Diperiksa: 27 November 2026. Versi di kode: **0.8.0**
(`MainForm.cs` → `const string Versi = "0.8.0 (info mesin, template)"`).
Total ±6.760 baris C# + 4 skrip PowerShell + ±800 baris uji konsol.

Aplikasi portable: exe + folder `data\` di sampingnya. Kompilasi memakai
`csc.exe` .NET Framework 4, `/platform:x86` (wajib karena `zkemkeeper` 32-bit).

## Berkas sumber (`src/`, 23 berkas)

| Berkas | Baris | Isi |
|---|---|---|
| `Program.cs` | 44 | Titik masuk, loop login → form utama → keluar akun |
| `MainForm.cs` | 1.380 | Jendela utama: daftar mesin, 6 tab (Log absensi, Info mesin, Semua mesin, User, Sidik jari, Bantuan), pengurut kolom, salin tempel, `HandPanel` gambar tangan untuk memilih jari |
| `Settings.cs` | 225 | `MesinItem` (nama, IP, port, `IngatKey`, `TanpaKey`, `NamaDiHris`, `NamaLama`), penyimpanan XML `mesin.hdtdata`, Comm Key DPAPI `rahasia.hdtsec`, migrasi dari format bersandi lama |
| `Crypto.cs` | 64 | AES-256-CBC + PBKDF2 (20.000 iterasi), awalan `HDT1|` — dipakai `Brankas` dan format lama |
| `Dpapi.cs` | 116 | Enkripsi Windows (`CryptProtectData`), awalan `HDT2` |
| `Brankas.cs` | 119 | Kunci template 64 byte dibungkus kata sandi login tiap peran (level ≥ 3) |
| `TemplateStore.cs` | 194 | Template jari: AES-256-CBC + HMAC-SHA256 terikat `mesin|id|jari`, verifikasi baca-balik, tabel `kunci_template` |
| `Db.cs` | 257 | Skema SQLite v1–v3 (13 tabel + view `v_karyawan_lokal`), migrasi bertahap, cadangan `BackupDatabase` |
| `SnapshotUser.cs` | 93 | Snapshot user mesin → `user_mesin` (hapus lalu isi ulang per mesin) |
| `InfoMesin.cs` | 72 | Peta 16 field info mesin → tabel `mesin` |
| `Dev.cs` | 394 | Semua panggilan `zkemkeeper`: koneksi, info, user, kartu, template, `StartEnrollEx` |
| `LogTarik.cs` | 405 | `BacaLog`: baca seluruh log mesin (maks 2 juta), filter tanggal/cari, ekspor CSV + manifest |
| `KelolaSalinan.cs` | 616 | Salinan tarikan: daftar aktif, tempat sampah 14 hari, hash SHA-256, kirim ke HRIS, tandai terkirim |
| `KirimHris.cs` | 437 | Kirim punch ke `push_punches`: batch ≤500, urut waktu, parsing balasan, berkas `.hdterr`, dialog progres |
| `KirimUser.cs` | 295 | Kirim snapshot user ke `push_device_users` (template tidak dikirim) |
| `Bandingkan.cs` | 469 | Bandingkan dua mesin: user, privilege, hash template per jari |
| `ImporLama.cs` | 353 | Impor CSV aplikasi absensi lama: deteksi penyandian/pemisah, sinonim judul kolom, `pemetaan_impor.txt` |
| `Peran.cs` | 250 | 5 peran (user…administrator), hash PBKDF2 `pengguna.hdtusr`, login, ganti sandi |
| `Dialogs.cs` | 238 | `Dlg.Prompt` dan `MesinDialog` (tambah/ubah mesin + tes koneksi) |
| `PengaturanHris.cs` | 240 | URL HRIS + token 48 karakter (`hris_`), DPAPI, tes koneksi, hapus token |
| `DatabaseForm.cs` | 225 | Penampil database read-only: cari, sembunyikan kolom kosong, ekspor CSV |
| `PemilihMesin.cs` | 192 | `PilihMesinForm` + `MesinPicker` (pengganti ComboBox) |
| `AlatBantu.cs` | 81 | `AuditLog` per kategori + `PilihMesin.Gaya` |

## Skrip PowerShell

| Berkas | Isi |
|---|---|
| `build.ps1` | Kompilasi dengan `csc.exe` x86, menolak build bila `data/`, `bin/`, `*.exe` terdaftar di Git, menyalin pustaka SQLite |
| `ambil_sqlite.ps1` | Unduh System.Data.SQLite.Core dari NuGet (atau pakai `.nupkg` lokal) ke `lib/` |
| `cek_data.ps1` | Cek isi `hdt.sqlite` tanpa menampilkan data pribadi; relaunch ke PowerShell 32-bit |
| `uji_sqlite/jalankan*.ps1` (5 berkas) | Penjalan uji konsol (`UjiDb`, `UjiDbV2`, `UjiImpor`, `UjiSnapshot`, `UjiSqlite`) |

## Uji (`uji_sqlite/`)

| Berkas | Baris | Cakupan |
|---|---|---|
| `UjiSqlite.cs` | 266 | Skema v1, cadangan |
| `UjiDb.cs` | 148 | Buka/migrasi dasar |
| `UjiDbV2.cs` | 142 | Migrasi v2, view gabungan |
| `UjiImpor.cs` | 143 | Impor CSV aplikasi lama |
| `UjiSnapshot.cs` | 107 | Snapshot user |
| `analisa_selisih.ps1` | 53 | Analisa selisih data (baca saja) |

**Tidak ada uji otomatis untuk `KirimHris`, `BacaCsv`, `Salinan`, `Brankas`,
dan `Peran`.** Semua uji yang ada menyentuh lapisan database, bukan jaringan
atau kriptografi alur.

## Berkas data (tidak masuk Git)

`bin/data/` berisi `mesin.hdtdata`, `rahasia.hdtsec`, `hris.hdtsec`,
`pengguna.hdtusr`, `db/hdt.sqlite`, `cadangan/tmpl_*.hdttmpl`, `tarikan/*.csv`,
`log/*.hdtlog`, `pindai_jejak.txt`. `.gitignore` sudah mengecualikan `data/`,
`bin/`, `*.hdt*`, `*.exe`, `*.dll`.

## Catatan versi

- `git status` menandai `.gitignore`, `README.md`, `src/Crypto.cs` sebagai
  modified, tetapi `git diff` kosong → hanya perbedaan akhir baris (LF/CRLF).
- `README.md` masih menulis "Status: tahap 2" dan "Comm Key ... kata sandi
  aplikasi", keduanya tidak lagi benar.
- `README.md` menjanjikan folder `docs\` panduan; folder itu belum ada.
