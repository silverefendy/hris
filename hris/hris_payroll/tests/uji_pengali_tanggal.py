"""K-137: uji pengali lembur per tanggal (fungsi murni dan pemasangan per tanggal; tanpa tulis DB).

Jalankan: bench --site hris-uji.local execute hris.hris_payroll.tests.uji_pengali_tanggal.jalankan
"""
from datetime import date

import frappe

from hris.hris_payroll.services import department_rule as dr
from hris.hris_payroll.services import payroll_slip as ps


def _hari(tgl, lembur_menit=0, pengali=None):
    b = {
        "status": "Hadir", "scheduled_hours": 8, "late_deduction_hours": 0,
        "early_leave_deduction_hours": 0, "overtime_minutes": lembur_menit,
        "absence_deducted": 0, "absence_class": "", "work_date": tgl,
    }
    if pengali is not None:
        b["pengali"] = pengali
    return b


def _jumlah(hasil, nama):
    for k in hasil.get("komponen", []):
        if k["nama"] == nama:
            return k["jumlah"]
    return None


def _ada(teks_list, potongan):
    return any(potongan in t for t in teks_list)


def jalankan():
    ok = []
    gagal = []

    def cek(nama, kondisi, ket=""):
        (ok if kondisi else gagal).append(nama)
        print("OK    " if kondisi else "GAGAL ", nama, ket)

    d1, d2, d3 = date(2026, 10, 19), date(2026, 10, 20), date(2026, 10, 21)

    # Bulanan, gaji 2.400.000 / 24 jam = 100.000 per jam
    baris = [_hari(d1, 60, 1.0), _hari(d2, 120, 1.5), _hari(d3, 0)]
    h = ps.hitung_komponen("Bulanan", 2400000, baris, pengali=1.0)
    cek("T1 Bulanan dua pengali: 1x1.0 + 2x1.5 = 400000", _jumlah(h, "Lembur") == 400000, str(_jumlah(h, "Lembur")))
    cek("T1b catatan rincian pengali berubah", _ada(h["catatan"], "Pengali lembur berubah"))

    baris = [_hari(d1, 60), _hari(d2, 120), _hari(d3, 0)]
    h = ps.hitung_komponen("Bulanan", 2400000, baris, pengali=1.5)
    cek("T2 Bulanan tanpa kunci pengali memakai pengali slip: 3x1.5 = 450000", _jumlah(h, "Lembur") == 450000, str(_jumlah(h, "Lembur")))
    cek("T2b tanpa catatan perubahan", not _ada(h["catatan"], "Pengali lembur berubah"))

    baris = [_hari(d1, 60, 1.0), _hari(d2, 120, 1.0), _hari(d3, 0, 1.0)]
    h = ps.hitung_komponen("Bulanan", 2400000, baris, pengali=1.5)
    cek("T3 Bulanan satu kelompok 1.0 mengalahkan pengali slip: 3x1.0 = 300000", _jumlah(h, "Lembur") == 300000, str(_jumlah(h, "Lembur")))
    cek("T3b satu kelompok tanpa catatan perubahan", not _ada(h["catatan"], "Pengali lembur berubah"))

    # Harian, upah 160.000 / 8 jam = 20.000 per jam
    baris = [_hari(d1, 60, 1.0), _hari(d2, 120, 1.5), _hari(d3, 0)]
    h = ps.hitung_komponen("Harian", 160000, baris, pengali=1.0)
    cek("T4 Harian dua pengali: 1x20000x1.0 + 2x20000x1.5 = 80000", _jumlah(h, "Lembur") == 80000, str(_jumlah(h, "Lembur")))
    cek("T4b catatan pengali berubah (Harian)", _ada(h["catatan"], "Pengali lembur berubah"))

    baris = [_hari(d1, 60), _hari(d2, 120), _hari(d3, 0)]
    h = ps.hitung_komponen("Harian", 160000, baris, pengali=1.0)
    cek("T5 Harian tanpa kunci pengali: 3x20000x1.0 = 60000", _jumlah(h, "Lembur") == 60000, str(_jumlah(h, "Lembur")))

    # _pasang_pengali_harian dengan resolve palsu (tanpa DB aturan)
    asli = dr.resolve
    dipanggil = []

    def palsu(dept, tgl, parameter="overtime_multiplier"):
        dipanggil.append(tgl)
        return {"nilai": 1.5 if tgl >= d2 else 1.0, "aturan": "X", "department": dept}

    try:
        dr.resolve = palsu
        baris = [_hari(d1, 60), _hari(d2, 0), _hari(d3, 30), _hari(d3, 30)]
        galat = ps._pasang_pengali_harian("All Departments", baris)
        cek("T6 pemasangan tanpa galat", galat is None, str(galat))
        cek("T6b hanya hari ber-lembur dicari, satu kali per tanggal", dipanggil == [d1, d3], str(dipanggil))
        cek("T6c pengali terpasang sesuai tanggal", baris[0].get("pengali") == 1.0 and baris[2].get("pengali") == 1.5 and "pengali" not in baris[1])

        def galat_resolve(dept, tgl, parameter="overtime_multiplier"):
            raise frappe.ValidationError("Tidak ada aturan berlaku")

        dr.resolve = galat_resolve
        baris = [_hari(d1, 60)]
        galat = ps._pasang_pengali_harian("All Departments", baris)
        cek("T7 resolve gagal menghasilkan pesan (slip dilewati)", bool(galat) and "Pengali lembur tanggal" in galat, str(galat))

        dr.resolve = lambda *a, **k: {"nilai": 0}
        galat = ps._pasang_pengali_harian("All Departments", [_hari(d1, 60)])
        cek("T8 nilai nol ditolak", bool(galat) and "tidak valid" in galat, str(galat))
    finally:
        dr.resolve = asli

    print("HASIL: OK %d, GAGAL %d" % (len(ok), len(gagal)))
