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
