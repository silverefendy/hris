"""BPJS pada HRIS Payroll Slip (K-133 langkah 3).

Iuran karyawan dipotong sekali sebulan pada slip terakhir yang tanggal bayarnya jatuh di bulan itu
(bulan dari tanggal bayar). Tarif hanya dari HRIS BPJS Rate; tidak ada tarif di kode ini.
"""

import calendar
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal

import frappe
from frappe import _
from frappe.utils import cstr, flt, getdate

from hris.hris_payroll.services.payroll_schedule import compute_pay_date, compute_period, params_from_doc

SLIP = "HRIS Payroll Slip"
SCHEDULE = "HRIS Payroll Schedule"
RATE = "HRIS BPJS Rate"
UPAH_HARIAN = "Upah Harian"
PROGRAM = (
    ("BPJS Kesehatan", "bpjs_kes_enrolled", "Iuran BPJS Kesehatan"),
    ("JHT", "bpjs_jht_enrolled", "Iuran JHT"),
    ("JP", "bpjs_jp_enrolled", "Iuran JP"),
    ("JKK", "bpjs_jkk_enrolled", "Iuran JKK"),
    ("JKM", "bpjs_jkm_enrolled", "Iuran JKM"),
)


# ---------- angka ----------
def _d(nilai):
    return Decimal(str(flt(nilai)))


def _rupiah(nilai):
    return int(Decimal(nilai).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _rp(n):
    return "{0:,}".format(int(n)).replace(",", ".")


def _persen(x):
    return "%g" % flt(x)


def hitung_iuran(dasar, batas, tarif_karyawan, tarif_perusahaan):
    """Fungsi murni. batas kosong atau 0 = tanpa batas. Hasil dalam rupiah bulat (setengah ke atas)."""
    d = _d(dasar)
    b = _d(batas)
    if b > 0 and d > b:
        d = b
    return {
        "dasar_iuran": _rupiah(d),
        "iuran_karyawan": _rupiah(d * _d(tarif_karyawan) / Decimal(100)),
        "bagian_perusahaan": _rupiah(d * _d(tarif_perusahaan) / Decimal(100)),
    }


# ---------- bulan dan periode (murni, tanpa database) ----------
def _ym(tanggal):
    t = getdate(tanggal)
    return (t.year, t.month)


def _rentang_bulan(tanggal):
    t = getdate(tanggal)
    return date(t.year, t.month, 1), date(t.year, t.month, calendar.monthrange(t.year, t.month)[1])


def terakhir_bulan_murni(params, offset_hari, aturan_minggu, akhir_periode, tanggal_bayar):
    """True bila periode berikutnya sudah dibayar di bulan lain (periode ini = slip terakhir bulan itu)."""
    _awal, akhir_next = compute_period(params, getdate(akhir_periode) + timedelta(days=1))
    bayar_next = compute_pay_date(akhir_next, offset_hari, aturan_minggu)
    return _ym(bayar_next) != _ym(tanggal_bayar)


def sebelumnya_murni(params, offset_hari, aturan_minggu, awal_periode, tanggal_bayar, maks=12):
    """Daftar (awal, akhir) periode sebelumnya yang tanggal bayarnya jatuh di bulan yang sama."""
    hasil = []
    awal = getdate(awal_periode)
    for _i in range(maks):
        a, b = compute_period(params, awal - timedelta(days=1))
        bayar = compute_pay_date(b, offset_hari, aturan_minggu)
        if _ym(bayar) != _ym(tanggal_bayar):
            break
        hasil.append((a, b))
        awal = a
    return hasil


# ---------- data ----------
def _jadwal(period):
    doc = frappe.get_doc(SCHEDULE, period.payroll_schedule)
    return params_from_doc(doc), doc.pay_date_offset_days, doc.sunday_rule


def _slip_lain_bulan(employee, period_name, tanggal_bayar):
    awal, akhir = _rentang_bulan(tanggal_bayar)
    return frappe.db.sql(
        """
        select name, period_start, period_end, pay_type, base_amount, working_days
        from `tabHRIS Payroll Slip`
        where employee = %(e)s and payroll_period != %(p)s and pay_date between %(a)s and %(b)s
        """,
        {"e": employee, "p": period_name, "a": awal, "b": akhir},
        as_dict=True,
    )


def _upah_harian_slip(names):
    if not names:
        return {}
    baris = frappe.db.sql(
        """
        select parent, sum(amount) as total from `tabHRIS Payroll Slip Item`
        where parenttype = %(t)s and parent in %(n)s and component = %(c)s
        group by parent
        """,
        {"t": SLIP, "n": tuple(names), "c": UPAH_HARIAN},
        as_dict=True,
    )
    return {r.parent: flt(r.total) for r in baris}


def _dasar_harian(he_name, period, gaji, hasil, basis):
    """Dasar iuran karyawan Harian: jumlah seluruh slip Harian di bulan itu, termasuk slip ini."""
    lain = [s for s in _slip_lain_bulan(he_name, period.name, period.pay_date) if s.pay_type == "Harian"]
    if basis == "Gaji Penuh":
        sendiri = _d(gaji.amount) * int(hasil["ringkasan"]["working_days"])
        lainnya = sum((_d(s.base_amount) * int(s.working_days or 0) for s in lain), Decimal(0))
    else:
        sendiri = sum((_d(k["jumlah"]) for k in hasil["komponen"] if k["nama"] == UPAH_HARIAN), Decimal(0))
        upah = _upah_harian_slip([s.name for s in lain])
        lainnya = sum((_d(v) for v in upah.values()), Decimal(0))
    return sendiri + lainnya, len(lain)


def _tarif(company, program, kelas, akhir_periode):
    baris = frappe.db.sql(
        """
        select name, employee_rate, company_rate, wage_cap
        from `tabHRIS BPJS Rate`
        where company = %(c)s and program = %(p)s and ifnull(risk_class, '') = %(k)s
          and is_active = 1 and effective_from <= %(a)s
        order by effective_from desc limit 1
        """,
        {"c": company, "p": program, "k": kelas, "a": akhir_periode},
        as_dict=True,
    )
    return baris[0] if baris else None


# ---------- gabungan ----------
def hitung_bpjs_slip(he, period, gaji, hasil):
    """Mengembalikan {"komponen", "rincian", "catatan"} atau {"dilewati": teks}.

    he = baris HRIS Employee, period = dokumen HRIS Payroll Period, gaji = baris HRIS Employee Pay,
    hasil = keluaran hitung_komponen.
    """
    kosong = {"komponen": [], "rincian": [], "catatan": []}
    kolom = [p[1] for p in PROGRAM] + ["bpjs_jkk_risk_class", "bpjs_wage_basis"]
    flag = frappe.db.get_value("HRIS Employee", he.name, kolom, as_dict=True) or {}
    ikut = [p for p in PROGRAM if flag.get(p[1])]
    if not ikut:
        return kosong

    bulan = getdate(period.pay_date).strftime("%m-%Y")
    params, offset, aturan = _jadwal(period)
    catatan = []

    if not terakhir_bulan_murni(params, offset, aturan, period.period_end, period.pay_date):
        catatan.append(
            _("BPJS bulan {0} tidak dipotong pada slip ini; dipotong pada slip terakhir yang tanggal bayarnya jatuh di bulan itu.").format(bulan)
        )
        for s in _slip_lain_bulan(he.name, period.name, period.pay_date):
            if getdate(s.period_start) > getdate(period.period_end):
                catatan.append(
                    _("Slip {0} (periode berikutnya di bulan yang sama) membawa iuran BPJS. Hitung Ulang slip itu agar dasar iuran mengikuti perubahan ini.").format(s.name)
                )
        return {"komponen": [], "rincian": [], "catatan": catatan}

    for a, b in sebelumnya_murni(params, offset, aturan, period.period_start, period.pay_date):
        if not frappe.db.exists(SLIP, {"employee": he.name, "period_start": a, "period_end": b}):
            catatan.append(
                _("Slip periode {0} sampai {1} belum ada; dasar iuran BPJS mungkin kurang. Buat slip itu, lalu Hitung Ulang slip ini.").format(a, b)
            )

    if gaji.pay_type == "Bulanan":
        dasar = _d(gaji.amount)
        dasar_teks = _("Gaji Pokok")
    else:
        basis = cstr(flag.get("bpjs_wage_basis")) or "Gaji Final"
        dasar, jumlah_lain = _dasar_harian(he.name, period, gaji, hasil, basis)
        dasar_teks = _("{0}: slip ini ditambah {1} slip Harian lain di bulan {2}").format(basis, jumlah_lain, bulan)

    komponen = []
    rincian = []
    for program, _kolom, nama in ikut:
        kelas = ""
        if program == "JKK":
            kelas = cstr(flag.get("bpjs_jkk_risk_class")).strip()
            if not kelas:
                return {
                    "dilewati": _(
                        "Peserta JKK tetapi Kelas Risiko JKK kosong. Penyebab: field Kelas Risiko JKK di data karyawan belum diisi. "
                        "Tindakan: HRD mengisi Kelas Risiko JKK di HRIS Employee, lalu Buat Slip lagi."
                    )
                }
        tarif = _tarif(he.company, program, kelas, period.period_end)
        if not tarif:
            return {
                "dilewati": _(
                    "Peserta {0} tetapi tarif belum ada. Penyebab: tidak ada HRIS BPJS Rate aktif untuk {0}{1} yang berlaku sampai {2}. "
                    "Tindakan: Payroll Manager mengisi tarif di HRIS BPJS Rate, lalu Buat Slip lagi."
                ).format(program, (" kelas " + kelas) if kelas else "", period.period_end)
            }
        h = hitung_iuran(dasar, tarif.wage_cap, tarif.employee_rate, tarif.company_rate)
        dibatasi = h["dasar_iuran"] < _rupiah(dasar)
        rincian.append(
            {
                "program": program,
                "risk_class": kelas,
                "base_amount": _rupiah(dasar),
                "wage_cap": flt(tarif.wage_cap),
                "capped_base": h["dasar_iuran"],
                "employee_rate": flt(tarif.employee_rate),
                "company_rate": flt(tarif.company_rate),
                "employee_amount": h["iuran_karyawan"],
                "company_amount": h["bagian_perusahaan"],
                "rate_ref": tarif.name,
                "basis": dasar_teks,
            }
        )
        if h["iuran_karyawan"] > 0:
            teks = "{0} x {1}%".format(_rp(h["dasar_iuran"]), _persen(tarif.employee_rate))
            if dibatasi:
                teks += " " + _("(dasar dibatasi batas upah {0})").format(_rp(_rupiah(_d(tarif.wage_cap))))
            komponen.append({"nama": nama, "tipe": "Potongan", "jumlah": h["iuran_karyawan"], "dasar": teks})

    catatan.append(
        _("BPJS bulan {0} dipotong pada slip ini (slip terakhir yang tanggal bayarnya jatuh di bulan itu). Dasar: {1}.").format(bulan, dasar_teks)
    )
    return {"komponen": komponen, "rincian": rincian, "catatan": catatan}
