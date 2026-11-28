# Alur Sistem (dari dokumen, kode, dan skrip)

Diperiksa: 27 November 2026. Semua alur disusun dari kode yang ada, bukan dari
rencana. Tanda `[...]` = berkas sumber.

## 1. Alur absensi: mesin → payroll

```
[Mesin ZKTeco]
   │  (a) agen Windows push_punches        (b) Pull pyzk dari server
   ▼                                       ▼
[agent_api.py] ───────────────► [punch_ingest.py] ◄──────── [pull_device.py]
                                        │  kunci: punch_key (mesin|ID|waktu)
                                        ▼
                                 [HRIS Raw Log]  status: Menunggu/Tidak Cocok
                                        │  cocokkan ke Employee via attendance_device_id
                                        ▼
                                 [rematch_raw_log.py]
                                        │
                        [shift_schedule.py]  Assignment → Rotasi → Jadwal mingguan
                                        │
                                        ▼  (manual / batch / job)
                        [working_hour.py: compute_day]  → [HRIS Working Hour]
                                        │  Hadir / Tidak Lengkap / Tidak Hadir / Libur / Tidak Terjadwal
                                        │  potongan telat, pulang cepat, lembur, tanda tinjauan
                                        ▼
                        [HRIS Payroll Period]  Draft → Ditinjau → Final (kunci WH)
                                        │
                                        ▼
                        [payroll_slip.py] → [HRIS Payroll Slip]  (BPJS, PPh 21, komponen)
                                        │
                                        ▼
                        [payroll_summary.py] / [HRIS Biaya Tenaga Kerja]
```

Pintu masuk yang dipakai HRD sehari-hari: Page **Konsol Mesin** → Tarik Log →
Status → (bila perlu) Hapus Raw Log; lalu **Hitung Periode** di list Working Hour.

## 2. Alur Device Tool (aplikasi C#)

```
[Login peran] ──► [Daftar mesin] ──► [Tarik log absensi]
                                          │  BacaLog (hanya membaca mesin)
                                          ▼
                        data\tarikan\tarikan_<mesin>_<stamp>.csv + .hdtman
                                          │  hash SHA-256 di .hdtman
                                          ▼
                                  [Kelola salinan]
                              ┌───────────┼────────────┐
                              ▼           ▼            ▼
                        Kirim ke HRIS  Tempat sampah  Hapus permanen
                              │        (14 hari)      (peran manager)
                              ▼
                    push_punches (batch ≤500) → .hdterr bila ada baris gagal
                              │
                              ▼
                    .hdtman ditambah baris "terkirim=<waktu>|host|c=|d=|e="
```

Jalur lain di aplikasi yang sama:

| Fitur | Arah | Menyentuh HRIS? |
|---|---|---|
| Info mesin | baca mesin | ya, tersimpan ke tabel `mesin` SQLite lokal |
| Ringkas semua mesin / Cek semua | baca port + status | tidak |
| User (cek/tambah uji/list) | baca/tulis mesin (ID uji 999…) | tidak |
| Sidik jari (baca/picu/simpan) | baca mesin | tidak (template lokal) |
| Kirim user HRIS | baca mesin → `push_device_users` | ya |
| Bandingkan 2 mesin | baca dua mesin | tidak |
| Impor aplikasi lama | CSV → SQLite lokal | tidak |
| Cadangkan DB / Lihat database | SQLite lokal | tidak |
| Pengaturan HRIS | URL + token (DPAPI) | tidak |

## 3. Alur payroll (rinci)

```
Jadwal gaji (HRIS Payroll Schedule)
   │  menentukan periode & tanggal bayar
   ▼
Payroll Period  ──► Periksa Kesiapan (uji_period_kesiapan)
   │                 ├─ WH belum dihitung
   │                 ├─ hari Tidak Hadir belum diklasifikasi (Bulanan)
   │                 └─ karyawan Hadir tanpa baris gaji
   ▼
Buat Slip (massal per cakupan / per karyawan)
   │  gaji pokok ── dari HRIS Employee Pay (Bulanan/Harian, tarif per hari)
   │  potongan absen ── dari klasifikasi Working Hour (6a)
   │  lembur ── pengali dari Department Rule (per tanggal berlaku, K-137)
   │  komponen ── HEC per karyawan / HCA per Grup atau Department
   │  BPJS ── angka tetap, sekali sebulan (slip pertama)
   │  PPh 21 TER ── sekali sebulan (slip terakhir), bruto semua slip bulan itu
   ▼
Ditinjau → Final (slip terkunci; koreksi lewat buka kembali periode)
```

## 4. Alur migrasi & rilis (operasi)

```
git push (Efendy) ──► git pull di server ──► bench migrate ──► restart bench
                                                   │
        ┌──────────────────────────────────────────┘
        ▼
  cek_pasca.sh <site>  ── kode keluar 0 = SEMUA OK
        │
        ▼
  uji browser per peran  ──► catat di docs/progress
```

Untuk K-102 khusus:

```
runbook_k102.sh cadangan → produksi_k102.sh siap → mulai
   → department coba → department salin → migrate → jalankan (dry→apply)
   → cek_pasca → uji asap → maintenance OFF
```

## 5. Alur dokumen (aturan repo)

```
Diskusi rancangan → persetujuan Efendy → skrip (Efendy jalankan)
   → uji skrip + uji browser → perbaikan → commit
   → docs/decisions (keputusan baru)
   → docs/progress/status.md + session-log.md (akhir sesi)
```

`CLAUDE.md` menetapkan urutan baca: `status.md` → `decisions/README.md` →
`session-log.md` → `ai-workflow.md`.

## 6. Titik rawan pada alur

| Titik | Risiko | Sumber |
|---|---|---|
| Raw Log `Tidak Cocok` | punch tidak masuk WH sampai dicocokkan ulang | `rematch_raw_log.py` |
| `last_pull_at` maju walau 0 punch | mesin kosong tampak "pernah ditarik" | catatan 0.7.2 |
| Salinan Device Tool vs Pull | dua sumber data untuk mesin yang sama; cakupan tanggal bisa berbeda | catatan 0.7.2 |
| Slip terakhir bulan terlewat | PPh 21 bulan itu tidak terpotong | catatan K-134 |
| Departemen dipinjam | pengali lembur memakai `rule_department`, bukan Department karyawan | K-138 |
| Template jari di disk | berkas `tmpl_*.hdttmpl` **tidak terenkripsi** | `Dev.ReadTemplates` |
