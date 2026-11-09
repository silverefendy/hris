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
