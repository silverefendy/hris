# Keputusan 7 November 2026 (K-127)

Dasar: [keputusan-2026-11-04.md](keputusan-2026-11-04.md) (K-100, K-109, K-110, K-112) dan [../business/payroll-rancangan.md](../business/payroll-rancangan.md).

| No | Keputusan | Tanggal | Status |
|---|---|---|---|
| K-127 | Rancangan `HRIS Employee Pay` (riwayat gaji per orang). **Field:** `employee` (tautan ke `HRIS Employee`, wajib), `employee_name` dan `company` (otomatis dari karyawan), `pay_type` (Bulanan atau Harian), `amount` (wajib, lebih dari 0), `payroll_schedule` (wajib, aktif, satu company dengan karyawan), `effective_from` (wajib), `effective_to` (otomatis; kosong berarti baris yang sedang berlaku), `change_reason` (wajib bila karyawan sudah punya baris sebelumnya), tab Audit Trail dengan pola bersama. Satu baris memuat jenis gaji, nominal, dan jadwal sekaligus. **Aturan:** baris baru menutup baris lama otomatis; rentang berlaku dua baris milik karyawan yang sama tidak boleh tumpang tindih (K-100); nominal pada baris lama dikunci, perubahan lewat baris baru; tanpa hak hapus; tanggal berlaku mundur boleh, pengecekan periode Final ditegakkan setelah `HRIS Payroll Period` ada (K-109). **Jenis gaji:** karyawan mingguan memakai `pay_type` Harian dengan jadwal gaji bertipe Mingguan; upah disimpan per hari dan dibayar per minggu, tidak masuk berarti tidak digaji (menegaskan A3). **Hak akses:** HRIS Payroll Manager semua baris; HRIS Payroll Admin hanya harian, tidak boleh melihat gaji bulanan (K-110); HRIS Direksi baca semua; HR biasa tidak punya akses. Komponen lain (tunjangan, potongan) ditunda ke fase 2 bersama BPJS dan PPh21 | 2026-11-07 | Disetujui, belum dibuat. Pembatasan per baris untuk Payroll Admin (form, list view, kotak pilihan Link, laporan, Audit Trail) wajib diuji di site uji. Catatan: opsi `hris_pay_type` pada `HRIS Employee` belum dibaca; cocokkan dengan `pay_type` sebelum dibuat |

## Catatan
- `pay_type` berupa pilihan tetap (Select) yang tersimpan di definisi DocType. Menambah jenis baru (misalnya Per Jam, yang di rancangan payroll sudah disiapkan tetapi belum aktif) berarti menambah opsi lewat `migrate` ditambah rumus hitung untuk jenis itu. Mengganti nama atau menghapus opsi yang sudah dipakai baris lama berisiko, sehingga perubahan sebaiknya hanya penambahan.

## Belum diputuskan
- Komponen lain pada gaji (tunjangan, potongan) dan nasibnya di fase 2.
- Apakah daftar jenis gaji perlu dijadikan master tersendiri bila jenis baru sering muncul (belum ada kebutuhan saat ini).
