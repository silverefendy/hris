"""Uji tarif Pasal 17 di HRIS PPh21 Settings (K-142 3b-C). Angka FIKTIF. Semua perubahan di-rollback.

bench --site hris-uji.local execute hris.hris_payroll.tests.uji_pph21_pasal17.jalankan
"""

import frappe
from frappe.utils import flt

from hris.hris_payroll.services.pph21_rate import find_rate17

SETTINGS = "HRIS PPh21 Settings"
ANAK = "HRIS PPh21 Pasal17 Row"


def cek(nama, kondisi, info=""):
    print(("OK     " if kondisi else "GAGAL  ") + nama + (" | " + str(info) if info else ""))


def baris(sejak, dari, sampai, tarif, terbuka=0):
    return {"effective_from": sejak, "bruto_from": dari, "bruto_to": sampai, "open_ended": terbuka, "rate_percent": tarif}


def simpan(daftar):
    st = frappe.get_doc(SETTINGS)
    st.set("pasal17_rates", [])
    for b in daftar:
        st.append("pasal17_rates", b)
    st.save(ignore_permissions=True)


def ditolak(daftar):
    try:
        simpan(daftar)
    except frappe.ValidationError:
        return True
    return False


def tarif(bruto, tanggal):
    r = find_rate17(bruto, tanggal)
    return None if r is None else flt(r.rate_percent)


def jalankan():
    n0 = frappe.db.count(ANAK)
    aktif0 = frappe.db.get_single_value(SETTINGS, "enabled")
    s30 = "2030-01-01"
    set30 = [baris(s30, 0, 60000000, 5), baris(s30, 60000001, 250000000, 15), baris(s30, 250000001, None, 25, 1)]
    try:
        simpan(set30)
        cek("Q1 tiga baris tersimpan dan terbaca kembali", len(frappe.get_doc(SETTINGS).pasal17_rates) == 3)
        cek("Q2 bruto 30 juta -> 5%", tarif(30000000, "2030-06-01") == 5, tarif(30000000, "2030-06-01"))
        cek("Q3 bruto 100 juta -> 15%", tarif(100000000, "2030-06-01") == 15)
        cek("Q4 bruto 1 miliar (tanpa batas atas) -> 25%", tarif(1000000000, "2030-06-01") == 25)
        cek("Q5 sebelum Berlaku Sejak -> tidak ada tarif (None)", find_rate17(30000000, "2029-12-31") is None)

        simpan(set30 + [baris("2031-01-01", 0, 100000000, 7), baris("2031-01-01", 100000001, None, 30, 1)])
        cek("Q6 set baru berlaku sejak 2031, set lama tetap berlaku untuk 2030",
            tarif(50000000, "2031-02-01") == 7 and tarif(50000000, "2030-06-01") == 5,
            (tarif(50000000, "2031-02-01"), tarif(50000000, "2030-06-01")))

        cek("Q7 rentang tumpang tindih dalam satu set ditolak",
            ditolak([baris(s30, 0, 100, 5), baris(s30, 50, 200, 10)]))
        cek("Q8 tarif 150 dan -1 ditolak",
            ditolak([baris(s30, 0, 100, 150)]) and ditolak([baris(s30, 0, 100, -1)]))
        cek("Q9 Bruto Dari negatif dan Sampai < Dari ditolak",
            ditolak([baris(s30, -1, 100, 5)]) and ditolak([baris(s30, 100, 50, 5)]))
        cek("Q10 dua baris tanpa batas atas dalam satu set ditolak",
            ditolak([baris(s30, 0, None, 5, 1), baris(s30, 100, None, 10, 1)]))
    except Exception as e:
        cek("Q berhenti karena galat", False, repr(e)[:400])
    finally:
        frappe.db.rollback()
    cek("Q11 rollback: baris tarif dan Aktif kembali seperti semula",
        frappe.db.count(ANAK) == n0 and frappe.db.get_single_value(SETTINGS, "enabled") == aktif0)
