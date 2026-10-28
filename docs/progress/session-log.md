# Session Log

## 2026-10-27
- Analisis kode `hr_app` dan `hr_payroll`, inventaris HRMS v16, keputusan arsitektur awal.
- Kerangka dokumentasi dibuat.
- Server kerja: upgrade Frappe dan ERPNext, HRMS terpasang bersih di site kerja, `default_site` diarahkan ke site kerja. Detail di [operations/environment.md](../operations/environment.md).
- Isu ikon desk dijelaskan (perilaku bawaan mode grid ikon lama), lalu diparkir.
- Struktur diputuskan: lima modul; `hris_cml` dihapus (commit 853d504).
- Aturan penamaan diputuskan: semua DocType dan role berawalan `HRIS `.
- Enam role HRIS dibuat; `required_apps` diisi; app `hris` terpasang di site kerja (commit aa6c418).
- Catatan: install pertama gagal (`No module named 'hris.hris_cml'`) dan berhasil pada percobaan ulang setelah `clear-cache`. Dugaan penyebab: peta modul di cache; belum dibuktikan. Bila `modules.txt` berubah, jalankan `bench clear-cache` sebelum `install-app`.
- Keputusan CI: ubah pemicu ke `main` (belum diterapkan).
- Dokumentasi diperbarui (keputusan, status, temuan tambahan, lingkungan).

## 2026-10-28
- Rancangan Attendance dibahas dan diputuskan (K-18 sampai K-28): HRIS mandiri, bridge hanya HRIS ke ERPNext, tinjauan per baris, ID sama di semua mesin, masuk/keluar oleh HRIS, punch ganda otomatis, aturan ubah data dan audit trail, HRIS Device lengkap, zona waktu WIB.
- `HRIS Device` dipasang dan diuji (skrip dan form). Pengecekan menemukan: `mandatory_depends_on` hanya berlaku di browser, sehingga wajib IP untuk mode Pull dipindah ke controller.
- `HRIS Raw Log` dipasang: nama dokumen dari mesin + ID user + waktu (duplikat ditolak), pencocokan Employee, alasan ubah wajib, status tinjauan. Uji skrip lolos.
- Audit trail: API `get_audit_trail` (hanya DocType `HRIS `, cek izin baca) dan tab "Audit Trail HRIS" di form; warna indikator di list view; penguncian form untuk non-editor.
- Uji UI Raw Log menemukan field `company` (wajib, read-only, tersembunyi) memblokir simpan di browser; diperbaiki dengan `fetch_from: device.company`. Setelahnya: simpan, alasan wajib, tab audit, dan perubahan status berhasil.
- Zona waktu site kerja diganti dari Asia/Kolkata ke Asia/Jakarta.
- Kendala dan pelajaran:
  - Tab di skrip heredoc hilang saat ditempel ke terminal (tab completion), menyebabkan `IndentationError`. Skrip memakai spasi.
  - Di `bench console` yang dialirkan lewat heredoc, blok bertingkat tidak dieksekusi tanpa baris kosong; pakai `exec(open(file).read(), {"frappe": frappe})`.
  - Perubahan JSON DocType harus mengubah `modified` dan diikuti `migrate` dalam satu blok yang sama.
  - Uji lewat skrip tidak cukup; validasi di browser perlu diuji lewat form.
- Dokumentasi: `data-model`, `platform-boundaries`, `permissions`, `attendance-flow`, keputusan 0002 dan K-18 sampai K-28, status, roadmap, lingkungan, testing.
- Belum: Report "HRIS Audit Trail", jalur data mesin, working hour/shift.

## 2026-10-28 (sesi lanjutan: Bagian A shift dan grup)
- Dipasang dan diuji: `HRIS Shift`, `HRIS Employee Group` (+ jadwal mingguan), `HRIS Holiday`, Custom Field dan hook validasi di `Employee`. Rename shift dan grup berhasil (ID dan nama ikut berganti).
- K-29: `Department` tetap master ERPNext (modul Setup). Holiday ditambah centang "Berlaku untuk Semua Company".
- Audit tab dipasang di semua DocType HRIS lewat JS bersama `hris_audit_trail.js` (dimuat via `app_include_js`) dan satu file JS kecil per DocType. `audit_trail.py` kini membaca tabel anak (ditambah, dihapus, diubah); struktur `Version` tabel anak terbukti bekerja di v16, di skrip uji maupun di form.
- K-30: penomoran tanpa hash dengan YYMM. Holiday `HOL-2610-0001` teruji (dua nomor berurutan, rollback). Data libur lama bernomor hash tidak di-rename; dihapus manual.
- Detik di jam shift dibulatkan ke menit (opsional; muncul hanya karena uji log audit).
- Commit: fd1c1c2 (Bagian A), 22126c0 (penomoran Holiday), 3efd73b (pembulatan detik).
- Kendala dan pelajaran:
  - Field Link Company bisa terisi otomatis dari default pengguna, sehingga "Company kosong" tidak boleh dipakai sebagai arti "semua company". Dipakai centang eksplisit; data lama dirapikan lewat skrip satu kali.
  - Perapian data lewat `set_value` tidak tercatat di audit trail; wajar untuk master data, bukan untuk perubahan biasa.
  - Pemicu otomatis audit tab untuk semua DocType tidak dipakai karena bergantung event Frappe yang belum diverifikasi; dipilih satu JS kecil per DocType (lihat [development/doctype-checklist.md](../development/doctype-checklist.md)).
- Belum: Bagian B (rotasi dan Shift Assignment), data awal contoh, jalur data mesin.

## 2026-10-28 (sesi lanjutan: Bagian B rotasi dan Shift Assignment)
- Script 6 (`HRIS Shift Rotation` + tabel anak `HRIS Shift Rotation Day`, commit fd8b082) dan Script 7 (`HRIS Employee Group` memilih Jadwal Mingguan atau Rotasi, commit 27947d5) lolos. Uji browser Script 7: rotasi yang dipakai grup ditolak diubah dengan pesan yang menyebut grup; pindah ke Jadwal Mingguan tercatat di audit (Jenis Jadwal, Rotasi, Tanggal Mulai).
- Script 8 (commit 4fcb41b): `HRIS Shift Assignment` dan service `shift_schedule.py`. Pemasangan lolos (backup, migrate tanpa error). Uji otomatis 8c lolos 20 pemeriksaan: rotasi (5), jadwal mingguan (4), assignment (4), penolakan tumpang tindih, alasan kosong, tanggal terbalik, shift nonaktif, libur (2), audit (1); semua di-rollback.
- K-31 sampai K-33 dicatat (rotasi, Shift Assignment, urutan penentuan shift dan aturan libur).
- Kendala dan pelajaran:
  - Uji 8c pertama berhenti sendiri karena site belum punya Employee Active (pengaman skrip bekerja). Skrip direvisi: bila tidak ada karyawan Active, dibuat karyawan sementara (butuh Gender, tanggal lahir, tanggal bergabung, Company) lalu rollback.
  - Nama field grup di `Employee` tidak ditebak; service mencarinya dari meta lewat daftar Link field yang menunjuk `HRIS Employee Group` (hasil: `hris_employee_group`).
  - Penolakan "alasan kosong" datang dari validasi field wajib Frappe, bukan dari pesan di controller; keduanya menolak, jadi hasilnya sama.
  - File `.py` ditulis dengan spasi lalu dikonversi ke tab (gaya Frappe) dengan `sed` setelah dibuat.
- Pembacaan kode setelah push menghasilkan empat temuan kecil (lihat `progress/status.md`, bagian Temuan).
- Belum: uji browser Shift Assignment, data awal contoh, working hour, jalur data mesin.

## 2026-10-29 (sesi lanjutan: cek dan perbaikan temuan kode)
- Empat temuan pembacaan kode dicek dulu lewat skrip baca-saja (grep dan konsol) sebelum diperbaiki. Hasil: nama field `schedule_section` ganda terbukti di JSON, meta, dan `tabDocField` (hanya di Employee Group; label section kedua menimpa yang pertama); `get_shift_for_weekday` tanpa pemanggil; belum ada data yang terkena temuan 4.
- Pembacaan controller menemukan celah tambahan: `HRIS Shift Rotation` tidak mengunci status Aktif. Diputuskan K-34 (rotasi tidak boleh dinonaktifkan selama dipakai grup aktif) alih-alih menambal service.
- Perbaikan (commit efd88fa): section Employee Group diganti nama dan dirapikan, deskripsi `weekly_schedule` diperbarui, `get_shift_for_weekday` dihapus, `validate_deactivation` ditambahkan di rotasi. Backup, migrate, dan clear-cache dalam satu blok lolos; uji konsol lolos (meta tanpa nama ganda, fungsi hilang, rotasi terpakai grup aktif ditolak dan boleh dinonaktifkan setelah grup nonaktif, semua di-rollback); uji browser lolos.
- Pengecekan `HRIS Shift`: belum ada kunci nonaktif maupun kunci perubahan jam; karena jadwal dihitung saat dibutuhkan, mengubah jam shift mengubah tanggal lampau. Dicatat di "Belum diputuskan", dibahas bersama working hour.
- Pelajaran:
  - Cek dulu dengan skrip baca-saja, baru perbaiki; hasil cek mengubah rekomendasi (dari menambal service ke mengunci di rotasi).
  - Patch file `.py` dengan penggantian teks yang di-`assert` dan penulisan ulang JSON utuh lebih aman daripada penyuntingan manual; skrip berhenti bila file target punya perubahan lokal.
  - Jam OS server tampaknya UTC (`date` mencetak 23:29 saat log backup mencatat 06:29 WIB); nilai `modified` pada JSON mengikuti jam OS.
  - Mengganti nama Section Break aman karena tidak punya kolom di database.
- Keputusan: karyawan contoh dibuat lewat skrip dan dihapus otomatis setelah uji.
- Belum: rancangan dan skrip data awal contoh, uji browser Shift Assignment, working hour, jalur data mesin.
