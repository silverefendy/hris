"""Uji K-136: patch aturan akar idempoten (site uji saja)."""

import frappe
from frappe.utils import flt
from frappe.utils.nestedset import get_root_of

SITE = "hris-uji.local"
frappe.init(site=SITE, sites_path=".")
frappe.connect()
frappe.set_user("Administrator")

from hris.patches.v1_0.buat_aturan_akar_department import execute  # noqa: E402

RULE = "HRIS Department Rule"
ok = 0
gagal = 0


def cek(kode, kondisi, ket):
    global ok, gagal
    if kondisi:
        ok += 1
        print("OK      {0} {1}".format(kode, ket))
    else:
        gagal += 1
        print("GAGAL   {0} {1}".format(kode, ket))


def utama():
    akar = get_root_of("HRIS Department")
    semua = frappe.get_all(RULE, fields=["name", "department", "overtime_multiplier", "is_active"])
    if not (len(semua) == 1 and semua[0].department == akar and flt(semua[0].overtime_multiplier) == 1.0 and semua[0].is_active):
        print("BERHENTI: uji butuh tepat 1 aturan akar aktif 1.0. Ada:", semua)
        return
    asli = semua[0].name
    cek("S0", True, "aturan akar tunggal: {0} ({1})".format(asli, akar))

    execute()
    cek("P1a", frappe.db.count(RULE) == 1, "execute() saat aturan akar ada tidak menambah aturan")
    execute()
    cek("P1b", frappe.db.count(RULE) == 1, "execute() kedua kali tetap 1 aturan")

    try:
        frappe.db.set_value(RULE, asli, "is_active", 0)
        execute()
        aktif = frappe.get_all(
            RULE, filters={"department": akar, "is_active": 1},
            fields=["name", "effective_from", "overtime_multiplier"],
        )
        cek("P2a", len(aktif) == 1 and frappe.db.count(RULE) == 2, "aturan akar tidak aktif: dibuat tepat 1 aturan baru ({0})".format(aktif))
        cek(
            "P2b",
            len(aktif) == 1 and flt(aktif[0].overtime_multiplier) == 1.0 and str(aktif[0].effective_from) == "2000-01-01",
            "aturan baru bernilai 1.0 berlaku 2000-01-01",
        )
        execute()
        cek("P2c", frappe.db.count(RULE) == 2, "execute() lagi tidak menambah aturan")
    finally:
        frappe.db.rollback()

    sisa = frappe.get_all(RULE, fields=["name", "is_active"])
    cek("P3a", len(sisa) == 1 and sisa[0].name == asli, "setelah rollback hanya aturan asli: {0}".format(sisa))
    cek("P3b", len(sisa) == 1 and sisa[0].is_active == 1, "aturan asli kembali aktif")


try:
    utama()
finally:
    frappe.destroy()
print("HASIL OK {0} GAGAL {1}".format(ok, gagal))
