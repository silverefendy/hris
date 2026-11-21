"""Jam koreksi ditolak bila Klasifikasi Absen terisi (hari Tidak Hadir). Di-rollback.
  bench --site hris-uji.local execute hris.hris_payroll.tests.uji_jam_koreksi_klasifikasi.jalankan
"""
from datetime import datetime

import frappe
from frappe.utils import get_time, getdate

from hris.hris_payroll.services.period_lock import is_locked

WH = "HRIS Working Hour"


def _bebas(emp, day):
    try:
        return not is_locked(emp, day)
    except Exception:
        return False


def _cari(filters):
    for r in frappe.get_all(
        WH, filters=filters,
        fields=["name", "employee", "work_date", "shift_start"], limit=60,
    ):
        if r.shift_start and _bebas(r.employee, r.work_date):
            return r
    return None


def _mulai(r):
    return datetime.combine(getdate(r.work_date), get_time(r.shift_start))


def jalankan():
    if frappe.local.site != "hris-uji.local":
        print("Site bukan hris-uji.local; berhenti.")
        return
    ok = total = 0
    try:
        # K1: hari Tidak Hadir + Klasifikasi Absen + jam koreksi -> ditolak aturan baru
        r = _cari({"status": "Tidak Hadir", "is_holiday": 0, "absence_class": ["in", ["", None]]})
        if not r:
            print("INFO  K1 dilewati: tidak ada hari Tidak Hadir yang bisa dipakai (aturan belum terbukti)")
        else:
            d = frappe.get_doc(WH, r.name)
            d.absence_class = "Lainnya"
            d.absence_note = "uji klasifikasi"
            d.manual_check_in = _mulai(r)
            d.review_note = "uji (data uji)"
            pesan = ""
            try:
                d.save()
            except Exception as e:
                pesan = str(e)
            total += 1
            if "Klasifikasi Absen terisi" in pesan:
                ok += 1
                print("OK    K1 jam koreksi ditolak bila Klasifikasi Absen terisi (%s)" % r.name)
            else:
                print("GAGAL K1 | %s | pesan: %s" % (r.name, pesan or "(tidak ditolak)"))
            frappe.db.rollback()

        # K2: kontrol, hari Tidak Lengkap tanpa klasifikasi, jam koreksi tersimpan
        r = _cari({"status": "Tidak Lengkap", "review_status": "Menunggu",
                   "check_in": ["is", "not set"], "check_out": ["is", "set"]})
        if not r:
            print("INFO  K2 dilewati: tidak ada kandidat Tidak Lengkap")
        else:
            d = frappe.get_doc(WH, r.name)
            d.manual_check_in = _mulai(r)
            d.review_note = "uji (data uji)"
            total += 1
            try:
                d.save()
                ok += 1
                print("OK    K2 tanpa Klasifikasi Absen, jam koreksi tersimpan (%s)" % r.name)
            except Exception as e:
                print("GAGAL K2 | %s" % e)
    finally:
        frappe.db.rollback()
    print("Lulus %d dari %d" % (ok, total))
