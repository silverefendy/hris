import calendar
from datetime import date, timedelta

import frappe
from frappe.utils import cint, getdate

DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]


def _clamp(tahun, bulan, hari):
    # Tanggal 31 di bulan pendek memakai hari terakhir bulan itu.
    terakhir = calendar.monthrange(tahun, bulan)[1]
    return date(tahun, bulan, min(hari, terakhir))


def _geser_bulan(tahun, bulan, delta):
    idx = tahun * 12 + (bulan - 1) + delta
    return idx // 12, idx % 12 + 1


def _akhir_periode_sekitar(hari_list, tanggal):
    # Cukup bulan -1, 0, +1: akhir periode berikutnya dan sebelumnya pasti ada di rentang ini.
    hasil = set()
    for delta in (-1, 0, 1):
        tahun, bulan = _geser_bulan(tanggal.year, tanggal.month, delta)
        for hari in hari_list:
            hasil.add(_clamp(tahun, bulan, hari))
    return sorted(hasil)


def compute_period(params, tanggal):
    """Hitung (awal, akhir) periode yang memuat `tanggal`. Tanpa akses database.

    params: dict dengan kunci schedule_type, dan sesuai tipe:
    cut_off_day | cut_off_days (list) | week_start_day | period_days + anchor_date.
    """
    tipe = params["schedule_type"]

    if tipe in ("Bulanan", "Tanggal Tetap"):
        if tipe == "Bulanan":
            hari_list = [cint(params["cut_off_day"])]
        else:
            hari_list = [cint(h) for h in params["cut_off_days"]]
        akhir_semua = _akhir_periode_sekitar(hari_list, tanggal)
        akhir = min(c for c in akhir_semua if c >= tanggal)
        sebelumnya = max(c for c in akhir_semua if c < akhir)
        return sebelumnya + timedelta(days=1), akhir

    if tipe == "Mingguan":
        mulai_idx = DAYS.index(params["week_start_day"])
        awal = tanggal - timedelta(days=(tanggal.weekday() - mulai_idx) % 7)
        return awal, awal + timedelta(days=6)

    if tipe == "Harian":
        n = cint(params["period_days"])
        acuan = getdate(params["anchor_date"])
        urutan = (tanggal - acuan).days // n
        awal = acuan + timedelta(days=urutan * n)
        return awal, awal + timedelta(days=n - 1)

    raise ValueError("Jenis jadwal tidak dikenal: %s" % tipe)


def compute_pay_date(akhir_periode, offset_hari, aturan_minggu):
    # Hanya hari bayar yang bergeser. Akhir periode tidak berubah.
    bayar = akhir_periode + timedelta(days=cint(offset_hari))
    if bayar.weekday() == 6 and aturan_minggu == "Maju ke Senin":
        bayar += timedelta(days=1)
    return bayar


def params_from_doc(doc):
    return {
        "schedule_type": doc.schedule_type,
        "cut_off_day": doc.cut_off_day,
        "cut_off_days": [r.day_of_month for r in (doc.cut_off_dates or [])],
        "week_start_day": doc.week_start_day,
        "period_days": doc.period_days,
        "anchor_date": doc.anchor_date,
    }


def get_period_for_date(schedule, tanggal):
    """Periode dan hari bayar untuk satu tanggal menurut satu jadwal gaji.

    Jadwal nonaktif tetap dilayani agar periode lama dapat dihitung ulang.
    """
    doc = frappe.get_doc("HRIS Payroll Schedule", schedule)
    tanggal = getdate(tanggal)
    awal, akhir = compute_period(params_from_doc(doc), tanggal)
    bayar = compute_pay_date(akhir, doc.pay_date_offset_days, doc.sunday_rule)
    return {"start": awal, "end": akhir, "pay_date": bayar}
