# Agent API: penerimaan punch dari agen Windows

Diperbarui: 30 Oktober 2026. Keputusan: [K-46 sampai K-56](../decisions/0003-jalur-data-mesin.md).

## 1. Gambaran

Agen Windows (middleware) membaca log dari mesin lewat SDK lalu mengirimnya ke HRIS lewat satu endpoint HTTP. Jalur Pull pyzk (Sesi 3) memakai fungsi penyimpan yang sama.

```
Mesin -> agen Windows --HTTP POST + token--> push_punches
                                              |-> verify_agent_request (agent_auth.py)
                                              |-> save_punches (punch_ingest.py)
                                                    |-> HRIS Raw Log (source = Agen Windows)
```

## 2. Komponen

Path dasar: `hris/hris_attendance/`

| File | Fungsi |
|---|---|
| `integrations/agent_api.py` | `push_punches(device, punches)`: `allow_guest=True`, hanya POST |
| `services/agent_auth.py` | `hash_token`, `verify_agent_request()` (header, saklar, hash waktu-konstan, daftar IP, pembatas, log ke logger `hris_agent`) |
| `services/punch_ingest.py` | `save_punches(device, punches, source)`: penyimpan bersama untuk semua jalur |
| `doctype/hris_attendance_settings/` | DocType Single: `agent_enabled`, `agent_token_prefix`, `agent_token_hash` (tersembunyi), `token_generated_on`, `token_generated_by`, `allowed_ips`, tombol Generate / Rotate Token |

## 3. Kontrak endpoint

```
POST http://<IP server>:8000/api/method/hris.hris_attendance.integrations.agent_api.push_punches
Header: X-HRIS-Token: <token>     Content-Type: application/json
Body:   {"device": "<nama HRIS Device>",
         "punches": [{"device_user_id": "1001", "punch_time": "2026-10-30 07:42:10",
                      "verify_mode": "1", "punch_status_raw": "0",
                      "raw_payload": {}}]}
Balasan: {"message": {"device", "received", "created", "duplicate", "error",
          "results": [{"index", "status", "name" atau "message"}]}}
```

| Kondisi | Hasil | Terverifikasi |
|---|---|---|
| Token kosong, salah, saklar mati, IP tidak diizinkan, atau terblokir | HTTP 401, pesan seragam "Token agen tidak valid." Alasan sebenarnya hanya di log `hris_agent` | Ya (HTTP dan log) |
| Metode GET | HTTP 403 | Ya |
| Device tidak terdaftar, tidak aktif, atau jalurnya tidak dicentang | HTTP 417 (seluruh permintaan ditolak) | Ya (device tidak terdaftar) |
| Batch lebih dari 500, `punches` bukan daftar | Seluruh permintaan ditolak | Uji console saja |
| Waktu rusak, berzona, masa depan, `device_user_id` kosong, baris bukan objek | Baris itu `error`, baris lain tetap diproses (HTTP 200) | Ya (baris rusak) |
| Daftar kosong | Detak: hanya memperbarui `last_agent_at` (HTTP 200) | Ya |
| Baris valid, lalu kirim ulang | `created` 1, lalu `duplicate` 1 | Ya |

## 4. Alasan penolakan di log

File log: `logs/hris_agent.log` di bench. Alasan yang tercatat: `saklar mati`, `token kosong`, `ip tidak diizinkan`, `diblokir`. Waktu di log tampaknya UTC (selisih 7 jam dari WIB); belum diverifikasi.

## 5. Hasil uji (30 Okt 2026)

| Uji | Cara | Hasil |
|---|---|---|
| Console Sesi 1, 2A, 2B | Skrip di `bench console` | Semua lulus |
| Token, GET, detak, device tidak terdaftar, baris rusak, baris valid, duplikat | PowerShell dari PC kantor | Lulus |
| Saklar mati menolak token benar | Log `alasan=saklar mati` | Lulus |
| Daftar IP | Isi daftar lalu `curl` dari server: 401, log `ip tidak diizinkan`; kosongkan: 200 | Lulus |
| Rotasi token | Token lama 200, generate, token baru 200, token lama 401 | Lulus |
| Browser | Last Agent Sync terisi; Raw Log `source` = Agen Windows (read-only), Owner `Guest`, satu baris (tanpa duplikat) | Lulus |
| Raw Payload tampil di form | Tidak terlihat di screenshot | Belum terkonfirmasi |

Kegagalan PowerShell sebelumnya (10 lulus, 4 gagal) berasal dari urutan di browser (Simpan belum selesai saat Enter ditekan), bukan bug server; terbukti lewat `curl`. Data uji sudah dihapus.

## 6. Keamanan

| Hal | Catatan |
|---|---|
| Endpoint Guest | Perlindungan: token 256-bit, hash di database, saklar mati secara default, pesan error seragam |
| `frappe.local.request_ip` | Setahu saya membaca `X-Forwarded-For` bila ada, sehingga bisa dipalsukan tanpa proxy tepercaya. Daftar IP dan pembatas hanya lapisan tambahan; perlindungan utama adalah token. Verifikasi di dokumentasi Frappe |
| HTTP polos di LAN | Token terlihat bagi yang menyadap jaringan. Wajar untuk LAN tertutup; wajib HTTPS bila dibuka ke internet |
| Absensi palsu | Pemegang token dapat menyisipkan log palsu sampai Working Hour dan payroll. Rotasi token dan Allowed IPs adalah mitigasinya |
| Token di chat atau terminal | Jangan ketik token di teks prompt `read -p`; tempel di baris kosong (`read -s`). Token yang pernah tampil harus dirotasi |

## 7. Sebelum produksi (belum dikerjakan, perlu persetujuan)

- `developer_mode` dimatikan (mode ini juga membuat edit DocType lewat UI menulis ulang file JSON di app).
- Server pengembangan (`bench start`, `frappe serve`, tanpa nginx) diganti nginx, supervisor, dan HTTPS.
- Worker perlu dimuat ulang bila ada job background baru (web dimuat ulang otomatis oleh server pengembangan, worker tidak).
- Rotasi token.

## 8. Pelajaran dari uji

- Jangan menempel skrip berisi `Read-Host` ke konsol PowerShell; buat file `.ps1` lewat here-string lalu jalankan dengan `-ExecutionPolicy Bypass -File`.
- Alamat server ERP dan alamat mesin absensi berbeda; skrip uji memeriksa `/api/method/ping` lebih dulu.
- Setiap perubahan Settings di browser harus benar-benar tersimpan (tanda "Not Saved" hilang) sebelum menjalankan uji berikutnya; verifikasi lewat skrip baca-saja.
- Blok heredoc panjang yang ditempel bisa kehilangan baris pertama; jalankan per langkah (buat file, jalankan, hapus).
