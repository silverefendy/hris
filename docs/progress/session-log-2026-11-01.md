# Session Log: 1 November 2026 (Impor Department, Employee, dan pencocokan Raw Log)

Catatan: dipisah dari `session-log.md`, mengikuti pola `session-log-2026-10-31.md`. Hanya hitungan dan ID, tanpa data pribadi.

## Ringkasan
- 164 Department diimpor di bawah akar `PTCML - CML` (field `Department.hris_device_dept_id`). Tree View diperiksa di browser: struktur dan nama bergaris miring tampil benar.
- 4 custom field Employee dibuat: `hris_data_status`, `hris_data_note`, `hris_payroll_code`, `hris_payroll_code_alt`.
- 1.077 Employee diimpor (skrip `impor_employee2.py`, mode LAPORAN, COBA, lalu SIMPAN). Hasil: 949 `Lengkap`, 128 `Perlu Dilengkapi`, 1.074 punya Department, 979 punya `hris_payroll_code` (semua unik). Backup sebelum SIMPAN: 18:27 WIB.
- 4.487 baris HRIS Raw Log dicocokkan ulang (skrip `rematch_rawlog.py`, mode LAPORAN, COBA, lalu SIMPAN). Hasil: `Menunggu` 5.245, `Tidak Cocok` 110 (satu ID yang ditahan). Backup sebelum SIMPAN: 21:04 WIB.

## Temuan
- Status Raw Log ditetapkan saat baris dibuat (`before_validate`, hanya `is_new()`). Mengimpor Employee tidak mengubah baris lama.
- Tombol "Cocokkan Ulang" disebut di rangkuman sesi sebelumnya, tetapi **belum pernah dibuat**. Penelusuran kode hanya menemukan `match_employee` per dokumen. Itu rencana, bukan fitur.
- Status akhir setelah cocok adalah `Menunggu` (terhubung ke Employee, menunggu review HR), bukan "Cocok".
- Mengubah `employee` pada Raw Log lama wajib `change_reason` dan role HR Admin, HRIS Manager, atau System Manager. Pencocokan ulang memakai `doc.save()` dengan alasan "Pencocokan ulang setelah impor Employee" (4.487 baris).
- Alur Raw Log ke Working Hour (dibaca dari kode): hitung per Employee per hari lewat `compute_day`, dipicu manual lewat `recalculate_working_hours` (tanggal sampai paling lambat kemarin), hanya memakai log berstatus Menunggu, Disetujui, atau Terkirim. Hasil di `HRIS Working Hour`, kunci `unique_key`.
- `get_schedule_for_date` mencari jadwal dari Shift Assignment, lalu Rotasi grup, lalu Jadwal Mingguan grup. Employee tanpa grup dan tanpa Shift Assignment mendapat sumber "Tidak ada".
- `hooks.py` tidak punya `scheduler_events` aktif. Tidak ada hitung otomatis terjadwal.

## Kendala dan pelajaran
- Saya (Claude) sempat menyebut tombol Cocokkan Ulang sudah ada, berdasarkan rangkuman. Screenshot membuktikan sebaliknya. Pelajaran: buktikan fitur dari kode sebelum menjadikannya langkah.
- Tampilan terminal saat paste heredoc berantakan; yang menentukan adalah `py_compile`, jumlah baris, dan hasil LAPORAN/COBA.
- Scrollback terminal yang berisi perintah lama bisa terbaca seperti dijalankan dua kali; stempel waktu backup membedakannya.

## Belum
- Grup atau Shift Assignment untuk 66 Employee yang punya punch (prasyarat hitung Working Hour); isi `working_hour.py` baris 120 sampai 302 belum dibaca.
- Verifikasi HRD atas 128 Employee `Perlu Dilengkapi`, termasuk 54 resign-masih-punch.
- Cek browser form Employee (4 field baru).
- ID ditahan (menunggu KTP), ID 12182 (masuk 2026-11-04), 13 aktif-gaji tanpa ID mesin.
- Custom field Department dan Employee belum masuk repo (patch atau fixtures).
- Tombol Cocokkan Ulang di Konsol Mesin (perlu rancangan).
- Hapus berkas sementara di `/home/it/import` setelah semua selesai.

## Sesi malam 1 November 2026: grup, uji hitung, penandaan

Selesai:
- Grup `Security Malam` dibuat; `hris_employee_group` terisi untuk 65 Employee (51 `Lapangan Harian`, 14 `Security Malam`), K-83.
- `calculate_working_hour` diuji pada data nyata (telat, lembur, satu punch, hanya pulang, Sabtu, Minggu, hari tanpa punch, shift lewat tengah malam), semuanya dengan rollback; angka sesuai hitungan manual.
- Penandaan tinjau dirapikan (K-84) dan lembur hanya dihitung bila Hadir (K-85); dua commit di-push.
- Raw Log: 5.245 baris terhubung ke Employee; 110 baris (satu ID tanpa Employee) berstatus Tidak Cocok.

Temuan:
- Mesin mengirim punch bergerombol 4 sampai 6 kali dalam hitungan detik; sebelum K-84 setiap hari ikut antrean tinjau.
- Punch masuk security malam nyata sekitar 18:30 sampai 19:30 dan pulang sekitar 06:00 sampai 07:59, berbeda dari shift sistem 20:00 sampai 08:00.
- Nama Department memuat kode dan awalan; pencocokan grup memakai akhiran nama.
- Hari kerja biasa tanpa punch tidak ditandai tinjau (status Tidak Hadir cukup sebagai penyaring).

Tertunda:
- Jam kerja resmi security (HRD) lalu ubah form Shift.
- Restart worker lalu uji hitung ulang dari UI.
- Keputusan untuk satu ID tanpa Employee (110 punch).
- Grup untuk Employee selain 65 yang sudah terisi (jalur mesin lain belum ditarik).
- Rancangan tombol Cocokkan Ulang di Konsol Mesin.
- Pindahkan K-78 sampai K-85 ke tabel README.md bila disetujui.

## Sesi lanjutan 1 sampai 2 November 2026: tombol Cocokkan Ulang

Selesai:
- Tombol Cocokkan Ulang di list view Raw Log dengan Cek Dulu per ID, penyaring ID dan rentang tanggal (K-87); 110 punch satu ID yang baru dibuat Employee-nya sudah terhubung; Raw Log kini semuanya berstatus Menunggu.
- Jam kerja security malam tetap 20:00 sampai 08:00 tanpa toleransi khusus (K-86).

Temuan:
- Raw Log menuntut `change_reason` yang baru saat `employee` diubah; alasan yang sama dengan sebelumnya ditolak. Alasan Cocokkan Ulang kini memuat tanggal dan jam.
- Label "ID Mesin" menyesatkan karena berarti ID karyawan di mesin, bukan nama mesin; label diganti.

Tertunda:
- Grup untuk Employee selain 65 yang sudah terisi.
- Restart worker lalu uji hitung ulang Working Hour dari UI.
- Pindahkan K-78 sampai K-87 ke tabel README.md bila disetujui.

## Sesi lanjutan 2 November 2026: custom field masuk repo

Selesai:
- Inventaris baca-saja: dari 31 Custom Field Employee dan Department, 7 milik HRIS; sisanya milik HRMS. Tidak ada `fixtures`, `install.py` baru membuat 2 field (K-88).
- `install.py` dilengkapi: 6 Custom Field Employee, 1 Custom Field Department, 4 Property Setter Employee, idempoten, server tidak ditimpa (076e4b7).
- Terbukti: definisi kode identik dengan server, jumlah Custom Field dan Property Setter tidak berubah.

- Pemasangan dari nol dan `after_migrate` terbukti di site uji kosong (dihapus setelah uji).

Temuan:
- `attendance_device_id` bukan Custom Field, melainkan field standar HRMS.
- 4 Property Setter Employee sebelumnya hanya ada di server (dibuat 27 Oktober), tidak di repo.
- K-87 menulis "teruji di UI" padahal hanya versi awal yang diklik; sudah dikoreksi di catatan.

Tertunda:
- Uji UI dialog Cocokkan Ulang versi terakhir.
- Grup untuk Employee ID 11356 dan Employee selain 65.
- Restart worker lalu uji hitung ulang Working Hour dari UI.
- Info potongan pulang awal security (K-86) ke HRD.
- Pindahkan K-78 sampai K-88 ke tabel README.md bila disetujui.
