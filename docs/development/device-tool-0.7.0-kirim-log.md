# HRIS Device Tool 0.7.0: Kirim Log ke HRIS

Diperbarui: Selasa, 24 Nov 2026, 13:30 WIB (perkiraan)
Status kode: commit `307f916` di GitHub (`main`). Diuji di server **uji** (`hris-uji.local`, `http://10.1.0.26:8001`). Belum dipakai di produksi.
Dokumen terkait: `docs/development/device-tool-rencana-kirim-log.md`, `docs/architecture/agent-api.md`.

## 1. Ringkasan

Device Tool kini bisa mengirim salinan log yang sudah ditarik dari mesin (CSV di folder `data\tarikan`) ke HRIS lewat endpoint agen (`push_punches`). Tombol ada di jendela **Kelola salinan**. Kirim ulang aman: baris yang sudah ada dihitung `duplicate`, bukan data ganda.

## 2. Komponen

| Berkas (`tools/device_tool/src`) | Isi |
|---|---|
| `KirimHris.cs` (baru) | Pembaca CSV, pembuat JSON, pengirim batch 500, dialog progress (bar, hitungan, penghitung waktu, tombol Batal), tes koneksi |
| `PengaturanHris.cs` (baru) | Penyimpanan token terenkripsi Windows (`data\hris.hdtsec`) dan dialog **Pengaturan HRIS** |
| `Settings.cs` | Field `MesinItem.NamaDiHris` dan `AppData.UrlHris` |
| `Dialogs.cs` | Kolom **Nama di HRIS** di dialog Tambah/Ubah mesin |
| `KelolaSalinan.cs` | Kolom **Terkirim ke HRIS**, tombol **Kirim ke HRIS (dicentang)** dan **Pengaturan HRIS**, penanda `terkirim=` di manifest, berkas `.hdterr`, peringatan hapus salinan belum terkirim |
| `Peran.cs` | `OnKirimHris` = supervisor, `OnPengaturanHris` = administrator |
| `MainForm.cs` | Versi `0.7.0 (kirim log ke HRIS)` |

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
| Token | Terenkripsi DPAPI per PC dan akun Windows. Tidak ada di `mesin.hdtdata`, tidak pernah ditulis ke log aktivitas. Di PC lain diisi sekali lagi |
| Format token | Diperiksa di PC sebelum dikirim (48 karakter, awalan `hris_`) agar token salah tidak menambah hitungan blokir |
| HTTP 401 atau 417 atau jaringan | Pengiriman **berhenti** di kegagalan pertama, tanpa percobaan ulang otomatis |
| Blokir server | `agent_auth.py`: 10 kegagalan per 600 detik per **IP** memblokir semua pengirim dari IP itu (termasuk agen PowerShell) |
| Satu token | HRIS Attendance Settings hanya menyimpan satu token. Rotate memutus agen PowerShell dan Device Tool sekaligus |
| Source di Raw Log | `Agen Windows`. Pembeda: `raw_payload` = `{"via":"Device Tool","workcode":N}` (string, disimpan apa adanya oleh `punch_ingest.py`) |
| Kunci duplikat | `punch_key` = `{nama device}\|{ID}\|{waktu sampai detik}` (`raw_log_naming.py`) |

## 5. Hasil Uji (24 Nov 2026)

| Uji | Hasil | Bukti |
|---|---|---|
| Heartbeat (daftar kosong) ke server uji | Lulus | HTTP 200, device `CML Lapangan Kiri` |
| Tes koneksi dari dialog Pengaturan HRIS | Lulus | Pesan BERHASIL, HTTP 200 |
| Kirim 200 baris, lalu kirim ulang | Lulus | `created 200`, lalu `duplicate 200` |
| Kirim penuh CSV Kiri (7.821 baris) | Lulus | `created 7621`, `duplicate 200`, `error 0`, 23 detik, 16 batch |
| Kirim dari Kelola salinan (Kiri, 7.821 baris) | Lulus | `duplicate 7821`, `error 0`, 9 detik |
| Token salah | Lulus | Berhenti di batch 1, pesan HTTP 401, satu permintaan |
| Token tidak lengkap | Lulus | Ditolak di PC, tidak ada permintaan ke server |
| Raw Log hasil kirim | Lulus | Source Agen Windows, Device benar, waktu WIB sama, Employee otomatis cocok |
| Token tidak ada di `mesin.hdtdata` | Lulus | `Select-String` tanpa hasil |
| CSV yang sudah diubah | Terdeteksi | CSV Kanan tampil `BERUBAH` (merah) di Kelola salinan |

**Belum diuji:**

| Uji | Catatan |
|---|---|
| Kolom Terkirim terisi setelah kirim | Perlu dilihat setelah dialog progress ditutup |
| Berkas `data\hris.hdtsec` terbentuk | Perlu dilihat setelah Simpan |
| Peran user ditolak kirim, supervisor ditolak Pengaturan HRIS | Perlu login bergantian |
| Peringatan hapus salinan belum terkirim | Perlu salinan berstatus belum terkirim (misalnya PLTB) |
| HTTP 417 lewat aplikasi (mesin tanpa Via Windows Agent) | Perlu token valid dan CSV PLTB |
| Pull dan Agent bersamaan (Showroom) | Perlu keputusan mencentang Via Agent di CML Showroom |
| Judul aplikasi `0.7.0` dan Ubah mesin menyimpan Nama di HRIS | Nama di HRIS sudah terbukti terbaca saat kirim |

## 6. Temuan

| Temuan | Arti |
|---|---|
| CSV Kanan (`tarikan_Kanan_20261123_125718.csv`) berformat waktu `dd/MM/yyyy HH:mm` tanpa detik dan hash `BERUBAH` | Berkas kemungkinan pernah dibuka dan disimpan ulang di spreadsheet (dugaan, belum terbukti). **Jangan dikirim.** Tarik ulang dari mesin |
| Empat mesin (Kiri, Sizing, Finishing, Kanan) belum punya Raw Log di `hris-uji.local` walau `last_pull_at` terisi | Belum diselidiki. Kiri kini terisi dari uji ini |
| `Created By` Raw Log = Guest | Wajar: endpoint agen memakai `allow_guest`. Belum dibandingkan dengan Raw Log lama WP 221 |

## 7. Keterbatasan Saat Ini

- Satu alamat server dan satu token per PC. Berpindah antara server uji dan produksi berarti mengisi ulang Pengaturan HRIS. Token produksi dan uji berbeda.
- Pemetaan Nama di HRIS bersifat manual per mesin. Bila nama mesin di aplikasi diubah, salinan lama yang manifest-nya memuat nama lama tidak menemukan pasangannya dan kirim ditolak dengan pesan jelas.
- Berkas `.hdterr` tidak ikut dipindah ke sampah atau dihapus bersama pasangan CSV dan manifest.
- Teks tab Bantuan masih menyebut "salin SELURUH folder aplikasi" dan belum menyebut token HRIS yang harus diisi ulang di PC lain.

## 8. Rencana Berikutnya

| Urutan | Pekerjaan |
|---|---|
| 1 | Selesaikan uji yang tertunda (bagian 5) |
| 2 | Tarik ulang CSV Kanan dari mesin |
| 3 | Putuskan uji Pull vs Agent (Showroom), lalu centang Via Windows Agent di device lain |
| 4 | Uji di produksi (`erp.ciptamebel.co.id:8000`) dengan token produksi, setelah semua uji lulus |
| 5 | Matikan Via Pull per device hanya setelah kiriman Device Tool terbukti benar |
| 6 | Pekerjaan daftar lain: impor CSV, generator ID 5 digit, aturan distribusi, ubah privilege, hapus user/log, sinkron jam, restart |
