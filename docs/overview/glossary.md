# Glosarium

| Istilah | Arti |
|---|---|
| HRIS | Human Resource Information System |
| HRMS | Modul HR bawaan ERPNext (app `hrms`) |
| Raw Log | Log absensi mentah dari mesin |
| Bridge | Pemetaan data HRIS ke ERPNext; hanya satu arah (HRIS ke ERPNext) dan ditunda (K-19) |
| Punch / tempelan | Satu kali karyawan menempelkan jari atau wajah di mesin; menjadi satu baris Raw Log |
| Shift | Jam kerja tetap (`HRIS Shift`): jam mulai, jam selesai, toleransi, jendela tempel, istirahat |
| Lintas tengah malam | Shift yang selesai di hari berikutnya (misalnya 23:00 sampai 07:00) |
| Jendela tempel | Rentang menit sebelum mulai dan sesudah selesai shift tempat tempelan masih dianggap milik shift itu; jendela sesudah selesai juga batas lembur |
| Grup karyawan | `HRIS Employee Group`: kumpulan karyawan yang memakai pola jadwal yang sama, terhubung lewat field `hris_employee_group` di Employee |
| Jadwal Mingguan | Jenis jadwal grup: shift sama tiap minggu; hari yang tidak terdaftar dianggap libur |
| Rotasi | Jenis jadwal grup: pola siklus per hari (shift atau libur) yang berulang sejak Tanggal Mulai Rotasi |
| Siklus | Satu putaran pola rotasi; panjangnya sama dengan jumlah baris pola |
| Shift Assignment | Penimpaan jadwal satu karyawan untuk rentang tanggal tertentu (tukar shift, pinjam karyawan); mengalahkan rotasi dan jadwal mingguan |
| Dipinjam untuk Grup | Field opsional di Shift Assignment: grup yang meminjam karyawan |
| HRIS Holiday | Hari libur nasional, cuti bersama, atau libur khusus satu company |
| Audit trail | Riwayat perubahan field (siapa, kapan, nilai lama dan baru) dari Version; tab "Audit Trail HRIS" di form |
