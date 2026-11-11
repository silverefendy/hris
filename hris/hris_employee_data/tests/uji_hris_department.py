"""Uji HRIS Department tahap 1 (K-136): penamaan, pohon, penolakan, izin per peran. Semua di-rollback.
Jalankan dari folder sites: ../env/bin/python <path ini>."""

import sys

import frappe
from frappe.utils.nestedset import get_descendants_of

SITE = "hris-uji.local"
DT = "HRIS Department"
PERAN = {
    "HR Admin": ("zz-uji-dept-hr@example.com", "HRIS HR Admin", (True, True, True, False)),
    "Manager": ("zz-uji-dept-mgr@example.com", "HRIS Manager", (True, True, True, False)),
    "Payroll Admin": ("zz-uji-dept-pa@example.com", "HRIS Payroll Admin", (True, False, False, False)),
    "Direksi": ("zz-uji-dept-dir@example.com", "HRIS Direksi", (True, False, False, False)),
}

frappe.init(site=SITE, sites_path=".")
frappe.connect()
frappe.set_user("Administrator")

hasil = []


def cek(nama, kondisi, rinci=""):
    hasil.append(bool(kondisi))
    print(("OK      " if kondisi else "GAGAL   ") + nama + ("" if kondisi or not rinci else "  " + str(rinci)))


def sebagai(email, fn):
    frappe.set_user(email)
    try:
        return fn()
    finally:
        frappe.set_user("Administrator")


def buat_user(email, nama, role):
    frappe.get_doc(
        {
            "doctype": "User", "email": email, "first_name": nama, "enabled": 1,
            "send_welcome_email": 0, "user_type": "System User", "roles": [{"role": role}],
        }
    ).insert(ignore_permissions=True)
    frappe.clear_cache(user=email)


def baru(nama, company, parent=None, is_group=0):
    d = frappe.get_doc(
        {"doctype": DT, "department_name": nama, "company": company, "parent_department": parent, "is_group": is_group}
    )
    d.insert()
    return d


def gagal(fn):
    try:
        fn()
    except Exception as exc:
        return type(exc).__name__
    return None


def uji():
    ada = bool(frappe.db.exists("DocType", DT))
    cek("D0 DocType HRIS Department ada", ada)
    if not ada:
        return
    cek("D0 DocType berbentuk pohon", bool(frappe.get_meta(DT).is_tree))
    cek("D0 tabel ada", frappe.db.table_exists(DT))

    company = frappe.db.get_value("Company", {}, "name")
    abbr = frappe.get_cached_value("Company", company, "abbr")
    cek("D0 ada Company untuk uji", bool(company))
    if not company:
        return

    induk = baru("ZZ Uji Induk", company, is_group=1)
    cek("N1 nama otomatis memuat singkatan company", induk.name == "ZZ Uji Induk - %s" % abbr, induk.name)
    anak = baru("ZZ Uji Anak", company, parent=induk.name, is_group=1)
    daun = baru("ZZ Uji Daun", company, parent=anak.name, is_group=0)
    induk.reload(); anak.reload(); daun.reload()
    cek("P1 anak berada di dalam rentang induk", induk.lft < anak.lft < anak.rgt < induk.rgt, (induk.lft, anak.lft, anak.rgt, induk.rgt))
    cek("P2 cucu menjadi turunan induk", daun.name in get_descendants_of(DT, induk.name), get_descendants_of(DT, induk.name))

    cek("R1 nama ganda ditolak", gagal(lambda: baru("ZZ Uji Induk", company, is_group=1)) is not None)
    cek("R2 induk bukan Is Group ditolak", gagal(lambda: baru("ZZ Uji Salah", company, parent=daun.name)) is not None)
    def validasi_tanpa_company():
        d = frappe.get_doc({"doctype": DT, "department_name": "ZZ Uji Tanpa Company", "parent_department": induk.name})
        d.company = None
        d.validate()

    cek("R3 company wajib untuk bukan akar", gagal(validasi_tanpa_company) is not None)

    for nama, (email, role, _) in PERAN.items():
        if frappe.db.exists("Role", role):
            buat_user(email, "ZZ Uji " + nama, role)
    for nama, (email, role, harapan) in PERAN.items():
        if not frappe.db.exists("Role", role):
            print("LEWAT   peran %s tidak ada (tidak dihitung)" % role)
            continue
        h = sebagai(email, lambda: tuple(bool(frappe.has_permission(DT, p)) for p in ("read", "write", "create", "delete")))
        cek("I %s: (baca, tulis, buat, hapus) = %s" % (nama, harapan), h == harapan, h)


try:
    uji()
finally:
    frappe.set_user("Administrator")
    frappe.db.rollback()
    for _n, (email, _r, _h) in PERAN.items():
        frappe.clear_cache(user=email)
    sisa_user = [e for _n, (e, _r, _h) in PERAN.items() if frappe.db.exists("User", e)]
    sisa_dept = frappe.db.count(DT, {"department_name": ["like", "ZZ Uji%"]}) if frappe.db.table_exists(DT) else 0
    cek("Z user dan Department uji tidak tersisa", not sisa_user and sisa_dept == 0, (sisa_user, sisa_dept))
    frappe.destroy()

print("HASIL OK %d GAGAL %d" % (sum(hasil), len(hasil) - sum(hasil)))
sys.exit(0 if all(hasil) else 1)
