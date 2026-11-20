# C1 dan C4: Tinjauan dan Koreksi Hari Tidak Lengkap

Status per 21 Nov 2026: C1 live di produksi (migrate dan uji browser 21 Nov). C4 tahap 1 lulus uji di situs uji, belum di produksi.

## Latar

Hari berstatus Tidak Lengkap (salah satu punch hilang) atau Tidak Hadir perlu keputusan HRD sebelum masuk slip gaji.

## C1: Hasil Tinjauan Tidak Lengkap

- Field `incomplete_outcome` di HRIS Working Hour, pilihan: Dihitung Hadir atau Dihitung Tidak Hadir.
- Status Sudah Ditinjau pada hari Tidak Lengkap mewajibkan hasil dan catatan tinjauan. Perubahan tercatat di Audit Trail HRIS.
- Slip gaji (`payroll_slip`) membagi hari Tidak Lengkap menjadi tiga kelompok menurut `incomplete_outcome`: dihitung hadir, dihitung tidak hadir, belum ditinjau. Kolom dibaca hanya bila ada di database (`has_column`), sehingga kode aman sebelum migrate.
- Uji: empat modul uji baru, regresi penuh 78 modul (SAMA 74, BEDA 0, ERROR 0, BARU 4). Commit `abeedef`.
- Belum diverifikasi di situs uji: Hitung Ulang tidak menghapus hasil tinjauan, dan mengembalikan status ke Menunggu mengosongkan hasil.

## C4: Jam koreksi HRD

Keputusan: hari yang diisi jam koreksi dihitung penuh sebagai Hadir; lembur tidak pernah berasal dari jam koreksi.

- Modul murni `jam_koreksi.py` (tanpa database): jendela masuk dan pulang, validasi, penyuntikan punch sintetis ke `compute_day`. Uji murni 22 dari 22.
- Tahap 1 (field `manual_check_in` dan `manual_check_out`, aturan controller). Uji database 10 dari 10 di situs uji:
  - hanya untuk hari Tidak Lengkap atau Tidak Hadir;
  - tidak bersama Hasil Tinjauan C1 dan tidak bersama Penyesuaian (jam);
  - wajib ada jadwal shift, jam masuk di dalam jendela masuk, jam pulang tidak melewati akhir shift;
  - Catatan Tinjauan wajib berisi alasan; status otomatis Sudah Ditinjau.
- Commit `13d28f9` dan `f319dae`.
- Belum: penyuntikan jam koreksi di `calculate_working_hour`, JS form, penghapusan massal, migrate produksi.

## Pelajaran operasional

- Produksi dijalankan lewat `bench start` (honcho). Web memuat ulang kode sendiri saat berkas berubah, tetapi worker dan scheduler tidak: perubahan kode yang dipakai pekerjaan latar butuh restart penuh.
- Folder kode dipakai bersama produksi dan situs uji. Migrate produksi membawa semua perubahan JSON DocType yang ada di folder itu, jadi urutan (kembalikan berkas, migrate, pulihkan) dipakai untuk menahan perubahan yang belum siap.
- Waktu Error Log memakai zona situs (WIB), sedangkan `now()` MariaDB dan `date` server UTC. Bandingkan dengan batas waktu WIB yang dihitung di shell.
- Penambal berkas aktif memakai mode CEK bawaan, pemeriksaan AST daftar method class, baru TERAPKAN.

## Skrip runbook (di luar repo, folder `~/runbook_k142`)

`regresi_v2.sh`, `pracek_c1.sh`, `pasca_c1.sh`, `migrate_c1_a2.sh`, `restart_bench.sh`, `verifikasi_pasca_restart.sh`, `cek_c4_sebelum_migrate.sh`, `patch_c4_json_controller.py`.
