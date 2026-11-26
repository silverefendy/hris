# Kartu Profil HRIS Employee

Status: selesai dan lulus uji di site uji (26 Nov 2026). Hanya tampilan, struktur DocType tidak diubah.

## Tujuan

Menampilkan HRIS Employee sebagai kartu bertab yang rapi, dengan edit langsung per bagian, riwayat perubahan, dan banner cerah, tanpa menggantikan Form Edit bawaan.

## Berkas

| Berkas | Fungsi |
|---|---|
| `hris/public/js/hris_employee_card.js` | Logika kartu, edit per bagian, riwayat |
| `hris/public/css/hris_employee_card.css` | Gaya kartu, warna Form Edit, banner |
| `hris/hooks.py` | `app_include_js` dan `app_include_css` (masing-masing satu baris) |

## Fitur

| Fitur | Penjelasan |
|---|---|
| Dua tampilan | Kartu Profil dan Form Edit, dipilih lewat menu **Tampilan**, tersimpan per browser (localStorage `hris_employee_view`). Dokumen baru selalu masuk Form Edit |
| Tab | Profil, Pekerjaan, Payroll dan BPJS, Status dan Sinkron, Riwayat |
| Tab Payroll dan BPJS | Hanya muncul untuk peran yang punya izin baca `permlevel 1` |
| Edit per bagian | Tombol **Ubah** di tiap section memakai kontrol asli Frappe. Simpan lewat `frm.set_value` lalu `frm.save()`, jadi validasi dan hook tetap berjalan |
| Field dikunci | Field `read_only` dan field tanpa izin tulis tidak bisa diubah dari kartu |
| Ganti foto | Lewat `frappe.ui.FileUploader` ke field `image` |
| Riwayat | Ringkasan 5 perubahan terakhir di tab Profil, tabel lengkap (maksimal 300 baris) di tab Riwayat. Data dari `hris.hris_attendance.services.audit_trail.get_audit_trail`, yang sudah menyaring berdasarkan izin |
| WhatsApp | Tautan hanya untuk nomor seluler (awalan 08 atau 628) |
| Warna Form Edit | Garis kiri berwarna per section dan tab aktif beraksen emas, lewat kelas `hk-form-warna` |
| Banner | Cerah (variabel `--hk-head-a/b/c` di CSS), tetap gelap di mode gelap Frappe |

## Keamanan dan ketahanan

- Semua kode kartu dibungkus `try/catch`. Jika terjadi galat, form biasa tampil kembali.
- Data sensitif mengikuti `permlevel`. Server tidak mengirim field itu ke peran lain.
- Nilai yang ditampilkan di-escape (`frappe.utils.escape_html`).

## Uji yang dilakukan (site uji)

Kartu, tab, edit dan simpan, Batal, field Link dan tanggal, ganti foto, peran tanpa `permlevel 1`, mode gelap, Form Edit berwarna, kepesertaan BPJS dan Iuran turunan, riwayat ringkas dan penuh, Console tanpa galat.

## Cara mengembalikan (rollback)

1. Kembalikan berkas dari commit sebelumnya (`git checkout <commit-sebelumnya> -- hris/public/js/hris_employee_card.js hris/public/css/hris_employee_card.css`).
2. Untuk mematikan total: hapus dua baris `hris_employee_card` di `hooks.py`.
3. `bench --site <site> clear-cache` dan muat ulang browser dengan Ctrl+Shift+R.

## Pelajaran

- Satu galat saat membangun HTML kartu membuat seluruh kartu kembali ke form biasa (fallback). Pada versi awal, baris Iuran memakai teks biasa, padahal kode mengharapkan fungsi (`i.h is not a function`). Kasus ini hanya muncul pada karyawan tanpa kepesertaan BPJS. Uji selalu dengan karyawan yang datanya kosong dan yang datanya lengkap.
- Detail API `frappe.ui.form.make_control` dan `FileUploader` di Frappe v16 diverifikasi lewat uji langsung. Rujukan: source `frappe/public/js/frappe/form/controls`.

## Yang belum dikerjakan

- Grup Shift di header (bukan field DocType HRIS Employee, butuh sumber dari penugasan shift).
- Galat `socket.io` port 9000 (realtime) di Console, tidak berhubungan dengan kartu.

## Tema banner

| Hal | Penjelasan |
|---|---|
| Pilihan | Biru Langit (default), Hijau Mint, Krem Emas, Oranye Lembut, Gelap, lewat menu **Tampilan** |
| Penyimpanan | Per browser (`localStorage`, kunci `hris_employee_tema`) |
| Cara kerja | Atribut `data-tema` pada `.hk-kartu`, CSS mengatur variabel warna per tema |
| Mode gelap Frappe | Banner tetap gelap (selektor `html:not([data-theme="dark"])`) |
| Menambah tema | Tambah satu entri di array `TEMA` (JS) dan satu blok `.hk-kartu[data-tema="..."]` (CSS) |
