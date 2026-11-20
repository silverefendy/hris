# Keputusan 19 November 2026 — Hapus massal Working Hour

- Tanggal: 2026-11-19
- Status: disetujui

## Konteks
Hitung Working Hour massal menghasilkan puluhan ribu dokumen, sebagian besar milik karyawan tanpa baris gaji. Hapus bawaan Frappe satu per satu tidak praktis, menyimpan salinan di Deleted Document, dan tidak mengenal aturan slip atau periode Final.

## Keputusan
1. Fitur Hapus Massal di list view dengan Cek Dulu (dry run), konfirmasi dengan mengetik jumlah, dan job per batch 1000.
2. Hanya System Manager dan HRIS Direksi, dicek di server.
3. Blokir bila di bawah slip Final atau Payroll Period Final, termasuk kunci periode tanpa slip. Slip Draft/Ditinjau, Menunggu belum ditinjau, dan input manual hanya peringatan dengan konfirmasi.
4. Audit memakai DocType baru HRIS Hapus WH Log (HRIS Pull Run tidak cocok: device dan company wajib).
5. Saklar site `hris_hapus_wh_aktif`, bawaan 0, karena folder app dipakai bersama situs produksi.
6. Guard `on_trash` pada HRIS Working Hour agar jalur hapus bawaan tidak melewati blokir.
7. Hapus massal memakai `frappe.db.delete` (tanpa salinan Deleted Document), lalu membersihkan Version dan Comment per batch.

## Alternatif yang dipertimbangkan
- Membatasi izin Delete lewat JSON DocType: ditolak karena mengubah struktur DocType yang berjalan.
- Memakai HRIS Pull Run sebagai audit: ditolak karena jenis dan field wajibnya tidak cocok.
- Memakai `delete_doc` per dokumen: ditolak karena lambat dan menumpuk salinan di Deleted Document.

## Konsekuensi
- Dokumen terhapus tidak punya salinan pemulihan. Data dapat dibuat ulang dari Raw Log, kecuali input manual HR (itu sebabnya ada peringatan).
- `on_trash` aktif di semua situs yang memakai folder app setelah proses di-restart, termasuk produksi, tanpa `migrate`.
- DocType HRIS Hapus WH Log baru ada di situs yang sudah di-migrate. Di produksi belum.
