# HRIS Device Tool: Rencana Kirim Log ke HRIS dan Daftar Pekerjaan

Diperbarui: Selasa, 24 Nov 2026, 08:57 WIB
Status kode: Device Tool 0.6.3, commit terakhir `20ae27d` (di GitHub). Belum ada kode kirim log. Dokumen ini hanya rencana dan catatan.
Dokumen terkait: `docs/development/device-tool-peran-dan-comm-key.md`, `docs/architecture/agent-api.md`, `docs/development/agen-windows.md`.

## 0. Cara Melanjutkan di Chat atau Claude Lain

| Hal | Isi |
|---|---|
| Peran | Claude = developer utama dan partner perencanaan. Efendy (IT Support, Medan) menjalankan skrip, menguji, dan push sendiri |
| Batas Claude | Hanya boleh membuat berkas `.md`. Berkas lain diberikan sebagai skrip PowerShell (here-string, bukan heredoc bash) |
| Urutan kerja | 1) diskusi rancangan tanpa kode, 2) Efendy setuju, 3) skrip + penjelasan + tabel uji + skrip commit, 4) Efendy jalankan dan lapor, 5) perbaiki dan catat di `.md` |
| Gaya | Bahasa Indonesia, istilah teknis Inggris, terstruktur, timestamp WIB (jam:menit) di awal jawaban, akhiri dengan ringkasan: selesai, tertunda, berikutnya |
| PC | **Kantor** `D:\Git\hris` (sekarang dipakai), **rumah** `C:\Users\Efendy\documents\git\hris`. Jalankan skrip patch di satu PC saja, lalu commit dan push dari situ. PC lain cukup `git pull` |
| Kompilasi | `tools\device_tool\build.ps1` (csc .NET 4, **C# 5**: tanpa `$""`, `?.`, `nameof`, expression-bodied). Tutup aplikasi sebelum build |
| Jangan di-add | `.gitignore`, `README.md`, `build.ps1`, `Crypto.cs` (hanya beda akhir baris di PC rumah). Keputusan `.gitattributes` menunggu persetujuan eksplisit |

Gotcha PowerShell: bungkus `if/else` dalam `& { ... }`; patch dengan jangkar teks satu baris; regex memakai string kutip tunggal; validasi semua jangkar sebelum menulis; cadangkan ke `%TEMP%`; tulis UTF-8 tanpa BOM.

## 1. Fakta Sisi HRIS (dari berkas yang sudah dibaca)

| Fakta | Sumber | Status |
|---|---|---|
| Endpoint: `POST /api/method/hris.hris_attendance.integrations.agent_api.push_punches`, hanya POST, `allow_guest` | `agent_api.py`, `agent-api.md` | Terverifikasi (uji 30 Okt) |
| Autentikasi: header `X-HRIS-Token`. Token salah, kosong, saklar mati, IP tidak diizinkan, atau terblokir = HTTP 401 pesan seragam | `agent-api.md` | Terverifikasi |
| Ada pembatas: percobaan salah berulang membuat pengirim **diblokir** | `agent-api.md` (alasan `diblokir`) | Aturan blokirnya belum dibaca (`agent_auth.py`) |
| Body: `device` (nama HRIS Device) + `punches` (daftar objek) | `agent_api.py` | Terverifikasi |
| Kunci baris: `device_user_id`, `punch_time`, `verify_mode`, `punch_status_raw`, `raw_payload` | `punch_ingest.py` | Terverifikasi |
| `punch_time`: WIB **tanpa zona**; lebih dari 1 hari di masa depan = baris error | `punch_ingest.py` | Terverifikasi |
| Maksimal 500 punch per permintaan. Lebih dari itu seluruh permintaan ditolak | `punch_ingest.py` | Terverifikasi di kode |
| Device harus terdaftar, **aktif**, dan **"Via Windows Agent" (`use_agent`) dicentang**. Bila tidak, seluruh permintaan ditolak (HTTP 417) | `punch_ingest.py` | Terverifikasi di kode |
| Duplikat ditolak oleh nama dokumen Raw Log `device-userid-waktu`. Kirim ulang aman (`created 1`, lalu `duplicate 1`). Mesin ikut dalam kunci | `punch_ingest.py`, `agent-api.md` | Terverifikasi |
| Balasan: `received`, `created`, `duplicate`, `error`, `results[{index,status,name/message}]`. Baris rusak = `error`, baris lain tetap diproses | `punch_ingest.py` | Terverifikasi |
| Daftar kosong = heartbeat (hanya memperbarui `last_agent_at`) | `agent_api.py` | Terverifikasi |
| Source yang dikenal: `Agen Windows`, `Pull pyzk`, `Impor File`. Endpoint ini selalu memakai `Agen Windows` | `punch_ingest.py` | Terverifikasi |
| HRIS Device: `autoname = field:device_name` (nama dokumen = Device Name), `device_code` (awalan nama Raw Log), `serial_number` wajib dan unik, `ip_address`, `port` | `hris_device.json/.py` | Terverifikasi |
| Token dikelola di **HRIS Attendance Settings**: `agent_enabled`, `agent_token_prefix`, `agent_token_hash`, `allowed_ips`, tombol Generate / Rotate | `agent-api.md`, Efendy | Hanya **satu** token untuk semua pengirim |
| Tidak ada endpoint baca daftar device atau pembanding hash di server | `agent-api.md` | Terverifikasi |

Belum dibaca: DocType HRIS Raw Log (`.json`/`.py`), `agent_auth.py`, `hris_attendance_settings` (`.json`/`.py`), jalur "Impor File" di HRIS (apakah ada tombol impor atau hanya fungsi).

## 2. Rencana Fitur: Kirim Log ke HRIS (Tahap 5a)

### Keputusan (disetujui "ikut saran")

| # | Keputusan |
|---|---|
| 1 | Uji pertama ke server **uji** (`hris-uji.local`). Produksi (`erp.ciptamebel.co.id`) setelah lulus |
| 2 | Pengirim dari **Kelola salinan** dulu. Tombol langsung setelah Tarik log menyusul |
| 3 | Token memakai token HRIS Attendance Settings yang sudah ada |
| 4 | Tambah kolom **Nama di HRIS** per mesin di dialog Tambah/Ubah mesin |
| 5 | Source tetap `Agen Windows` (tanpa ubah server). Pembeda: `raw_payload` berisi `{"via":"Device Tool","workcode":N}` |

### Catatan dan koreksi

| Hal | Penjelasan |
|---|---|
| Token tidak bisa khusus Device Tool | Settings hanya menyimpan satu token. Agen PowerShell dan Device Tool berbagi token. **Rotasi token memutus keduanya.** Token terpisah per pengirim butuh perubahan server (disimpan sebagai pekerjaan opsional di bagian 4) |
| Pemetaan mesin | "Otomatis" belum mungkin karena tidak ada endpoint baca device. Tahap pertama: isi manual sekali per mesin. Otomatis (cocok IP atau serial) menunggu endpoint baru |
| Prasyarat per mesin | HRIS Device harus ada, aktif, dan "Via Windows Agent" dicentang. Dicek lewat daftar HRIS Device sebelum uji |
| Daftar IP | Bila Allowed IPs diisi, IP PC kantor (dan rumah, bila terjangkau server) harus masuk daftar |
| Token salah | Device Tool **berhenti pada HTTP 401 pertama** dan tidak mencoba ulang, agar tidak memicu blokir |
| HTTPS/TLS | .NET 4 tidak otomatis memakai TLS 1.2. Di kode: `ServicePointManager.SecurityProtocol = (SecurityProtocolType)3072` bila memakai HTTPS. URL dasar dapat diatur (HTTP LAN atau HTTPS) |
| `workcode` | Tidak ada di kontrak. Dititipkan di `raw_payload` |

### Rancangan teknis

| Hal | Rencana |
|---|---|
| Berkas baru | `KirimHris.cs` (pengirim) dan perubahan kecil di `Settings.cs` (kolom mesin, URL, token), `Dialogs.cs` (kolom "Nama di HRIS"), `KelolaSalinan.cs` (kolom Terkirim, tombol Kirim), `Peran.cs` (aksi baru), `MainForm.cs` (tombol Pengaturan HRIS) |
| Penyimpanan token dan URL | Token: DPAPI (pola `Dpapi.cs`, bukan di `mesin.hdtdata`). URL: berkas pengaturan biasa. Per PC |
| Cara kirim | `HttpWebRequest` (C# 5), JSON dibuat manual (tanpa pustaka), batch 500, urut waktu |
| Perkiraan batch | WP 221 (1154 baris) = 3 batch; PLTB (6352) = 13; Kiri (7459) = 15 |
| Hasil | Dialog ringkasan: diterima, `created`, `duplicate`, `error`. Baris `error` disimpan ke berkas `.hdterr` di samping salinan dengan alasannya |
| Penanda terkirim | Baris `terkirim=` (waktu, server, created, duplicate, error) ditambahkan ke manifest `.hdtman`. Hash CSV tidak terpengaruh (manifest bukan bagian hash). Kolom **Terkirim** di Kelola salinan |
| Kirim ulang | Aman (duplikat ditolak server). Tombol kirim tidak mengubah CSV |
| Hapus salinan belum terkirim | Peringatan tambahan sebelum hapus ke sampah dan hapus permanen |
| Pagar peran | Kirim ke HRIS: supervisor (2). Isi token, URL, dan pemetaan: administrator (5). Daftarkan di `Peran.cs` |
| Log aktivitas | Kategori `tarik-log`, hanya jumlah dan nama berkas. **Token tidak pernah dicatat** |
| Versi | 0.7.0 (kirim ke HRIS) |

### Tabel uji (rencana)

| # | Uji | Hasil benar |
|---|---|---|
| 1 | Kirim daftar kosong (tes koneksi/heartbeat) | HTTP 200, Last Agent Sync device terisi |
| 2 | Token salah | Pesan jelas, berhenti, tidak ada percobaan ulang |
| 3 | Salinan kecil dari mesin uji | `created` = jumlah baris |
| 4 | Kirim ulang salinan yang sama | `duplicate` = jumlah baris, `created` 0 |
| 5 | Mesin tanpa "Via Windows Agent" | Pesan penolakan device terbaca jelas |
| 6 | Salinan besar (PLTB, 13 batch) | Selesai, jumlah cocok, UI tidak membeku |
| 7 | Cek Raw Log di HRIS | `source` = Agen Windows, `device` benar, waktu WIB sama dengan CSV |
| 8 | Peran `user` mencoba kirim | Ditolak (butuh supervisor) |
| 9 | Hapus salinan belum terkirim | Ada peringatan |

### Yang masih dibutuhkan sebelum kode

1. Unggah: DocType HRIS Raw Log (`.json`, `.py`), `agent_auth.py`, `hris_attendance_settings` (`.json`, `.py`).
2. Cek di HRIS: daftar HRIS Device sudah memuat 9 mesin? Nama persisnya? "Via Windows Agent" dicentang? Isi Allowed IPs?
3. Alamat server uji (host atau IP, port) dan apakah dapat dijangkau dari PC kantor.
4. Token baru dari Settings dipakai khusus uji. Jangan ditempel ke chat.

## 3. Daftar Pekerjaan Lain (Berurutan)

| Urutan | Pekerjaan | Ukuran | Catatan |
|---|---|---|---|
| 1 | Tahap 5a: kirim log ke HRIS (bagian 2) | Besar | Menunggu berkas dan jawaban bagian 2 |
| 2 | Impor CSV ke HRIS (cadangan, wajib tetap ada) | Sedang | Perlu baca jalur "Impor File" di HRIS. Kolom `workcode` tidak punya tempat di kontrak |
| 3 | Pengecekan duplikat timbal balik HRIS dan Device Tool (ID+jam sama, mesin beda) | Sedang | Kunci server memuat mesin, jadi kasus ini tidak terdeteksi otomatis |
| 4 | Generator ID 5 digit lintas mesin (berikutnya `99903`, ID uji `99901` dan `99902` terpakai) | Sedang | ID tertinggi dicari lintas semua mesin. Auto increment yang bisa di-refresh dan di-reset |
| 5 | Aturan distribusi per department dan tahap Salin user/jari antar mesin | Besar | Menunggu pertanyaan terbuka 1 dan 2. Tanpa hapus otomatis. Disimpan di Device Tool dulu, nanti DocType HRIS |
| 6 | 2e ubah privilege, 2f hapus user/log (konfirmasi 2x, awalnya hanya ID uji) | Sedang | Pagar: direksi untuk hapus, manager untuk restart. Pengaman 2f belum dijawab |
| 7 | Sinkron jam (`SetDeviceTime`), restart mesin, Pindai `GetDeviceInfo(1,1..68)` | Sedang | Konfirmasi 2x, restart di luar jam masuk dan pulang |
| 8 | 3b pendengar event (aplikasi terpisah), StartEnrollEx flag 0/1, StartIdentify, wajah | Besar | Butuh `Interop.zkemkeeper.dll` |
| 9 | Hapus log mesin per tanggal | Besar | **Ditunda**. Nama fungsi SDK (`DeleteAttlogBetweenTheDate`, `DeleteAttlogByTime`) belum terverifikasi. Minta Efendy mengirim potongan dokumentasi SDK (cari "DeleteAttlog"). Syarat: log aman di HRIS, CSV+hash ada, konfirmasi 2x |
| 10 | Tarik log terjadwal dan otomatis terus-menerus | Besar | Hanya dicatat. Manual dulu |
| 11 | Dokumen `.md` untuk 0.6.3 dan tahap 5a | Kecil | Digabung setelah 5a selesai |

### Pekerjaan opsional di server HRIS (perlu persetujuan, tidak mengubah core)

| Usulan | Manfaat |
|---|---|
| Endpoint baca daftar device (nama, IP, serial) untuk pemetaan otomatis | Mengganti isian manual "Nama di HRIS" |
| Token per pengirim (agen PowerShell dan Device Tool terpisah) | Rotasi satu tidak memutus yang lain |
| Source baru `Device Tool` di `SOURCES` | Pembeda yang bersih di Raw Log, tanpa `raw_payload` |
| Endpoint pembanding hash CSV | Hash C# dan HRIS dibandingkan langsung |

### Kebersihan kode (kecil, kapan saja)

- `PilihMesin.Gaya` di `AlatBantu.cs` tidak terpakai lagi sejak 0.6.3.
- `Crypto.cs` hanya dipakai untuk migrasi berkas lama. Boleh dihapus setelah semua PC termigrasi.
- Teks tab Bantuan masih memuat "salin SELURUH folder aplikasi"; Comm Key harus diisi sekali di PC lain.
- Tombol **Buka folder data** dan **Bersihkan log** belum dipagari (batas "pagar pengaman, bukan keamanan penuh").

## 4. Pertanyaan Terbuka

1. Karyawan resign lalu masuk lagi di department lain (contoh Sizing ke Finishing): bagaimana aturannya di mesin?
2. Karyawan cukup di mesin lokasinya atau di semua mesin? (menahan tahap Salin)
3. Pengaman fitur hapus 2f belum dijawab.
4. `.gitattributes` untuk menyeragamkan akhir baris (mengubah banyak berkas, perlu persetujuan eksplisit).
5. Pagar restart, ubah privilege, dan hapus: manager atau direksi? (rancangan sekarang: manager untuk restart, direksi untuk hapus.)
6. Perlu token per pengirim dan endpoint baca device di server (bagian opsional di atas)?

## 5. Fakta Teknis yang Perlu Diingat

| Fakta | Nilai |
|---|---|
| Mesin (9), port 4370 | Kiri `10.1.0.211`, Sizing `.212`, Finishing `.215`, Kanan `.216`, Showroom `.217`, Cemara `.218`, Sena `.219`, PLTB `.220`, WP 221 `.221`. Comm Key sungguhan hanya di WP 221 |
| `GetDeviceStatus` | Indeks 25 membuat aplikasi crash; batas aman 1-24 |
| Verifikasi di log | 1 = sidik jari, 15 = wajah |
| Status log | WP 221 = 255 di semua baris; Kanan = 0 (tidak mencatat masuk/pulang sungguhan) |
| Format salinan | CSV `device_user_id;punch_time;verify_mode;punch_status_raw;workcode`, UTF-8 tanpa BOM, CRLF. Manifest `.hdtman` berisi `format=hdt-log-1`, `sha256`, dan seterusnya |
| Peran | user < supervisor < manager < direksi < administrator. Aksi yang tidak terdaftar otomatis butuh administrator |
| Comm Key | DPAPI per PC (`HDT2`). Di PC lain diisi sekali lagi |
