"""Uji Per Bulan pada jadwal Mingguan sintetis (dibuat di transaksi, di-rollback).

bench --site hris-uji.local execute hris.hris_payroll.tests.uji_per_bulan_mingguan.jalankan
"""

from datetime import date, timedelta

import frappe
from frappe.utils import getdate

from hris.hris_payroll.services.giliran_bulan import giliran_bulan
from hris.hris_payroll.services.komponen_slip import hitung_tunjangan
from hris.hris_payroll.services.payroll_schedule import compute_pay_date, compute_period, params_from_doc

SCHEDULE = "HRIS Payroll Schedule"
NILAI = 300000
DASAR = {"nilai": NILAI, "berlaku": True}


def cek(nama, kondisi, info=""):
    print(("OK     " if kondisi else "GAGAL  ") + nama + (" | " + str(info) if info else ""))


def hec_penuh(p):
    return [{"name": "HEC-SINT", "status": "Berlaku", "amount": 0, "date_from": p.period_start, "date_to": p.period_end}]


def jumlah(p, basis, waktu, g):
    return hitung_tunjangan("Harian", basis, DASAR, hec_penuh(p), p.period_start, p.period_end, [], g, waktu)["jumlah"]


def buat_periode(doc, n=14):
    params = params_from_doc(doc)
    a, z = compute_period(params, date(2030, 2, 25))
    hasil = []
    for i in range(n):
        a, z = getdate(a), getdate(z)
        bayar = getdate(compute_pay_date(z, doc.pay_date_offset_days, doc.sunday_rule))
        hasil.append(frappe._dict(name="SINT-%d" % (i + 1), payroll_schedule=doc.name,
                                  period_start=a, period_end=z, pay_date=bayar))
        a, z = compute_period(params, z + timedelta(days=1))
    return hasil


def jalankan():
    doc = None
    try:
        company = (frappe.get_all(SCHEDULE, pluck="company", limit=1) or frappe.get_all("Company", pluck="name", limit=1) or [None])[0]
        doc = frappe.get_doc({
            "doctype": SCHEDULE, "schedule_name": "UJI MINGGUAN PER BULAN", "company": company,
            "schedule_type": "Mingguan", "is_active": 1, "pay_date_offset_days": 4,
            "sunday_rule": "Tetap", "week_start_day": "Senin",
        })
        doc.insert(ignore_permissions=True)
        cek("M1 jadwal Mingguan sintetis dibuat", True, doc.name)
    except Exception as e:
        cek("M1 jadwal Mingguan sintetis dibuat", False, repr(e)[:400])
        frappe.db.rollback()
        return
    nama_jadwal = doc.name
    try:
        periode = buat_periode(doc)
        gil = {p.name: giliran_bulan(p) for p in periode}

        def g(p):
            return gil[p.name] or {"pertama": None, "terakhir": None}

        for p in periode:
            print("INFO   %s %s s/d %s bayar %s giliran %s" % (p.name, p.period_start, p.period_end, p.pay_date, gil[p.name]))
        berurutan = all(
            (periode[i].period_start - periode[i - 1].period_end).days == 1 and (periode[i].period_end - periode[i].period_start).days == 6
            for i in range(1, len(periode)))
        cek("M2 14 periode mingguan berurutan", len(periode) == 14 and berurutan)
        grup = {}
        for p in periode:
            grup.setdefault((p.pay_date.year, p.pay_date.month), []).append(p)
        lengkap = list(grup)[:-1]  # bulan terakhir hanya sebagian
        ukuran = [len(grup[k]) for k in lengkap]
        cek("M3 hanya slip pertama bulan yang bertanda pertama",
            len(lengkap) >= 3 and all([g(p)["pertama"] for p in grup[k]] == [True] + [False] * (len(grup[k]) - 1) for k in lengkap))
        cek("M4 hanya slip terakhir bulan yang bertanda terakhir",
            len(lengkap) >= 3 and all([g(p)["terakhir"] for p in grup[k]] == [False] * (len(grup[k]) - 1) + [True] for k in lengkap))
        cek("M5 bulan bayar berisi 4 atau 5 slip, dan ada yang 5", len(lengkap) >= 3 and set(ukuran) <= {4, 5} and 5 in ukuran, ukuran)
        cek("M6 Per Bulan Slip Pertama: sekali sebulan di slip pertama",
            all([jumlah(p, "Per Bulan", "Slip Pertama", g(p)) for p in grup[k]] == [NILAI] + [0] * (len(grup[k]) - 1) for k in lengkap))
        cek("M7 Per Bulan Slip Terakhir: sekali sebulan di slip terakhir",
            all([jumlah(p, "Per Bulan", "Slip Terakhir", g(p)) for p in grup[k]] == [0] * (len(grup[k]) - 1) + [NILAI] for k in lengkap))
        cek("M8 Per Slip: tiap slip (pembanding)",
            all([jumlah(p, "Per Slip", "Slip Pertama", g(p)) for p in grup[k]] == [NILAI] * len(grup[k]) for k in lengkap))
    except Exception as e:
        cek("M2-M8 berhenti karena galat", False, repr(e)[:400])
    finally:
        frappe.db.rollback()
    cek("M9 rollback: jadwal sintetis tidak tersisa", not frappe.db.exists(SCHEDULE, nama_jadwal))
