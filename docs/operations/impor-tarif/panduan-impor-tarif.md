# Panduan Impor Tarif TER dan Pasal 17

Diperbarui: 16 November 2026

Angka pada templat adalah **FIKTIF** (kategori `UJICSV`). Isi tarif sebenarnya hanya dari peraturan yang sudah diverifikasi HRD atau konsultan pajak. Kode HRIS tidak memuat angka pajak.

## 1. Konsep

Tarif TER dan Pasal 17 disimpan sebagai banyak baris. Baris dengan **Berlaku Sejak** yang sama membentuk satu set. Yang dipakai adalah set dengan tanggal terbaru yang tidak melewati tanggal acuan. Set lama tetap tersimpan untuk slip lama.

## 2. Kolom

| Kolom | TER | Pasal 17 | Isi |
|---|---|---|---|
| Kategori TER | ya | tidak ada | Contoh A, B, C. Otomatis huruf besar |
| Berlaku Sejak | ya | ya | Format `dd-mm-yyyy` (pengaturan sistem) |
| Aktif | ya | ya | 1 atau 0 |
| Bruto Dari | ya | ya | Angka polos, tanpa titik ribuan |
| Tanpa Batas Atas | ya | ya | 1 untuk baris terakhir, selain itu 0 |
| Bruto Sampai | bila bukan tanpa batas | sama | Kosongkan bila Tanpa Batas Atas = 1 |
| Tarif (%) | ya | ya | Persen, 0 sampai 100 |

## 3. Langkah

1. Buka **Data Import**, **New**. Pilih DocType `HRIS PPh21 TER Rate` atau `HRIS PPh21 Pasal17 Rate`, tipe **Insert New Records**.
2. Klik **Download Template** dan cocokkan header dengan templat di folder ini. **Templat unduhan Frappe yang berlaku bila berbeda.**
3. Isi, simpan sebagai CSV, lampirkan, lalu **Start Import**. Gunakan **Preview** lebih dulu.
4. Isi **Tarif TER lebih dulu**, baru pemetaan PTKP di Pengaturan PPh 21, karena kategori pemetaan harus ada di Tarif TER aktif.

## 4. Aturan yang ditegakkan

- Rentang tidak boleh beririsan dalam satu set (kategori dan tanggal sama).
- Hanya satu baris Tanpa Batas Atas per set.
- Tarif 0 sampai 100, Bruto Dari tidak negatif, Bruto Sampai tidak lebih kecil dari Bruto Dari.

## 5. Galat umum

| Gejala | Penyebab | Tindakan |
|---|---|---|
| Rentang bertumpang tindih | Dua baris beririsan | Perbaiki rentang |
| Kolom tidak dikenali | Header berbeda | Pakai templat unduhan Frappe |
| Tanggal salah | Format bukan dd-mm-yyyy | Ubah format tanggal |
| Desimal salah (1,5 jadi 15) | Format angka | Lihat hasil uji di bagian 6 |

## 6. Hasil uji format desimal

Diuji 16 November 2026 di `hris-uji.local` (Data Import, Insert New Records, 3 baris per DocType).

| Hal | Hasil |
|---|---|
| Header CSV | Cocok dengan templat unduhan Frappe |
| Tarif `1,5` | Tersimpan sebagai 1,5% (format Indonesia aman, tidak jadi 15) |
| Penomoran | TER `PTR-#####`, Pasal 17 `P17-YYMM-####` terbentuk saat impor |
| Impor ulang berkas yang sama | Ditolak per baris: rentang bertumpang tindih. Validasi berjalan lewat impor |
| Baris valid dan baris bentrok dalam satu berkas | Baris valid tetap masuk, baris bentrok gagal. Periksa **Import Log** |

Catatan:

- Hanya **System Manager** yang punya izin Import pada kedua DocType.
- Layar progres bisa macet di 0%. Muat ulang halaman, lalu cek status di daftar Data Import.
- Data uji (kategori `UJICSV`, tanggal 01-01-2030) sudah dihapus dari site uji.
