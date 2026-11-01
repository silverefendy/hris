# Keputusan 1 November 2026 (K-78 sampai K-85)

Catatan: berkas sementara. Pindahkan barisnya ke tabel `README.md` bila disetujui.

| # | Keputusan | Tanggal | Status |
|---|---|---|---|
| K-78 | 164 Department diimpor dari data mesin di bawah akar `PTCML - CML`. Field `Department.hris_device_dept_id` (Data, unik, read-only) menjadi kunci pemetaan departemen mesin ke Department | 2026-11-01 | Diterapkan, teruji tabel dan Tree View |
| K-79 | 4 custom field Employee: `hris_data_status` (Lengkap atau Perlu Dilengkapi), `hris_data_note`, `hris_payroll_code`, `hris_payroll_code_alt` (dua terakhir read-only). Status Perlu Dilengkapi dipakai HRD untuk menyaring daftar kerja | 2026-11-01 | Diterapkan, terverifikasi lewat tabel Custom Field |
| K-80 | Impor 1.077 Employee. Kunci pencocokan `Badgenumber` (mesin) = `code` (aplikasi gaji), dibandingkan sebagai teks persis. Gender konflik atau tidak diketahui = `Prefer not to say` plus penanda. Tanggal lahir kosong atau janggal = `1900-01-01` plus penanda (laporan umur wajib mengecualikan). Tanggal masuk pengganti = punch pertama. Department dari departemen mesin; 3 Employee aktif di departemen BERHENTI/OUT tanpa Department. `hris_employee_group` dan `hris_pay_type` tidak diisi | 2026-11-01 | Diterapkan (COBA lalu SIMPAN, error 0) |
| K-81 | 54 ID berstatus resign (September 2026) di aplikasi gaji tetapi masih punch diimpor sebagai `Active`, data dari mesin, `hris_payroll_code` kosong, penanda "perlu verifikasi HRD". **Sementara**: penyebab resign massal belum terbukti | 2026-11-01 | Diterapkan, menunggu verifikasi HRD |
| K-82 | Pencocokan ulang Raw Log lama lewat `doc.save()` dengan `change_reason`, bukan SQL langsung, agar validasi dan riwayat perubahan tetap berjalan. Hanya baris `Tidak Cocok`. Aturan cocok sama dengan `match_employee` (ID mesin, company, Active, tepat satu hasil) | 2026-11-01 | Diterapkan (4.487 baris; sisa 110 baris = 1 ID ditahan) |
| K-83 | Pengisian `hris_employee_group` untuk 65 Employee berdasarkan jam masuk modus (punch berstatus mesin 0) dan akhiran nama Department. Jam 06 sampai 08 dengan Department berakhiran ANGGOTA atau ANGGOTA HARIAN masuk `Lapangan Harian` (51). Jam 18 dengan Department berakhiran ANGGOTA masuk `Security Malam` (14). Dua ID dikecualikan (satu belum punya Employee, satu berada di Department induk). Grup `Security Malam` dibuat: Jadwal Mingguan, Senin sampai Minggu, shift `Security Malam`, tanpa Department. **Sementara**: flag masuk/keluar mesin tidak andal (K-23) dan 28 ID punya punch jam 18 yang cukup banyak; koreksi lewat form Employee | 2026-11-01 | Diterapkan (backup, COBA, SIMPAN; 65 baru, error 0) |
| K-84 | Penandaan `needs_review` pada `HRIS Working Hour` hanya untuk anomali nyata. Alasan log berstatus Menunggu dihapus. Punch yang diabaikan ditandai hanya bila lebih dari 10 menit dari Masuk atau Pulang (`GEROMBOL_MENIT`), karena mesin mengirim punch bergerombol 4 sampai 6 kali dalam hitungan detik. Punch di luar jendela ditandai (shift biasa: sisa tanggal yang sama; shift lewat tengah malam: margin 180 menit, `MARGIN_LUAR_MENIT`). Angka hitungan tidak berubah | 2026-11-01 | Diterapkan (7cc6a6d), teruji 8 kasus dengan rollback |
| K-85 | Lembur hanya dihitung bila status Hadir. Hari Tidak Lengkap berlembur 0 dan HRD menyesuaikan, selaras K-41 | 2026-11-01 | Diterapkan (4d63cb0), teruji 5 kasus dengan rollback |

## Belum diputuskan
- Tombol Cocokkan Ulang di Konsol Mesin: perlu rancangan.
- Penetapan grup atau Shift Assignment untuk Employee hasil impor selain 65 yang sudah terisi (K-83).
- Cara HRD memperbaiki penanda 1900-01-01, gender, dan Department kosong.
- Jam kerja resmi security malam dan pagi: punch nyata masuk sekitar 18:30 sampai 19:30 dan pulang sekitar 06:00 sampai 07:59, sedangkan shift di sistem 20:00 sampai 08:00. Bila tidak diubah, hampir semua security terpotong pulang awal 1 sampai 2 jam per hari. Menunggu HRD; perubahan lewat form HRIS Shift.
- Satu ID dengan 110 punch Oktober belum punya Employee (ditahan saat impor); alasan penahanan dan keputusan impor belum dikonfirmasi.
- Pengujian hitung ulang Working Hour lewat UI setelah worker direstart (uji sejauh ini lewat console).
