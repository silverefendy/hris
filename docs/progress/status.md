# Status Proyek

Diperbarui: 28 Oktober 2026 (malam)

## Kondisi terkini
- App `hris` terpasang di site kerja (Frappe 16.53.0, ERPNext 16.52.1, HRMS 16.52.0).
- Modul HRIS Attendance berisi DocType terpasang dan teruji skrip: `HRIS Device`, `HRIS Raw Log`, `HRIS Shift`, `HRIS Employee Group` (+ tabel anak jadwal mingguan), `HRIS Holiday`, `HRIS Shift Rotation` (+ tabel anak pola), dan `HRIS Shift Assignment`. Custom Field dan hook validasi di `Employee` untuk grup karyawan (`hris_employee_group`).
- Service `services/shift_schedule.py` menjawab "karyawan X pada tanggal Y masuk shift apa" (K-33). Belum dipanggil modul lain; pemakai pertama nanti modul working hour.
- Tab "Audit Trail HRIS" ada di semua DocType HRIS; API `get_audit_trail` membaca perubahan field biasa dan tabel anak, teruji di v16.
- Arah arsitektur: HRIS mandiri; dari HRMS/ERPNext hanya `Employee` dan `Company` (K-18). Bridge hanya arah HRIS ke ERPNext, ditunda (K-19).
- `Department` memakai master ERPNext (K-29). Penomoran tanpa hash dengan YYMM (K-30).
- Zona waktu site kerja: Asia/Jakarta (K-28).
- Belum ada koneksi ke mesin; jalur data diparkir. Log hanya bisa masuk manual atau lewat skrip.
- Site kerja belum production dan belum punya karyawan Active; uji otomatis membuat karyawan sementara lalu rollback.
- Kode terbaru sudah di-push ke `origin main` (fd8b082 rotasi, 27947d5 tipe jadwal grup, 4fcb41b Shift Assignment dan service jadwal).

## Selesai
| Item | Keterangan |
|---|---|
| Struktur modul, penamaan, enam role, `required_apps`, instal | Sesi 27 Okt (aa6c418, 853d504) |
| Analisis repo lama | `ANALISIS_REPO_LAMA.md` dan `ANALISIS_REPO_LAMA_TAMBAHAN.md` |
| Keputusan K-18 sampai K-33 | Lihat `decisions/README.md` |
| `HRIS Device` | 16 field, serial wajib dan unik, field koneksi, validasi IP/port, aturan Pull di controller |
| `HRIS Raw Log` | 25 field, nama anti-duplikat, pencocokan Employee, alasan ubah wajib, status tinjauan |
| `HRIS Shift` | Jam mulai/selesai, lintas tengah malam, durasi, toleransi, jendela, istirahat; detik dibulatkan ke menit |
| `HRIS Employee Group` | Jenis Jadwal (Jadwal Mingguan atau Rotasi), tanggal mulai rotasi, jadwal mingguan (tabel anak), department opsional, filter shift per company |
| `HRIS Holiday` | Jenis libur, centang "Berlaku untuk Semua Company", cegah tanggal dobel, penomoran `HOL-YYMM-NNNN` |
| `HRIS Shift Rotation` | Pola siklus per hari (shift atau libur), panjang siklus otomatis, pola dikunci bila dipakai grup (K-31) |
| `HRIS Shift Assignment` | Penimpaan jadwal per karyawan per rentang, alasan wajib, nonaktif sebagai pembatalan, anti tumpang tindih (K-32) |
| Service `shift_schedule` | `get_schedule_for_date` dan `get_employee_schedule` (whitelisted, maksimal 62 hari); urutan Assignment, Rotasi, Mingguan (K-33) |
| Audit trail semua DocType HRIS | Tab di form; teruji skrip dan browser |
| Uji skrip Shift Assignment dan jadwal | 20 pemeriksaan lolos (rotasi, mingguan, assignment, 4 penolakan, libur, audit), di-rollback |
| Zona waktu | Asia/Jakarta |

## Belum teruji
- Form `HRIS Shift Assignment` di browser (8 langkah uji; ditunda sampai ada karyawan Active).
- Rotasi dengan shift lintas tengah malam pada data nyata (security).
- `shift_schedule` dengan karyawan dan grup nyata, serta pemanggilan `get_employee_schedule` dari browser.
- Pencocokan Employee dengan karyawan nyata.
- Pengguna non-editor (Operator): penguncian form.
- Log berstatus Terkirim terkunci di form.
- Hook validasi grup di `Employee` dengan data karyawan nyata.

## Temuan dari pembacaan kode (28 Okt, belum diuji atau diperbaiki)
| # | Temuan | Prioritas |
|---|---|---|
| 1 | `hris_employee_group.json` memakai nama field `schedule_section` dua kali (dua Section Break, dua entri di `field_order`). Migrate dan uji lolos, tetapi nama ganda berisiko. Memperbaikinya berarti mengubah struktur DocType berjalan, jadi perlu konfirmasi dulu. | Sedang |
| 2 | Deskripsi field `weekly_schedule` masih menyebut grup dengan rotasi "diatur lewat Shift Assignment"; tidak sesuai K-31. | Rendah |
| 3 | Pencarian shift mingguan ada dua: `get_shift_for_weekday` di controller grup dan `_weekly_row` di service. Cabang rentang melewati hari Minggu di service tidak terjangkau karena controller menolaknya (harus dua baris). Belum dicek apakah `get_shift_for_weekday` dipakai di tempat lain. | Rendah |
| 4 | Service tidak mengecek rotasi nonaktif saat menghitung (hanya grup nonaktif); pengecekan rotasi aktif hanya saat grup disimpan. | Rendah, perlu keputusan |

## Tertunda
| Item | Catatan |
|---|---|
| Data awal contoh (karyawan, shift, grup, rotasi security, libur) | Menunggu keputusan: lewat skrip atau input manual |
| Report "HRIS Audit Trail" | Ditunda atas permintaan Efendy |
| Jalur data mesin | Cek menu ADMS dan model/firmware mesin lebih dulu |
| Pemetaan `verify_mode` | Menunggu jalur data dan uji mesin |
| CI | Pemicu `ci.yml` diubah ke `main` (K-15), belum diterapkan |
| Lisensi final | `license.txt` masih placeholder; MIT sementara |
| Pre-commit | Konfigurasi ada, hook git belum aktif |
| Navigasi | Sidebar modul dan Dock menunggu keputusan |
| Judul app | "HRIS CML" masih di README, `hooks.py`, `pyproject.toml` |
| Isu ikon desk | Diparkir (lihat `operations/environment.md`) |

## Langkah berikutnya
1. Data awal contoh (karyawan, shift, grup, rotasi security, libur), lalu uji browser Shift Assignment.
2. Diskusi rancangan working hour: jam kerja dari Raw Log dan jadwal, jendela tempel, punch ganda, telat/lembur, shift lintas tengah malam. Tanpa kode dulu.
3. Putuskan temuan 1 sampai 4 di atas (perbaikan kecil, satu skrip).
4. Cek menu ADMS, model, dan firmware pada mesin (penentu jalur data).
5. Terapkan CI ke `main`; putuskan lisensi dan nama merek.
6. Opsional: Report "HRIS Audit Trail".
