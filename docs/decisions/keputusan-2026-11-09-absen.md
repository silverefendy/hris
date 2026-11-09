# Keputusan 9 November 2026: Klasifikasi Absen (K-131)

Dasar: [keputusan-2026-11-09-payroll-slip.md](keputusan-2026-11-09-payroll-slip.md) (K-130, aturan A tentang absen yang ditentukan HRD).

## K-131 Klasifikasi Absen di `HRIS Working Hour`

| Aspek | Keputusan |
|---|---|
| Tujuan | HRD menentukan sebab hari **Tidak Hadir** karyawan Bulanan, supaya potongan gaji (K-130) dapat dihitung otomatis. Sementara, sampai `HRIS Absence` dibuat |
| Field baru | `absence_class` (Mangkir, Cuti, Sakit, Izin, Lainnya), `has_doctor_note`, `has_supervisor_instruction`, `annual_leave_exhausted`, `absence_deducted` (Dipotong Gaji), `absence_note`, `classified_by`, `classified_on` |
| Aturan potong | Mangkir: dipotong. Cuti: tidak dipotong, kecuali cuti tahunan habis. Izin: dipotong, kecuali ada instruksi atasan. Sakit: dipotong, kecuali ada surat dokter. Lainnya: HRD memilih manual dan catatan wajib. Aturan lain menyusul bersama `HRIS Absence` |
| Besar potongan | Satu hari = gaji pokok dibagi hari kerja nyata periode (K-130). Aturan hitung ini dibuat bersama `HRIS Payroll Slip`, bukan di K-131 |
| Hari Tidak Hadir, karyawan Bulanan | Ditandai **Perlu Tinjauan** dengan status tinjauan Menunggu. Menggantikan kalimat K-41 "Tidak Hadir tidak ditandai". Karena K-128 menghalangi Final selama ada baris Menunggu, absen yang belum diklasifikasi menghalangi Final |
| Hari Tidak Hadir, karyawan Harian | Aturan Efendy (9 Nov 2026): bila tidak ada absensi datang maupun pulang dan tidak ada laporan ke HRD, hari itu dianggap tidak masuk, tanpa tanda tinjauan. Bila hanya ada salah satu punch (status Tidak Lengkap), tetap ditandai untuk diperbaiki HRD (perilaku K-41 yang sudah ada). HRD tetap boleh mengklasifikasi hari Tidak Hadir Harian secara manual bila ada laporan |
| Pembacaan jenis gaji | Dari `HRIS Employee Pay` yang berlaku pada tanggal kerja, lewat `HRIS Employee.erpnext_employee`. Bila karyawan belum punya baris gaji, jenisnya tidak diketahui dan diperlakukan seperti Bulanan (ditandai), supaya tidak ada yang lolos tanpa terlihat |
| Saat klasifikasi diisi | Status tinjauan otomatis menjadi Sudah Ditinjau; pelaku dan waktu tercatat |
| Validasi | Klasifikasi hanya untuk status Tidak Hadir; Sudah Ditinjau tanpa klasifikasi ditolak pada baris Tidak Hadir yang perlu tinjauan (kecuali oleh hitung ulang); klasifikasi Lainnya wajib catatan |
| Hitung ulang | Klasifikasi dipertahankan. Bila hari itu menjadi bukan Tidak Hadir, klasifikasi dibersihkan. Tinjauan Sudah Ditinjau pada Tidak Hadir yang perlu klasifikasi tetapi belum diklasifikasi kembali ke Menunggu |
| Tanda Perlu Tinjauan | Tetap tercentang setelah HRD selesai: tanda itu mencatat bahwa hari tersebut punya alasan tinjauan, sedangkan Status Tinjauan menunjukkan sudah atau belum diselesaikan (sesuai K-43) |
| Penjaga field (K-42) | Field klasifikasi masuk daftar yang boleh diubah manusia, dengan batas peran yang sama (HRIS HR Admin, HRIS Manager, System Manager) dan terkunci setelah periode Final (K-128) |

### Berkas yang diubah
`hris_working_hour.json`, `hris_working_hour.py`, `services/working_hour.py` (modul `hris_attendance`), dan berkas baru `services/absence_rule.py` (aturan potong murni, tanpa database). Pembaruan untuk karyawan Harian menambah `hris_payroll/services/pay_type.py`.

### Dampak pada keputusan lama
| Keputusan | Perubahan |
|---|---|
| K-41 | Tidak Hadir karyawan Bulanan (atau jenis gaji tidak diketahui) kini ditandai perlu tinjauan |
| K-42 | Daftar field yang boleh diubah manusia bertambah (field klasifikasi) |
| K-43 | Aturan mempertahankan Sudah Ditinjau: Tidak Hadir yang perlu klasifikasi tetapi belum diklasifikasi kembali ke Menunggu |

## Status (9 Nov 2026)
| Item | Hasil |
|---|---|
| Uji skrip di `hris-uji.local` | **OK 33, GAGAL 0**: delapan field, sepuluh aturan murni, lima belas perilaku database (selalu rollback, data uji nol) |
| Commit dan push kode klasifikasi | `097a946` |
| Uji browser (baris Zaskia Aulia, 17-10-2026) | Lulus: hitung ulang menandai Tidak Hadir; klasifikasi Sakit dengan surat dokter (tidak dipotong) dan Izin (dipotong); status tinjauan otomatis Sudah Ditinjau; pelaku dan waktu tercatat; hitung ulang mempertahankan klasifikasi; penolakan Lainnya tanpa catatan dan Sudah Ditinjau tanpa klasifikasi. Belum dilaporkan: Lainnya dengan catatan dan pilihan Dipotong Gaji manual |
| Aturan karyawan Harian | Dibuat sebagai patch tersendiri; menunggu uji |
| Regresi Working Hour lama (R1 sampai R4) | Tidak ada di repo dan tidak ditemukan di server |
| Produksi | Belum; perubahan JSON ikut terbentuk di produksi saat `migrate` K-102 karena folder app dipakai bersama |

## Pelajaran
- Uji database untuk dokumen `HRIS Working Hour` harus memuat ulang dokumen dari database setelah `insert` dan setelah penolakan yang disengaja. Tanpa itu, penjaga K-42 dan pemeriksaan cap waktu Frappe memberi galat palsu.
- Sebelum go-live, aturan karyawan Harian hanya berlaku bila karyawan sudah punya baris `HRIS Employee Pay`. Tanpa baris gaji, semua hari Tidak Hadir ditandai.

## Belum diputuskan
- **K-132 (usul):** memindahkan tautan `HRIS Working Hour`, `HRIS Raw Log`, dan `HRIS Shift Assignment` dari `Employee` ERPNext ke `HRIS Employee`, sesuai arah bahwa HRIS Employee adalah sumber utama. Perubahan struktur besar; butuh penjelasan risiko dan konfirmasi sebelum dikerjakan.
- Rancangan `HRIS Absence` (usul modul HRIS Attendance): cuti, sakit, izin, saldo cuti, dan pengisian klasifikasi otomatis.
- Perlakuan hari **Tidak Lengkap** pada gaji Bulanan.
