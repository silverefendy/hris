"""Uji PTKP nominal dan biaya jabatan di HRIS PPh21 Settings (K-142 3b-A dan 3b-B). Semua perubahan di-rollback.

bench --site hris-uji.local execute hris.hris_payroll.tests.uji_pph21_ptkp.jalankan
"""

import frappe
from frappe.utils import flt

SETTINGS = "HRIS PPh21 Settings"
ANAK = "HRIS PPh21 PTKP Map"


def cek(nama, kondisi, info=""):
    print(("OK     " if kondisi else "GAGAL  ") + nama + (" | " + str(info) if info else ""))


def simpan(**nilai):
    st = frappe.get_doc(SETTINGS)
    for k, v in nilai.items():
        if k == "baris":
            st.set("ptkp_map", [])
            for b in v:
                st.append("ptkp_map", b)
        else:
            st.set(k, v)
    st.save(ignore_permissions=True)
    return st


def ditolak(**nilai):
    try:
        simpan(**nilai)
    except frappe.ValidationError:
        return True
    return False


def jalankan():
    n_anak0 = frappe.db.count(ANAK)
    aktif0 = frappe.db.get_single_value(SETTINGS, "enabled")
    persen0 = frappe.db.get_single_value(SETTINGS, "biaya_jabatan_persen")
    maks0 = frappe.db.get_single_value(SETTINGS, "biaya_jabatan_maks_tahun")
    try:
        frappe.get_doc({"doctype": "HRIS PPh21 TER Rate", "ter_category": "UJIP", "effective_from": "2030-01-01",
                        "enabled": 1, "bruto_from": 0, "open_ended": 1, "rate_percent": 1}).insert(ignore_permissions=True)
        simpan(baris=[{"ptkp_status": "ZZ/0", "ter_category": "UJIP", "ptkp_amount": 1000000}])
        r = frappe.get_doc(SETTINGS).ptkp_map
        cek("P1 PTKP nominal tersimpan dan terbaca kembali", len(r) == 1 and flt(r[0].ptkp_amount) == 1000000, [x.as_dict().get("ptkp_amount") for x in r])

        simpan(baris=[{"ptkp_status": "ZZ/1", "ter_category": "UJIP"}])
        r = frappe.get_doc(SETTINGS).ptkp_map
        cek("P2 baris tanpa PTKP nominal tetap boleh (nilai 0)", len(r) == 1 and flt(r[0].ptkp_amount) == 0)

        cek("P3 PTKP nominal negatif ditolak",
            ditolak(baris=[{"ptkp_status": "ZZ/2", "ter_category": "UJIP", "ptkp_amount": -1}]))

        simpan(baris=[], biaya_jabatan_persen=5, biaya_jabatan_maks_tahun=6000000)
        st = frappe.get_doc(SETTINGS)
        cek("P4 biaya jabatan tersimpan dan terbaca kembali",
            flt(st.biaya_jabatan_persen) == 5 and flt(st.biaya_jabatan_maks_tahun) == 6000000,
            (st.biaya_jabatan_persen, st.biaya_jabatan_maks_tahun))

        cek("P5 persen di luar 0 sampai 100 ditolak (150 dan -1)",
            ditolak(biaya_jabatan_persen=150) and ditolak(biaya_jabatan_persen=-1))

        cek("P6 batas setahun negatif ditolak", ditolak(biaya_jabatan_maks_tahun=-5))
    except Exception as e:
        cek("P berhenti karena galat", False, repr(e)[:400])
    finally:
        frappe.db.rollback()
    cek("P7 rollback: pemetaan, Aktif, dan biaya jabatan kembali seperti semula",
        frappe.db.count(ANAK) == n_anak0
        and frappe.db.get_single_value(SETTINGS, "enabled") == aktif0
        and frappe.db.get_single_value(SETTINGS, "biaya_jabatan_persen") == persen0
        and frappe.db.get_single_value(SETTINGS, "biaya_jabatan_maks_tahun") == maks0)
