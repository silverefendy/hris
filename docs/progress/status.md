# Status Proyek

Diperbarui: 29 Oktober 2026 (siang)

## Kondisi terkini
- App `hris` terpasang di site kerja (Frappe 16.53.0, ERPNext 16.52.1, HRMS 16.52.0).
- Modul HRIS Attendance berisi DocType terpasang dan teruji: `HRIS Device`, `HRIS Raw Log`, `HRIS Shift`, `HRIS Employee Group` (+ tabel anak jadwal mingguan), `HRIS Holiday`, `HRIS Shift Rotation` (+ tabel anak pola), dan `HRIS Shift Assignment`. Custom Field dan hook validasi di `Employee` untuk grup karyawan (`hris_employee_group`).
- Service `services/shift_schedule.py` menjawab "karyawan X pada tanggal Y masuk shift apa" (K-33). Belum dipanggil modul lain; pemakai pertama nanti modul working hour.
- Tab "Audit Trail HRIS" ada di semua DocType HRIS; API `get_audit_trail` membaca perubahan field biasa dan tabel anak, teruji di v16.
- Arah arsitektur: HRIS mandiri; dari HRMS/ERPNext hanya `Employee` dan `Company` (K-18). Bridge hanya arah HRIS ke ERPNext, ditunda (K-19).
- `Department` memakai master ERPNext (K-29). Penomoran tanpa hash dengan YYMM (K-30).
- Zona waktu site kerja: Asia/Jakarta (K-28).
- Belum ada koneksi ke mesin; jalur data diparkir. Log hanya bisa masuk manual atau lewat skrip.
- Site kerja belum production dan belum punya karyawan Active; uji otomatis membuat karyawan sementara lalu menghapusnya.
- Data di site (cek 29 Okt): 1 Company, 4 HRIS Shift (Lapangan Senin - Kamis, Lapangan Sabtu, Lapangan Jumat, Malam lintas tengah malam), 2 HRIS Employee Group, 1 HRIS Shift Rotation, 1 HRIS Holiday, 0 Employee, 0 Shift Assignment. Sebagian adalah sisa uji (lihat Tertunda).
- Data contoh `ZZ-UJI` (4 karyawan, 1 rotasi, 1 grup rotasi, 2 Shift Assignment dari uji browser) dibuat lewat skrip lalu dihapus; pemeriksaan sisa di site `erp.ciptamebel.co.id` (29 Okt, skrip baca-saja): semua 0, total Employee 0, total Shift Assignment 0.
- Jadwal mingguan grup nyata `Lapangan Harian` (dari keluaran skrip 29 Okt): Senin sampai Kamis shift `Lapangan Senin - Kamis`, Jumat shift `Lapangan Jumat`, Sabtu shift `Lapangan Sabtu`, dan Minggu shift `Malam` (wajib). Baris Minggu hanya percobaan dan akan disempurnakan dengan aturan yang berlaku.
- Rancangan working hour disetujui (K-35 sampai K-39); belum ada kode.
- Kode terbaru sudah di-push ke `origin main` (fd8b082 rotasi, 27947d5 tipe jadwal grup, 4fcb41b Shift Assignment dan service jadwal, efd88fa perbaikan Employee Group dan penguncian rotasi).

## Selesai
| Item | Keterangan |
|---|---|
| Struktur modul, penamaan, enam role, `required_apps`, instal | Sesi 27 Okt (aa6c418, 853d504) |
| Analisis repo lama | `ANALISIS_REPO_LAMA.md` dan `ANALISIS_REPO_LAMA_TAMBAHAN.md` |
| Keputusan K-18 sampai K-39 | Lihat `decisions/README.md` |
| `HRIS Device` | 16 field, serial wajib dan unik, field koneksi, validasi IP/port, aturan Pull di controller |
| `HRIS Raw Log` | 25 field, nama anti-duplikat, pencocokan Employee, alasan ubah wajib, status tinjauan |
| `HRIS Shift` | Jam mulai/selesai, lintas tengah malam, durasi, toleransi, jendela, istirahat; detik dibulatkan ke menit |
| `HRIS Employee Group` | Jenis Jadwal (Jadwal Mingguan atau Rotasi), tanggal mulai rotasi, jadwal mingguan (tabel anak), department opsional, filter shift per company. Section form dirapikan (efd88fa): `schedule_type_section` dan `weekly_section`; section jadwal mingguan tersembunyi pada tipe Rotasi |
| `HRIS Holiday` | Jenis libur, centang "Berlaku untuk Semua Company", cegah tanggal dobel, penomoran `HOL-YYMM-NNNN` |
| `HRIS Shift Rotation` | Pola siklus per hari (shift atau libur), panjang siklus otomatis, pola dikunci bila dipakai grup (K-31), tidak bisa dinonaktifkan selama dipakai grup aktif (K-34) |
| `HRIS Shift Assignment` | Penimpaan jadwal per karyawan per rentang, alasan wajib, nonaktif sebagai pembatalan, anti tumpang tindih (K-32) |
| Service `shift_schedule` | `get_schedule_for_date` dan `get_employee_schedule` (whitelisted, maksimal 62 hari); urutan Assignment, Rotasi, Mingguan (K-33) |
| Audit trail semua DocType HRIS | Tab di form; teruji skrip dan browser |
| Uji skrip Shift Assignment dan jadwal | 20 pemeriksaan lolos (rotasi, mingguan, assignment, 4 penolakan, libur, audit), di-rollback |
| Perbaikan temuan pembacaan kode (efd88fa) | Teruji skrip konsol dan browser, lihat bagian Temuan |
| Zona waktu | Asia/Jakarta |
| Data awal contoh `ZZ-UJI` (29 Okt) | Skrip pembuat dan pembersih lolos. Jadwal 7 hari (29 Okt sampai 4 Nov) sesuai harapan: grup mingguan bersumber `Jadwal Mingguan`; grup rotasi (Malam, Malam, Libur, Libur mulai 29 Okt) bersumber `Rotasi` dengan shift Malam pada 29, 30 Okt, 2, 3 Nov dan libur pada 31 Okt, 1 Nov, 4 Nov |
| Uji browser Shift Assignment (29 Okt) | Langkah 1 sampai 7 lolos: simpan (`SAS-2610-0001` dan `SAS-2610-0002`, karyawan `HR-EMP-00001`); tumpang tindih ditolak dengan pesan menyebut assignment yang bentrok; alasan kosong ditolak (pesan field wajib); tanggal sampai sebelum tanggal dari ditolak; nonaktif lalu simpan ulang berhasil; field "Dipinjam untuk Grup" tersimpan; tab Audit Trail mencatat pembuatan dokumen, Aktif 1 menjadi 0, dan pengisian "Dipinjam untuk Grup" |
| Pembersihan data contoh dan pemeriksaan sisa | Skrip pembersih menghapus 2 Shift Assignment dan 4 Employee; skrip baca-saja `hris_check.py` memastikan semua sisa 0 |
| Server di `da94503` | Efendy sudah `git pull origin main` (29 Okt) |
| Rancangan working hour | K-35 sampai K-39 disetujui Efendy (29 Okt); lihat `decisions/README.md` |

## Belum teruji
- Pemanggilan `get_employee_schedule` dari konsol browser (belum dilaporkan); dengan karyawan contoh lewat skrip sudah lolos.
- Rotasi dengan shift lintas tengah malam pada data nyata (security). Jadwal rotasi shift Malam sudah teruji dengan karyawan contoh; perhitungan jam kerja belum ada.
- `shift_schedule` dengan karyawan dan grup nyata. Dengan karyawan contoh sudah teruji lewat skrip.
- Pencocokan Employee dengan karyawan nyata.
- Pengguna non-editor (Operator): penguncian form.
- Log berstatus Terkirim terkunci di form.
- Hook validasi grup di `Employee` dengan data karyawan nyata.

## Temuan dari pembacaan kode (28 Okt) dan penyelesaiannya (29 Okt)
Dicek dulu lewat skrip baca-saja (grep dan konsol), baru diperbaiki dengan persetujuan Efendy.

| # | Temuan | Hasil cek | Penyelesaian |
|---|---|---|---|
| 1 | `hris_employee_group.json` memakai fieldname `schedule_section` dua kali | Terbukti di JSON, meta Frappe, dan `tabDocField`; hanya di Employee Group. Label section kedua menimpa yang pertama, sehingga "Jenis Jadwal" tidak tampil | Selesai (efd88fa): diganti `schedule_type_section` dan `weekly_section`, urutan dirapikan |
| 2 | Deskripsi `weekly_schedule` usang soal rotasi | Terbukti | Selesai (efd88fa) |
| 3 | Dua pencarian shift mingguan | `get_shift_for_weekday` tanpa pemanggil | Selesai (efd88fa): fungsi dihapus. Cabang rentang melewati Minggu di `_weekly_row` (service) dibiarkan; tidak terjangkau dan tidak berbahaya |
| 4 | Service tidak mengecek rotasi nonaktif | Tidak ada data yang terkena; controller rotasi ternyata tidak mengunci status Aktif | Selesai (efd88fa) lewat K-34; service tidak diubah |

Temuan baru dari pengecekan: `HRIS Shift` belum punya kunci nonaktif maupun kunci perubahan jam. Karena hasil working hour menyimpan salinan jam shift (K-35), riwayat working hour tidak terpengaruh perubahan shift; kunci nonaktif shift yang dipakai masih belum diputuskan.

## Tertunda
| Item | Catatan |
|---|---|
| Pembersihan sisa uji (manual) | Holiday "Merdeka" bernomor hash lama (input ulang agar bernomor `HOL-YYMM-NNNN`), grup "Uji Rotasi", rotasi "Rotasi Baru". Urutan hapus: grup, rotasi, Holiday |
| Baris Minggu di grup `Lapangan Harian` | Hanya percobaan; disempurnakan nanti dengan aturan yang berlaku |
| Penomoran setelah uji | Counter `HR-EMP-` kembali ke 0 setelah data contoh dihapus (diduga karena Frappe menurunkan counter saat dokumen nomor terakhir dihapus; belum diverifikasi di kode Frappe). Penomoran `SAS` tidak tampil sebagai baris di `tabSeries`; penyebabnya belum diketahui dan tidak ada tindakan yang diminta |
| Working hour: field baru di `HRIS Shift` | Akhir masuk, awal pulang, ukuran blok potongan, jam dipotong per blok (K-36, K-37). Dicek dulu lewat skrip baca-saja: nama dan satuan field jendela yang ada dan nilai toleransi pada 4 shift nyata. Nilai awal Malam perlu disesuaikan (480 menit, lihat K-36) |
| Working hour: punch tidak lengkap | Ditunda atas permintaan Efendy |
| Report "HRIS Audit Trail" | Ditunda atas permintaan Efendy |
| Jalur data mesin | Cek menu ADMS dan model/firmware mesin lebih dulu |
| Pemetaan `verify_mode` | Menunggu jalur data dan uji mesin |
| Role `HRIS Employee Admin` | Disetujui (K-27), belum dibuat |
| CI | Pemicu `ci.yml` diubah ke `main` (K-15), belum diterapkan |
| Lisensi final | `license.txt` masih placeholder; MIT sementara |
| Pre-commit | Konfigurasi ada, hook git belum aktif |
| Navigasi | Sidebar modul dan Dock menunggu keputusan |
| Judul app | "HRIS CML" masih di README, `hooks.py`, `pyproject.toml` |
| Isu ikon desk | Diparkir (lihat `operations/environment.md`) |
| `docs/architecture/attendance-flow.md` | Belum memuat rancangan working hour (K-35 sampai K-39) |

## Langkah berikutnya
1. Skrip baca-saja untuk memeriksa field jendela dan toleransi di `HRIS Shift` dan nilai pada 4 shift nyata.
2. Berdasarkan hasil cek: skrip penambahan field di `HRIS Shift` (setelah penjelasan risiko dan konfirmasi), lalu service perhitungan working hour dan DocType hasilnya.
3. Hapus manual tiga sisa uji dan input ulang libur 17 Agustus 2027.
4. Cek menu ADMS, model, dan firmware pada mesin (penentu jalur data).
5. Terapkan CI ke `main`; putuskan lisensi dan nama merek.
6. Opsional: Report "HRIS Audit Trail".
