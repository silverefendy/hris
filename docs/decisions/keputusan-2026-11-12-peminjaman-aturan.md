# K-138: Peminjaman karyawan (P9), aturan khusus per karyawan, dan komponen aturan

Tanggal: 12 Nov 2026. Status: keputusan Efendy (sesi 12 Nov); **belum ada kode**. Lanjutan K-136 dan K-137.

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
