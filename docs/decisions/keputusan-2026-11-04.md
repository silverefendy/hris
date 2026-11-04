# Keputusan 4 November 2026 (K-100 sampai K-104)

Dasar: [payroll-rancangan.md](../business/payroll-rancangan.md). Belum ada kode.

| No | Keputusan | Tanggal | Status |
|---|---|---|---|
| K-100 | Satu karyawan punya satu jadwal gaji pada satu waktu; pergantian jadwal lewat tanggal berlaku, bukan dua jadwal aktif bersamaan | 2026-11-03 | Disetujui, belum dibuat |
| K-101 | `HRIS Employee` menjadi form utama untuk semua pekerjaan HRD. Employee ERPNext hanya cermin **satu arah** (HRIS ke ERPNext): dibuat dan diperbarui oleh HRIS, tidak diedit manual, dan perubahan langsung di ERPNext tidak kembali ke HRIS. Tautan lama (Raw Log, Working Hour, dan lainnya) tetap ke Employee ERPNext; HRIS Employee menyimpan tautan ke Employee ERPNext-nya. Gagal sinkron harus tampak jelas (penanda dan tombol coba lagi). Merevisi sebagian K-18 | 2026-11-04 | Disetujui, belum dibuat |
| K-102 | Migrasi sekali 1.077 Employee menjadi HRIS Employee. Hanya membaca data lama, dan **diuji dulu di site uji** sebelum produksi | 2026-11-04 | Disetujui, belum dibuat |
| K-103 | `Department` tetap master ERPNext (K-29) untuk sekarang. Ditinjau ulang setelah HRIS Employee stabil | 2026-11-04 | Ditunda |
| K-104 | Field HRIS Employee mencakup kelompok identitas, dokumen, kontak, kerja, keuangan, dan absensi, termasuk tanggal dan alasan resign, probation, serta akhir perjanjian kerja. Data sensitif (KTP, rekening, BPJS, golongan darah, foto) dibatasi hak aksesnya dan nomor KTP serta rekening dienkripsi. Rincian field menyusul di rancangan | 2026-11-04 | Disetujui, belum dibuat |

## Belum diputuskan
- Rancangan rinci HRIS Employee (field, hak akses, enkripsi, sinkron).
- Rancangan rinci HRIS Payroll Schedule dan HRIS Employee Pay.
- Cuti dan izin selain sakit.
