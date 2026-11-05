import frappe

DOMAIN = "uji.local"
PERAN = {
    "manager": "HRIS Manager",
    "operator": "HRIS Attendance Operator",
    "payroll": "HRIS Payroll Admin",
}
DOCTYPE_PAYROLL = [
    "HRIS Working Hour", "HRIS Shift", "HRIS Shift Rotation",
    "HRIS Shift Assignment", "HRIS Holiday", "HRIS Employee Group",
]


def _email(kode):
    return "izin.%s@%s" % (kode, DOMAIN)


def _baca(user, doctype):
    return bool(frappe.has_permission(doctype, "read", user=user))


def _role_halaman(baris_role, user):
    return bool(set(frappe.get_roles(user)) & {r.role for r in baris_role})


def siapkan():
    """Buat 3 user uji (tanpa password). Hanya untuk site uji."""
    if "uji" not in frappe.local.site:
        print("BERHENTI: bukan site uji")
        return "berhenti"
    for kode, role in PERAN.items():
        email = _email(kode)
        if frappe.db.exists("User", email):
            frappe.delete_doc("User", email, force=True, ignore_permissions=True)
        u = frappe.get_doc({
            "doctype": "User", "email": email, "first_name": "Izin " + kode,
            "send_welcome_email": 0, "user_type": "System User",
        })
        u.append("roles", {"role": role})
        u.insert(ignore_permissions=True)
    frappe.db.commit()
    print("user uji izin siap")
    return "siap"


def periksa():
    mgr, ops, pay = _email("manager"), _email("operator"), _email("payroll")
    meta = frappe.get_meta("HRIS Employee")
    hasil = [
        ("manager baca Employee", _baca(mgr, "HRIS Employee")),
        ("manager tulis Employee", bool(frappe.has_permission("HRIS Employee", "write", user=mgr))),
        ("manager baca Data Sensitif (L1)", 1 in meta.get_permlevel_access("read", user=mgr)),
        ("manager TIDAK tulis Data Sensitif (L1)", 1 not in meta.get_permlevel_access("write", user=mgr)),
        ("operator baca Pull Run", _baca(ops, "HRIS Pull Run")),
        ("operator TIDAK baca Employee", not _baca(ops, "HRIS Employee")),
    ]
    halaman = frappe.get_doc("Page", "konsol-mesin")
    hasil.append(("operator boleh membuka Konsol Mesin", _role_halaman(halaman.roles, ops)))
    for dt in DOCTYPE_PAYROLL:
        hasil.append(("payroll baca %s" % dt, _baca(pay, dt)))
    hasil.append(("payroll TIDAK baca Raw Log", not _baca(pay, "HRIS Raw Log")))
    laporan = frappe.get_all("Report", filters={"name": ["like", "%Working Hour%"]}, pluck="name")
    if laporan:
        rep = frappe.get_doc("Report", laporan[0])
        hasil.append(("payroll boleh membuka laporan %s" % laporan[0], _role_halaman(rep.roles, pay)))
    else:
        hasil.append(("laporan Working Hour ditemukan", False))
    gagal = 0
    for nama, ok in hasil:
        print(("OK     " if ok else "GAGAL  ") + nama)
        gagal += 0 if ok else 1
    ringkas = "TOTAL: %d OK, GAGAL %d" % (len(hasil) - gagal, gagal)
    print(ringkas)
    return ringkas


def bersihkan():
    for kode in PERAN:
        email = _email(kode)
        if frappe.db.exists("User", email):
            frappe.delete_doc("User", email, force=True, ignore_permissions=True)
    frappe.db.commit()
    print("dibersihkan")
    return "dibersihkan"


PERAN_LANJUT = {
    "direksi": "HRIS Direksi",
    "eadmin": "HRIS Employee Admin",
}


def siapkan_lanjut():
    """Buat user uji untuk Direksi dan Employee Admin. Hanya site uji."""
    if "uji" not in frappe.local.site:
        print("BERHENTI: bukan site uji")
        return "berhenti"
    for kode, role in PERAN_LANJUT.items():
        email = _email(kode)
        if frappe.db.exists("User", email):
            frappe.delete_doc("User", email, force=True, ignore_permissions=True)
        u = frappe.get_doc({
            "doctype": "User", "email": email, "first_name": "Izin " + kode,
            "send_welcome_email": 0, "user_type": "System User",
        })
        u.append("roles", {"role": role})
        u.insert(ignore_permissions=True)
    frappe.db.commit()
    print("user uji lanjut siap")
    return "siap"


def _sebagai(user, fn):
    """Jalankan fn sebagai user. True bila tidak ada PermissionError."""
    frappe.set_user(user)
    try:
        fn()
        return True
    except frappe.PermissionError:
        return False
    except Exception:
        return True  # cek izin lolos; error lain berasal dari logika sesudahnya
    finally:
        frappe.set_user("Administrator")


def periksa_lanjut():
    from hris.hris_attendance.report.hris_working_hour_ringkasan import (
        hris_working_hour_ringkasan as laporan,
    )
    from hris.hris_attendance.services import pull_device

    dire, adm = _email("direksi"), _email("eadmin")
    ops, pay = _email("operator"), _email("payroll")
    meta = frappe.get_meta("HRIS Employee")

    def tulis(user, dt):
        return bool(frappe.has_permission(dt, "write", user=user))

    hasil = [
        ("direksi baca Employee", _baca(dire, "HRIS Employee")),
        ("direksi baca Data Sensitif (L1)", 1 in meta.get_permlevel_access("read", user=dire)),
        ("direksi TIDAK tulis Employee", not tulis(dire, "HRIS Employee")),
        ("direksi TIDAK tulis Data Sensitif (L1)", 1 not in meta.get_permlevel_access("write", user=dire)),
        ("direksi baca Payroll Schedule", _baca(dire, "HRIS Payroll Schedule")),
        ("direksi baca Raw Log", _baca(dire, "HRIS Raw Log")),
        ("direksi TIDAK tulis Raw Log", not tulis(dire, "HRIS Raw Log")),
        ("employee admin tulis Employee", tulis(adm, "HRIS Employee")),
        ("employee admin tulis Data Sensitif (L1)", 1 in meta.get_permlevel_access("write", user=adm)),
        ("employee admin TIDAK baca Raw Log", not _baca(adm, "HRIS Raw Log")),
        ("employee admin TIDAK baca Payroll Schedule", not _baca(adm, "HRIS Payroll Schedule")),
    ]
    dev = frappe.db.get_value("HRIS Device", {}, "name")
    if dev:
        hasil.append(("operator lolos cek tarik log", _sebagai(ops, lambda: pull_device._check_pull_access(dev))))
        hasil.append(("payroll DITOLAK cek tarik log", not _sebagai(pay, lambda: pull_device._check_pull_access(dev))))
    else:
        hasil.append(("ada HRIS Device untuk menguji tarik log", False))
    hasil += [
        ("payroll lolos cek laporan", _sebagai(pay, lambda: laporan.execute({}))),
        ("direksi lolos cek laporan", _sebagai(dire, lambda: laporan.execute({}))),
        ("operator DITOLAK cek laporan", not _sebagai(ops, lambda: laporan.execute({}))),
    ]
    gagal = 0
    for nama, ok in hasil:
        print(("OK     " if ok else "GAGAL  ") + nama)
        gagal += 0 if ok else 1
    ringkas = "TOTAL: %d OK, GAGAL %d" % (len(hasil) - gagal, gagal)
    print(ringkas)
    return ringkas


def bersihkan_lanjut():
    for kode in PERAN_LANJUT:
        email = _email(kode)
        if frappe.db.exists("User", email):
            frappe.delete_doc("User", email, force=True, ignore_permissions=True)
    frappe.db.commit()
    print("dibersihkan lanjut")
    return "dibersihkan lanjut"
