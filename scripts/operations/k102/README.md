# Runbook migrasi K-102 (arsip acuan)

Dibuat: 7 November 2026.

**Status (12 November 2026): migrasi produksi K-102 BELUM dijalankan.** Tabel HRIS Employee belum ada di `erp.ciptamebel.co.id` (diperiksa dengan SELECT). Semua uji dan gladi baru dilakukan di `hris-uji.local`.

Salinan skrip yang akan dipakai untuk migrasi Employee ke HRIS Employee (K-102)
di server `erp.ciptamebel.co.id`. Skrip yang akan dijalankan sebenarnya berada di
`/home/it/runbook_k102/`. Salinan ini hanya arsip supaya skrip tidak hilang
bila server bermasalah. Bila keduanya berbeda, periksa dengan `diff`.

## Isi

| Berkas | Fungsi |
|---|---|
| `runbook_k102.sh` | Fungsi dasar: cadangan, restore, pemeriksaan |
| `gladi_k102.sh` | Gladi resik di site uji (`hris-uji.local`) |
| `produksi_k102.sh` | Pintu masuk produksi: `cadangan`, `siap`, `mulai`, `pulihkan` |
| `diag_erp_k102.sh` | Diagnosa kondisi server dan commit |
| `diag_db_k102.sh` | Diagnosa database (memanggil `diag_db_k102.py`) |
| `diag_db_k102.py` | Pemeriksaan jumlah dan kondisi Employee |

## Aturan penting

- Tanpa variabel `SITE_TARGET=hris-uji.local`, sasaran `produksi_k102.sh`
  adalah **produksi**.
- Skrip tidak menyimpan password. Password root MariaDB dibaca lewat prompt
  tersembunyi.
- Keluaran skrip (`*.txt`, `*.path`) tidak boleh masuk repo; sudah diabaikan
  oleh `.gitignore` di folder ini.
- Server mencetak waktu UTC (WIB = UTC+7).

## Urutan migrasi produksi

Lihat `docs/progress/go-live.md` bagian 9 dan `docs/operations/deployment.md`.
