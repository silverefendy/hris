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
