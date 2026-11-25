# Generator ID Finger dan Catatan Celah Data 4 Nov 2026

Status per Rabu, 25 Nov 2026, 10:55 WIB.

## 1. Generator ID Finger

### Tujuan

Memberi nomor ID Finger (`attendance_device_id` di HRIS Employee) yang tidak bentrok dengan ID yang sudah dipakai di mesin absensi.

### Aturan

- Nomor berikutnya = **angka terbesar + 1**.
- Angka terbesar dicari dari tiga sumber, lalu diambil yang paling besar:

| Sumber | Terbesar per 25 Nov 2026 (produksi) |
|---|---|
| Employee ERPNext | 12196 |
| HRIS Employee | 12196 |
| Raw Log mesin | 12266 |

- Hasil di produksi saat itu: **12267**.
- Raw Log ikut dihitung supaya ID yang sudah didaftarkan di mesin, tetapi belum menjadi karyawan, tidak dipakai ulang.

### Cara pakai (HRIS Employee)

1. Buka dokumen HRIS Employee yang kolom ID Finger-nya masih kosong.
2. Klik tombol **Buat ID Finger**.
3. Dialog menampilkan nomor usulan dan angka terbesar per sumber. Bila ada angka aneh (misalnya ID uji 99xxx), terlihat sebelum disetujui.
4. **Yes**: kolom terisi dan muncul pengingat "Daftarkan ID di mesin". **No**: kolom tetap kosong.
5. Tombol tidak tampil bila kolom ID Finger sudah terisi.

### Lokasi kode

- Fungsi: `hris.hris_employee_data.services.id_finger.ambil_id_berikutnya`
- Commit: `60d0f53` (25 Nov 2026)

### Verifikasi (hanya membaca)

```bash
cd ~/erp
bench --site erp.ciptamebel.co.id execute hris.hris_employee_data.services.id_finger.ambil_id_berikutnya
```

Keluaran memuat `berikutnya`, `terbesar`, dan rincian per sumber. Perintah ini tidak menyimpan apa pun.

### Hasil uji

| Uji | Hasil |
|---|---|
| Skrip (site uji) | 6 OK, 0 GAGAL |
| Browser B1 sampai B6 (site uji) | Lulus |

### Catatan operasional

- Jangan memakai nomor dari generator untuk karyawan baru **sebelum semua mesin selesai dikirim ke HRIS**. Selama Raw Log belum lengkap, angka terbesar bisa lebih kecil dari kenyataan di mesin.
- Folder kode dipakai bersama site uji dan produksi. Tombol baru tampil di produksi setelah `bench --site erp.ciptamebel.co.id clear-cache`. Jalankan setelah semua mesin terkirim.
- Generator hanya **mengusulkan** nomor. Pendaftaran ID di mesin tetap dilakukan manual.

## 2. Via Windows Agent pada Tujuh Mesin

Pada 25 Nov 2026 pukul 10:43 WIB, setelah backup database, kolom **Via Windows Agent** dicentang untuk tujuh mesin:
CML Cemara, CML Sena, CML Sizing, PLTB 220, CML Lapangan Kanan, CML Lapangan Kiri, CML Finishing.

CML Showroom dan WP 221 sudah tercentang sebelumnya. Kolom `last_agent_at` ketujuh mesin tersebut masih kosong, artinya belum ada kiriman dari Agent.

## 3. Celah Data 4 Nov 2026

### Fakta dari Raw Log (25 Nov 2026)

| Mesin | Pull pyzk berakhir | Data Agent mulai |
|---|---|---|
| Cemara, Sena, Sizing, PLTB 220, Kanan, Kiri, Finishing | 4 Nov sekitar 07:59 sampai 08:41 | Belum ada |
| Showroom | 4 Nov 08:18 | 4 Nov 17:00:02 |
| WP 221 | (tidak memakai Pull) | Punch pertama setelah 3 Nov 18:00 adalah 4 Nov 17:00:02 |

### Artinya

- Tujuh mesin belum punya data sejak 4 Nov pagi. Data itu **masih ada di mesin** (bila mesin tidak dibersihkan lagi) dan harus ditarik lewat Device Tool lalu dikirim ke HRIS.
- Jam pembersihan mesin pada 4 Nov **belum dikonfirmasi**. Hanya orang yang membersihkan yang tahu pastinya. Selisih antara akhir Pull dan jam pembersihan adalah data yang berpotensi tidak tercatat di mana pun.
- Dugaan (belum diperiksa): ada jeda beberapa jam pada 4 Nov antara akhir Pull dan awal data Agent.

### Temuan terkait ID

- Raw Log tanpa Employee: 957 baris, 53 ID berbeda.
- ID di atas 12196 yang belum menjadi Employee: 13 ID (12197 sampai 12266). Daftar ini perlu diserahkan ke HRD agar diinput dengan ID mesin yang sama.
- Pencocokan ulang (`check_rematch`) saat ini: bisa dicocokkan 0 baris, karena Employee-nya belum ada.

## 4. Langkah Berikutnya

| # | Pekerjaan |
|---|---|
| 1 | Kirim tujuh mesin lewat Device Tool, satu per satu, catat hasil `created`, `duplicate`, `error` |
| 2 | Jalankan ulang `cek_status_mesin.py`, bandingkan dengan angka di atas |
| 3 | Serahkan daftar ID tanpa Employee ke HRD |
| 4 | Pencocokan ulang Raw Log setelah karyawan terinput |
| 5 | `clear-cache` produksi agar tombol Buat ID Finger tampil |
| 6 | Pembersihan ID uji 99901 dan 99902 di site uji |

## 5. Belum Diketahui

- Jam pembersihan mesin pada 4 Nov.
- Apakah Kiri dan Finishing dapat dikirim dari PC rumah (belum ada di daftar Device Tool di PC tersebut).
