# C4 tahap 5: mesin hitung jam koreksi dan tampilan form

Status: selesai di hris-uji.local, commit 7cd4ffb (21 Nov 2026). Migrate produksi belum.

## Perilaku

| Hal | Aturan |
|---|---|
| Hari berjam koreksi | Dihitung Hadir, tinjauan tetap Sudah Ditinjau, lembur tidak pernah dari jam koreksi |
| Punch asli muncul belakangan (opsi A) | Hari dihitung dari punch asli, jam koreksi diabaikan tetapi tersimpan, alasan "Jam koreksi diabaikan" |
| Jam masuk koreksi saja | Tidak menghapus potongan pulang awal bila punch pulang asli memang cepat; isi juga jam pulang koreksi bila perlu |
| Kosongkan jam koreksi | Setelah Hitung Ulang hari kembali Tidak Lengkap dan Menunggu |
| Audit Trail | Setiap perubahan jam, status, dan hasil hitung tercatat (sumber: Version, track_changes) |

## Perubahan

- `services/working_hour.py`: memanggil `hitung_dengan_koreksi`; `tahan_tinjauan` menjaga Sudah Ditinjau.
- `hris_working_hour.js`: blok C4 ditambahkan di akhir. Nama hari di bawah Tanggal Kerja. Hitung Ulang otomatis setelah Simpan bila jam koreksi berubah.
- `hris_working_hour.json`: section baru "Koreksi Hari Tidak Lengkap" (Hasil Tinjauan Tidak Lengkap, Jam Masuk, Jam Pulang Koreksi). Tidak ada field data diganti nama atau tipe.

## Bukti uji

uji_jam_koreksi 22/22, _db 10/10, _mesin 10/10, _u7 8/8. Regresi 21 Nov: SAMA 78, BEDA 0, ERROR 0, BARU 4.

## Pelajaran operasional

1. Perintah pemulihan (`cp ... .bak`) jangan ditulis sebagai satu baris siap tempel; ia menimpa penambal yang sudah terpasang.
2. Mode CEK tidak menulis apa pun; pastikan argumen TERAPKAN benar-benar dijalankan.
3. Heredoc dengan indentasi Tab memicu autocomplete saat ditempel ke terminal; gunakan spasi pada skrip penempel.
4. Hari berjam koreksi baru berubah setelah Hitung Ulang; JS otomatis menutup celah lupa menekan tombol.

## Tertunda

- Aturan: tolak jam koreksi bila Klasifikasi Absen terisi.
- Migrate produksi C4 (persetujuan eksplisit) dan restart.
- Serial Number HRIS Device "WP 221" dikembalikan dari 123abcd.
