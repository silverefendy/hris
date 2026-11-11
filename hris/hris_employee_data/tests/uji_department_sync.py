"""Uji sinkron HRIS Department -> Department ERPNext (K-136 tahap 3). Semua di-rollback.
Syarat: tahap 2 sudah disalin dan adopsi sudah dijalankan di site uji.
Jalankan dari folder sites: ../env/bin/python <path ini>."""

import sys

import frappe

SITE = "hris-uji.local"
DT = "HRIS Department"
ROOT = "All Departments"
PENGGUNA = {
    "HR Admin": ("zz-uji-sync-hr@example.com", "HRIS HR Admin"),
    "Payroll Admin": ("zz-uji-sync-pa@example.com", "HRIS Payroll Admin"),
}

frappe.init(site=SITE, sites_path=".")
frappe.connect()
frappe.set_user("Administrator")

hasil = []


def cek(nama, kondisi, rinci=""):
    hasil.append(bool(kondisi))
    print(("OK      " if kondisi else "GAGAL   ") + nama + ("" if kondisi or not rinci else "  " + str(rinci)))


def gagal(fn):
    try:
        fn()
    except Exception as exc:
        return type(exc).__name__
    return None


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


def baru(nama, company, parent=None, is_group=0, lewati_sinkron=False):
    d = frappe.get_doc(
        {"doctype": DT, "department_name": nama, "company": company, "parent_department": parent, "is_group": is_group}
    )
    d.flags.skip_sync = lewati_sinkron
    d.insert()
    d.reload()
    return d


def erp(nama):
    return frappe.db.get_value("Department", nama, ["parent_department", "disabled", "company"], as_dict=True)


def uji():
    root = frappe.db.get_value(DT, ROOT, ["name", "erpnext_department"], as_dict=True)
    cek("A0 akar HRIS ada dan sudah diadopsi", bool(root and root.erpnext_department), root)
    if not (root and root.erpnext_department):
        return
    company = frappe.db.get_value(DT, {"company": ["is", "set"]}, "company")
    abbr = frappe.get_cached_value("Company", company, "abbr")

    induk = baru("ZZ Uji Sinkron", company, is_group=1)
    cek("S1 induk Berhasil", induk.sync_status == "Berhasil", (induk.sync_status, induk.sync_error))
    cek("S1 nama ERPNext = nama HRIS", induk.erpnext_department == "ZZ Uji Sinkron - %s" % abbr, induk.erpnext_department)
    e = erp(induk.erpnext_department) if induk.erpnext_department else None
    cek("S1 induk ERPNext = akar ERPNext", bool(e) and e.parent_department == root.erpnext_department, e)
    cek("S1 tidak nonaktif dan company sama", bool(e) and not e.disabled and e.company == company, e)

    anak = baru("ZZ Uji Anak", company, parent=induk.name)
    e = erp(anak.erpnext_department) if anak.erpnext_department else None
    cek("S2 anak mengikuti induk ERPNext", bool(e) and e.parent_department == induk.erpnext_department, e)

    anak.is_active = 0
    anak.save()
    anak.reload()
    cek("S3 nonaktif HRIS menonaktifkan ERPNext", bool(erp(anak.erpnext_department)) and erp(anak.erpnext_department).disabled == 1)

    anak.department_name = "ZZ Uji Ganti"
    cek("S4 ganti nama setelah tersinkron ditolak", gagal(anak.save) is not None)
    anak.reload()

    induk2 = baru("ZZ Uji Induk Belum", company, is_group=1, lewati_sinkron=True)
    anak2 = baru("ZZ Uji Anak Belum", company, parent=induk2.name)
    cek("S5 induk belum tersinkron: status Gagal", anak2.sync_status == "Gagal", anak2.sync_status)
    cek("S5 Department ERPNext tidak dibuat", not frappe.db.exists("Department", "ZZ Uji Anak Belum - %s" % abbr))

    from hris.hris_employee_data.services.department_sync import sinkron_ulang

    for nama, (email, role) in PENGGUNA.items():
        if frappe.db.exists("Role", role):
            buat_user(email, "ZZ Uji " + nama, role)
    email_pa, role_pa = PENGGUNA["Payroll Admin"]
    email_hr, role_hr = PENGGUNA["HR Admin"]
    if frappe.db.exists("Role", role_pa):
        cek("I Payroll Admin tidak boleh Sinkron Ulang", sebagai(email_pa, lambda: gagal(lambda: sinkron_ulang(induk.name))) is not None)
    if frappe.db.exists("Role", role_hr):
        cek("I HR Admin boleh Sinkron Ulang", sebagai(email_hr, lambda: gagal(lambda: sinkron_ulang(induk.name))) is None)


try:
    uji()
finally:
    frappe.set_user("Administrator")
    frappe.db.rollback()
    for _n, (email, _r) in PENGGUNA.items():
        frappe.clear_cache(user=email)
    sisa_user = [e for _n, (e, _r) in PENGGUNA.items() if frappe.db.exists("User", e)]
    sisa_hris = frappe.db.count(DT, {"department_name": ["like", "ZZ Uji%"]})
    sisa_erp = frappe.db.count("Department", {"department_name": ["like", "ZZ Uji%"]})
    cek("Z user dan Department uji tidak tersisa", not sisa_user and sisa_hris == 0 and sisa_erp == 0, (sisa_user, sisa_hris, sisa_erp))
    frappe.destroy()

print("HASIL OK %d GAGAL %d" % (sum(hasil), len(hasil) - sum(hasil)))
sys.exit(0 if all(hasil) else 1)
