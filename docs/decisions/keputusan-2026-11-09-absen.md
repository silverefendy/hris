# Keputusan 9 November 2026: Klasifikasi Absen (K-131)

Dasar: [keputusan-2026-11-09-payroll-slip.md](keputusan-2026-11-09-payroll-slip.md) (K-130, aturan A tentang absen yang ditentukan HRD).

## K-131 Klasifikasi Absen di `HRIS Working Hour`

| Aspek | Keputusan |
|---|---|
| Tujuan | HRD menentukan sebab setiap hari **Tidak Hadir**, supaya potongan gaji Bulanan (K-130) dapat dihitung otomatis. Sementara, sampai `HRIS Absence` dibuat |
| Field baru | `absence_class` (Mangkir, Cuti, Sakit, Izin, Lainnya), `has_doctor_note`, `has_supervisor_instruction`, `annual_leave_exhausted`, `absence_deducted` (Dipotong Gaji), `absence_note`, `classified_by`, `classified_on` |
| Aturan potong | Mangkir: dipotong. Cuti: tidak dipotong, kecuali cuti tahunan habis. Izin: dipotong, kecuali ada instruksi atasan. Sakit: dipotong, kecuali ada surat dokter. Lainnya: HRD memilih manual dan catatan wajib. Aturan lain menyusul bersama `HRIS Absence` |
| Besar potongan | Satu hari = gaji pokok dibagi hari kerja nyata periode (K-130). Aturan hitung ini dibuat bersama `HRIS Payroll Slip`, bukan di K-131 |
| Hari Tidak Hadir | Kini ditandai **Perlu Tinjauan** dengan status tinjauan Menunggu. Menggantikan kalimat K-41 "Tidak Hadir tidak ditandai". Karena K-128 menghalangi Final selama ada baris Menunggu, absen yang belum diklasifikasi menghalangi Final |
| Saat klasifikasi diisi | Status tinjauan otomatis menjadi Sudah Ditinjau; pelaku dan waktu tercatat |
| Validasi | Klasifikasi hanya untuk status Tidak Hadir; Sudah Ditinjau tanpa klasifikasi ditolak pada Tidak Hadir (kecuali oleh hitung ulang); klasifikasi Lainnya wajib catatan |
| Hitung ulang | Klasifikasi dipertahankan. Bila hari itu menjadi bukan Tidak Hadir, klasifikasi dibersihkan. Tinjauan Sudah Ditinjau pada Tidak Hadir tanpa klasifikasi kembali ke Menunggu |
| Penjaga field (K-42) | Field klasifikasi masuk daftar yang boleh diubah manusia, dengan batas peran yang sama (HRIS HR Admin, HRIS Manager, System Manager) dan terkunci setelah periode Final (K-128) |

### Berkas yang diubah
`hris_working_hour.json`, `hris_working_hour.py`, `services/working_hour.py` (modul `hris_attendance`), dan berkas baru `services/absence_rule.py` (aturan potong murni, tanpa database).

### Dampak pada keputusan lama
| Keputusan | Perubahan |
|---|---|
| K-41 | Tidak Hadir sekarang ditandai perlu tinjauan |
| K-42 | Daftar field yang boleh diubah manusia bertambah (field klasifikasi) |
| K-43 | Aturan mempertahankan Sudah Ditinjau: Tidak Hadir tanpa klasifikasi kembali ke Menunggu |

## Status
| Item | Hasil |
|---|---|
| Uji skrip di `hris-uji.local` (9 Nov 2026) | **OK 33, GAGAL 0**: delapan field, sepuluh aturan murni, lima belas perilaku database (selalu rollback, data uji nol) |
| Uji browser | Belum |
| Regresi Working Hour | Belum dijalankan ulang |
| Commit dan push kode | Belum |
| Produksi | Belum; perubahan JSON ikut terbentuk di produksi saat `migrate` K-102 karena folder app dipakai bersama |

## Pelajaran
- Uji database untuk dokumen `HRIS Working Hour` harus memuat ulang dokumen dari database setelah `insert` dan setelah penolakan yang disengaja. Tanpa itu, penjaga K-42 dan pemeriksaan cap waktu Frappe memberi galat palsu.
- Efek samping yang perlu diperhatikan: hari Tidak Hadir lama berstatus Menunggu setelah dihitung ulang. Skrip regresi yang mengasumsikan Tidak Perlu perlu disesuaikan.

## Belum diputuskan
- **K-132 (usul):** memindahkan tautan `HRIS Working Hour`, `HRIS Raw Log`, dan `HRIS Shift Assignment` dari `Employee` ERPNext ke `HRIS Employee`, sesuai arah bahwa HRIS Employee adalah sumber utama. Perubahan struktur besar; butuh penjelasan risiko dan konfirmasi sebelum dikerjakan.
- Rancangan `HRIS Absence` (usul modul HRIS Attendance): cuti, sakit, izin, saldo cuti, dan pengisian klasifikasi otomatis.
- Perlakuan hari **Tidak Lengkap** pada gaji Bulanan.
