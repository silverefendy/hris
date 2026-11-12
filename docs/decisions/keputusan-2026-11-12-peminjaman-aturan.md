# K-138: Peminjaman karyawan (P9), aturan khusus per karyawan, dan komponen aturan

Tanggal: 12 Nov 2026. Status: keputusan Efendy (sesi 12 Nov); **tahap 1, 2, dan 3 selesai dan teruji di hris-uji (13 Nov)**. Lanjutan K-136 dan K-137.

## 1. Jawaban Efendy

| Butir | Jawaban |
|---|---|
| P1 | Peminjaman boleh dipilih lewat Employee Group atau Department (atau); bila keduanya ada, di Employee dipilih default ikut yang mana |
| P2 | HRD yang mencatat; belum perlu persetujuan; bila nanti perlu, diatur bersama manager HRD |
| P3 | Bisa per jam dan per hari |
| P4 | Hanya pengali lembur yang ikut Department tujuan |
| P5 | Slip membaca Department per hari dari Working Hour |
| E1 | Semua jenis aturan bisa berbeda antar Department, tetapi tidak semua Department punya insentif atau tunjangan; cara memasukkannya perlu dirancang |
| E2 | Nilai per Department belum ada |
| E5 | Aturan khusus karyawan ditetapkan Manager dan Direksi; semua parameter boleh berbeda (customized) |
| K1 | Shift malam hanya untuk Security, 20.00 sampai 08.00, tanpa istirahat (sudah sesuai data) |
| K2 | HRD tahu jadwal migrasi; cukup dicatat |
| K3 | Efendy sendiri yang online saat migrasi |
| K4 | Latihan penuh langkah 2b di hris-uji dari cadangan erp terbaru, jam dicatat |

## 2. Rancangan fase 1 (per hari penuh)

| Bagian | Rancangan |
|---|---|
| HRIS Shift Assignment | Tambah field Dipinjam ke Department (Link HRIS Department); Dipinjam untuk Grup tetap ada. Boleh diisi salah satu atau keduanya |
| Penentuan Department tujuan | Department terisi dipakai; bila hanya Grup, Department milik Grup itu; Grup tanpa Department ditolak saat simpan dengan pesan jelas; bila keduanya terisi dan berbeda, ditentukan pilihan Ikut Department atau Grup di HRIS Employee (bawaan Department) |
| HRIS Employee | Tambah pilihan Ikut Department atau Grup (nama field ditetapkan saat implementasi) |
| Working Hour | Field Department per hari diisi Department tujuan pada hari dipinjam, selain itu Department karyawan; perlu Hitung Ulang untuk periode yang sudah ada |
| Payroll Slip | Pengali lembur dicari per tanggal memakai Department hari itu (bukan Department karyawan) |
| Hanya pengali lembur | Parameter lain ditunda sampai daftar komponen ada |

Contoh: Budi (Department Produksi) dipinjam 20 Okt ke Department Finishing: lembur 20 Okt memakai aturan Finishing, hari lain aturan Produksi.

## 3. Ditunda

| Fitur | Catatan |
|---|---|
| Peminjaman per jam (fase 2) | Aturan lembur pada jam sesudah jam peminjaman belum diputuskan; menyentuh cara Working Hour memecah jam |
| Aturan khusus per karyawan | DocType terpisah (nomor keputusan menyusul); membuat hanya Manager atau Direksi; urutan penelusuran: aturan karyawan, lalu peminjaman, lalu Department (naik ke akar) |
| Komponen tambahan (E1) | Menunggu daftar komponen yang benar-benar ada, apakah kena pajak, dan apakah masuk dasar BPJS; perlu cara menyatakan "tidak berlaku" yang berbeda dari "ikut induk" |

## 4. Risiko perubahan DocType

| Perubahan | Risiko |
|---|---|
| Field baru di HRIS Shift Assignment | Rendah: field peminjaman lama kosong di kedua site; field lama tidak dihapus |
| Field baru di HRIS Employee | Rendah: tabel belum ada di erp sebelum K-102, kolom terbentuk saat migrasi, nilai bawaan Department |
| Working Hour mengisi Department dari peminjaman | Sedang: perlu Hitung Ulang dan uji regresi slip |

## 5. Urutan kerja

1. P9 fase 1 (kode dan uji di hris-uji).
2. Latihan penuh langkah 2b (gladi_k102.sh) sesudah P9, karena gladi menimpa isi hris-uji dan field baru ikut terlatih.
3. Malam migrasi K-102 setelah tanggal ditentukan.

Belum dijawab: apakah penarikan absensi mesin bergantung pada erp saat mode maintenance; daftar komponen E1; tanggal malam K-102.

## 6. Keputusan tahap 2 (12 sampai 13 Nov 2026)

| No | Keputusan |
|---|---|
| 1 | Peminjaman dibuat, diubah, atau dibatalkan setelah Working Hour terhitung: hari terkait dihitung ulang otomatis bila belum final |
| 2 | Periode Final: terkunci, hanya ditandai `needs_review`. Periode Draft boleh dihitung ulang |
| 3 | Department dibaca dari HRIS Employee, bukan Employee ERPNext. Department ERPNext hanya menerima salinan dari HRIS Department |
| 4 | Baris `Sudah Ditinjau` atau ber-`adjustment_hours` tidak 0 (periode belum Final): tidak dihitung ulang, hanya ditandai (melindungi koreksi HRD) |
| 5 | Penanda `needs_review` boleh ditulis pada baris periode Final lewat `frappe.db.set_value` |
| 6 | Cabang transisi: jatuh ke Department Employee ERPNext hanya selama tabel HRIS Employee belum ada (sebelum K-102 di produksi); boleh dihapus setelah K-102 selesai dan stabil |

## 7. Hasil implementasi dan uji

| Tahap | Isi | Commit | Uji (hris-uji.local) |
|---|---|---|---|
| 1 | Field peminjaman, `tentukan_department`, validasi Grup tanpa Department, jadwal membawa Department tujuan, `rule_department` di Working Hour (read-only) | `ab4908f` | `uji_p9_tahap1` OK 17 |
| 2 | Working Hour mengisi `rule_department`; hook Shift Assignment (`on_update`, `after_delete`) menghitung ulang atau menandai | `904efc9` | `uji_p9_tahap2` OK 11 |
| 2 | Uji alur penuh hook: pinjam, persempit, hapus, penugasan biasa, Sudah Ditinjau, adjustment, periode Final | `6f053d7` | `uji_p9_alur` OK 9 |

Tahap 2 tidak butuh `migrate` di erp; sebelum K-102 hook tidak berbuat apa-apa bila tidak ada penugasan pinjam.

## 8. Koreksi asumsi dan batasan yang diketahui

- Koreksi: "Disetujui" dan "Terkirim" adalah status HRIS Raw Log, bukan status Working Hour. Penguncian ditentukan oleh `period_lock.is_locked`, yaitu HRIS Payroll Period berstatus Final.
- Penanda di periode Final memakai `db.set_value`, sehingga tidak masuk Audit Trail (`Version`); jejaknya ada di teks `review_reason`.
- Baris `Sudah Ditinjau` yang ditandai kembali menjadi `Menunggu`.
- Perubahan Department milik Grup belum memicu hitung ulang (keputusan terpisah).
- Filter Department di hitung ulang massal (`working_hour_batch._employees`) masih memakai Department Employee ERPNext (keputusan terpisah).
- Belum diuji dengan baris Final dan Sudah Ditinjau dari data produksi; alur uji memakai data uji dengan rollback.

## 9. Tahap 3: slip memakai rule_department (13 Nov 2026)

| Butir | Keputusan atau hasil |
|---|---|
| Baris `needs_review=1` | Tetap dihitung dengan nilai tersimpan |
| `rule_department` kosong | Jatuh ke Department karyawan, lalu akar (angka slip lama tidak bergeser) |
| `_pengali_lembur` (satu pengali per slip) | Tidak diubah; field `overtime_multiplier` di slip tetap pengali Department karyawan, pengali per hari tampil di rincian komponen |
| Perubahan kode (`655300a`) | `payroll_slip.py`: kolom `rule_department` ikut dibaca bila ada (`has_column`, aman sebelum migrate); `_pasang_pengali_harian` memakai Department per hari, kunci cache (Department, tanggal) |
| Uji baru | `uji_p9_slip` OK 6 (S1 satu hari dipinjam: lembur 463.918; S2 dan S3 identik dengan sebelum tahap 3: 432.990) |
| Regresi | slip utuh OK 16, BPJS OK 68, PPh 21 OK 22, slip OK 77, massal OK 19, tahap 1/2/alur OK 17/11/9 |
| Belum terverifikasi | Teks catatan "Pengali lembur berubah di periode ini" belum diperiksa lewat uji (angka lembur sudah membuktikan logikanya) |
