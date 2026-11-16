"""Uji validasi Kategori TER di pemetaan PTKP (K-142). Semua perubahan di-rollback.

bench --site hris-uji.local execute hris.hris_payroll.tests.uji_pph21_kategori.jalankan
"""

import frappe

from hris.hris_payroll.doctype.hris_pph21_settings.hris_pph21_settings import kategori_ter
from hris.hris_payroll.services.pph21_rate import kategori_ter_aktif

SETTINGS = "HRIS PPh21 Settings"
RATE = "HRIS PPh21 TER Rate"


def cek(nama, kondisi, info=""):
    print(("OK     " if kondisi else "GAGAL  ") + nama + (" | " + str(info) if info else ""))


def simpan(kategori):
    st = frappe.get_doc(SETTINGS)
    st.set("ptkp_map", [])
    st.append("ptkp_map", {"ptkp_status": "ZZ/0", "ter_category": kategori})
    st.save(ignore_permissions=True)
    return st


def ditolak(kategori):
    try:
        simpan(kategori)
    except frappe.ValidationError:
        return True
    return False


def jalankan():
    n0 = frappe.db.count(RATE)
    aktif0 = frappe.db.get_single_value(SETTINGS, "enabled")
    try:
        tarif = frappe.get_doc({"doctype": RATE, "ter_category": "UJIK", "effective_from": "2030-01-01",
                                "enabled": 1, "bruto_from": 0, "open_ended": 1, "rate_percent": 1}).insert(ignore_permissions=True)
        cek("K1 kategori yang tidak ada di tarif ditolak", ditolak("UJIKX"))
        st = simpan("ujik")
        cek("K2 kategori yang ada diterima dan dinormalkan huruf besar", frappe.get_doc(SETTINGS).ptkp_map[0].ter_category == "UJIK")
        cek("K3 daftar kategori aktif memuat UJIK", "UJIK" in kategori_ter_aktif() and "UJIK" in kategori_ter())
        tarif.enabled = 0
        tarif.save(ignore_permissions=True)
        cek("K4 tarif dinonaktifkan: kategori hilang dari daftar", "UJIK" not in kategori_ter_aktif())
        cek("K5 tarif nonaktif: pemetaan baru ditolak", ditolak("UJIK"))
    except Exception as e:
        cek("K berhenti karena galat", False, repr(e)[:400])
    finally:
        frappe.db.rollback()
    cek("K6 rollback: tarif dan Aktif kembali seperti semula",
        frappe.db.count(RATE) == n0 and frappe.db.get_single_value(SETTINGS, "enabled") == aktif0)
