# 0003 — Jalur data mesin absensi

- Tanggal: 2026-10-30
- Status: disetujui (diterapkan di Sesi 1, 2A, 2B; Pull pyzk menyusul di Sesi 3)

## Konteks

Ada delapan mesin absensi. Uji dari server (29 Okt) menunjukkan tujuh mesin bisa ditarik langsung lewat library `pyzk`, sedangkan satu mesin (tipe Solution) tidak. Mesin itu hanya bisa dijangkau lewat SDK Windows (`zkemkeeper`), dan SDK itu hanya jalan di Python/PowerShell 32-bit. Karena itu dibutuhkan agen Windows (middleware) yang mengirim log ke HRIS lewat HTTP.

DocType `HRIS Device` dan `HRIS Raw Log` sudah ada sejak 28 Okt, jadi rancangan awal ("Attendance Device/Raw Log" baru) disesuaikan, bukan dibuat ulang.

Nama dan alamat mesin tidak ditulis di dokumentasi (aturan CLAUDE.md). Gunakan `<nama device>` dan `<IP server>`.

## Keputusan

| No | Keputusan |
|---|---|
| K-46 | Nama DocType tetap `HRIS Device` dan `HRIS Raw Log`. Tidak dibuat DocType baru. |
| K-47 | `HRIS Device`: jalur data ditandai dua centang, `use_agent` (Via Windows Agent) dan `use_pull` (Via Pull pyzk). Satu mesin boleh memakai keduanya. Field read-only `last_agent_at` dan `last_pull_at`. Section baru "Data Channels". Rencana `pull_method` tunggal ditinggalkan. |
| K-48 | `HRIS Raw Log`: tambah `source` (Select: kosong, `Agen Windows`, `Pull pyzk`, `Impor File`) dan `raw_payload` (Long Text, read-only). Keduanya `set_only_once` (ditegakkan server, terbukti di uji) sehingga tidak bisa diubah setelah tersimpan. Tidak ada `unique_key` dan tidak ada `match_status`: pencocokan karyawan memakai `employee` kosong ditambah `review_status` yang sudah ada. |
| K-49 | `comm_key` dan `connection_mode` di Device dibiarkan. `connection_mode` kini warisan; kode baru hanya melihat `use_pull`. Comm Key untuk agen disimpan di sisi agen, bukan di Frappe. Sebagian besar mesin tidak memakai Comm Key. |
| K-50 | IP dan port wajib bila `connection_mode == "Pull (IP)"` atau `use_pull`. Ditulis dua kali: `mandatory_depends_on` di JSON (browser, memakai `\|\|`) dan di controller `hris_device.py` (server, memakai `or`), karena `mandatory_depends_on` hanya dievaluasi di browser. |
| K-51 | Anti-duplikat memakai nama dokumen Raw Log (`mesin-ID-waktu`, K-30 pengecualian). Jalur agen dan pull boleh jalan bersamaan tanpa baris ganda; duplikat memicu `DuplicateEntryError` dan dihitung `duplicate`. |
| K-52 | Autentikasi agen memakai token buatan sendiri di DocType Single `HRIS Attendance Settings`, bukan user API key Frappe. Hanya hash yang disimpan; saklar `agent_enabled` default mati; daftar `allowed_ips` opsional; pembatas 10 kegagalan per 10 menit per IP; pesan error seragam; tombol Generate / Rotate Token (System Manager atau HRIS Manager), token lama langsung mati. Keputusan ini mengganti rencana awal user API key + role operator; izin role agen di Raw Log sudah dicabut. |
| K-53 | Kontrak penerimaan punch (`save_punches`): satu device per panggilan, maksimal 500 baris, savepoint per baris, hasil per baris `created` / `duplicate` / `error` (duplikat dianggap sukses). Waktu punch WIB tanpa zona, format `YYYY-MM-DD HH:MM:SS`; waktu lebih dari 1 hari ke depan ditolak. Device wajib terdaftar, aktif, dan jalurnya dicentang. Raw Log dibuat dengan `ignore_permissions`; `owner` = `Guest` untuk jalur agen. |
| K-54 | `last_agent_at` dan `last_pull_at` diperbarui lewat `frappe.db.set_value(..., update_modified=False)` agar Audit Trail Device (`track_changes`) tidak dipenuhi detak. |
| K-55 | Scheduler, hitung ulang otomatis, dan impor tetap manual dulu. Saklar otomatisasi (default mati) ditambahkan ke Settings bersama fitur masing-masing; hook scheduler baru didaftarkan saat fiturnya dibuat. |
| K-56 | ERP berjalan di LAN dengan HTTP. Bila dibuka ke internet, HTTPS wajib dan Allowed IPs sebaiknya diisi. Lihat butir "Sebelum produksi" di [../architecture/agent-api.md](../architecture/agent-api.md). |

## Alternatif yang dipertimbangkan

| Alternatif | Alasan tidak dipilih |
|---|---|
| `pull_method` tunggal (satu jalur per mesin) | Satu mesin bisa dilayani dua jalur; dua centang lebih fleksibel |
| User API key Frappe + role agen | Dipilih token buatan sendiri (pilihan Efendy): bisa dirotasi, tidak membuat user, izin agen tidak melekat di Raw Log |
| `unique_key` di Raw Log | Nama dokumen sudah menjadi kunci unik |
| ADMS / push dari mesin | Ditinggalkan |
| Scheduler otomatis sejak awal | Data nyata belum dipercaya HRD; manual dulu |

## Konsekuensi

- Endpoint agen memakai `allow_guest=True`; perlindungannya adalah token 256-bit, hash di database, saklar default mati, dan pesan error seragam.
- Pemegang token dapat menyisipkan log palsu yang ikut ke Working Hour dan Payroll. Karena itu rotasi token dan Allowed IPs disediakan.
- Log Raw Log berstatus `Menunggu` membuat hari kerja ditandai "perlu tinjau". Bila semua mesin masuk otomatis, beban tinjauan HRD naik.
- Arti status `Terkirim` pada Raw Log belum diketahui (tidak ada kode yang mengisinya; hanya mengunci edit dan ikut dihitung, K-44).
