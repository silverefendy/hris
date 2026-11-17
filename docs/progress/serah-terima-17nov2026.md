# Serah Terima Sesi 17 November 2026

Cakupan: K-142 sesi 4 (impor CSV tarif PPh 21) dan perbaikan seluruh uji usang. Disusun agar sesi Claude berikutnya bisa melanjutkan. Hanya memuat hal yang terbukti di sesi ini; yang belum diketahui ditandai.

## 1. Konteks dan cara kerja

- Repo `silverefendy/hris`, branch `main`. Bench `/home/it/erp`, site uji `hris-uji.local`, server `cmlerp`, user `it`.
- Aturan kerja: `CLAUDE.md` dan `docs/development/ai-workflow.md`. Claude hanya menulis `.md`; selain itu skrip heredoc yang dijalankan Efendy. Satu modul per sesi. Alur: diskusi, persetujuan, skrip, uji, perbaikan, catat.
- Skrip panjang dan skrip bergerbang **ditulis ke berkas** (`cat > berkas <<'OUTER'`) lalu dijalankan dengan `bash berkas`. Jangan memakai `exit` pada perintah yang ditempel langsung ke terminal: sesi SSH ikut tertutup.
- Pola patch berkas: `python3` dengan `assert s.count(pola) == 1`, cadangan `.bak`, lalu `py_compile` atau `bash -n`.
- Jam server UTC (WIB = UTC + 7). `bench execute` mencetak `NameError: name 'hris' is not defined` ketika fungsi melempar galat; galat aslinya ada di atas baris itu.

## 2. Commit sesi ini (semua sudah di-push)

| Commit | Isi |
|---|---|
| `d2f6916` | K-142: `allow_import` TER dan Pasal 17, izin Import hanya System Manager |
| `43dc860` | Catatan K-142 sesi 4 |
| `b2c5a6a` | `docs/development/rencana-perbaikan-uji.md` |
| `8673e75` | `uji_bpjs_peserta`: S10 memakai baris ZZ sendiri |
| `2fb0208` | Rencana uji diperbarui |
| `e64c8d1` | `uji_hris_employee`, `uji_sinkron`, `uji_tampilan` |
| `5bf9aac` | `uji_k102`, `uji_k126` |

## 3. Keadaan uji per 17 November 2026 (15:13 WIB)

- 67 modul uji terukur: 66 punya patokan, 1 `UKUR` (`uji_kecepatan_hca`, hanya dicek tanpa galat). `ERROR 0`, `BEDA 0`, tidak ada uji usang tersisa.
- Angka patokan yang diperbaiki sesi ini: `uji_izin` 31, `uji_bpjs_peserta` 10, `uji_hris_employee` 22, `uji_sinkron` 19, `uji_tampilan` 10, `uji_k102` 14, `uji_k126` 12 (semua gagal 0). Contoh angka lama yang stabil: `uji_bpjs_slip` 68, `uji_pph21_rate` 32. `uji_pph21_server` memakai hash keluaran `1119d97c4747`.
- Tabel kunci (16 dan 17 November sama): HRIS Employee Component 3, Employee Pay 3, Payroll Period 1, Payroll Slip 1, Payroll Slip Item 3. Sisa data uji `UJICSV` dan `2030-01-01` = 0.

## 4. Alat regresi (di server, di luar repo): `/home/it/runbook_k142/`

- `regresi_v2.sh`: menjalankan semua `uji_*.py` di app. Prasyarat: `HRIS PPh21 Settings.enabled` bukan 1. Keluaran di `/tmp/regresi_v2_<tanggal>_<jam>/` (`RINGKASAN.txt`, `snapshot.txt`).
- Status: `SAMA`, `BEDA`, `BARU`, `BARU-GAGAL`, `ERROR`, `USANG-SAMA`, `USANG-BERUBAH`, `UKUR`. Simpan patokan hanya atas perintah Efendy: `bash regresi_v2.sh --simpan <folder hasil>`.
- Modul dengan siklus khusus di penjalan: `uji_izin` (siapkan, siapkan_lanjut, periksa, periksa_lanjut, bersihkan, bersihkan_lanjut), `uji_tampilan` (siapkan dengan argumen, periksa, periksa_audit, bersihkan), `uji_k126` (periksa dan periksa_resign). Modul lain dipanggil lewat `jalankan`, dengan fallback `periksa`.
- `patokan_regresi.txt` (66 baris). `usang_diketahui.txt` kosong. Penjalan **tidak** lagi mengisi daftar usang otomatis (cacat isi-ulang sudah dihapus).
- Gerbang pada skrip: pakai pencocokan persis (`grep -qx 'ERROR: 0'`). Pola `grep '^ERROR'` salah karena cocok dengan `ERROR: 0`.

## 5. Temuan yang jangan diulang

- **`uji_izin`**: 12 gagal berasal dari penjalan yang tidak memanggil `siapkan`. Bukan bug izin. `izin.py` (`after_migrate`) hanya memastikan role dan role laporan.
- **`uji_bpjs_peserta` S10**: gagal karena `HRE-00335` (di site uji) punya `pph21_enrolled = 1`. Riwayat Version: diubah Administrator pada 10 November 2026 pukul 16:19 sampai 16:23; `modified` 16:54 tanpa catatan Version. Data tidak diubah. Produksi tidak terpengaruh. S10 kini memakai baris ZZ dan mencetak INFO jumlah baris data nyata yang bercentang menyala.
- **Aturan ID Finger** (controller HRIS Employee): (1) antar HRIS Employee hanya yang berstatus Aktif; (2) terhadap Employee ERPNext berlaku untuk semua status termasuk Left, kecuali Employee yang tertaut ke dokumen itu. Akibatnya ID Finger karyawan Resign tidak bisa dipakai ulang oleh karyawan baru.
- **Objek dokumen basi**: setelah `insert`, tautan `erpnext_employee` diisi lewat `db.set_value` saat sinkron, sehingga objek di memori tidak punya tautan itu. Uji yang `save()` objek yang sama harus `reload()` dulu. Ini artefak uji. Di antarmuka dokumen selalu dimuat ulang.
- **`uji_sinkron` nomor 12**: kegagalan sinkron kini disimulasikan dengan `mock.patch.object(employee_sync, "_terapkan")`, karena tanggal tidak valid sudah ditolak di sumber (K-126).
- **`uji_tampilan`**: `siapkan` butuh `gender` dan `birth_date` serta `skip_sync`; `periksa_audit` juga memakai `skip_sync` agar tidak meninggalkan Employee ERPNext. Uji ini memakai `commit`, jadi selalu akhiri dengan `bersihkan`.
- **`uji_k102` dan `uji_k126`**: dulu mengambil Employee ERPNext pertama ber-ID Finger dari data nyata (`HR-EMP-01078`, ID 11356, tertaut ke `HRE-01097`, orang yang sama), sehingga rusak begitu dokumen HRIS itu ada. Kini membuat Employee ERPNext ZZ sendiri dan di-rollback. (Catatan lama yang menyebut ID itu "dipegang dua pihak" keliru dan sudah dikoreksi.)
- **Pola data uji yang terbukti**: HRIS Employee wajib `employee_name`, `birth_date`, `gender`, `company`, `date_of_joining`, `status` (bawaan Aktif); `doc.flags.skip_sync = True`; `insert(ignore_permissions=True)`; `frappe.db.rollback()` di `finally`. Nomor seri penamaan ikut kembali setelah rollback.
- `migrasi_employee` memakai `commit` pada `migrasi` dan `verifikasi`: jangan dijalankan sembarangan di site uji.

## 6. Hanya ada di site uji, belum di produksi

`allow_import` dan izin Import pada `HRIS PPh21 TER Rate` dan `HRIS PPh21 Pasal17 Rate` (K-142). Produksi memperolehnya saat K-102. Gladi `fase1` harus mencakup keduanya, dan sebaiknya memeriksa izin peran (jalankan `uji_izin`).

## 7. Belum dikerjakan

1. **Penutupan sesi sesuai `CLAUDE.md`**: perbarui `docs/progress/status.md` dan `session-log.md`. Catatan: `status.md` diperbarui sampai 15 Nov dan sebagian besar akurat (koreksi 17 Nov: dugaan awal bahwa berkas ini sangat usang keliru). Pembaruan 17 Nov sudah ditambahkan; sisanya merapikan tabel Belum teruji dan Tertunda.
2. Empat dokumen `site_config`, runbook K-102, dan sidebar tertunda: belum ada datanya. Minta Efendy menjalankan `ls /home/it/erp/apps/hris/docs` agar ditulis dari berkas yang ada.
3. Opsional, S10b: cek `COLUMN_DEFAULT` enam kolom centang di `information_schema` (ditawarkan, belum dipilih).
4. Opsional: periksa modul uji lain yang punya lebih dari satu fungsi `periksa*`/`jalankan*` (selain `uji_izin`, `uji_tampilan`, `uji_k126`), karena penjalan hanya memanggil satu fungsi. Belum dicek. Perintah: `cd /home/it/erp/apps/hris && for f in $(find hris -name 'uji_*.py'); do c=$(grep -cE '^def (periksa|jalankan)' $f); [ $c -gt 1 ] && echo "$c $f"; done`
5. Kredensial HTTPS Git diminta setiap push. Opsi: `git config --global credential.helper store` (verifikasi di dokumentasi Git).


## 8. Pembaruan susulan (17 November 2026, malam)

- Butir 7.1 selesai: `status.md` dan `session-log.md` diperbarui (`a36362e`).
- Butir 7.4 selesai: hanya tiga modul berfungsi ganda dan ketiganya sudah ditangani.
- Dokumen keputusan K-142 dibuat: [../decisions/keputusan-2026-11-17-k142.md](../decisions/keputusan-2026-11-17-k142.md).
- Masih terbuka: butir 7.2 (dokumen `site_config`, runbook K-102 di repo, sidebar), 7.3 (S10b), 7.5 (kredensial Git). Jalur teknis berikutnya: gladi ulang `fase1` dan K-102.

## 9. Pembaruan susulan (17 November 2026, sore)

- W6 lulus, gladi resik K-102 lulus (fase 2 terbukti), regresi SAMA 66 setelah situs uji dipulihkan. Rincian: [status.md](status.md) bagian "Pembaruan 17 Nov 2026, sore".
- Jalur teknis berikutnya: migrasi produksi K-102 lewat `produksi_k102.sh`.
