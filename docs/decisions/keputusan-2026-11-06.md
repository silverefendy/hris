# Keputusan 6 November 2026 (K-126 dan pelaksanaan K-102)

Dasar: [keputusan-2026-11-04.md](keputusan-2026-11-04.md) (K-100 sampai K-117, termasuk K-101 dan K-102) dan [keputusan-2026-11-05.md](keputusan-2026-11-05.md) (K-118 sampai K-121).

Catatan penomoran: K-122 sampai K-125 belum tercatat di repo saat berkas ini dibuat. Nomor itu ditambahkan setelah isinya dipastikan, tanpa mengubah nomor di bawah.

| No | Keputusan | Tanggal | Status |
|---|---|---|---|
| K-126 | Validasi `HRIS Employee` agar sinkron ke Employee ERPNext tidak gagal. **V1:** Tanggal Bergabung harus setelah Tanggal Lahir (tanggal sama ditolak; lebih ketat dari ERPNext yang menerimanya, dibiarkan karena datanya absurd dan tidak pernah membuat sinkron gagal). **V1b:** Tanggal Resign tidak boleh sebelum Tanggal Bergabung, hanya untuk status Resign; tanggal sama diterima, sebangun dengan `validate_from_to_dates` ERPNext yang hanya menolak bila tanggal akhir lebih awal. **V2:** ID Finger dicek ke `tabEmployee` untuk semua status kecuali Employee yang tertaut; ID Finger karyawan resign tidak boleh dipakai ulang selama Employee lama masih memegangnya. **V3:** banner oranye di form bila status sinkron Gagal (`public/js/hris_sync_status.js`). Keputusan tambahan Efendy: `hris_data_status` yang kosong dimigrasi sebagai `data_status` kosong dan jumlahnya dilaporkan | 2026-11-06 | Diterapkan (8a16ade), di-push. Teruji skrip: `uji_k126.periksa` 8 OK, `periksa_resign` 4 OK. Teruji browser: B1 sampai B4, B6, B8, C2, C3 (status Aktif mengosongkan Tanggal Resign, sesuai rancangan), C4 (tanggal resign sama diterima); banner tampil untuk galat sinkron nyata |
| K-102 (pelaksanaan) | Migrasi sekali Employee menjadi HRIS Employee, hanya membaca data lama. Field baru `data_status` dan `data_note` ("Kelengkapan Data") di `HRIS Employee`. Alat `services/migrasi_employee.py`: `dry_run`, `migrasi` (semua atau tidak sama sekali, wajib konfirmasi nama site), `verifikasi` (dan `terapkan=1` untuk menandai Berhasil), `latih` (tulis lalu rollback). Verifikasi membandingkan `employee_name`, bukan `first_name`, karena sinkron menaruh nama lengkap di `first_name`. `uji_k102.py`: 14 uji logika pemetaan dan pembanding | 2026-11-06 | Diterapkan di kode (7278bb7), di-push. Migrasi **belum** dijalankan di produksi. Latihan di site uji: lulus (lihat di bawah). Runbook produksi: [../operations/deployment.md](../operations/deployment.md) |

## Hasil uji K-102 di `hris-uji.local` (6 November 2026)

| Uji | Hasil |
|---|---|
| `dry_run` | `SIAP`: 1.078 Employee akan dibuat, 0 bermasalah. `data_status`: 949 Lengkap, 128 Perlu Dilengkapi, 1 kosong. Tidak ada `reports_to` |
| `latih` (tulis lalu rollback) | 1.078 dokumen ditulis dalam sekitar 3 detik, verifikasi sekitar 1,5 detik, hasil SAMA, jumlah HRIS Employee sebelum dan sesudah rollback sama |
| Gladi resik penuh | Cadangan produksi, restore ke site uji, migrate, `cek`, `jalankan` (dibuat 1.078, verifikasi SAMA, status sinkron Berhasil 1.078, tabel Employee tidak berubah), restore ulang mengembalikan HRIS Employee ke 0 |
| Tampilan browser | Data karyawan hasil migrasi tampil benar, Audit Trail bersih, filter "Status Kelengkapan Data" tampil di daftar |
| Diff `hris_employee.json` | Kecil dan bersih (23 baris tambah, 1 ubah; gaya `indent=4`). Percobaan pertama memakai tebakan indentasi yang salah (diff 878 baris) dan diganti dengan pencocokan persis |

## Catatan keputusan latihan
- Latihan migrasi memakai `hris-uji.local` (salinan produksi) tanpa site baru: tabel Employee site uji terbukti identik dengan produksi (1.078 baris, `MAX(modified)` sama).
- Dua syarat tetap berlaku: cek keusangan diulang tepat sebelum produksi (otomatis di `produksi_k102.sh siap`), dan latihan restore sudah dilakukan (6 Nov).

## Catatan teknis
- **Sinkron pertama:** Simpan pertama pada karyawan hasil migrasi memicu sinkron ke Employee. `verifikasi` SAMA untuk semua field yang dikirim sinkron, jadi hampir semua Employee tidak berubah. Pengecualian: nama. Hanya satu Employee yang punya `last_name` terisi (`HR-EMP-01078`; `middle_name` terisi 0), sehingga paling banyak satu Employee yang namanya terpecah ulang. `employee_name` tetap sama.
- **Batasan Audit Trail:** baris "Status Sinkron" dan "Pesan Error Sinkron" bisa tampil bila status sinkron berubah di luar form (SQL manual atau pengguna lain) lalu form yang basi disimpan. Terlihat pada uji dengan SQL langsung. Risiko pemakaian normal kecil. Opsi perbaikan nanti: saring field sinkron dari tampilan Audit Trail.
- **Mekanisme ERPNext (terbukti dari `employee.py`):** `validate_from_to_dates` memeriksa tanggal lahir ke tanggal bergabung, tanggal bergabung ke tanggal pensiun, tanggal berhenti, dan akhir kontrak; hanya menolak bila tanggal akhir lebih awal.
- **Mute email di site uji** (`mute_emails=1`) disengaja: belum ada email yang disetel.

## Belum diputuskan
- Cara me-restart `erp` di produksi dan jadwal produksi (di luar jam kerja HRD).
- Apakah skrip runbook (`/home/it/runbook_k102/`) dimasukkan ke repo (misalnya `scripts/`); sekarang hanya ada di server.
- Perbaikan tampilan Audit Trail (penyaringan field sinkron).
- Isi dan penomoran K-122 sampai K-125 (belum ada di repo).
