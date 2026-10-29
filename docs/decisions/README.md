# Daftar Keputusan

Diperbarui: 29 Oktober 2026 (siang)

## Sudah diputuskan
| No | Keputusan | Tanggal | Status |
|---|---|---|---|
| K-01 | Satu app `hris` untuk semua; lima modul terpisah (Core, Attendance, Employee Data, Payroll, Reports) | 2026-10-27 | Diterapkan |
| K-02 | Nama teknis `hris`; hindari `hrms`; nama merek menyusul | 2026-10-27 | Aktif |
| K-03 | `required_apps`: frappe, erpnext, hrms | 2026-10-27 | Diterapkan (perlu ditinjau ulang, lihat K-18) |
| K-04 | Aturan reuse HRMS: ada dan lengkap dipakai; tidak ada kustom; ada tapi kurang bridge + custom (data sinkron) | 2026-10-27 | Diganti sebagian oleh K-18 (absensi, shift, payroll) |
| K-05 | Komponen gaji custom, dikelola DocType HRIS sendiri | 2026-10-27 | Aktif |
| K-06 | Log absensi lebih lengkap dari HRMS (istirahat, pulang cepat, dll.); praktik "pinjam karyawan" antar bagian harus didukung | 2026-10-27 | Aktif |
| K-07 | Device diinput manual lewat form, tanpa hardcode | 2026-10-27 | Diterapkan (HRIS Device) |
| K-08 | Kode lama (`hr_app`, `hr_payroll`) ditulis ulang; hanya referensi, patch lama tidak dibawa | 2026-10-27 | Aktif |
| K-09 | Layout standar Frappe (bukan `src/`); services dan integrations sebagai sub-package dalam modul | 2026-10-27 | Aktif |
| K-10 | Semua DocType, child table, dan role milik app wajib memuat awalan `HRIS ` | 2026-10-27 | Aktif |
| K-11 | Enam role: HRIS Attendance Operator, HRIS Attendance Supervisor, HRIS HR Admin, HRIS Payroll User, HRIS Payroll Admin, HRIS Manager | 2026-10-27 | Diterapkan |
| K-12 | Modul bawaan `hris_cml` dihapus | 2026-10-27 | Diterapkan (853d504) |
| K-13 | HRIS Core tahap awal hanya role; `HRIS Settings` menyusul bersama kebutuhan nyata pertama | 2026-10-27 | Aktif |
| K-14 | Lisensi MIT sementara | 2026-10-27 | Sementara |
| K-15 | Pemicu CI diubah dari `version-16` ke `main` | 2026-10-27 | Belum diterapkan |
| K-16 | Isu ikon desk bawaan ERPNext dibiarkan/diparkir | 2026-10-27 | Diparkir |
| K-17 | Alur git: Efendy push ke `origin main`; Claude hanya push `.md` setelah Efendy `git pull origin main` | 2026-10-27 | Aktif |
| K-18 | HRIS mandiri: dari HRMS/ERPNext hanya `Employee` dan `Company`; shift, attendance, payroll, laporan dibuat di HRIS ([0002](0002-hris-mandiri-dan-bridge-keluar.md)) | 2026-10-28 | Aktif |
| K-19 | Bridge ke ERPNext/HRMS hanya arah HRIS ke ERPNext (mapping); integrasi langsung ke akun payroll/accounting ditunda | 2026-10-28 | Aktif |
| K-20 | Dokumen karyawan (perjanjian kerja, foto, KTP) dikelola di sisi HRIS; rancangan di modul Employee Data | 2026-10-28 | Aktif |
| K-21 | Log mentah satu baris per log; ditinjau HRD per baris lewat list view dengan filter dan aksi massal; tanpa DocType review tambahan | 2026-10-28 | Diterapkan |
| K-22 | ID karyawan sama di semua mesin; pencocokan lewat `Employee.attendance_device_id` (+ company, status Active) | 2026-10-28 | Diterapkan |
| K-23 | Status masuk/keluar dari mesin diabaikan; HRIS menentukan masuk/keluar, shift, dan waktu kerja | 2026-10-28 | Aktif (menunggu modul working hour) |
| K-24 | Punch ganda otomatis: masuk = tempelan paling awal, pulang = paling akhir; log lain diabaikan otomatis (tetap tersimpan); batas hari kerja ditentukan modul working hour | 2026-10-28 | Aktif (menunggu modul working hour) |
| K-25 | Data sumber log hanya boleh diubah HRIS HR Admin, HRIS Manager, atau System Manager dengan alasan baru setiap kali; audit trail dari Version, tab "Audit Trail HRIS" di form (report menyusul) | 2026-10-28 | Diterapkan |
| K-26 | `HRIS Device` lengkap: mode koneksi (Pull IP / Push ADMS), IP, port (default 4370), model, firmware; serial wajib dan unik; Comm Key per mesin | 2026-10-28 | Diterapkan |
| K-27 | Role tambahan untuk input data karyawan (nama usulan: `HRIS Employee Admin`) | 2026-10-28 | Disetujui, belum dibuat |
| K-28 | Zona waktu site kerja: Asia/Jakarta (WIB), agar audit trail berwaktu WIB | 2026-10-28 | Diterapkan |
| K-29 | `Department` tetap master ERPNext (modul Setup), dipakai lewat `Employee.department`; HRIS tidak membuat Department sendiri; field `department` di HRIS Employee Group opsional. Audit tab dipasang di semua DocType HRIS (Raw Log tetap). HRIS Holiday punya centang "Berlaku untuk Semua Company" | 2026-10-28 | Diterapkan |
| K-30 | Tidak ada penomoran hash di DocType HRIS; penomoran memuat YYMM dengan format `PREFIX-YYMM-NNNN`. Holiday `HOL-YYMM-NNNN` (4 digit), YYMM dari tanggal dibuat; data lama bernomor hash dihapus manual, tidak di-rename. Pengecualian: HRIS Raw Log (nama = kunci anti-duplikat), DocType bernama dari field nama, dan tabel anak | 2026-10-28 | Diterapkan (Holiday, 22126c0) |
| K-31 | Rotasi shift: `HRIS Shift Rotation` (nama dari field `rotation_name`) dengan tabel anak `HRIS Shift Rotation Day`; satu baris = satu hari siklus, boleh hari libur, minimal satu hari berisi shift, panjang siklus dihitung otomatis. Hari ke-n = (tanggal - tanggal mulai) mod panjang siklus. `HRIS Employee Group` memilih salah satu: Jadwal Mingguan atau Rotasi (tidak bercampur). Tipe Rotasi mewajibkan rotasi dan Tanggal Mulai Rotasi (hari ke-1) serta mengosongkan jadwal mingguan; tipe Jadwal Mingguan mengosongkan rotasi. Pola dan company rotasi yang sudah dipakai grup dikunci: buat rotasi baru lalu pindahkan grupnya | 2026-10-28 | Diterapkan (fd8b082, 27947d5) |
| K-32 | `HRIS Shift Assignment` (`SAS-YYMM-NNNN`, YYMM dari tanggal dibuat) untuk menimpa jadwal per karyawan per rentang tanggal (tukar shift, pinjam karyawan). Isi: karyawan, tanggal dari/sampai, shift, alasan wajib, centang Aktif, field opsional "Dipinjam untuk Grup". Tanpa approval; dibuat HRD dan tercatat di audit trail. Pembatalan dengan mematikan centang Aktif (HR Admin tanpa hak hapus, riwayat tetap ada). Validasi: tanggal sampai tidak sebelum dari; karyawan Active; shift aktif dan satu company dengan karyawan; tidak tumpang tindih dengan Assignment aktif lain milik karyawan yang sama. `company` dan nama karyawan diisi dari server | 2026-10-28 | Diterapkan (4fcb41b), teruji skrip dan browser (29 Okt) |
| K-33 | Urutan penentuan shift karyawan pada satu tanggal (service `shift_schedule`): 1) Shift Assignment aktif, 2) Rotasi grup, 3) Jadwal Mingguan grup, 4) tidak ada (bukan hari kerja). Hari libur (HRIS Holiday) ditandai terpisah: dari Assignment dianggap masuk kerja, dari rotasi atau jadwal mingguan dianggap tidak masuk. Jadwal dihitung saat dibutuhkan, tidak disimpan per hari. Sebelum tanggal mulai rotasi dianggap belum berlaku | 2026-10-28 | Diterapkan (4fcb41b), teruji skrip |
| K-34 | Rotasi tidak boleh dinonaktifkan selama masih dipakai grup aktif: `HRIS Shift Rotation` menolak perubahan Aktif menjadi nonaktif dan menyebut nama grup yang memakainya; grup nonaktif tidak menghalangi. Dengan begitu grup aktif tidak pernah menunjuk rotasi nonaktif, sehingga service `shift_schedule` tidak perlu mengecek status rotasi | 2026-10-29 | Diterapkan (efd88fa), teruji skrip dan browser |
| K-35 | Working hour: satu baris hasil per karyawan per hari kerja. Hari kerja shift lintas tengah malam dihitung ke tanggal shift dimulai. Masuk = punch pertama dalam jendela masuk, pulang = punch terakhir dalam jendela pulang (melanjutkan K-24). Detik pada punch dibuang (pembulatan ke bawah ke menit). Hasil disimpan beserta salinan jam shift dan aturan yang dipakai saat dihitung, sehingga perubahan shift di kemudian hari tidak mengubah riwayat. Hitung ulang lewat tombol per karyawan dan periode; hitung otomatis menyusul setelah jalur data mesin jelas | 2026-10-29 | Rancangan disetujui, belum dikodekan |
| K-36 | Jendela punch memiliki empat batas: awal masuk (sudah ada, contoh 120 menit sebelum jam mulai), akhir masuk ("batas terlambat", baru), awal pulang ("batas pulang cepat", baru), akhir pulang (sudah ada, contoh 240 menit setelah jam selesai, batas maksimal lembur). Validasi: akhir masuk harus lebih awal dari awal pulang (tidak boleh tumpang tindih). Nilai awal untuk dua batas baru: 240 menit pada shift nyata; atasan boleh mengubah bila ketentuan berubah. Catatan: pada shift berdurasi 480 menit (Malam 22:00 sampai 06:00), 240 + 240 menit bertemu di titik yang sama sehingga nilai awal Malam perlu disesuaikan saat penerapan | 2026-10-29 | Rancangan disetujui, belum dikodekan |
| K-37 | Potongan telat dan pulang cepat: tanpa toleransi; telat dihitung dari jam mulai shift ke punch masuk, pulang cepat dari punch pulang ke jam selesai; potongan = pembulatan ke atas (menit / 60) jam, kelipatan 1 jam (1 sampai 60 menit potong 1 jam, 61 sampai 120 menit potong 2 jam, dan seterusnya). Jam kerja efektif = jam kerja terjadwal (durasi shift dikurangi istirahat) dikurangi potongan telat dan pulang cepat, minimal 0; diturunkan dari jadwal, bukan dari selisih punch. Parameter (akhir masuk, awal pulang, ukuran blok potongan, jam dipotong per blok) disimpan di `HRIS Shift` (opsi A); perbedaan antar company atau shift dibedakan lewat shift | 2026-10-29 | Rancangan disetujui, belum dikodekan |
| K-38 | Lembur dicatat sebagai fakta, bukan nilai uang: menit setelah jam selesai (dibatasi akhir pulang) dan centang "ada lembur"; tanpa persetujuan; tanpa pengali. Masuk lebih awal dari jam mulai tidak dihitung lembur. Lembur dicatat terpisah dan tidak menutup potongan telat. Pada hari tanpa jadwal (libur, Minggu), jam di luar jadwal dicatat dengan penanda jenis. Pembulatan dan pengali menyusul di Payroll | 2026-10-29 | Rancangan disetujui, belum dikodekan |
| K-39 | Baris working hour menyalin grup dan departemen karyawan pada hari itu; "Dipinjam untuk Grup" (dari Shift Assignment) juga dibawa. Keduanya belum memengaruhi hitungan working hour; pengaruh pada gaji per departemen menyusul di Payroll | 2026-10-29 | Rancangan disetujui, belum dikodekan |

## Belum diputuskan
- Nama merek dan lisensi final (implikasi GPLv3 ERPNext/HRMS perlu diverifikasi).
- Jalur data mesin (ADMS/push, agen Windows via SDK, pull lewat IP); diparkir sampai menu ADMS, model, dan firmware mesin dicek.
- Working hour: punch tidak lengkap (hanya masuk atau hanya pulang, atau punch di luar jendela) dan statusnya (Hadir, Tidak Lengkap, Tidak Hadir); ditunda atas permintaan Efendy.
- Aturan lembur lanjutan (pembulatan, pengali, hari libur) dan aturan khusus shift Malam (security); keduanya menyusul bila ada aturannya.
- Nilai awal batas jendela untuk shift Malam (lihat catatan K-36).
- Pengaruh "Dipinjam untuk Grup" pada laporan, lembur, dan insentif (K-39 hanya mencatat).
- `HRIS Shift`: apakah shift nonaktif boleh bila masih dipakai grup, rotasi, atau assignment. Perubahan jam shift tidak lagi merusak hasil working hour yang sudah disimpan (K-35), tetapi tanggal lampau yang dihitung lewat `shift_schedule` tetap mengikuti jam shift terbaru.
- Cuti dan izin; insentif; komponen gaji spesifik.
- Akuntansi gaji: jurnal otomatis ke ERPNext atau cukup laporan.
- Apakah `hrms` tetap `required_apps` jika hanya Employee yang dipakai.
- Pemetaan `verify_mode` (jari/wajah) dan arti "no akun" dan "no induk" di Raw Log.
- Merek/model mesin untuk uji template wajah; prioritas 3 bulan.
- Satu atau dua bench untuk production; nasib site uji lama.
- Navigasi: Sidebar modul dan Dock (usulan), bukan Desktop Icon.

Templat keputusan rinci: [0001-template.md](0001-template.md). Keputusan rinci: [0002](0002-hris-mandiri-dan-bridge-keluar.md). Checklist DocType baru: [../development/doctype-checklist.md](../development/doctype-checklist.md).
