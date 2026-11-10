"""BPJS pada HRIS Payroll Slip (K-133, aturan angka tetap).

HRD menginput angka iuran karyawan per program di HRIS Employee. Slip hanya memotong angka itu, tanpa persentase.
Dipotong sekali sebulan, pada slip pertama menurut jadwal yang tanggal bayarnya jatuh di bulan itu
(bulan dari tanggal bayar). Pada jadwal Bulanan, slip itu adalah satu-satunya slip bulan tersebut.
"""

from datetime import timedelta
from decimal import ROUND_HALF_UP, Decimal

import frappe
from frappe import _
from frappe.utils import flt, getdate

from hris.hris_payroll.services.payroll_schedule import compute_pay_date, compute_period, params_from_doc

SCHEDULE = "HRIS Payroll Schedule"
PROGRAM = (
    ("BPJS Kesehatan", "bpjs_kes_enrolled", "bpjs_kes_amount", "Iuran BPJS Kesehatan"),
    ("JHT", "bpjs_jht_enrolled", "bpjs_jht_amount", "Iuran JHT"),
    ("JP", "bpjs_jp_enrolled", "bpjs_jp_amount", "Iuran JP"),
    ("JKK", "bpjs_jkk_enrolled", "bpjs_jkk_amount", "Iuran JKK"),
    ("JKM", "bpjs_jkm_enrolled", "bpjs_jkm_amount", "Iuran JKM"),
)


# ---------- angka ----------
def _d(nilai):
    return Decimal(str(flt(nilai)))


def _rupiah(nilai):
    return int(Decimal(nilai).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _rp(n):
    return "{0:,}".format(int(n)).replace(",", ".")


# ---------- penentu slip pertama (murni, tanpa database) ----------
def _ym(tanggal):
    t = getdate(tanggal)
    return (t.year, t.month)


def pertama_bulan_murni(params, offset_hari, aturan_minggu, awal_periode, tanggal_bayar):
    """True bila periode sebelumnya dibayar di bulan lain (periode ini = slip pertama bulan itu)."""
    _awal, akhir_sebelum = compute_period(params, getdate(awal_periode) - timedelta(days=1))
    bayar_sebelum = compute_pay_date(akhir_sebelum, offset_hari, aturan_minggu)
    return _ym(bayar_sebelum) != _ym(tanggal_bayar)


# ---------- data ----------
def _jadwal(period):
    doc = frappe.get_doc(SCHEDULE, period.payroll_schedule)
    return params_from_doc(doc), doc.pay_date_offset_days, doc.sunday_rule


# ---------- gabungan ----------
def hitung_bpjs_slip(he, period, gaji, hasil):
    """Mengembalikan {"komponen", "rincian", "catatan"}.

    he = baris HRIS Employee, period = dokumen HRIS Payroll Period, gaji = baris HRIS Employee Pay,
    hasil = keluaran hitung_komponen (dipakai hanya untuk peringatan gaji bersih negatif).
    """
    kosong = {"komponen": [], "rincian": [], "catatan": []}
    kolom = [p[1] for p in PROGRAM] + [p[2] for p in PROGRAM]
    # Query langsung agar tidak terhalang izin field (permlevel) pemanggil.
    data = frappe.db.get_value("HRIS Employee", he.name, kolom, as_dict=True) or {}
    ikut = [p for p in PROGRAM if data.get(p[1])]
    if not ikut:
        return kosong

    bulan = getdate(period.pay_date).strftime("%m-%Y")
    params, offset, aturan = _jadwal(period)
    if not pertama_bulan_murni(params, offset, aturan, period.period_start, period.pay_date):
        return {
            "komponen": [],
            "rincian": [],
            "catatan": [
                _("BPJS bulan {0} tidak dipotong pada slip ini; dipotong sekali pada slip pertama yang tanggal bayarnya jatuh di bulan itu.").format(bulan)
            ],
        }

    komponen = []
    rincian = []
    total = 0
    for program, _kolom_ikut, kolom_jumlah, nama in ikut:
        jumlah = _rupiah(_d(data.get(kolom_jumlah)))
        total += jumlah
        rincian.append({"program": program, "employee_amount": jumlah, "basis": _("Angka tetap dari data karyawan")})
        if jumlah > 0:
            komponen.append({"nama": nama, "tipe": "Potongan", "jumlah": jumlah, "dasar": _("Angka tetap {0}").format(_rp(jumlah))})

    catatan = [
        _("BPJS bulan {0} dipotong pada slip ini (slip pertama yang tanggal bayarnya jatuh di bulan itu). Angka tetap dari data karyawan.").format(bulan)
    ]
    pendapatan = sum((_d(k["jumlah"]) for k in hasil["komponen"] if k["tipe"] == "Pendapatan"), Decimal(0))
    potongan = sum((_d(k["jumlah"]) for k in hasil["komponen"] if k["tipe"] == "Potongan"), Decimal(0))
    bersih = pendapatan - potongan - total
    if bersih < 0:
        catatan.append(
            _("Peringatan: gaji bersih dari komponen otomatis negatif ({0}) setelah iuran BPJS. Belum termasuk komponen Manual. Periksa sebelum Ditinjau.").format(
                _rp(_rupiah(bersih))
            )
        )
    return {"komponen": komponen, "rincian": rincian, "catatan": catatan}
