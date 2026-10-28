# Lingkungan Kerja

Diperbarui: 28 Oktober 2026. Tanpa IP, kata sandi, atau nama mesin internal.

## Bench kerja (development)
| Komponen | Kondisi |
|---|---|
| OS | Ubuntu 24.04 |
| Python / Node | 3.14 / 24 |
| Database | MariaDB 11.8 (lokal) |
| Mode | Development (`bench start`); tanpa nginx dan supervisor |
| frappe | 16.53.0 (`version-16`) |
| erpnext | 16.52.1 |
| hrms | 16.52.0 |
| hris | 0.0.1 (`main`), terpasang di site kerja |

## Site
| Site | Kondisi |
|---|---|
| Site kerja | Belum production, belum berisi data. Target pengembangan. Zona waktu System Settings: Asia/Jakarta (diganti dari Asia/Kolkata pada 28 Okt 2026) |
| Site uji lama | Schema database lama, kode sudah baru. Jangan dipakai dan jangan di-migrate. Nasib (pulihkan atau hapus) belum diputuskan |

## Aturan kerja
- Selalu `bench --site <nama>`; jangan `bench update` biasa (men-migrate semua site, termasuk site uji lama).
- Backup sebelum perubahan besar: `bench --site <nama> backup`.
- Setelah mengubah `modules.txt`, jalankan `bench clear-cache` sebelum `install-app`.
- Setelah mengubah JSON DocType, naikkan `modified` lalu jalankan `bench --site <nama> migrate` dan `clear-cache`; JS form/list butuh hard refresh browser. Mode development memuat kode Python baru tanpa restart.
- `frappe`, `erpnext`, `hrms` memakai remote `upstream` (hanya fetch dan `merge --ff-only`, tidak pernah push). `hris` dan `wms` memakai `origin`.

## Isu ikon desk (diparkir)
Beberapa ikon bawaan ERPNext tidak tampil (Organization, Subcontracting, Accounts Setup, Banking, Budget, Share Management, Subscription, Taxes, Welcome Workspace) setelah upgrade ke ERPNext 16.52.

- **Kesimpulan:** bukan kerusakan; perilaku bawaan di mode grid ikon lama. Data dan fitur utuh.
- **Sebab:** di mode grid ikon lama (`Desktop Settings.desktop_page = "Desktop Icons"`), ikon tipe Link hanya tampil bila modulnya cocok dengan sidebar modul.
- **Fitur yang pindah:** Subcontracting ke sidebar Manufacturing; Organization dan Subscription ke Setup; Banking, Taxes, Budget ke Accounts. Share Management tidak ditemukan di lima sidebar yang diperiksa.
- **Keputusan:** dibiarkan sementara. Opsi di masa depan: pindah ke mode Apps lewat Desktop Settings (belum diuji; perlu backup dan konfirmasi). Jangan ubah record Desktop Icon, Workspace, Sidebar, atau Dock tanpa persetujuan.

## Rencana production (draf, belum disetujui)
- Reverse proxy di server gateway (TLS, pembatasan login), meneruskan ke bench lewat jaringan privat.
- Di bench: matikan `bench start`, `developer_mode` 0, aktifkan scheduler, `bench setup production`, firewall, backup terjadwal, snapshot VM sebelum go-live.
- Perlu diverifikasi sebelum dipakai: pemilihan site dari header `Host`, header `X-Forwarded-Proto`, konfigurasi `host_name`.
- Open question: production dan pengembangan di bench yang sama atau terpisah (saran: bench kedua untuk production).
