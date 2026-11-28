# HRIS Device Tool — Tahap A (versi 0.9.0)

Disusun: 28 November 2026. Diperbarui: 28 November 2026, 07:10 WIB.

Status: **kode di-push (commit `3543649`, 06:45 WIB); uji baru sebagian dilaporkan**.

## 1. Tujuan
Merapikan susunan menu dan menampilkan karyawan dari semua mesin dalam satu daftar.

Contoh: satu ID yang terdaftar di beberapa mesin tampil sebagai satu baris, dengan rincian tiap mesin di bawahnya.

## 2. Isi

| Bagian | Keterangan |
|---|---|
| Tab utama | Karyawan, Log absensi, Mesin, Pengaturan, Bantuan |
| Karyawan | Satu baris per ID, cari, saringan, urut kolom, rincian per mesin, ekspor CSV |
| Saringan | Semua, Nama berbeda, Tanpa sidik jari, Hanya 1 mesin |
| Ambil user / sidik jari | Mesin dipilih dengan centang |
| Mesin | Daftar mesin, Ringkasan semua, Info mesin, User di mesin, Sidik jari |
| Pengaturan | Umum, Koneksi HRIS, Database & cadangan, Akun & kata sandi |
| Catatan aktivitas | Bisa dibuka dan ditutup |

Layar Karyawan hanya membaca database lokal. Tahap ini tidak mengubah skema database dan tidak menambah penulisan ke mesin.

## 3. Arti tampilan

| Tampilan | Arti |
|---|---|
| `?` pada Sidik jari | Template mesin tersebut belum diambil |
| `0` pada Sidik jari | Semua mesin tempat ID berada sudah dibaca dan tidak ada jari |
| Sorotan oranye | Nama berbeda antar mesin |
| Departemen kosong | Tidak ada data departemen untuk ID itu di database lokal |

Huruf besar/kecil dan spasi ganda tidak dianggap beda nama.

## 4. Hak akses
- Cek database: manager ke atas.
- Ekspor karyawan: manager ke atas.
- Koneksi HRIS: masih administrator. Usulan "manager ke atas" menunggu konfirmasi karena melonggarkan aturan lama.

## 5. Berkas (`tools/device_tool`)

| Berkas | Perubahan |
|---|---|
| `src/MainForm.cs` | Susunan menu baru |
| `src/Peran.cs` | Hak akses |
| `src/Karyawan.cs` | Baru: penggabungan data per ID |
| `src/KaryawanPanel.cs` | Baru: layar Karyawan |
| `src/PilihBanyakMesin.cs` | Baru: dialog pilih mesin |
| `uji_sqlite/UjiKaryawan.cs` | Baru: uji K0–K13 (data fiktif) |
| `uji_sqlite/jalankan_karyawan.ps1` | Baru: menjalankan uji |

## 6. Menjalankan

Dari folder utama repo, di PowerShell:

```powershell
git pull
powershell -ExecutionPolicy Bypass -File tools\device_tool\uji_sqlite\jalankan_karyawan.ps1
powershell -ExecutionPolicy Bypass -File tools\device_tool\build.ps1
.\tools\device_tool\bin\HrisDeviceTool.exe
```

## 7. Hasil pemeriksaan

| Pemeriksaan | Hasil |
|---|---|
| Kompilasi Mono (C# 5, x86) | Berhasil |
| Uji K0–K13 dengan Mono SQLite | Lulus |
| Aplikasi berjalan di Windows | Ya |
| Ambil user dari mesin yang terdaftar di PC uji | Berhasil (satu mesin pada percobaan kedua) |
| Daftar gabungan, rincian per mesin, sorotan nama berbeda | Tampil |
| Tab Mesin dan Pengaturan > Umum | Tampil |

### Belum dilaporkan
- Skrip uji karyawan di Windows.
- Ambil sidik jari.
- Cari, saringan, urut kolom, ekspor CSV.
- Sub-tab Info mesin, User di mesin, Sidik jari.
- Tarik log dan Kelola salinan.
- Pembatasan untuk role `user`.

## 8. Langkah berikutnya
Urutan tahap: B (log ke database dan jumlah tap), F (shift dari HRIS dan laporan), E1 (karyawan baru dan sinkron), C (jari per orang), E2 (daftar ke mesin), D (salin jari), G (foto/wajah).
