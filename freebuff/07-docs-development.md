# Rangkuman: `docs/development`

Diperiksa: 27 November 2026.

## Berkas

| Berkas | Ukuran | Isi | Status |
|---|---|---|---|
| `agen-windows.md` | 6,3 KB | Agen Windows (SDK zkemkeeper 32-bit), kontrak endpoint, token, `allowed_ips` | Sesuai kode |
| `device-tool-0.7.0-kirim-log.md` | 7,7 KB | Device Tool 0.7.x: tarik log → kelola salinan → kirim ke HRIS, hasil uji 24 Nov | Sebagian sudah usang (versi kini 0.8.0) |
| `device-tool-0.7.2-catatan.md` | 3,0 KB | Perubahan 0.7.2 (tab, baris status), temuan data mesin, status produksi | Sesuai |
| `device-tool-peran-dan-comm-key.md` | 4,5 KB | Tahap 3d–0.6.2: peran/login, Comm Key DPAPI | Sesuai |
| `device-tool-rencana-kirim-log.md` | 13 KB | Rencana kirim log + daftar pekerjaan lain | Sebagian sudah selesai (jadi rencana usang) |
| `doctype-checklist.md` | 2,4 KB | Checklist DocType HRIS baru (penamaan, audit tab, izin, uji) | Berlaku |
| `generator-id-finger-dan-celah-4-nov.md` | 4,5 KB | Status generator ID Finger per 25 Nov | Berlaku |
| `kartu-profil-employee.md` | 4,0 KB | Kartu profil HRIS Employee, selesai 26 Nov | Berlaku |
| `rancangan-generator-id-karyawan.md` | 3,2 KB | Rancangan U1–U7 | U1–U7 disetujui; sebagian sudah dikodekan (`id_finger.py`) |
| `rencana-perbaikan-uji.md` | 3,5 KB | Rencana perbaikan uji usang 17 Nov | Selesai (5 commit) |
| `testing.md` | 2,1 KB | Cara uji | **Usang**: menyatakan "unit test per modul belum ditulis", padahal ada ±80 berkas uji |
| `ai-workflow.md` | 1,1 KB | Aturan kerja AI: hanya `.md` yang di-push, sisanya heredoc | Berlaku |
| `coding-standards.md` | 51 B | "Kerangka — belum diisi" | **Kosong** |
| `contribution.md` | 74 B | "Kerangka — belum diisi" | **Kosong** |
| `development.md` | 94 B | "Kerangka — belum diisi" | **Kosong** |

## Temuan

1. Tiga berkas kosong membuat aturan kontribusi dan standar kode tidak punya
   acuan tertulis, padahal praktiknya sudah jelas (tab, awalan `HRIS `,
   `PATCH`, audit tab).
2. `testing.md` paling menyesatkan: isinya bertentangan dengan isi folder
   `tests/` yang berisi puluhan uji.
3. Empat berkas Device Tool cukup berlapis (0.7.0, 0.7.2, peran, rencana).
   Tidak ada berkas untuk 0.7.3/0.8.0, padahal commit terakhir 0.8.0.
4. `rencana-perbaikan-uji.md` sudah selesai tetapi belum ditandai selesai.
