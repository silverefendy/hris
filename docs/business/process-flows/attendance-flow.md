# Alur: Absensi dari mesin sampai Attendance

- Aktor: Admin/Operator, sistem HRIS, HRD (HR Admin/Manager)
- Pemicu: karyawan menempel jari/wajah di mesin

## Gambaran

```
Mesin -> [jalur data, belum diputuskan] -> HRIS Raw Log
      -> tinjau HRD (per baris, baris janggal diberi tanda)
      -> HRIS Attendance (memakai working hour HRIS)
      -> Payroll HRIS
      -> bridge HRIS ke ERPNext (ditunda)
```

## Langkah
1. Operator mendaftarkan mesin di `HRIS Device` (company, jenis, nomor seri, Comm Key).
2. Log dari mesin masuk ke `HRIS Raw Log`, satu baris per log, dengan semua informasi mesin.
3. Sistem menyalin `company` dari Device, mencocokkan ID user mesin dengan `Employee.attendance_device_id`, lalu mengisi `employee`. Status awal: Menunggu (cocok) atau Tidak Cocok.
4. Sistem memberi penanda otomatis (punch ganda diabaikan otomatis, ID tidak dikenal; telat/lembur/di luar jam shift menyusul).
5. HRD membuka list view, memfilter, lalu meninjau per baris. Baris janggal berwarna.
6. HR Admin/Manager menyetujui atau menolak. Mengubah data wajib disertai alasan.
7. Log Disetujui diproses menjadi `HRIS Attendance` memakai working hour kelompok karyawan (tahap berikutnya), lalu berstatus Terkirim.

## Pengecualian
- ID tidak dikenal atau tidak cocok: HRD memperbaiki data Employee atau menolak log.
- Punch ganda (lebih dari satu tempelan dalam satu hari kerja): ditangani otomatis. Masuk = tempelan paling awal, pulang = tempelan paling akhir. Log lainnya ditandai diabaikan otomatis, tetap tersimpan, dan HRD dapat mengoreksi dengan alasan (tercatat di audit trail).
- Status masuk/keluar dari mesin diabaikan; HRIS yang menentukan.
- Setiap perubahan tercatat di audit trail: waktu, apa yang berubah, siapa.
- Mesin tidak terhubung: tidak ada log baru; jalur data masih diparkir.
