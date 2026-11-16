"""Uji tarif Pasal 17 sebagai DocType terpisah (K-142 3b-C ulang). Angka FIKTIF. Semua perubahan di-rollback.

bench --site hris-uji.local execute hris.hris_payroll.tests.uji_pph21_pasal17.jalankan
"""

import frappe
from frappe.utils import flt, nowdate

from hris.hris_payroll.services.pph21_rate import find_rate17

DT = "HRIS PPh21 Pasal17 Rate"
SETTINGS = "HRIS PPh21 Settings"


def cek(nama, kondisi, info=""):
    print(("OK     " if kondisi else "GAGAL  ") + nama + (" | " + str(info) if info else ""))


def buat(sejak, dari, sampai, tarif, terbuka=0, aktif=1):
    return frappe.get_doc({"doctype": DT, "effective_from": sejak, "bruto_from": dari, "bruto_to": sampai,
                           "open_ended": terbuka, "rate_percent": tarif, "enabled": aktif}).insert(ignore_permissions=True)


def ditolak(*args, **kw):
    try:
        buat(*args, **kw)
    except frappe.ValidationError:
        return True
    return False


def tarif(bruto, tanggal):
    r = find_rate17(bruto, tanggal)
    return None if r is None else flt(r.rate_percent)


def jalankan():
    n0 = frappe.db.count(DT)
    aktif0 = frappe.db.get_single_value(SETTINGS, "enabled")
    s30 = "2030-01-01"
    try:
        a = buat(s30, 0, 60000000, 5)
        buat(s30, 60000001, 250000000, 15)
        buat(s30, 250000001, None, 25, 1)
        awalan = "P17-" + nowdate()[2:4] + nowdate()[5:7] + "-"
        cek("Q1 tiga baris tersimpan, penomoran P17-YYMM-NNNN", frappe.db.count(DT) == n0 + 3 and a.name.startswith(awalan), a.name)
        cek("Q2 bruto 30 juta -> 5%", tarif(30000000, "2030-06-01") == 5, tarif(30000000, "2030-06-01"))
        cek("Q3 bruto 100 juta -> 15%", tarif(100000000, "2030-06-01") == 15)
        cek("Q4 bruto 1 miliar (tanpa batas atas) -> 25%", tarif(1000000000, "2030-06-01") == 25)
        cek("Q5 sebelum Berlaku Sejak -> tidak ada tarif (None)", find_rate17(30000000, "2029-12-31") is None)
        buat("2031-01-01", 0, 100000000, 7)
        buat("2031-01-01", 100000001, None, 30, 1)
        cek("Q6 set baru berlaku 2031, set lama tetap berlaku untuk 2030",
            tarif(50000000, "2031-02-01") == 7 and tarif(50000000, "2030-06-01") == 5,
            (tarif(50000000, "2031-02-01"), tarif(50000000, "2030-06-01")))
        cek("Q7 rentang tumpang tindih dalam satu set ditolak", ditolak(s30, 50000000, 70000000, 9))
        cek("Q8 tarif 150 dan -1 ditolak", ditolak("2032-01-01", 0, 100, 150) and ditolak("2032-01-01", 0, 100, -1))
        cek("Q9 Bruto Dari negatif dan Sampai < Dari ditolak",
            ditolak("2032-01-01", -1, 100, 5) and ditolak("2032-01-01", 100, 50, 5))
        cek("Q10 dua baris tanpa batas atas dalam satu set ditolak",
            ditolak(s30, 300000000, None, 30, 1))
    except Exception as e:
        cek("Q berhenti karena galat", False, repr(e)[:400])
    finally:
        frappe.db.rollback()
    cek("Q11 rollback: baris tarif dan Aktif kembali seperti semula",
        frappe.db.count(DT) == n0 and frappe.db.get_single_value(SETTINGS, "enabled") == aktif0)
