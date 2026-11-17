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
| `uji_bpjs_peserta` (S10) | 1 gagal: baris HRE-00335 punya `pph21_enrolled` = 1 (data sisa uji browser di site uji) | Opsi B: uji membuat baris `ZZ` sendiri (pilihan Efendy) | Menunggu pembacaan pola (diag7) |
| `uji_hris_employee`, `uji_sinkron`, `uji_tampilan` | Berhenti dengan galat validasi, 0 OK 0 GAGAL. Dugaan: lebih tua dari validasi K-122, K-123, K-126 | Disesuaikan ke validasi baru | Berkas belum dibaca |
| `uji_k102`, `uji_k126` | 2 gagal masing-masing. ID Finger 11356 dipegang `HR-EMP-01078` dan `HRE-01097` | Pakai baris buatan sendiri | Menunggu pola `ZZ` |

## 3. Urutan kerja

1. Pola pembuatan baris `ZZ` (dibuat sekali, dipakai ulang): baca field wajib dan hook sinkron HRIS Employee.
2. `uji_bpjs_peserta` S10 dengan baris `ZZ`.
3. `uji_hris_employee`, `uji_sinkron`, `uji_tampilan` (satu keluarga validasi): baca berkas, rancang, setujui, script.
4. `uji_k102`, `uji_k126`.

Alur per uji: baca berkas, jelaskan bagian usang, disetujui, script, jalankan regresi, simpan patokan hanya atas perintah.
