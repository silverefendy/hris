# Rangkuman: Modul `hris_employee_data`

Diperiksa: 27 November 2026. Data karyawan, pohon Department, aturan Department,
dan migrasi dari `Employee` ERPNext.

## DocType

| DocType | Berkas | Isi |
|---|---|---|
| `HRIS Employee` | `hris_employee.py` (134) + `.js` (83) | Data karyawan HRIS: 5 tab, ID Finger, No Induk, PTKP, BPJS, field payroll |
| `HRIS Department` | `hris_department.py` + `.js` + `_tree.js` | Pohon Department milik HRIS, sumber utama (K-136) |
| `HRIS Department Rule` | `hris_department_rule.py` | Aturan per parameter, diwariskan naik ke akar; `overtime_multiplier` |
| `HRIS Department Rule Component` | `hris_department_rule_component.py` | Baris anak nilai komponen per Department |

## Layanan

| Berkas | Baris | Fungsi |
|---|---|---|
| `migrasi_employee.py` | 320 | K-102: salin `Employee` → `HRIS Employee`, mode coba/terapkan, cadangan |
| `department_sync.py` | 167 | Sinkron satu arah HRIS Department → Department ERPNext |
| `employee_sync.py` | 162 | Sinkron data karyawan (ID Finger, grup, status) |
| `migrasi_department.py` | 134 | Salin pohon Department + buat aturan akar dalam satu transaksi |
| `id_finger.py` | 62 | Generator ID Finger (lanjutan rancangan U1–U7) |

## Uji

| Berkas | Cakupan |
|---|---|
| `tests/uji_hris_employee.py` (155) | Struktur + validasi HRIS Employee |
| `tests/uji_izin.py` (181) | Izin per peran |
| `tests/uji_tampilan.py` (111) | Tampilan form |
| `tests/uji_sinkron.py` (221) | Sinkron Employee |
| `tests/uji_department_sync.py` (129) | Sinkron Department |
| `tests/uji_hris_department.py` (119) | Pohon Department |
| `tests/uji_tahap4a.py` (43) | Link tahap 4a |
| `tests/uji_bpjs_peserta.py` (90) | Field BPJS peserta |
| `uji_k102.py` (174), `uji_k126.py` (186), `uji_id_finger.py` (43) | K-102, K-126, ID Finger (di akar modul) |

## Kondisi

- K-102 sudah dijalankan di produksi 17 Nov 2026 malam: 1.078 baris `Berhasil`,
  tabel `Employee` tidak berubah, `cek_pasca` SEMUA OK.
- `HRIS Department` menyalin 164 Department + akar "All Departments".
- Risiko yang sudah ditangani: `migrate` pada database tanpa pohon Department
  melewati patch aturan akar; ditutup `migrasi_department.py` (satu transaksi).
- Belum: uji browser per peran pasca-migrasi, sinkron dua arah (memang tidak
  diinginkan), `HRIS Absence` (masih rancangan).
