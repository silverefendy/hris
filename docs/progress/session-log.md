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

## 2026-10-28 (sesi lanjutan: Bagian A shift dan grup)
- Dipasang dan diuji: `HRIS Shift`, `HRIS Employee Group` (+ jadwal mingguan), `HRIS Holiday`, Custom Field dan hook validasi di `Employee`. Rename shift dan grup berhasil (ID dan nama ikut berganti).
- K-29: `Department` tetap master ERPNext (modul Setup). Holiday ditambah centang "Berlaku untuk Semua Company".
- Audit tab dipasang di semua DocType HRIS lewat JS bersama `hris_audit_trail.js` (dimuat via `app_include_js`) dan satu file JS kecil per DocType. `audit_trail.py` kini membaca tabel anak (ditambah, dihapus, diubah); struktur `Version` tabel anak terbukti bekerja di v16, di skrip uji maupun di form.
- K-30: penomoran tanpa hash dengan YYMM. Holiday `HOL-2610-0001` teruji (dua nomor berurutan, rollback). Data libur lama bernomor hash tidak di-rename; dihapus manual.
- Detik di jam shift dibulatkan ke menit (opsional; muncul hanya karena uji log audit).
- Commit: fd1c1c2 (Bagian A), 22126c0 (penomoran Holiday), 3efd73b (pembulatan detik).
- Kendala dan pelajaran:
  - Field Link Company bisa terisi otomatis dari default pengguna, sehingga "Company kosong" tidak boleh dipakai sebagai arti "semua company". Dipakai centang eksplisit; data lama dirapikan lewat skrip satu kali.
  - Perapian data lewat `set_value` tidak tercatat di audit trail; wajar untuk master data, bukan untuk perubahan biasa.
  - Pemicu otomatis audit tab untuk semua DocType tidak dipakai karena bergantung event Frappe yang belum diverifikasi; dipilih satu JS kecil per DocType (lihat [development/doctype-checklist.md](../development/doctype-checklist.md)).
- Belum: Bagian B (rotasi dan Shift Assignment), data awal contoh, jalur data mesin.

## 2026-10-28 (sesi lanjutan: Bagian B rotasi dan Shift Assignment)
- Script 6 (`HRIS Shift Rotation` + tabel anak `HRIS Shift Rotation Day`, commit fd8b082) dan Script 7 (`HRIS Employee Group` memilih Jadwal Mingguan atau Rotasi, commit 27947d5) lolos. Uji browser Script 7: rotasi yang dipakai grup ditolak diubah dengan pesan yang menyebut grup; pindah ke Jadwal Mingguan tercatat di audit (Jenis Jadwal, Rotasi, Tanggal Mulai).
- Script 8 (commit 4fcb41b): `HRIS Shift Assignment` dan service `shift_schedule.py`. Pemasangan lolos (backup, migrate tanpa error). Uji otomatis 8c lolos 20 pemeriksaan: rotasi (5), jadwal mingguan (4), assignment (4), penolakan tumpang tindih, alasan kosong, tanggal terbalik, shift nonaktif, libur (2), audit (1); semua di-rollback.
- K-31 sampai K-33 dicatat (rotasi, Shift Assignment, urutan penentuan shift dan aturan libur).
- Kendala dan pelajaran:
  - Uji 8c pertama berhenti sendiri karena site belum punya Employee Active (pengaman skrip bekerja). Skrip direvisi: bila tidak ada karyawan Active, dibuat karyawan sementara (butuh Gender, tanggal lahir, tanggal bergabung, Company) lalu rollback.
  - Nama field grup di `Employee` tidak ditebak; service mencarinya dari meta lewat daftar Link field yang menunjuk `HRIS Employee Group` (hasil: `hris_employee_group`).
  - Penolakan "alasan kosong" datang dari validasi field wajib Frappe, bukan dari pesan di controller; keduanya menolak, jadi hasilnya sama.
  - File `.py` ditulis dengan spasi lalu dikonversi ke tab (gaya Frappe) dengan `sed` setelah dibuat.
- Pembacaan kode setelah push menghasilkan empat temuan kecil (lihat `progress/status.md`, bagian Temuan).
- Belum: uji browser Shift Assignment, data awal contoh, working hour, jalur data mesin.

## 2026-10-29 (sesi lanjutan: cek dan perbaikan temuan kode)
- Empat temuan pembacaan kode dicek dulu lewat skrip baca-saja (grep dan konsol) sebelum diperbaiki. Hasil: nama field `schedule_section` ganda terbukti di JSON, meta, dan `tabDocField` (hanya di Employee Group; label section kedua menimpa yang pertama); `get_shift_for_weekday` tanpa pemanggil; belum ada data yang terkena temuan 4.
- Pembacaan controller menemukan celah tambahan: `HRIS Shift Rotation` tidak mengunci status Aktif. Diputuskan K-34 (rotasi tidak boleh dinonaktifkan selama dipakai grup aktif) alih-alih menambal service.
- Perbaikan (commit efd88fa): section Employee Group diganti nama dan dirapikan, deskripsi `weekly_schedule` diperbarui, `get_shift_for_weekday` dihapus, `validate_deactivation` ditambahkan di rotasi. Backup, migrate, dan clear-cache dalam satu blok lolos; uji konsol lolos; uji browser lolos.
- Pengecekan `HRIS Shift`: belum ada kunci nonaktif maupun kunci perubahan jam; karena jadwal dihitung saat dibutuhkan, mengubah jam shift mengubah tanggal lampau. Dicatat di "Belum diputuskan".
- Pelajaran:
  - Cek dulu dengan skrip baca-saja, baru perbaiki; hasil cek mengubah rekomendasi (dari menambal service ke mengunci di rotasi).
  - Patch file `.py` dengan penggantian teks yang di-`assert` dan penulisan ulang JSON utuh lebih aman daripada penyuntingan manual; skrip berhenti bila file target punya perubahan lokal.
  - Jam OS server tampaknya UTC (`date` mencetak 23:29 saat log backup mencatat 06:29 WIB); nilai `modified` pada JSON mengikuti jam OS.
  - Mengganti nama Section Break aman karena tidak punya kolom di database.
- Keputusan: karyawan contoh dibuat lewat skrip dan dihapus otomatis setelah uji.

## 2026-10-29 (sesi lanjutan: data contoh, uji browser Assignment, rancangan working hour)
- Skrip data contoh `ZZ-UJI` (di luar repo) dijalankan: membuat rotasi, grup rotasi, dan 4 karyawan, mencetak jadwal 7 hari, lalu membersihkan. Jadwal terverifikasi: grup `Lapangan Harian` bersumber `Jadwal Mingguan`; grup rotasi bersumber `Rotasi`.
- Temuan data: jadwal mingguan `Lapangan Harian` saat itu memuat baris Minggu = shift `Malam` (wajib). Efendy menyatakan itu hanya percobaan; barisnya dihapus.
- Uji browser `HRIS Shift Assignment` langkah 1 sampai 7 lolos. Pemanggilan `get_employee_schedule` dari konsol browser belum dilaporkan.
- Pemeriksaan baca-saja setelah pembersihan: sisa `ZZ-UJI` semua 0, total Employee 0, total Shift Assignment 0.
- Koreksi catatan sebelumnya (59b0902): penomoran `HR-EMP` kembali ke 0 setelah data contoh dihapus (diduga karena Frappe menurunkan counter; belum diverifikasi di kode Frappe).
- Rancangan working hour dibahas dan disetujui (K-35 sampai K-39), kemudian direvisi.
- Pelajaran:
  - `bench console` yang dialirkan lewat pipa tidak bisa membaca input; penantian Enter dilakukan di skrip bash. Pembersih dipasang lewat `trap`.
  - Skrip uji memakai tanggal tetap, bukan tanggal sistem, karena jam OS server tampaknya UTC.
  - Perintah pemeriksaan selalu memakai `--site`; `bench console` tanpa `--site` bisa membaca site yang tidak dimaksud.

## 2026-10-29 (sesi lanjutan: HRIS Shift untuk working hour)
- Pengecekan baca-saja `HRIS Shift`; Efendy memperbarui daftar shift menjadi 8 shift. Perhitungan bentrok yang diberikan sebelumnya memakai data lama (4 shift) sehingga keliru dan dikoreksi.
- Skrip pertama (`hris_shift_run.sh`) dan kedua (`hris_shift_run2.sh`) lolos: field aturan working hour ditambah, `early_leave_limit_min` dan aturan tumpang tindih dihapus, aturan pulang direvisi (K-36), istirahat diisi, validasi baru. Commit e1cd6f7.
- Efendy mengusulkan aturan pulang baru (tanpa jendela awal pulang; minimal 60 menit setelah masuk; punch di luar batas diberi tanda untuk HRD). Aturan lembur: minimal 30 menit, kelipatan 30, dibulatkan ke bawah (K-38).
- Penamaan `WH-YYMMDD-NNNN` dengan `unique_key` (K-40); punch kurang = "Tidak Lengkap" (K-41).
- Pelajaran:
  - Jangan menghitung dari data catatan lama; ambil ulang data nyata sebelum menghitung.
  - Skrip kedua yang menyentuh file yang sama tidak boleh berhenti hanya karena file itu sudah berubah oleh skrip pertama.
  - Menghapus field dari JSON DocType tidak menghapus kolomnya di tabel.

## 2026-10-29 (sesi lanjutan: Working Hour 5a, 5b, 5c-1)
- 5a (f607a0b, f582aff): DocType `HRIS Working Hour` (72 field, `unique_key` unik di database terverifikasi) dan tab Audit Trail. Penjaga controller (K-42).
- 5b (5230691): `services/working_hour.py`; 25 pemeriksaan skrip semua OK, di-rollback. Aturan hitung K-43 dan K-44.
- 5c-1 (523d70e): `services/working_hour_batch.py`, `hris_working_hour_list.js` (baru), `hris_working_hour.js` (tombol Hitung Ulang). Rancangan disetujui Efendy: cakupan Semua, Karyawan, Department, Grup; opsi lewati baris HRD; manual dulu; batas 31 hari sampai kemarin; hanya karyawan Active; indikator wajib agar masalah tidak tersembunyi (K-45).
- Pemasangan `hris_wh_run4.sh` lolos: backup, `py_compile`, uji T1 sampai T9 semua OK, `SEMUA OK`; ping worker `long` merespons dalam 1 detik; status git sesuai harapan. Efendy commit dan push (`5230691..523d70e`).
- Dugaan teknis yang terjawab: bentuk `frappe.cache` di v16 (`RedisWrapper`), `frappe.db.savepoint` dan `rollback(save_point=...)`, antrean `long` dan worker hidup.
- Yang belum teruji: tampilan browser 5c-1 (tombol, dialog, `depends_on`) dan job background sungguhan di atas 300 karyawan-hari. Efendy memutuskan uji browser menunggu data nyata karena site belum punya karyawan Active.
- Tambahan di luar permintaan awal (disetujui lewat penerimaan skrip): hari sebelum tanggal masuk karyawan dilewati; menu "Status Hitung".
- Pelajaran:
  - Skrip uji server tidak menguji sisi browser; jangan menyebut fitur browser "teruji" sebelum dicek di browser.
  - Memanggil `run_batch` langsung tidak membuktikan antrean berjalan; ping worker hanya membuktikan worker hidup.
- Docs K-42 sampai K-45, status, session-log, data-model, dan api diperbarui dan di-push oleh Claude atas izin Efendy (29 Okt).
- Belum: 5c-2 (warna list view, Report ringkasan), data nyata, jalur data mesin, istirahat Security, pembersihan sisa uji lama.

## 2026-10-30 (jalur data mesin, Sesi 1 sampai 2B)
- Arah jalur data diputuskan (29 sampai 30 Okt): semua mesin lewat middleware seperti mesin Solution, Pull pyzk tetap diimplementasikan, satu mesin boleh lebih dari satu jalur. Rinci di [0003](../decisions/0003-jalur-data-mesin.md) (K-46 sampai K-56).
- Sesi 1: field jalur data di `HRIS Device` dan `HRIS Raw Log`, validasi IP/port wajib bersyarat. Uji console lulus.
- Sesi 2A: `punch_ingest.save_punches` dan endpoint `push_punches`. Uji console lulus.
- Sesi 2B (d773aeb): token buatan sendiri di `HRIS Attendance Settings`, `agent_auth.py`, izin role agen dicabut. Uji console lulus.
- Uji HTTP, `curl`, dan browser lulus (ringkasan di [agent-api.md](../architecture/agent-api.md)). Data uji dihapus.
- Kendala dan pelajaran:
  - Uji PowerShell pertama gagal: skrip ber-`Read-Host` ditempel ke konsol dan baris berikutnya tertelan. Solusi: file `.ps1` lewat here-string.
  - Uji kedua gagal 13 dari 13: `-Base` memakai alamat mesin absensi, bukan server ERP. Skrip versi 2 memeriksa `/api/method/ping` lebih dulu.
  - Uji ketiga 10 lulus, 4 gagal: urutan di browser tidak sesuai (saklar belum tersimpan, Allowed IPs dan rotasi belum tersimpan saat Enter ditekan). Log `hris_agent.log` menunjukkan `saklar mati` dan `diblokir`, bukan kesalahan token. Pembatas 10 kegagalan per 10 menit ikut memblokir IP PC saat uji beruntun.
  - Pemeriksaan status lewat skrip baca-saja (`agent_enabled`, prefix, `modified`) membedakan "saklar tidak tersimpan" dari "token salah".
  - Blok heredoc panjang yang ditempel kehilangan baris `cat > ... <<'EOF'`, sehingga isi Python dijalankan sebagai perintah bash. Pecah menjadi langkah pendek.
  - Token sempat tampil di chat (diketik di teks prompt `read -p`, dan ditempel di chat). Token dirotasi setelah uji.
  - Temuan teknis: `mandatory_depends_on` hanya dievaluasi di browser; `set_only_once` ditegakkan server; `modified` JSON harus dinaikkan agar `migrate` mengenali perubahan; mencabut izin dilakukan dengan menghapus entri dan menaikkan `modified`.
  - Server berjalan dengan `bench start` (tanpa nginx dan HTTPS); web dimuat ulang otomatis, worker tidak.
- Belum: Sesi 3 (Pull pyzk), Sesi 4 (agen Windows), data nyata, perbaikan kecil Settings, sinkronisasi `data-model.md` dan `api.md`.

## 2026-10-30 sampai 31 (Pull pyzk)
- Pyzk 0.9 dipasang di env bench dan `pyproject.toml` (6e36db0). Patch `normalize_allowed_ips` lulus 3 dari 3 (057251c).
- Uji koneksi ke PLTB 220 berhasil (TCP, jam mesin sama dengan WIB).
- `services/pull_device.py` dan tombol "Ambil Info dari Mesin" (00eba4d).
- Penamaan Raw Log baru, `punch_key`, `raw_log_naming.py`, dan tarikan dengan `date_from`/`date_to` (009ff78).
- Tarikan satu minggu 25 sampai 31 Okt: 2.306 baris, 66 user, tanpa duplikat. Rincian dan keputusan: [0004](../decisions/0004-pull-pyzk-dan-penamaan-raw-log.md).
- Kendala dan pelajaran:
  - Placeholder harfiah (`NAMA DEVICE`, `IP_MESIN`, `Mesin Gudang`) dijalankan dua kali sebagai nilai sungguhan. Selalu beri nilai nyata, jangan contoh yang mirip nilai sungguhan.
  - Arti `uid` ditebak salah dua kali; dibuktikan dari data bahwa nomor berputar 0 sampai 65535.
  - Console dengan loop `for` multi-baris tidak mencetak hasil; pakai file `/tmp/*.py` lalu `exec(open(...).read(), {"frappe": frappe})`.
  - Tampilan terminal saat menempel heredoc panjang berantakan karena gema layar; yang menentukan adalah `py_compile` dan uji yang berjalan.
  - Setelah `enqueue_pull` pengecekan pertama menunjukkan 0 baris, lalu diduga worker tidak aktif. Dugaan itu **keliru**: `doctor` menunjukkan 1 worker online dan proses `bench worker` ada (filter `rq` sebelumnya cocok dengan `irq/` kernel). Seluruh 2.306 baris dibuat oleh job pada 09:02:26 sampai 09:02:32. Penyebab "0 baris" tidak terbukti; dugaan: dicek sebelum job selesai. Pelajaran: verifikasi asumsi infrastruktur dulu, dan beri waktu job background.
  - Temuan sampingan: server berjalan lewat `honcho` di terminal (`pts/0`), sehingga web dan worker ikut mati bila sesi terminal tertutup; `pause_scheduler` aktif di konfigurasi, jadi tarikan terjadwal belum akan berjalan; proses `esbuild` (bench watch) memakai sekitar 626 MB RAM. Dicatat untuk persiapan produksi.
- Belum: `device_record_no` (ditunda), data Employee, "Cocokkan Ulang", dialog tanggal dan tombol "Tarik Sekarang" (3c, kemudian selesai 31 Okt), penjadwalan tarikan, `WP 221`, perilaku mesin saat penuh.
- Cek `git log` untuk `hris_shift.json` dan `hris_shift.py` (revisi 29 Okt; status commit tidak diketahui dari sesi ini).
- Membaca `working_hour.py` utuh untuk memastikan query punch (per karyawan atau per mesin).
- Merapikan docstring `punch_ingest.py`.

## 2026-10-31 (Tarik Log, Hapus Raw Log, Konsol Mesin, HRIS Pull Run)
- Status tarikan diganti polling karena socket.io gagal lewat IP (K-67). Autofill browser mengisi password login ke Comm Key; dilindungi dengan `autocomplete="new-password"` (K-68). Commit b73cc9e.
- Hapus Raw Log per mesin dan rentang (K-69, 4f182b3); dialog dipusatkan di `hris_device_actions.js` (K-70, fc8114d); halaman Konsol Mesin (K-71).
- Data uji tarikan: tanggal yang dihapus untuk uji ditarik ulang dengan hasil identik, membuktikan data mesin utuh.
- Sesi A: DocType `HRIS Pull Run` (f387543). Penomoran dua awalan diuji: counter `{####}` dipakai bersama (K-74); dipilih diterima apa adanya. Form dan tab Audit Trail lolos uji browser.
- Sesi B: `pull_run_log.py` dan patch `pull_device.py`, `delete_raw_log.py` (5e886b9). Uji browser: tarik 927 punch (392 baru, 535 sudah ada), tarik ulang (0 baru, 927 sudah ada), hapus satu hari (535 baris), semuanya tercatat sebagai PR/DR.
- Keputusan: Pull Run merevisi sebagian K-46 (K-73); mesin Solution jalur agen dibangun di sesi tersendiri (K-72); tanpa pembersihan otomatis (K-75).
- Pelajaran:
  - Dugaan "counter terpisah per awalan" di `format:` tidak terbukti; uji dulu sebelum mengandalkan perilaku penamaan Frappe.
  - `bench execute` menerima path modul Python, bukan path file; untuk skrip sekali pakai gunakan `bench console`.
  - Commit sebelum uji browser membuat status "terpasang, belum teruji"; uji dulu, commit sesudahnya.
  - Pencatatan riwayat dibuat aman-gagal agar kegagalan catat tidak menghentikan tarikan atau hapus.
- Belum: Sesi C, kosmetik `depends_on`, agen Windows, tarik celah data, impor Employee, "Cocokkan Ulang".
- Catatan: penyimpanan memori proyek terblokir selama chat ini memakai konektor; dokumen ini menjadi catatan utama.

## 2026-10-31 (sesi lanjutan: Sesi C riwayat)
- Sesi C (0d0d669): fungsi `riwayat` di `pull_device.py` dan tabel riwayat di dialog Status (`hris_device_actions.js`), dipakai form Device dan Konsol Mesin. Tampilan teruji: tiga riwayat (tarik, tarik ulang, hapus) tampil benar (K-76).
- Kosmetik `depends_on` Pull Run lewat `migrate` (K-77; commit 92027bf).
- Keputusan Efendy: riwayat tidak dibatasi hanya Manager; role setara admin yang boleh menarik log juga melihat 10 baris teratas.
- Pelajaran:
  - Status cache (1 jam) dan riwayat database (permanen) adalah dua hal berbeda; tampilkan keduanya.
  - Skrip dengan anchor persis aman, tetapi anchor berisi tanda kutip dari catatan lama bisa gagal cocok; untuk dokumen lama pakai pencarian per awal baris.
- Belum: tarik celah data (tarik ulang 2 Okt, lalu 4-19 dan 21-23 Okt), `data-model.md` dan `api.md`, agen Windows untuk mesin jalur agen, uji akun HRIS HR Admin pada status terkini (`pull_status` masih menuntut hak write Device), laporan uji tampilan `depends_on`.
