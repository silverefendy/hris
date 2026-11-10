"""Uji izin per peran untuk PPh 21 (K-134): field PTKP di HRIS Employee, HRIS PPh21 Settings,
HRIS PPh21 TER Rate. Mengunci kondisi izin saat ini. Semua perubahan di-rollback.
Jalankan dari folder sites: ../env/bin/python <path ini>."""

import sys

import frappe

SITE = "hris-uji.local"
EMP = "HRIS Employee"
SETT = "HRIS PPh21 Settings"
TER = "HRIS PPh21 TER Rate"

# kunci: (email, role)
PERAN = {
    "HR Admin": ("zz-uji-pph-hr@example.com", "HRIS HR Admin"),
    "Payroll Admin": ("zz-uji-pph-pa@example.com", "HRIS Payroll Admin"),
    "Payroll Manager": ("zz-uji-pph-pm@example.com", "HRIS Payroll Manager"),
    "Direksi": ("zz-uji-pph-dir@example.com", "HRIS Direksi"),
}

# harapan izin PTKP (permlevel 1): bisa menulis atau hanya membaca
TULIS_PTKP = {"HR Admin": True, "Payroll Admin": False, "Payroll Manager": False, "Direksi": False}

# harapan izin DocType: (read, write, create, delete)
HARAPAN_SETT = {
    "HR Admin": (True, True, False, False),
    "Payroll Admin": (True, False, False, False),
    "Payroll Manager": (True, False, False, False),
    "Direksi": (True, False, False, False),
}
HARAPAN_TER = {
    "HR Admin": (True, True, True, False),
    "Payroll Admin": (True, False, False, False),
    "Payroll Manager": (True, False, False, False),
    "Direksi": (True, False, False, False),
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


def izin_emp(he):
    meta = frappe.get_meta(EMP)
    return {
        "read": bool(frappe.has_permission(EMP, "read", doc=he)),
        "write": bool(frappe.has_permission(EMP, "write", doc=he)),
        "lvl_read": list(meta.get_permlevel_access("read")),
        "lvl_write": list(meta.get_permlevel_access("write")),
    }


def coba_simpan(he):
    d = frappe.get_doc(EMP, he)
    d.ptkp_status = "K/1"
    try:
        d.save()
    except frappe.PermissionError:
        return "ditolak"
    except Exception as exc:
        return "galat lain: %s" % str(exc)[:200]
    return "tersimpan"


def izin_dt(dt):
    return tuple(bool(frappe.has_permission(dt, p)) for p in ("read", "write", "create", "delete"))


def uji():
    ada = {}
    for nama, (email, role) in PERAN.items():
        ada[nama] = bool(frappe.db.exists("Role", role))
        cek("P0 peran %s ada" % role, ada[nama])
    if not ada["HR Admin"] or not ada["Payroll Admin"]:
        print("BERHENTI: peran inti tidak ada")
        return

    n_cdp = frappe.db.count("Custom DocPerm", {"parent": ["like", "HRIS%"]})
    cek("P0 tidak ada Custom DocPerm HRIS yang menimpa izin", n_cdp == 0, "jumlah=%s" % n_cdp)

    he = frappe.db.get_value(EMP, {"status": "Aktif"}, "name")
    cek("P0 ada karyawan Aktif untuk uji", bool(he))
    if not he:
        return

    for nama, (email, role) in PERAN.items():
        if ada[nama]:
            buat_user(email, "ZZ Uji " + nama, role)

    for nama, (email, role) in PERAN.items():
        if not ada[nama]:
            print("LEWAT   peran %s tidak ada di site (tidak dihitung)" % role)
            continue

        e = sebagai(email, lambda: izin_emp(he))
        cek("E %s: bisa baca HRIS Employee" % nama, e["read"], e)
        cek("E %s: field PTKP terbaca (permlevel 1 di akses baca)" % nama, 1 in e["lvl_read"], e)
        cek(
            "E %s: akses tulis PTKP (permlevel 1) = %s" % (nama, TULIS_PTKP[nama]),
            (1 in e["lvl_write"]) == TULIS_PTKP[nama],
            e,
        )
        if not TULIS_PTKP[nama]:
            r = sebagai(email, lambda: coba_simpan(he))
            cek("E %s: simpan Status PTKP ditolak" % nama, r == "ditolak", r)

        s = sebagai(email, lambda: izin_dt(SETT))
        cek("S %s: Settings (baca, tulis, buat, hapus) = %s" % (nama, HARAPAN_SETT[nama]), s == HARAPAN_SETT[nama], s)

        t = sebagai(email, lambda: izin_dt(TER))
        cek("T %s: TER Rate (baca, tulis, buat, hapus) = %s" % (nama, HARAPAN_TER[nama]), t == HARAPAN_TER[nama], t)


try:
    uji()
finally:
    frappe.set_user("Administrator")
    frappe.db.rollback()
    for _, (email, _r) in PERAN.items():
        frappe.clear_cache(user=email)
    sisa = [e for _, (e, _r) in PERAN.items() if frappe.db.exists("User", e)]
    cek("Z user uji tidak tersisa", not sisa, sisa)
    frappe.destroy()

print("HASIL OK %d GAGAL %d" % (sum(hasil), len(hasil) - sum(hasil)))
sys.exit(0 if all(hasil) else 1)
