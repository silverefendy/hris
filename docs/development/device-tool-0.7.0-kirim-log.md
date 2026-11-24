# HRIS Device Tool 0.7.x: Kirim Log ke HRIS

Diperbarui: Selasa, 24 Nov 2026, sekitar 14:55 WIB
Status kode: 0.7.0 (`307f916`) dan 0.7.1 (`84f8211`) di GitHub (`main`). Diuji di server **uji** (`hris-uji.local`, `http://<server-uji>:8001`). Belum dipakai di produksi.
Versi 0.7.2 (menu dirapikan) sedang disiapkan dan belum tercatat di dokumen ini sebagai fitur teruji.
Dokumen terkait: `docs/development/device-tool-rencana-kirim-log.md`, `docs/architecture/agent-api.md`.

## 1. Ringkasan

Device Tool mengirim salinan log yang sudah ditarik dari mesin (CSV di folder `data\tarikan`) ke HRIS lewat endpoint agen (`push_punches`). Tombol ada di jendela **Kelola salinan**. Kirim ulang aman: baris yang sudah ada dihitung `duplicate`, bukan data ganda.

## 2. Komponen

| Berkas (`tools/device_tool/src`) | Isi |
|---|---|
| `KirimHris.cs` | Pembaca CSV, pembuat JSON, pengirim batch 500, dialog progress (bar, hitungan, penghitung waktu, tombol Batal), tes koneksi, pesan kegagalan terbaca |
| `PengaturanHris.cs` | Penyimpanan token terenkripsi Windows (`data\hris.hdtsec`) dan dialog **Pengaturan HRIS** |
| `Settings.cs` | `MesinItem.NamaDiHris`, `MesinItem.NamaLama`, `AppData.UrlHris` |
| `Dialogs.cs` | Kolom **Nama di HRIS** di dialog Tambah/Ubah mesin, dan pencatatan nama lama otomatis saat nama diganti |
| `KelolaSalinan.cs` | Kolom **Terkirim ke HRIS**, tombol **Kirim ke HRIS (dicentang)** dan **Pengaturan HRIS**, penanda `terkirim=` di manifest, tampilan tujuan di konfirmasi, peringatan hapus salinan belum terkirim |
| `Peran.cs` | `OnKirimHris` = supervisor, `OnPengaturanHris` = administrator |

## 3. Cara Pakai (Urutan Pertama Kali)

| # | Langkah | Siapa |
|---|---|---|
| 1 | Di HRIS: buka HRIS Device mesin terkait, centang **Via Windows Agent**, Save | HRD/IT |
| 2 | Di HRIS Attendance Settings: **Rotate token**, salin token (hanya tampil sekali) | HRIS Manager / System Manager |
| 3 | Di Device Tool, Ubah mesin: isi **Nama di HRIS** persis seperti Device Name di HRIS | administrator |
| 4 | Kelola salinan, **Pengaturan HRIS**: isi alamat server dan token (48 karakter, diawali `hris_`), **Tes koneksi**, **Simpan** | administrator |
| 5 | Tarik log mesin, buka Kelola salinan, centang salinan, **Kirim ke HRIS** | supervisor ke atas |

Aturan kirim: salinan hanya dikirim bila Nama di HRIS terisi dan hash `cocok`. Hash `BERUBAH` atau `tanpa hash` ditolak. Salinan ditandai terkirim hanya bila selesai penuh dengan `error 0`.

## 4. Keamanan dan Perilaku Penting

| Hal | Perilaku |
|---|---|
| Token | Terenkripsi DPAPI per PC dan akun Windows (`hris.hdtsec`). Tidak ada di `mesin.hdtdata`, tidak pernah ditulis ke log aktivitas. Di PC lain diisi sekali lagi |
| Format token | Diperiksa di PC sebelum dikirim (48 karakter, awalan `hris_`) agar token salah tidak menambah hitungan blokir |
| HTTP 401, 417, atau jaringan | Pengiriman **berhenti** di kegagalan pertama, tanpa percobaan ulang otomatis |
| Blokir server | `agent_auth.py`: 10 kegagalan per 600 detik per **IP** memblokir semua pengirim dari IP itu, termasuk agen PowerShell |
| Satu token | HRIS Attendance Settings hanya menyimpan satu token. Rotate memutus agen PowerShell dan Device Tool sekaligus |
| Source di Raw Log | `Agen Windows`. Pembeda: `raw_payload` = `{"via":"Device Tool","workcode":N}` (string, disimpan apa adanya oleh `punch_ingest.py`) |
| Kunci duplikat | `punch_key` = `{nama device}\|{ID}\|{waktu sampai detik}` (`raw_log_naming.py`) |
| Ganti nama mesin | Manifest salinan mencatat nama mesin saat ditarik. Sejak 0.7.1 nama lama dicatat otomatis (`NamaLama`) sehingga salinan lama tetap bisa dikirim. Nama yang persis sama dengan mesin saat ini selalu didahulukan. Konfirmasi kirim menampilkan tujuan, contoh `Kiri (kini bernama Lap Kiri) -> CML Lapangan Kiri` |
| Sandi peran | Sandi bawaan ada di kode. **Ganti semua sandi bawaan** lewat Ganti sandi sebelum dipakai orang lain |

## 5. Hasil Uji (24 Nov 2026, Server Uji)

| Uji | Hasil | Bukti |
|---|---|---|
| Heartbeat (daftar kosong) | Lulus | HTTP 200, device `CML Lapangan Kiri` |
| Tes koneksi dari dialog Pengaturan HRIS | Lulus | BERHASIL, HTTP 200 |
| Kirim 200 baris lalu kirim ulang | Lulus | `created 200`, lalu `duplicate 200` |
| Kirim penuh CSV Kiri (7.821 baris) lewat PowerShell | Lulus | `created 7621`, `duplicate 200`, `error 0`, 23 detik, 16 batch |
| Kirim dari Kelola salinan (Kiri) | Lulus | `duplicate 7821`, `error 0`, 9 detik. Kolom Terkirim terisi |
| Token salah | Lulus | Berhenti di batch 1, pesan HTTP 401, satu permintaan |
| Token tidak lengkap | Lulus | Ditolak di PC, tanpa permintaan ke server |
| Raw Log hasil kirim | Lulus | Source Agen Windows, Device benar, waktu WIB sama, Employee otomatis cocok |
| Token tersimpan dan tidak bocor | Lulus | `hris.hdtsec` 314 B berawalan HDT2, tidak ada `hris_` di `mesin.hdtdata` |
| Peran user ditolak kirim, supervisor ditolak Pengaturan HRIS | Lulus | Tercatat di log aktivitas |
| Peringatan hapus salinan belum terkirim | Lulus | Diuji manual |
| HTTP 417 lewat aplikasi | Lulus | CML Cemara (Via Agent belum dicentang) berhenti dengan 417, kolom Terkirim tetap `belum` |
| Pull dan Agent bersamaan (Showroom) | Lulus | Kirim 437 baris: `created 106`, `duplicate 331`, `error 0`. Server: Pull 1.057 ditambah Agen 106, tanpa ganda |
| Ubah mesin tetap menyimpan Nama di HRIS | Lulus | Setelah ganti nama, tes koneksi tetap memakai nama HRIS |
| Nama lama (0.7.1) | Lulus | Uji 1 sampai 4 lulus: salinan `mesin=Kiri` terkirim sebagai mesin Lap Kiri, pencatatan otomatis, pesan 417 terbaca |
| CSV yang sudah diubah | Terdeteksi | CSV Kanan tampil `BERUBAH` (merah) di Kelola salinan |

## 6. Temuan

| Temuan | Arti |
|---|---|
| Data Agent pertama Showroom bertanggal 19 Nov 17:00, tepat setelah data Pull terakhir (19 Nov 08:06) | Device Tool mengisi celah data yang tidak tertarik. Dugaan: Pull tidak berjalan rutin (belum diperiksa) |
| CSV Kanan berformat waktu `dd/MM/yyyy HH:mm` tanpa detik dan hash `BERUBAH` | Berkas kemungkinan pernah dibuka dan disimpan ulang di spreadsheet (dugaan). **Jangan dikirim.** Tarik ulang dari mesin |
| Tiga mesin (Sizing, Finishing, Kanan) belum punya Raw Log di `hris-uji.local` walau `last_pull_at` terisi | Belum diselidiki |
| `Created By` Raw Log = Guest | Wajar: endpoint agen memakai `allow_guest`. Belum dibandingkan dengan Raw Log lama WP 221 |

## 7. Keterbatasan Saat Ini

- Satu alamat server dan satu token per PC. Berpindah antara server uji dan produksi berarti mengisi ulang Pengaturan HRIS. Token produksi dan uji berbeda.
- Pemetaan Nama di HRIS manual per mesin.
- Nama lama hanya dicatat saat nama diganti lewat aplikasi versi 0.7.1 atau lebih baru. Penggantian nama sebelumnya perlu dicatat sekali lewat skrip.
- Berkas `.hdterr` belum ikut dipindah ke sampah atau dihapus bersama pasangannya (perbaikan disiapkan di 0.7.2).
- Teks tab Bantuan belum menyebut token HRIS yang harus diisi ulang di PC lain (perbaikan disiapkan di 0.7.2).

## 8. Rencana Berikutnya

| Urutan | Pekerjaan |
|---|---|
| 1 | 0.7.2: menu dirapikan (tab Log absensi, tombol dikelompokkan), `.hdterr` ikut sampah, teks Bantuan |
| 2 | Selidiki tiga mesin tanpa Raw Log, tarik ulang CSV Kanan |
| 3 | Centang Via Windows Agent di device lain (Via Pull dimatikan per device hanya setelah kiriman Device Tool terbukti benar) |
| 4 | Ganti sandi bawaan semua peran |
| 5 | Uji di produksi (`erp.ciptamebel.co.id:8000`) dengan token produksi |
| 6 | Pekerjaan daftar lain: impor CSV, generator ID 5 digit, aturan distribusi, ubah privilege, hapus user/log, sinkron jam, restart |
