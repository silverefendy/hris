# Rangkuman: `docs/architecture` dan `docs/business`

Diperiksa: 27 November 2026. Ringkasan per berkas.

## `docs/architecture/`

| Berkas | Ukuran | Isi | Status |
|---|---|---|---|
| `data-model.md` | 13 KB | Model data per 29 Okt: Device, Raw Log, Shift, Group, Rotation, Holiday, Working Hour, Pull Run | **Usang**: belum memuat `HRIS Employee`, Department, payroll, `device_code`, `punch_key`, Device User |
| `agent-api.md` | 5,8 KB | Kontrak `push_punches`: satu device, ≤500 baris, WIB, hasil per baris, batas 1 hari ke depan | Sesuai kode |
| `api.md` | 3,6 KB | Daftar fungsi `@frappe.whitelist()` per 29 Okt | **Usang**: belum memuat `push_device_users`, fungsi tarik/hapus, `riwayat` |
| `platform-boundaries.md` | 1,9 KB | Batas platform vs kode sendiri (K-18) | Sesuai |
| `architecture.md` | 69 B | "Kerangka — belum diisi" | **Kosong** |
| `integration.md` | 125 B | "Kerangka — belum diisi" | **Kosong** |

## `docs/business/`

| Berkas | Ukuran | Isi | Status |
|---|---|---|---|
| `process-flows/attendance-flow.md` | 1,8 KB | Alur mesin → Raw Log → Working Hour | Perlu disinkronkan dengan jalur agen dan Working Hour terbaru |
| `process-flows/hapus-working-hour.md` | 2,9 KB | Alur hapus massal 6b: Cek Dulu, job batch, guard | Sesuai kode |
| `process-flows/_template.md` | 83 B | Templat alur | — |
| `payroll-rancangan.md` | 5,2 KB | Rancangan payroll fase 1 (K-95–K-99) | Sebagian sudah diimplementasikan; dokumen tidak diperbarui |
| `business-rules.md` | 89 B | Tabel aturan bisnis | **Kosong** (hanya header) |

## Temuan

1. Dua dokumen arsitektur inti masih kerangka kosong; ini yang paling terasa
   karena pembaca baru akan mencari alur dan integrasi di sana.
2. `data-model.md` adalah dokumen paling jauh tertinggal: seluruh modul payroll
   dan Department tidak ada di sana.
3. `attendance-flow.md` sudah dipindah dari `architecture/` (tercatat di
   `status.md`), tetapi `CLAUDE.md` masih menyebut lokasi lama.
