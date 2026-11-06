# Session Log: 6 November 2026 (K-126, K-102, runbook produksi)

Catatan: dipisah dari `session-log.md`, mengikuti pola `session-log-2026-11-01.md`. Hanya hitungan dan ID, tanpa data pribadi. Zona waktu WIB; server mencetak waktu UTC.

## Ringkasan
- **K-126** (validasi `HRIS Employee`: V1, V1b, V2, V3) diterapkan di `hris-uji.local`, di-commit dan di-push (8a16ade). Uji skrip: `periksa` 8 OK, `periksa_resign` 4 OK. Uji browser B1 sampai B4, B6, B8, C2, C3, C4 lulus.
- **K-102** (migrasi Employee ke `HRIS Employee`): field `data_status` dan `data_note`, `services/migrasi_employee.py`, `uji_k102.py` (14 uji OK). Di-commit lokal 7278bb7 sekitar 12:05 dan di-push setelah gladi (`8a16ade..7278bb7`).
- **Latihan di site uji:** `dry_run` SIAP (1.078 akan dibuat, 0 bermasalah; 949 Lengkap, 128 Perlu Dilengkapi, 1 kosong); `latih` 1.078 dokumen dalam sekitar 3 detik, verifikasi SAMA, rollback bersih.
- **Keputusan:** salinan site uji identik dengan produksi (1.078 baris Employee, `MAX(modified)` sama), jadi tidak perlu site baru.
- **Runbook produksi:** `runbook_k102.sh` (7 perintah), `gladi_k102.sh` (fase1, fase2), `produksi_k102.sh` (cadangan, siap, mulai, pulihkan) dibuat di `/home/it/runbook_k102/`. Dua yang pertama sudah dijalankan di site uji.
- **Gladi resik lulus sekitar 15:25 sampai 15:35:** cadangan produksi (database 2,8 MiB), restore ke `hris-uji.local`, migrate (HRIS Employee 0), `awal` (Employee 1.078), `cek` LULUS, `jalankan` LULUS (dibuat 1.078, status Berhasil 1.078, tabel Employee tidak berubah), restore ulang mengembalikan HRIS Employee ke 0.
- Migrasi dijalankan ulang di site uji untuk uji browser. Cek karyawan di browser: data benar, Audit Trail bersih, filter "Status Kelengkapan Data" tampil.
- Cadangan `20261106_152714` disalin ke PC lewat `scp` dari Windows; hash SHA256 cocok dengan server.

## Temuan
- Tanggal Resign sebelum Tanggal Bergabung tersimpan di HRIS tetapi sinkron gagal di ERPNext; diperbaiki dengan V1b (hanya status Resign). `validate_from_to_dates` ERPNext hanya menolak bila tanggal akhir lebih awal, jadi tanggal sama diterima (terbukti di browser).
- HRIS menolak Tanggal Bergabung sama dengan Tanggal Lahir, ERPNext menerimanya; dibiarkan.
- Hanya satu Employee ber-`last_name` (`HR-EMP-01078`), `middle_name` 0. Sinkron pertama menaruh nama lengkap di `first_name`; `employee_name` tetap sama. Karena itu verifikasi K-102 membandingkan `employee_name`.
- Audit Trail menampilkan baris Status Sinkron bila status diubah lewat SQL langsung lalu form basi disimpan. Risiko pemakaian normal kecil; opsi perbaikan: saring field sinkron dari tampilan.
- Repo git ada di `apps/hris`, bukan di `/home/it/erp` (menjalankan git di folder bench menghasilkan `not a git repository`).
- Waktu server UTC (07:32 UTC = 14:32 WIB), nama berkas cadangan memuat waktu WIB (`152714`).
- `bench restore` pada site uji berjalan lancar dan setelahnya `migrate` memulihkan struktur HRIS Employee kosong.

## Kendala dan pelajaran
- Skrip F pertama menebak gaya indentasi `hris_employee.json` dan menggeser format (diff 878 baris). Skrip F2 memakai pencocokan persis (`indent=4`, diff 23 tambah 1 ubah). Pelajaran: untuk JSON besar, cocokkan gaya yang ada, jangan menebak.
- Salah ketik konfirmasi `hris.uji.local` (titik, bukan strip) membatalkan `jalankan` tanpa menulis apa pun; pengaman bekerja. Gladi diulang dari awal.
- `scp` dari server ke `D:\...` gagal karena `D:` dibaca sebagai nama host; solusinya menarik dari sisi Windows.
- Tabel "Langkah Berikutnya" dari sisi Claude sempat menuliskan peran terbalik (Anda membuat skrip); perannya: Claude membuat skrip, Efendy menjalankan.
- Hasil Langkah 6 (cek browser) baru dilaporkan setelahnya; dicatat apa adanya.

## Tambahan malam (21:24 sampai 22:47 WIB)
- D1 dan D2 lulus pada HRE-00274 di `hris-uji.local`: bagian Kelengkapan Data tampil; perubahan Status dan Catatan Kelengkapan Data tercatat di Audit Trail HRIS (pengguna, waktu WIB, nilai lama dan baru) dan dikembalikan. D1 sampai D4 semua lulus.
- `produksi_k102.sh` (`cadangan`, `siap`, `mulai`) lulus penuh di `hris-uji.local` lewat `SITE_TARGET`.
- Cara restart `erp` produksi: Ctrl+C lalu `bench start`. Uji per peran setelah migrasi produksi. Jadwal: saat lembur, belum pasti.
- Diagnosa baca-saja produksi (`diag_erp_k102.sh`, 22:47 WIB): hris `main` 47bfc12, tanpa commit belum di-push dan tanpa perubahan lokal; disk terpakai 18G, sisa 28G (39%); 12 berkas di `/home/it/cadangan_k102`. Bagian yang membaca database lewat `bench console` tidak mengeluarkan keluaran (pendekatan stdin tidak berfungsi), jadi kondisi tabel dan role produksi belum dikonfirmasi.

## Belum
- Cabang produksi pada `restore` di `runbook_k102.sh` belum pernah dijalankan.
- Kondisi database produksi (tabel `HRIS Employee`, role HRIS, jumlah dan `MAX(modified)` Employee) belum didiagnosa ulang; skrip diagnosa perlu perbaikan.
- Jadwal produksi (saat lembur), lalu uji per peran setelah migrasi.
- Memasukkan skrip runbook ke repo (belum diputuskan).
