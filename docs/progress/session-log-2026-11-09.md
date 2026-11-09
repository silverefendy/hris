# Catatan Sesi 9 November 2026

## Selesai
| Item | Hasil |
|---|---|
| `HRIS Payroll Period` (K-128) | Dibuat dan teruji di `hris-uji.local`: 9c0648a (Period, 7 Nov), 0ebc487 (aturan campuran, dialog bertautan, notifikasi in-app), 913268f (izin write Employee Pay, read Payroll Schedule untuk Manager, Jenis Gaji Admin dibatasi Harian, dialog kesiapan tampil semua dengan nama) |
| Hak akses Jadwal Gaji (K-129) | Payroll Manager boleh baca, tulis, buat Jadwal Gaji, tanpa hapus; hapus hanya System Manager (4807cba). Keterangan Jenis Gaji tidak lagi tertinggal di baris tersimpan |
| Uji skrip | Kesiapan OK 18 (K1 sampai K16), Period OK 28, regresi Working Hour OK 4, Employee Pay OK 30/4/5, GAGAL 0 |
| Uji browser per peran | Lulus: Payroll Admin (hanya Harian, R4b), Payroll Manager murni (form lengkap, pilih jadwal, buat dan ubah Jadwal Gaji tanpa Hapus), Administrator (dialog kesiapan, nama bisa diklik, Buat Baris Gaji mengisi Karyawan), Tinjau dan Kembalikan ke Draft dengan notifikasi, penolakan Final dengan pesan Tindakan dan Berwenang |
| Pembersihan data uji | Dua periode, empat baris gaji, tiga jadwal uji, notifikasi, dan dua user uji dihapus di `hris-uji.local` (cadangan diambil sebelumnya). Dua baris gaji yang bukan dibuat dalam sesi ini dikonfirmasi Efendy sebagai data uji |
| Push | 913268f dan 4807cba oleh Efendy; dokumen keputusan [keputusan-2026-11-09.md](../decisions/keputusan-2026-11-09.md) |

## Temuan dan pelajaran
- Uji skrip yang hanya memeriksa izin `create` meloloskan form kosong untuk Manager dan Admin (izin `write` kurang). Uji browser per peran wajib sebelum produksi.
- `bench console` tidak andal untuk skrip multibaris; pakai Python non-interaktif dari folder `sites`.
- `reload_doc` dengan reset izin memuat izin dari JSON, sehingga perubahan izin di site uji tidak memerlukan `migrate`.
- Kesimpulan awal bahwa tombol Buat Baris Gaji tidak mengisi Karyawan keliru; penyebabnya form dibuka lewat Tambah biasa.
- Jenis Gaji yang ditolak untuk Payroll Admin muncul sebagai pesan izin Frappe yang umum; diatasi dengan membatasi pilihan di form (server tetap menolak).

## Tertunda
| Item | Catatan |
|---|---|
| Siapa HRIS Payroll Manager | Belum diputuskan (K-110: Kepala HRD sementara memakai Payroll Admin); menentukan siapa yang boleh memfinalkan |
| Migrasi produksi K-102 | Menunggu jadwal; ikut membuat tabel `HRIS Employee Pay` dan `HRIS Payroll Period`. Izin Payroll Schedule baru perlu diverifikasi hasilnya di produksi |
| Kombinasi Jenis Gaji dan tipe jadwal | Belum diperiksa apakah sistem menolak kombinasi yang tidak cocok |
| Indeks `decisions/README.md` | Belum memuat K-127 sampai K-129 (berkas besar; rapikan terpisah) |
| Uji dengan akun peran asli di produksi | Setelah migrasi produksi |

## Langkah berikutnya
1. Satu fitur per sesi, dimulai dari diskusi rancangan: `HRIS Payroll Slip`, `Department Rule` (P8), lalu BPJS dan PPh 21.
2. Migrasi produksi K-102 sesuai checklist.
3. Keputusan siapa HRIS Payroll Manager.

---

# Tambahan: HRIS Payroll Slip (sesi malam, sampai 22:50 WIB)

## Selesai
| Item | Hasil |
|---|---|
| `HRIS Payroll Slip` (K-130) | Kode di `2f483dc`; perbaikan tampilan dan penomoran di `b11d89c` |
| Uji skrip | `uji_payroll_slip.py`: OK 77, GAGAL 0 (sebelumnya 72; ditambah cek nomor baris, urutan komponen, dan kolom Alasan) |
| Uji browser (hris-uji.local, Administrator) | Lulus: Buat Slip dan Buat Slip kedua kali (memperbarui, tidak menggandakan); Gaji Pokok 3.000.000 dan tarif per jam 61.855,67 (3.000.000 / 48,50 jam); kolom otomatis tidak bisa diedit; komponen Manual tanpa alasan ditolak; komponen Manual menambah Gaji Bersih dan tetap ada setelah Hitung Ulang; Tinjau dan Kembalikan ke Draft; Periode yang punya slip tidak bisa dihapus; slip Ditinjau tidak bisa diubah |
| Uji potongan absen | 1 hari diklasifikasi Mangkir menghasilkan Potongan Absen Rp 500.000 (3.000.000 / 6 hari kerja x 1 hari); diubah ke Sakit dengan surat dokter, potongan hilang; hari Tidak Hadir yang belum diklasifikasi tidak dipotong dan dicatat di Catatan Perhitungan |
| Audit Trail | Perubahan komponen dan total tercatat dengan waktu (WIB), pengguna, nilai lama dan baru |

## Temuan dan perbaikan
- Kolom Alasan tidak tampil di tabel Komponen. Perbaikan: `in_list_view` pada field `reason` dan `modified` JSON dinaikkan, karena `migrate` mengabaikan perubahan JSON bila `modified` tidak lebih baru.
- Nomor baris ganda setelah Hitung Ulang (baris Manual mempertahankan nomor lama). Perbaikan: urutkan Otomatis dulu, lalu nomori ulang 1..n sebelum simpan.

## Perilaku yang disengaja
- Menu Buat Slip hanya aktif saat Periode berstatus Draft.
- Finalkan Periode ditolak selama ada karyawan Hadir tanpa baris gaji (aturan kesiapan K-128 berlaku global). Di site uji ditemukan 285 karyawan; tidak dipaksa lolos.

## Tertunda
| Item | Catatan |
|---|---|
| Catatan Audit Hitung Ulang | Mencatat "baris dihapus lalu ditambah" untuk komponen yang nilainya sama; hanya bising, prioritas rendah |
| Pembersihan data uji slip | Skrip `p15` (mode COBA, lalu `--terapkan`); klasifikasi absen Working Hour uji dibiarkan |
| Indeks `decisions/README.md` | Belum memuat K-127 sampai K-129; rapikan terpisah |
| Pembuatan slip massal, per kelompok, dan per departemen | Rancangan disetujui (K-130), implementasi menyusul |
| BPJS dan PPh 21, Department Rule (P8) | Fitur berikutnya, mulai dari diskusi rancangan |
