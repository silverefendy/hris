# Rangkuman: Core, Reports, Setup, Public, Hooks, API

Diperiksa: 27 November 2026.

## `hris/hris_core` dan `hris/hris_reports`

| Folder | Isi |
|---|---|
| `hris_core` | **Kosong** — hanya `__init__.py` di `doctype/`, `services/`, `tests/`. Role inti dibuat di `setup/`. |
| `hris_reports` | **Kosong** — hanya `report/__init__.py` dan `tests/__init__.py` (laporan nyata ada di modul payroll/attendance). |

Keduanya masih terdaftar di `modules.txt` (5 modul). Modul kosong tidak
mengganggu, tetapi membuat menu modul tanpa isi.

## `hris/hooks.py` (314 baris)

| Bagian | Isi |
|---|---|
| Identitas | `app_name="hris"`, `app_title="HRIS CML"`, `app_license="mit"` → **placeholder, belum final** |
| Dependensi | `required_apps = ["frappe","erpnext","hrms"]` (K-03, masih dipertanyakan K-18) |
| Setup | `after_install`, `after_migrate` → `setup.install` + `setup.izin` |
| `doc_events` | Shift Assignment (on_update/after_delete) → hitung ulang aturan Department; `Employee.validate` → validasi grup |
| `app_include_js` | 4 berkas: `hris_audit_trail`, `hris_sync_status`, `hris_device_actions`, `hris_employee_card` — **semua ada** di `public/js/` |
| `app_include_css` | `hris_employee_card.css` — **ada** |
| `add_to_apps_screen` | Logo `images/hris-logo.svg` — **ada**; route `/desk/hris-attendance/hris` |
| `permission_query_conditions` + `has_permission` | 3 DocType payroll: Employee Pay, Payroll Slip, Employee Component (K-127/K-129) |

## `hris/setup/`

| Berkas | Isi | Catatan |
|---|---|---|
| `install.py` (170) | 6 role, Custom Field di Employee (6 field `hris_*`), Department (1 field), Property Setter Employee | Idempoten, tidak menimpa field yang ada |
| `roles.py` (24) | 4 role tambahan: Payroll Admin, Payroll Manager, Direksi, Employee Admin | **Duplikasi** dengan `HRIS_ROLES` di `install.py` — dua sumber daftar role |
| `izin.py` (37) | Role laporan Working Hour Ringkasan ditambahkan saat migrate | Karena role di JSON Report tidak ikut migrate |

## `hris/patches/`

| Berkas | Isi |
|---|---|
| `patches.txt` | Dua patch `post_model_sync` |
| `v1_0/buat_aturan_akar_department.py` | Membuat aturan akar Department (dilewati bila akar belum ada — ditangani langkah 2b runbook) |
| `seed_pay_component_e1.py` | Mengisi katalog `HRIS Pay Component` awal (nonaktif) |

## `hris/public/`

| Berkas | Baris | Isi |
|---|---|---|
| `js/hris_employee_card.js` | 712 | Kartu profil karyawan (foto, ringkasan, field baru) |
| `js/hris_device_actions.js` | 351 | Dialog Tarik Log / Status / Cek Dulu |
| `js/hris_audit_trail.js` | 48 | Tab Audit Trail di semua DocType HRIS |
| `js/hris_sync_status.js` | 21 | Indikator sinkron |
| `css/hris_employee_card.css`, `images/hris-logo.svg` | — | Aset tampilan |

## `hris/api/`

Hanya `__init__.py` (kosong). Endpoint nyata ada di
`hris_attendance/integrations/` (`agent_api.py`, `device_user_api.py`) dan
`hris_attendance/services/` (fungsi `@frappe.whitelist`).

## Catatan

- Nama app "HRIS CML" dan lisensi "mit" konsisten dengan `README.md` root, dan
  keduanya sudah tercatat sebagai butir tertunda. Bila diganti, harus diganti
  serentak di `hooks.py`, `pyproject.toml`, `README.md`.
- `modules.txt` memuat `HRIS Reports`, padahal modulnya kosong.
