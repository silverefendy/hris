"""Uji batas hari depan pada hitung massal. Tidak meninggalkan data (rollback).
  bench --site hris-uji.local execute hris.hris_payroll.tests.uji_hari_depan.jalankan
"""
import frappe
from frappe.utils import add_days, getdate, nowdate

from hris.hris_attendance.services import working_hour_batch as batch
from hris.hris_attendance.services.working_hour import DT


def jalankan():
    print("Saklar hris_batasi_hari_depan =", frappe.conf.get("hris_batasi_hari_depan", 1))
    emp = frappe.db.sql(
        "select employee from `tabHRIS Working Hour` group by employee order by count(*) desc limit 1"
    )[0][0]
    hari_ini = getdate(nowdate())
    filt = {"employee": emp, "work_date": [">=", hari_ini]}
    sebelum = frappe.db.count(DT, filt)
    params = {"from_date": str(add_days(hari_ini, -2)), "to_date": str(add_days(hari_ini, 2)), "skip_reviewed": 0}
    print("Karyawan:", emp, "| rentang:", params["from_date"], "s/d", params["to_date"], "| hari ini:", hari_ini)
    sesudah = None
    try:
        hasil = batch._process([{"name": emp, "date_of_joining": None}], params)
        print("Hasil _process:", hasil)
        sesudah = frappe.db.count(DT, filt)
    except Exception as exc:
        print("ERROR:", str(exc)[:200])
    finally:
        frappe.db.rollback()
    print("Dokumen pada hari ini dan setelahnya: sebelum =", sebelum, "| sesudah =", sesudah)
    print("Harapan (saklar 1): total = 2 (dua hari sebelum hari ini) dan jumlah dokumen hari ini dan setelahnya tidak berubah.")
