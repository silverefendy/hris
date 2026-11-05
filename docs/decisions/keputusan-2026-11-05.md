# Keputusan 5 November 2026 (K-118 sampai K-121)

Dasar: [../security/permissions.md](../security/permissions.md). Melanjutkan [keputusan-2026-11-04.md](keputusan-2026-11-04.md) (K-100 sampai K-117).

| No | Keputusan | Tanggal | Status |
|---|---|---|---|
| K-118 | Form `HRIS Employee` memakai tab "Audit Trail HRIS" lewat pola bersama (`Tab Break` `audit_trail_tab`, field HTML `audit_trail_html`, satu baris JS `hris.audit.render(frm)`) dan memiliki menu "Data Karyawan" di sidebar HRIS | 2026-11-05 | Diterapkan di site uji (124ec41). Teruji skrip: `periksa` 6 pemeriksaan OK (HR User tidak melihat KTP dan rekening, Payroll Admin melihat). Commit dibuat sebelum uji tampilan lulus (dicatat apa adanya). Tampilan browser: form dan tab Audit Trail terbuka; penyembunyian Data Sensitif di form belum diuji ulang per peran |
| K-119 | Audit Trail tidak boleh membocorkan field ber-permlevel: nilai lama dan nilai baru field yang permlevelnya tidak boleh dibaca pemanggil diganti `(disembunyikan)`. Baris riwayat tetap tampil (waktu, pengguna, nama field) agar jejak audit utuh. Berlaku juga untuk tabel anak (baris ditambah, dihapus, diubah). Dasar: `Meta.get_permlevel_access("read")`. Field yang tidak ditemukan di meta tetap tampil apa adanya. Menutup celah yang terbukti di browser: HR User dapat membaca nomor rekening lama dan baru lewat tab Audit Trail | 2026-11-05 | Diterapkan (1acccd5); teruji skrip `periksa_audit` 4 pemeriksaan OK dan tampilan browser. Cabang tabel anak belum teruji |
| K-120 | Izin per peran disusun di tiga lapis: izin DocType, role Page dan Report, serta cek role di kode Python (rinci di [permissions.md](../security/permissions.md)). Perubahan: `HRIS Manager` mendapat akses `HRIS Employee` (level 0 baca, tulis, buat; level 1 baca); `HRIS Attendance Operator` boleh menarik log dan membuka Konsol Mesin; `HRIS Payroll Admin` boleh membaca data absensi dan laporan Working Hour Ringkasan; role baru `HRIS Direksi` (hanya baca semua DocType HRIS termasuk Data Sensitif; tanpa Konsol Mesin dan Attendance Settings) dan `HRIS Employee Admin` (Employee level 0 dan 1 baca, tulis, buat; Employee Group baca). Role laporan ditambahkan lewat fungsi `after_migrate` di `hris/setup/izin.py` karena `migrate` tidak memperbarui role Report di database. Mewujudkan K-27 | 2026-11-05 | Diterapkan di kode (2a604e7); teruji skrip 31 pemeriksaan OK (15 + 16) di site uji. Belum: site kerja (butuh `migrate`), uji browser per peran, tarikan nyata oleh Operator |
| K-121 | Menu mengikuti izin DocType: satu sidebar HRIS, item tersembunyi bila role tidak punya hak baca; tidak ada workspace terpisah per role. Pemetaan orang ke role dilakukan lewat UI (data pengguna). Perubahan role atau izin lewat UI hanya berlaku di site itu dan tidak masuk repo, sehingga perubahan izin yang harus bertahan dibuat lewat kode | 2026-11-05 | Aktif |

## Catatan keputusan akses Data Sensitif (K-120)
- Tulis (isi dan ubah) KTP, rekening, BPJS, dan NPWP: HRIS Employee Admin, HRIS HR Admin, HR Manager, System Manager.
- Baca saja: HRIS Manager, HRIS Payroll Admin, HRIS Payroll Manager, HRIS Direksi.
- Tidak ada akses: HR User, Attendance Operator, Attendance Supervisor, HRIS Payroll User.
- Alasan: petugas input karyawan mengisi sendiri sehingga perlu hak tulis; payroll perlu rekening dan KTP; Direksi diizinkan melihat semuanya.

## Belum diputuskan
- Fitur Dokumen Karyawan (perjanjian kerja, foto KTP, kartu keluarga, softcopy dan hardcopy; dikelola satu petugas dokumen). Usulan: DocType terpisah dengan izin sendiri. Perlu diuji lebih dulu apakah lampiran bawaan form Employee dapat dibuka oleh role yang hanya punya hak baca dokumen (lampiran tidak mengikuti permlevel; dugaan, belum terbukti). Role petugas dokumen dibuat bersama fitur ini (K-20).
- Apakah `HRIS Direksi` perlu membaca `HRIS Attendance Settings` (isinya belum dibaca untuk menilai sensitivitas).
- Penyesuaian role pada `HRIS Payroll Schedule` bersama role gaji (K-115); `HRIS Payroll Manager` belum punya hak di sana.
- Hak tulis Data Sensitif untuk `HR Manager` (role ERPNext) dan `HRIS HR Admin`: dipertahankan seperti kondisi kode; perlu ditinjau bila peran HRD berubah.
- Pemusatan daftar role yang tersebar di delapan berkas Python menjadi satu modul.
- Jadwal `migrate` ke site kerja (cadangan, latihan di salinan segar).
