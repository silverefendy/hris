# 0004: Pull pyzk, penamaan Raw Log, dan penjaga duplikat

Tanggal: 30 sampai 31 Oktober 2026
Status: Diterapkan (commit 057251c, 6e36db0, 00eba4d, 009ff78)
Keputusan terkait: K-57 sampai K-66 di [README](README.md). Melanjutkan [0003](0003-jalur-data-mesin.md).

## Konteks
Jalur Pull pyzk (`use_pull`) dibuat setelah jalur agen. Uji ke mesin `PLTB 220` (model MB460, firmware Ver 6.60 May 14 2018) menemukan beberapa fakta yang mengubah rancangan awal, terutama soal penamaan Raw Log dan cara mencegah duplikat.

Catatan: IP, port, password, dan nomor seri mesin sengaja tidak dicatat di dokumen.

## Keputusan
| No | Keputusan | Ringkas |
|---|---|---|
| K-57 | Penamaan Raw Log | `{mesin}-{ID pegawai}-{YYMMDD}-{NNNNN}`, contoh `PLTB_220-6887-261031-00001` |
| K-58 | `punch_key` | Penjaga duplikat utama, menggantikan nama dokumen (K-51) |
| K-59 | Nomor record mesin (`uid`) | Bukan bagian kunci; `device_record_no` ditunda |
| K-60 | Penanda `punch` mesin | Tidak andal; hanya disimpan |
| K-61 | Rentang tarikan | Otomatis atau `date_from`/`date_to` |
| K-62 | Verifikasi mesin | Serial dicocokkan sebelum menarik; tombol "Ambil Info dari Mesin" |
| K-63 | Cara menjalankan | Antrean `long` atau console; aman diulang |
| K-64 | Tarik sebelum Employee ada | Status "Tidak Cocok", dicocokkan nanti |
| K-65 | Log di mesin | Aplikasi tidak pernah menghapus |
| K-66 | Dependensi | `pyzk>=0.9` di `pyproject.toml` |

## Rincian

### K-57 dan K-58: penamaan dan penjaga duplikat
- Nama dokumen: `{mesin}-{ID pegawai}-{YYMMDD}-{NNNNN}`. Tanggal diambil dari **waktu punch**, bukan waktu tarikan. Nomor urut 5 digit berulang tiap bulan untuk kombinasi mesin + ID + bulan (counter `getseries` dengan kunci `mesin-ID-YYMM`). Counter tidak direset setelah data uji dihapus.
- Karena nomor urut bergantung pada urutan penyimpanan, **nama tidak bisa dipakai untuk mendeteksi duplikat**. Tugas itu dipegang field `punch_key` = `mesin|ID|waktu sampai detik`.
- `punch_key`: tersembunyi, unik di database (indeks unik terverifikasi, `Non_unique = 0`), hanya diisi saat dokumen baru, tidak berubah walau HRD mengoreksi waktu punch (K-25).
- Efek ke keputusan lama: K-51 (anti-duplikat lewat nama dokumen) diganti; keputusan K-48 "tanpa `unique_key`" tidak berlaku lagi untuk `punch_key`; pengecualian Raw Log di K-30 ("nama = kunci anti-duplikat") tidak lagi akurat.
- Kode: `services/raw_log_naming.py` (`make_punch_key`, `build_raw_log_name`); `autoname` di `hris_raw_log.py` memanggil `build_raw_log_name`. `services/punch_ingest.py` tidak diubah; docstring-nya masih menyebut nama dokumen sebagai penjaga duplikat (usang).

### K-59: mengapa `uid` tidak dipakai sebagai kunci
- `uid` adalah nomor record di mesin. Nilainya berputar 0 sampai 65535, sedangkan kapasitas jejak transaksi mesin 100.000, jadi nomor berulang sebelum mesin penuh.
- Bila mesin direset atau diganti, punch yang sama bisa mendapat nomor baru dan terbaca sebagai punch baru (masuk ganda).
- Kunci `mesin + ID + waktu` tidak bergantung pada firmware.
- Nomor record tersimpan di `raw_payload`. Field `device_record_no` (untuk laporan kelengkapan, misalnya "rentang nomor di mesin vs jumlah di server") **ditunda** pada 31 Okt 2026; menunda tidak menghilangkan data.
- Catatan verifikasi: hitungan dari rentang `uid` (25278 sampai 65535 lalu 0 sampai 1161) menghasilkan 41.420, sedangkan jumlah record dari pyzk 41.431. Selisih 11 belum dijelaskan. Tidak memengaruhi keputusan karena `uid` bukan kunci.

### K-60: penanda `punch`
- Atribut pyzk per record: `user_id`, `timestamp`, `status`, `punch`, `uid`. `status` selalu 1.
- `punch` (0 dan 1) terbagi hampir rata, tetapi satu orang tercatat 5 kali berturut-turut `punch=0` dalam 18 detik. Tidak bisa dijadikan penentu masuk atau pulang.
- Disimpan hanya di `punch_status_raw`, sejalan dengan K-23. Punch berulang (selang sekitar 2 detik) sangat sering dan disaring di working hour (K-24), bukan saat tarikan.

### K-61: rentang tarikan
- Tanpa tanggal: dari `last_pull_at` dikurangi 1 hari. Tarikan pertama: default 2026-10-01.
- `date_from` dan `date_to` boleh diisi. Tarikan ber-`date_to` **tidak** memajukan `last_pull_at`.
- Masa percobaan: tarikan dibatasi 25 sampai 31 Oktober 2026.
- `get_attendance()` pyzk tidak bisa memfilter tanggal; tiap tarikan membaca seluruh log mesin lalu disaring di aplikasi. Waktu baca penuh belum diukur; penyimpanan 2.306 baris selesai sekitar 6 detik.

### K-62 sampai K-66: lainnya
- Setiap `pull()` membandingkan serial mesin dengan serial di `HRIS Device` dan berhenti bila berbeda.
- Tombol "Ambil Info dari Mesin" (`hris_device.js`, `fetch_device_info`) mengisi serial, firmware, dan model ke form tanpa menyimpan. Device Type `PLTB 220` diganti dari "Solution" ke "ZKTeco"; `use_pull` dicentang.
- `enqueue_pull` memasukkan job ke antrean `long`; `pull()` bisa juga dijalankan dari console. Keduanya aman diulang karena `punch_key`.
- Punch ditarik walau Employee belum ada; statusnya "Tidak Cocok" dan dicocokkan lewat "Cocokkan Ulang" (sesi tersendiri, belum dibuat).
- `pyzk>=0.9` ditambahkan ke `pyproject.toml` (terpasang bersama `future` 1.0.0).

## Bukti uji
| Uji | Hasil |
|---|---|
| Tarikan sungguhan #1 | 54 baru |
| Tarikan sungguhan #2 | 0 baru, 54 sudah ada |
| Jalur agen (`save_punches`) dengan punch yang sama | created 0, duplicate 1, error 0 |
| Nama sesuai pola, `punch_key` terisi dan unik | 54 dari 54 |
| Dry-run 25 sampai 31 Okt | 2.306 punch, 66 user, serial cocok |
| Tarikan satu minggu lewat antrean | 2.306 baris dibuat 31 Okt 2026 09:02:26 sampai 09:02:32 |
| Tarikan ulang dari console | baru 0, sudah ada 2.306, gagal 0 |
| Pemeriksaan hasil | 7 tanggal terisi (293, 336, 354, 391, 370, 390, 172), sumber `Pull pyzk`, status `Tidak Cocok`, nama sesuai pola 2.306 dari 2.306, `punch_key` unik |

Catatan: tanggal 31 Okt (172 punch) belum penuh saat ditarik.

## Risiko dan hal yang belum diketahui
- Perilaku mesin saat jejak transaksi penuh (menimpa data lama atau menolak punch) belum diketahui; cek manual MB460. Perkiraan kasar: terpakai 41.431 dari 100.000, laju sekitar 330 per hari, penuh dalam 5 sampai 6 bulan.
- Aplikasi tidak menghapus log di mesin (K-65).
- Sementara waktu mesin sama dengan WIB (terverifikasi pada PLTB 220); mesin lain perlu dicek.
- Mesin `WP 221` (kelas masalah kode 6001, sama seperti X609-S) belum bisa ditarik lewat pyzk; diparkir.
- Penyebab pengecekan "0 baris" tepat setelah `enqueue_pull` belum terbukti (dugaan: dicek sebelum job selesai). Job terbukti berjalan oleh worker aktif.
