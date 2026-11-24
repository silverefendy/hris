# Device Tool 0.7.2: Menu Dirapikan dan Temuan Data Mesin

Tanggal: 24 Nov 2026. Commit: `d6f7194`. Melengkapi `device-tool-0.7.0-kirim-log.md`.

## 1. Perubahan 0.7.2

| Perubahan | Berkas |
|---|---|
| Tab baru **Log absensi** (tab pertama): Tarik log mesin, Kelola salinan, alur kirim, ringkasan "Salinan aktif / Belum terkirim" | `MainForm.cs` |
| Cek semua dan Bandingkan 2 mesin pindah ke tab **Semua mesin** | `MainForm.cs` |
| Kiri berisi daftar mesin dan dua baris tiga tombol berlebar sama | `MainForm.cs` |
| Baris status: "Masuk sebagai", Ganti sandi, Keluar akun, Bersihkan log | `MainForm.cs` |
| Judul dialog Ubah mesin menampilkan nama lama | `Dialogs.cs` |
| Berkas `.hdterr` ikut dipindah ke sampah, dipulihkan, dan dihapus bersama pasangannya | `KelolaSalinan.cs` |

Fungsi tombol dan pagar peran tidak berubah.

## 2. Status Uji

| Uji | Status |
|---|---|
| Judul jendela dan tata letak | Terverifikasi dari screenshot |
| Ringkasan "Salinan aktif: 3, Belum terkirim: 1" | Terverifikasi dari screenshot |
| Uji 3-8 (hapus/pulihkan ringkasan, tab Semua mesin, baris status, maksimalkan, judul Ubah, Bantuan) | Belum dilaporkan satu per satu |
| `.hdterr` ikut sampah | Hanya terverifikasi kompilasi (belum ada berkas `.hdterr`) |

## 3. Temuan Data Mesin (HRIS Pull Run, hris-uji.local)

| Mesin | Pull 4 Nov (baru) | Hapus Raw Log 19 Nov |
|---|---|---|
| CML Lapangan Kiri | 8.914 | Ya (1 Agu - 19 Nov) |
| CML Lapangan Kanan | 4.506 | Ya (1 Jul - 19 Nov) |
| CML Finishing | 5.489 | Ya (1 Agu - 19 Nov) |
| CML Sizing | 1.800 | Ya (1 Agu - 19 Nov) |
| CML Cemara | 1.857 (lalu 803 pada 19 Nov) | Tidak |
| CML Sena | 1.202 | Tidak |
| CML Showroom | 726 (lalu 331 pada 19 Nov) | Tidak |

- Raw Log Kiri, Kanan, Finishing, dan Sizing kosong karena **dihapus pada 19 Nov**, bukan karena Pull gagal atau mesin kosong.
- Jumlah baris yang terhapus belum dibaca (kolom `jumlah_dihapus`).
- Salinan Device Tool semua mesin tampak mulai 4 Nov, berbeda dari data Pull 4 Nov yang lebih lama. Penyebab belum terbukti. Periksa `Rentang data` di Kelola salinan.
- Pull menyimpan `last_pull_at` meski 0 punch. Mesin kosong tetap tampak "pernah ditarik".

## 4. Galat Terulang (19-21 Nov)

`HRIS Hapus WH gagal` dan `HRIS Payroll Period: notifikasi gagal` berasal dari uji otomatis (traceback melewati `uji_period_kesiapan.py`), bukan galat pemakai.

## 5. Status Produksi

K-102 sudah ada di `erp.ciptamebel.co.id`: HRIS Employee 1.078 baris, HRIS Device 9, DocType HRIS Pull Run ada. Syarat uji produksi yang tersisa: device bernama sama dan Via Windows Agent tercentang, token produksi, URL dan token di Pengaturan HRIS, Tes koneksi, mulai dari satu mesin kecil.

## 6. Tertunda

Tarik ulang CSV Kanan, Via Windows Agent di Cemara/Sena/PLTB/Sizing/Finishing/Kanan, ganti sandi bawaan peran, putusan `.gitattributes`, profil server uji/produksi, daftar mesin belum terkirim (0.7.3), konfirmasi penghapusan Raw Log 19 Nov.
