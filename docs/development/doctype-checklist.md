# Checklist DocType HRIS Baru

Diperbarui: 28 Oktober 2026

Aturan tetap untuk setiap DocType baru di app `hris`. Berlaku sejak K-29 dan K-30 (lihat [decisions/README.md](../decisions/README.md)).

| # | Syarat | Catatan |
|---|---|---|
| 1 | Nama berawalan `HRIS ` dan `track_changes: 1` | K-10 |
| 2 | Penomoran tanpa hash dan memuat YYMM, format `PREFIX-YYMM-NNNN` | K-30. Contoh: Holiday `HOL-2610-0001` (`naming_rule: Expression`, `autoname: format:HOL-{YY}{MM}-{####}`). Jumlah digit disesuaikan volume (Attendance kemungkinan 5 digit). |
| 3 | Pengecualian penomoran | DocType yang namanya memang kunci anti-duplikat (HRIS Raw Log) atau diambil dari field nama (Device, Shift, Employee Group). Tabel anak, Version, dan Comment memakai hash internal Frappe. |
| 4 | Tab Break "Details" di awal; Tab Break "Audit Trail HRIS" (`depends_on: eval:!doc.__islocal`) dan field HTML `audit_trail_html` di akhir | Tidak ada kolom database yang berubah karena tab dan HTML tidak menyimpan data |
| 5 | File `<nama_doctype>.js` memanggil `hris.audit.render(frm)` di event `refresh` | Fungsi bersama ada di `hris/public/js/hris_audit_trail.js`, dimuat lewat `app_include_js` di `hooks.py` |
| 6 | Tabel anak tidak punya tab sendiri | Perubahannya muncul di tab audit dokumen induk (baris ditambah, dihapus, diubah) |
| 7 | Controller melewati field kosong di `validate` | Frappe menjalankan `validate` sebelum cek field wajib |
| 8 | Jangan memakai "Company kosong" sebagai arti khusus | Field Link Company bisa terisi otomatis dari default pengguna. Pakai field eksplisit (contoh: centang `applies_to_all_companies` di Holiday). |
| 9 | `mandatory_depends_on` tidak cukup | Hanya berlaku di browser. Wajib bersyarat harus dicek lagi di controller. |
| 10 | Perubahan JSON DocType | Ubah `modified`, lalu `migrate` dan `clear-cache` dalam satu blok. Backup dulu. |
| 11 | Uji lewat form di browser, termasuk tab audit | Uji skrip saja tidak cukup |
