# Keputusan 4 November 2026 (K-100 sampai K-112)

Dasar: [payroll-rancangan.md](../business/payroll-rancangan.md). Kode pertama: HRIS Payroll Schedule (K-105).

| No | Keputusan | Tanggal | Status |
|---|---|---|---|
| K-100 | Satu karyawan punya satu jadwal gaji pada satu waktu; pergantian jadwal lewat tanggal berlaku, bukan dua jadwal aktif bersamaan | 2026-11-03 | Disetujui, belum dibuat |
| K-101 | `HRIS Employee` menjadi form utama untuk semua pekerjaan HRD. Employee ERPNext hanya cermin **satu arah** (HRIS ke ERPNext): dibuat dan diperbarui oleh HRIS, tidak diedit manual, dan perubahan langsung di ERPNext tidak kembali ke HRIS. Tautan lama (Raw Log, Working Hour, dan lainnya) tetap ke Employee ERPNext; HRIS Employee menyimpan tautan ke Employee ERPNext-nya. Gagal sinkron harus tampak jelas (penanda dan tombol coba lagi). Merevisi sebagian K-18 | 2026-11-04 | Disetujui, belum dibuat |
| K-102 | Migrasi sekali 1.077 Employee menjadi HRIS Employee. Hanya membaca data lama, dan **diuji dulu di site uji** sebelum produksi | 2026-11-04 | Disetujui, belum dibuat |
| K-103 | `Department` tetap master ERPNext (K-29) untuk sekarang. Ditinjau ulang setelah HRIS Employee stabil | 2026-11-04 | Ditunda |
| K-104 | Field HRIS Employee mencakup kelompok identitas, dokumen, kontak, kerja, keuangan, dan absensi, termasuk tanggal dan alasan resign, probation, serta akhir perjanjian kerja. Data sensitif (KTP, rekening, BPJS, golongan darah, foto) dibatasi hak aksesnya dan nomor KTP serta rekening dienkripsi. Rincian field menyusul di rancangan | 2026-11-04 | Disetujui, belum dibuat |
| K-105 | `HRIS Payroll Schedule` dengan empat jenis: Bulanan (satu tanggal cut-off, contoh 26), Mingguan (hari awal minggu bebas, periode 7 hari; contoh Kamis sampai Rabu dan Sabtu sampai Jumat), Harian per N hari (tanggal acuan dan N), dan Tanggal Tetap (daftar tanggal cut-off, contoh 14 dan 28, dapat diubah lewat form). Tanggal 14 dan 28 adalah akhir periode. Cut-off lebih besar dari hari dalam bulan memakai hari terakhir bulan. Banyak jadwal bertipe sama per company diizinkan. Layanan `get_period_for_date` di `hris_payroll/services/payroll_schedule.py` | 2026-11-04 | Diterapkan; teruji 34 pemeriksaan skrip (hasil 0 gagal). Uji browser dan penjaga terkunci/nonaktif (menunggu `HRIS Employee Pay` dan `HRIS Payroll Period`) belum terbukti |
| K-106 | Hari bayar = akhir periode + jeda hari (`pay_date_offset_days`). Bila jatuh hari Minggu dan aturan `Maju ke Senin`, hari bayar maju ke Senin. Yang bergeser hanya hari bayar; akhir periode tidak berubah | 2026-11-04 | Diterapkan; teruji skrip |
| K-107 | Hari Minggu pada karyawan harian dan mingguan tidak dihitung kecuali ada lembur; tidak kerja berarti tidak dihitung. Selaras K-33 dan K-38. Dasar rumus ada di K-95 sampai K-99 | 2026-11-04 | Disetujui; dipakai saat Payroll Slip dibuat |
| K-108 | Urutan pekerjaan: `HRIS Employee` dibuat sebelum `HRIS Employee Pay`, agar tautan payroll tidak perlu dipindah setelah banyak slip gaji. Dikerjakan bertahap: site uji, rancangan, DocType dan sinkron satu arah, migrasi, lalu Employee Pay. Menggantikan usulan awal (Employee Pay dulu) | 2026-11-04 | Disetujui |
| K-109 | Aturan `HRIS Employee Pay`: gaji naik = baris baru dengan tanggal berlaku, baris lama ditutup otomatis, riwayat tetap. Perubahan nominal wajib alasan. Pindah jenis gaji (misal harian ke bulanan) lewat baris baru. Tanggal berlaku mundur boleh selama periode terkait belum Final (ditegakkan setelah `HRIS Payroll Period` ada) | 2026-11-04 | Disetujui; belum dibuat |
| K-110 | Akses data gaji hanya untuk role khusus gaji; role lain, termasuk HR biasa, tidak punya akses. Dua role bertingkat: Payroll Admin (karyawan harian dan mingguan, tidak boleh melihat gaji bulanan) dan Payroll Manager (melihat semua). Sementara Kepala HRD memakai role Payroll Admin; diatur ulang kemudian | 2026-11-04 | Disetujui; penegakan per baris perlu diuji di site uji |
| K-111 | Slip gaji memiliki kolom Adjustment (koreksi). Alasan wajib diisi dan hanya Payroll Manager yang boleh mengisi. Divalidasi di server | 2026-11-04 | Disetujui; dibuat bersama `HRIS Payroll Slip` |
| K-112 | Field `HRIS Employee` mengikuti profil aplikasi lama (identitas, kontak, kerja, bank, BPJS, status, foto). KTP dan rekening boleh dilihat role HRD dan payroll, role lain tidak. Foto disimpan. Nominal gaji tidak disimpan di `HRIS Employee`, hanya di `HRIS Employee Pay`. Melengkapi K-104; mekanisme enkripsi menunggu uji di site uji | 2026-11-04 | Disetujui; rincian field di sesi rancangan |

## Belum diputuskan
- Rancangan rinci HRIS Employee (field, hak akses, enkripsi, sinkron).
- Rancangan rinci HRIS Payroll Schedule dan HRIS Employee Pay.
- Cuti dan izin selain sakit.
