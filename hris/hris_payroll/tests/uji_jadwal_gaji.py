from datetime import date

import frappe

from hris.hris_payroll.services.payroll_schedule import (
    compute_pay_date,
    compute_period,
    get_period_for_date,
)


def _d(teks):
    t, b, h = (int(x) for x in teks.split("-"))
    return date(t, b, h)


B26 = {"schedule_type": "Bulanan", "cut_off_day": 26}
B31 = {"schedule_type": "Bulanan", "cut_off_day": 31}
KAMIS = {"schedule_type": "Mingguan", "week_start_day": "Kamis"}
SABTU = {"schedule_type": "Mingguan", "week_start_day": "Sabtu"}
H10 = {"schedule_type": "Harian", "period_days": 10, "anchor_date": date(2026, 11, 1)}
T1428 = {"schedule_type": "Tanggal Tetap", "cut_off_days": [14, 28]}

PERIODE = [
    ("Bulanan 26: 3 Nov", B26, "2026-11-03", "2026-10-27", "2026-11-26"),
    ("Bulanan 26: tepat cut-off 26 Okt", B26, "2026-10-26", "2026-09-27", "2026-10-26"),
    ("Bulanan 26: sehari setelah cut-off", B26, "2026-10-27", "2026-10-27", "2026-11-26"),
    ("Bulanan 26: lewat tahun", B26, "2026-12-30", "2026-12-27", "2027-01-26"),
    ("Bulanan 31: Februari 2027", B31, "2027-02-10", "2027-02-01", "2027-02-28"),
    ("Mingguan Kamis: Rabu 4 Nov", KAMIS, "2026-11-04", "2026-10-29", "2026-11-04"),
    ("Mingguan Kamis: Kamis 5 Nov", KAMIS, "2026-11-05", "2026-11-05", "2026-11-11"),
    ("Mingguan Sabtu: Jumat 6 Nov", SABTU, "2026-11-06", "2026-10-31", "2026-11-06"),
    ("Mingguan Sabtu: Sabtu 7 Nov", SABTU, "2026-11-07", "2026-11-07", "2026-11-13"),
    ("Harian 10 hari: 10 Nov", H10, "2026-11-10", "2026-11-01", "2026-11-10"),
    ("Harian 10 hari: 11 Nov", H10, "2026-11-11", "2026-11-11", "2026-11-20"),
    ("Harian 10 hari: sebelum acuan", H10, "2026-10-31", "2026-10-22", "2026-10-31"),
    ("Tetap 14/28: 3 Nov", T1428, "2026-11-03", "2026-10-29", "2026-11-14"),
    ("Tetap 14/28: 15 Nov", T1428, "2026-11-15", "2026-11-15", "2026-11-28"),
    ("Tetap 14/28: 29 Nov", T1428, "2026-11-29", "2026-11-29", "2026-12-14"),
    ("Tetap 14/28: 1 Mar 2027 (28 Feb)", T1428, "2027-03-01", "2027-03-01", "2027-03-14"),
]

BAYAR = [
    ("Bayar: akhir Minggu, maju ke Senin", "2026-11-29", 0, "Maju ke Senin", "2026-11-30"),
    ("Bayar: akhir Minggu, aturan Tetap", "2026-11-29", 0, "Tetap", "2026-11-29"),
    ("Bayar: akhir Sabtu + jeda 1 = Minggu, maju", "2026-11-28", 1, "Maju ke Senin", "2026-11-30"),
    ("Bayar: akhir Sabtu, tanpa jeda", "2026-11-28", 0, "Maju ke Senin", "2026-11-28"),
]


def _coba(company, label, nilai, harus_gagal):
    data = {"doctype": "HRIS Payroll Schedule", "schedule_name": "ZZ-UJI " + label, "company": company}
    data.update(nilai)
    doc = frappe.get_doc(data)
    gagal = False
    try:
        doc.insert()
    except frappe.ValidationError:
        gagal = True
    return gagal == harus_gagal, doc


def jalankan():
    hasil = []

    def catat(nama, ok, rinci=""):
        hasil.append(ok)
        print(("OK   " if ok else "GAGAL"), nama, rinci)

    for nama, params, tgl, awal, akhir in PERIODE:
        got = compute_period(params, _d(tgl))
        ok = got == (_d(awal), _d(akhir))
        catat(nama, ok, "" if ok else "diharapkan %s..%s, dapat %s..%s" % (awal, akhir, got[0], got[1]))

    for nama, akhir, offset, aturan, harap in BAYAR:
        got = compute_pay_date(_d(akhir), offset, aturan)
        ok = got == _d(harap)
        catat(nama, ok, "" if ok else "diharapkan %s, dapat %s" % (harap, got))

    company = frappe.get_all("Company", pluck="name", limit=1)[0]
    try:
        ok, _doc = _coba(
            company, "valid bulanan",
            {"schedule_type": "Bulanan", "cut_off_day": 26, "week_start_day": "Senin"}, False,
        )
        catat("DB: Bulanan valid disimpan", ok)
        catat("DB: field tipe lain dibersihkan", _doc.week_start_day in (None, ""))
        per = get_period_for_date(_doc.name, "2026-11-03")
        catat(
            "DB: get_period_for_date",
            per["start"] == _d("2026-10-27") and per["end"] == _d("2026-11-26") and per["pay_date"] == _d("2026-11-26"),
            str(per),
        )

        ok, _x = _coba(company, "cut-off 0", {"schedule_type": "Bulanan", "cut_off_day": 0}, True)
        catat("DB: cut-off 0 ditolak", ok)
        ok, _x = _coba(company, "cut-off 32", {"schedule_type": "Bulanan", "cut_off_day": 32}, True)
        catat("DB: cut-off 32 ditolak", ok)
        ok, _x = _coba(company, "mingguan kosong", {"schedule_type": "Mingguan"}, True)
        catat("DB: Mingguan tanpa hari awal ditolak", ok)
        ok, _x = _coba(
            company, "harian 0",
            {"schedule_type": "Harian", "period_days": 0, "anchor_date": "2026-11-01"}, True,
        )
        catat("DB: Harian panjang 0 ditolak", ok)
        ok, _x = _coba(company, "harian tanpa acuan", {"schedule_type": "Harian", "period_days": 7}, True)
        catat("DB: Harian tanpa tanggal acuan ditolak", ok)
        ok, _x = _coba(company, "tetap kosong", {"schedule_type": "Tanggal Tetap"}, True)
        catat("DB: Tanggal Tetap tanpa baris ditolak", ok)
        ok, _x = _coba(
            company, "tetap ganda",
            {"schedule_type": "Tanggal Tetap", "cut_off_dates": [{"day_of_month": 14}, {"day_of_month": 14}]}, True,
        )
        catat("DB: tanggal ganda ditolak", ok)
        ok, _x = _coba(
            company, "jeda negatif",
            {"schedule_type": "Bulanan", "cut_off_day": 26, "pay_date_offset_days": -1}, True,
        )
        catat("DB: jeda negatif ditolak", ok)

        ok, doc2 = _coba(
            company, "tetap urut",
            {"schedule_type": "Tanggal Tetap", "cut_off_dates": [{"day_of_month": 28}, {"day_of_month": 14}]}, False,
        )
        catat("DB: Tanggal Tetap valid disimpan", ok)
        catat("DB: tanggal diurutkan", [r.day_of_month for r in doc2.cut_off_dates] == [14, 28])
        per2 = get_period_for_date(doc2.name, "2026-11-03")
        catat(
            "DB: layanan Tanggal Tetap",
            per2["start"] == _d("2026-10-29") and per2["end"] == _d("2026-11-14"),
            str(per2),
        )
    finally:
        frappe.db.rollback()

    gagal = hasil.count(False)
    ringkas = "TOTAL %d pemeriksaan, GAGAL %d" % (len(hasil), gagal)
    print(ringkas)
    return ringkas
