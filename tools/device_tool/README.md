# HRIS Device Tool

Aplikasi Windows (WinForms, C#) untuk mengelola mesin absensi berbasis ZKTeco (zkemkeeper) yang dipakai HRIS.
Status: tahap 2 (Info mesin, User, Sidik Jari, Bantuan). Fitur lain menyusul bertahap.

## Prasyarat PC
- Windows dengan .NET Framework 4 (bawaan Windows 10/11)
- Komponen `zkemkeeper.dll` (32-bit) terdaftar di PC. Cek lewat tab Bantuan > Diagnostik
- Jaringan ke mesin (LAN atau VPN), biasanya port 4370

## Build (tanpa Visual Studio)
Jalankan dari folder ini:

    powershell -ExecutionPolicy Bypass -File .\build.ps1

Hasil: `bin\HrisDeviceTool.exe`

## Portabel
Seluruh pengaturan ada di folder `data\` di samping exe. Untuk pindah PC, salin SELURUH folder (exe + data).
Comm Key hanya tersimpan bila dicentang "Ingat Comm Key", terenkripsi dengan kata sandi aplikasi.

## Keamanan
- Folder `data\` berisi alamat mesin, Comm Key terenkripsi, dan template sidik jari (data biometrik). JANGAN dimasukkan ke Git.
- `.gitignore` sudah mengecualikannya, dan `build.ps1` menolak build bila berkas data atau hasil build terdaftar di Git.

## Panduan
Folder `docs\` (panduan pengguna, pemulihan, developer) ditambahkan setelah tiap tahap teruji.
