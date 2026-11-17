# Rencana Perbaikan Uji Usang

Dibuat 17 November 2026. Cakupan: hanya berkas `tests/*.py`. Tidak mengubah DocType, kode aplikasi, atau data nyata.

## 1. Prinsip

- Uji membuat data sendiri (awalan `ZZ`), memakai rollback, dan tidak bergantung pada data nyata.
- Uji yang memakai `commit` wajib membersihkan data bila berhenti di tengah.
- Penjalan regresi: `/home/it/runbook_k142/regresi_v2.sh` (di server, di luar repo). Patokan: `patokan_regresi.txt` (60 modul per 17 November 2026). Daftar uji gagal yang diketahui: `usang_diketahui.txt`.

## 2. Status per uji

| Uji | Keadaan | Keputusan | Status |
|---|---|---|---|
| `uji_izin` | 12 gagal hanya karena penjalan tidak memanggil `siapkan`. Siklus penuh: 31 OK, 0 GAGAL | Cukup ubah penjalan | Selesai 17 November 2026 |
| `uji_bpjs_peserta` (S10) | 1 gagal: baris HRE-00335 punya `pph21_enrolled` = 1 (riwayat Version: diubah Administrator pada 10 November 2026; asal belum dipastikan) | Opsi B: uji membuat baris `ZZ` sendiri (pilihan Efendy) | Selesai 17 November 2026 (commit 8673e75): 10 OK, 0 GAGAL |
| `uji_hris_employee` | Pemeriksaan 20 usang (ID Finger Resign kini tidak bisa dipakai ulang, unik di Employee ERPNext, K-126 V2). Pemeriksaan 21 dan 22 memakai objek dokumen basi setelah sinkron | 20 menjadi "ditolak", 22 menjadi reaktivasi dengan ID sendiri diterima, `reload()` sebelum `save()` | Selesai 17 November 2026 |
| `uji_sinkron` | Pemeriksaan 12 memakai tanggal tidak valid, kini ditolak di sumber (K-126) | Kegagalan sinkron disimulasikan dengan `mock.patch.object(employee_sync, "_terapkan")` | Selesai 17 November 2026: 19 OK, 0 GAGAL |
| `uji_tampilan` | `siapkan` tanpa `gender` dan `birth_date` (kini wajib); penjalan tidak memanggil `siapkan` | Tambah dua field dan `skip_sync`; penjalan v2 menjalankan siklus siapkan, periksa, periksa_audit, bersihkan | Selesai 17 November 2026: 10 OK, 0 GAGAL |
| `uji_k102`, `uji_k126` | Dua pemeriksaan gagal masing-masing. Uji mengambil Employee ERPNext pertama ber-ID Finger dari data nyata (kini `HR-EMP-01078`, sudah tertaut ke `HRE-01097`, orang yang sama), sehingga aturan ID antar HRIS Aktif muncul lebih dulu | Employee ERPNext `ZZ` buatan sendiri dalam transaksi, `rollback` di `finally`. Penjalan regresi menjalankan `periksa` dan `periksa_resign` untuk `uji_k126` | Selesai 17 November 2026: `uji_k102` 14 OK, `uji_k126` 12 OK |

## 3. Urutan kerja

1. Pola pembuatan baris `ZZ` (selesai): enam field wajib HRIS Employee, `doc.flags.skip_sync = True`, `insert(ignore_permissions=True)`, `frappe.db.rollback()` di `finally`. Contoh: `_buat_karyawan` di `uji_employee_pay.py` dan S10 di `uji_bpjs_peserta.py`.
2. `uji_bpjs_peserta` S10 dengan baris `ZZ` (selesai).
3. `uji_hris_employee`, `uji_sinkron`, `uji_tampilan` (satu keluarga validasi): selesai 17 November 2026.
4. `uji_k102`, `uji_k126`: selesai 17 November 2026.

Alur per uji: baca berkas, jelaskan bagian usang, disetujui, script, jalankan regresi, simpan patokan hanya atas perintah.
