# Pustaka SQLite untuk HRIS Device Tool

| Hal | Isi |
|---|---|
| Paket | System.Data.SQLite.Core 1.0.109.0 (nuget.org) |
| Lisensi | Public domain |
| Mesin SQLite | 3.24.0 |
| Arsitektur | 32-bit (x86), sesuai /platform:x86 di build.ps1 |
| System.Data.SQLite.dll (.NET 4.0) | SHA256 EB000BED426FB19B0FA91B6AA45E30A4CCD487215835755BFF9E109A04C94852 |
| x86\SQLite.Interop.dll | SHA256 9E08D48E4D8BC18099B845246C61B54D3718CFB1870C9547E61C733C991DFB69 |

## Memperbarui
Jalankan `..\ambil_sqlite.ps1 -Versi <versi>` lalu jalankan uji di `..\uji_sqlite\jalankan.ps1`.
Cek versi terbaru di https://www.nuget.org/packages/System.Data.SQLite.Core

## Catatan
DLL native dicari di subfolder `x86\` di samping exe. Salin keduanya ke folder `bin` saat build.
