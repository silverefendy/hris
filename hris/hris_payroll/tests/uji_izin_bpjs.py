"""Uji izin per peran untuk field BPJS di HRIS Employee (K-133). Semua perubahan di-rollback.
Jalankan dari folder sites: ../env/bin/python <path ini>."""

import frappe

SITE = "hris-uji.local"
EMP = "HRIS Employee"
EMAIL_HR = "zz-uji-izin-hr@example.com"
EMAIL_PAY = "zz-uji-izin-payroll@example.com"
ROLE_HR = "HRIS HR Admin"
ROLE_PAY = "HRIS Payroll Admin"
KOLOM = ["bpjs_kes_enrolled", "bpjs_kes_amount", "bpjs_tk_enrolled", "bpjs_tk_amount"]

frappe.init(site=SITE, sites_path=".")
frappe.connect()
frappe.set_user("Administrator")

hasil = []
state = {"he": None, "asli": None}


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


def izin(he):
    meta = frappe.get_meta(EMP)
    d = frappe.get_doc(EMP, he)
    d.apply_fieldlevel_read_permissions()
    return {
        "read": bool(frappe.has_permission(EMP, "read", doc=he)),
        "write": bool(frappe.has_permission(EMP, "write", doc=he)),
        "lvl_read": list(meta.get_permlevel_access("read")),
        "lvl_write": list(meta.get_permlevel_access("write")),
        "nilai": {k: d.get(k) for k in KOLOM},
    }


def coba_simpan(he):
    d = frappe.get_doc(EMP, he)
    d.bpjs_tk_amount = 1
    try:
        d.save()
    except frappe.PermissionError:
        return "ditolak"
    except Exception as exc:
        return "galat lain: %s" % str(exc)[:200]
    return "tersimpan"


def uji():
    ada_hr = frappe.db.exists("Role", ROLE_HR)
    ada_pay = frappe.db.exists("Role", ROLE_PAY)
    cek("P0a peran %s ada" % ROLE_HR, ada_hr)
    cek("P0b peran %s ada" % ROLE_PAY, ada_pay)
    if not (ada_hr and ada_pay):
        return
    he = frappe.db.get_value(EMP, {"status": "Aktif"}, "name")
    cek("P0c ada karyawan Aktif untuk uji", bool(he))
    if not he:
        return
    state["he"] = he
    state["asli"] = dict(frappe.db.get_value(EMP, he, KOLOM, as_dict=True))
    frappe.db.set_value(EMP, he, {"bpjs_kes_enrolled": 1, "bpjs_kes_amount": 30000, "bpjs_tk_enrolled": 1, "bpjs_tk_amount": 150000})
    buat_user(EMAIL_HR, "ZZ Uji Izin HR", ROLE_HR)
    buat_user(EMAIL_PAY, "ZZ Uji Izin Payroll", ROLE_PAY)

    hr = sebagai(EMAIL_HR, lambda: izin(he))
    cek("P1 HR Admin: boleh membaca karyawan", hr["read"], hr)
    cek("P2 HR Admin: boleh menulis karyawan", hr["write"], hr)
    cek("P3 HR Admin: boleh menulis field level 1 (BPJS)", 1 in hr["lvl_write"], hr["lvl_write"])
    cek(
        "P4 HR Admin: melihat angka BPJS (Kesehatan 30.000, Ketenagakerjaan 150.000)",
        hr["nilai"].get("bpjs_kes_amount") == 30000 and hr["nilai"].get("bpjs_tk_amount") == 150000 and hr["nilai"].get("bpjs_tk_enrolled") == 1,
        hr["nilai"],
    )

    pay = sebagai(EMAIL_PAY, lambda: izin(he))
    cek("P5 Payroll Admin: boleh membaca karyawan", pay["read"], pay)
    cek("P6 Payroll Admin: tidak boleh menulis karyawan", not pay["write"], pay)
    cek("P7 Payroll Admin: tidak punya akses tulis level 0 maupun 1", 0 not in pay["lvl_write"] and 1 not in pay["lvl_write"], pay["lvl_write"])
    cek("P8 Payroll Admin: punya akses baca level 1 (BPJS)", 1 in pay["lvl_read"], pay["lvl_read"])
    cek(
        "P9 Payroll Admin: melihat angka BPJS",
        pay["nilai"].get("bpjs_kes_amount") == 30000 and pay["nilai"].get("bpjs_tk_amount") == 150000,
        pay["nilai"],
    )
    hasil_simpan = sebagai(EMAIL_PAY, lambda: coba_simpan(he))
    cek("P10 Payroll Admin: percobaan simpan ditolak", hasil_simpan == "ditolak", hasil_simpan)
    cek("P11 angka di database tidak berubah setelah percobaan", frappe.db.get_value(EMP, he, "bpjs_tk_amount") == 150000, frappe.db.get_value(EMP, he, "bpjs_tk_amount"))


try:
    if frappe.local.site != SITE:
        raise SystemExit("Site bukan %s; berhenti." % SITE)
    uji()
finally:
    frappe.set_user("Administrator")
    frappe.db.rollback()
    for e in (EMAIL_HR, EMAIL_PAY):
        frappe.clear_cache(user=e)
    if hasil:
        sisa = [e for e in (EMAIL_HR, EMAIL_PAY) if frappe.db.exists("User", e)]
        cek("Z1 tidak ada sisa akun uji", not sisa, sisa)
        if state["he"]:
            sekarang = dict(frappe.db.get_value(EMP, state["he"], KOLOM, as_dict=True))
            cek("Z2 angka BPJS karyawan uji kembali seperti semula", sekarang == state["asli"], sekarang)
        print("HASIL: OK %d, GAGAL %d" % (hasil.count(True), hasil.count(False)))
    frappe.destroy()
