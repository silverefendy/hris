# Rangkuman: `scripts/operations/k102`

Diperiksa: 27 November 2026. Enam skrip + satu README, disimpan sebagai
**arsip acuan**; skrip yang benar-benar dijalankan ada di
`/home/it/runbook_k102/` di server.

| Berkas | Baris | Fungsi |
|---|---|---|
| `runbook_k102.sh` | 256 | Fungsi dasar: `cadangan`, `restore`, pemeriksaan, pembacaan password root lewat `read -s` |
| `produksi_k102.sh` | 153 | Pintu masuk produksi: `cadangan`, `siap`, `mulai`, `pulihkan`; tanpa `SITE_TARGET` sasaran = produksi |
| `gladi_k102.sh` | 91 | Gladi resik di site uji (termasuk langkah 2c `cek_pasca`) |
| `diag_erp_k102.sh` | 44 | Diagnosa server: commit app, status pohon kerja |
| `diag_db_k102.sh` | 6 | Pembungkus `diag_db_k102.py` |
| `diag_db_k102.py` | 31 | Pemeriksaan jumlah dan kondisi Employee |
| `cek_pasca.sh` | 41 | Cek pasca-migrasi, hanya membaca, keluar dengan kode status |
| `README.md` | 1,5 KB | Daftar isi + aturan penting |

## Isi `cek_pasca.sh` (yang paling penting)

Memeriksa dan mengembalikan kode keluar ≠ 0 bila ada yang salah:

- DocType ada: HRIS Employee, Employee Pay, Employee Component, Component Assignment,
  Pay Component, Payroll Slip BPJS, BPJS Rate, PPh21 Settings, PPh21 TER Rate,
  PPh21 Pasal17 Rate, Payroll Period, Payroll Slip, Department, Department Rule.
- Role ada: HR HR Admin, Employee Admin, Payroll Admin, Payroll Manager, Direksi.
- `allow_import=1` hanya pada dua DocType tarif; izin Import hanya System Manager.
- Katalog komponen aktif harus 0; PPh21 Settings `enabled` harus 0.
- Info: jumlah `tabEmployee`, `HRIS Employee`, PPh21 TER Rate.
- Pohon kerja `hris` dan `wms` harus bersih.

## Temuan

1. **`README.md` masih menyatakan "Status (12 November 2026): migrasi produksi
   K-102 BELUM dijalankan"**, padahal migrasi selesai 17 Nov 2026 19:50 WIB
   ([status.md](../docs/progress/status.md)). Ini kesalahan dokumen yang paling
   berpotensi membingungkan.
2. Tabel "Isi" di README **tidak memuat `cek_pasca.sh`**, padahal skrip itu ada
   dan justru dipakai di gladi (2c) dan produksi (5b).
3. `cek_pasca.sh` memakai `BENCH=/home/it/erp` yang ditulis tetap; aman untuk
   server ini, tetapi tidak portabel.
4. Skrip memeriksa `wms` di pohon kerja — ketergantungan pada app lain yang
   dicatat sebagai "dibiarkan" di `status.md`. Bila `wms` dihapus, cek ini gagal.
5. Semua skrip hanya membaca password lewat prompt; tidak ada rahasia tertanam.
   Sudah diperiksa, sesuai catatan 7 Nov.
