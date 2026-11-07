"""Uji K-127: Audit Trail dan Version untuk HRIS Employee Pay. Semua di-rollback.

Jalankan:
bench --site hris-uji.local execute hris.hris_payroll.tests.uji_employee_pay_audit.periksa
"""

import frappe
from frappe.utils import strip_html

hasil = []

USERS = {
    "admin": ("uji.aud.admin@uji.local", ["HRIS Payroll Admin"]),
    "manager": ("uji.aud.manager@uji.local", ["HRIS Payroll Manager"]),
    "direksi": ("uji.aud.direksi@uji.local", ["HRIS Direksi"]),
}


def _catat(nama, lulus, info=""):
    hasil.append(bool(lulus))
    print(("OK     " if lulus else "GAGAL  ") + nama + ((" | " + info) if info else ""))


def _info(nama, info=""):
    print("INFO   " + nama + ((" | " + info) if info else ""))


def _karyawan(perusahaan, nama):
    doc = frappe.get_doc(
        {
            "doctype": "HRIS Employee",
            "employee_name": nama,
            "birth_date": "1990-05-10",
            "gender": "Laki-laki",
            "company": perusahaan,
            "date_of_joining": "2020-01-01",
            "status": "Aktif",
        }
    )
    doc.flags.skip_sync = True
    doc.insert(ignore_permissions=True)
    return doc


def _pay(emp, jadwal, tipe, dari, alasan=None):
    isi = {
        "doctype": "HRIS Employee Pay",
        "employee": emp.name,
        "pay_type": tipe,
        "amount": 100000 if tipe == "Harian" else 3000000,
        "payroll_schedule": jadwal,
        "effective_from": dari,
    }
    if alasan:
        isi["change_reason"] = alasan
    return frappe.get_doc(isi).insert(ignore_permissions=True)


def _sebagai(email, fungsi):
    frappe.set_user(email)
    try:
        return fungsi()
    finally:
        frappe.set_user("Administrator")


def _jalankan(perusahaan):
    from hris.hris_attendance.services.audit_trail import get_audit_trail

    jadwal = frappe.get_doc(
        {
            "doctype": "HRIS Payroll Schedule",
            "schedule_name": "ZZ Uji Jadwal Audit",
            "company": perusahaan,
            "schedule_type": "Bulanan",
            "cut_off_day": 26,
            "is_active": 1,
        }
    ).insert(ignore_permissions=True)
    for email, peran in USERS.values():
        frappe.get_doc(
            {
                "doctype": "User",
                "email": email,
                "first_name": "ZZ Uji",
                "enabled": 1,
                "send_welcome_email": 0,
                "user_type": "System User",
                "roles": [{"role": r} for r in peran],
            }
        ).insert(ignore_permissions=True)

    h = _karyawan(perusahaan, "ZZ Audit Harian")
    b = _karyawan(perusahaan, "ZZ Audit Bulanan")
    h1 = _pay(h, jadwal.name, "Harian", "2026-01-01")
    _pay(h, jadwal.name, "Harian", "2026-07-01", "Kenaikan")
    b1 = _pay(b, jadwal.name, "Bulanan", "2026-01-01")
    _pay(b, jadwal.name, "Bulanan", "2026-07-01", "Kenaikan")

    jumlah_versi = frappe.db.count("Version", {"ref_doctype": "HRIS Employee Pay", "docname": ["in", [h1.name, b1.name]]})
    _info("jumlah Version untuk dua baris yang ditutup", str(jumlah_versi))

    u_admin, u_manager, u_direksi = (USERS[k][0] for k in ("admin", "manager", "direksi"))

    try:
        hasil_h = _sebagai(u_admin, lambda: get_audit_trail("HRIS Employee Pay", h1.name))
    except Exception as ex:  # noqa: BLE001
        _catat("T21a Payroll Admin boleh membuka Audit Trail baris Harian", False, repr(ex)[:150])
    else:
        _catat("T21a Payroll Admin boleh membuka Audit Trail baris Harian", True, "tipe hasil: " + type(hasil_h).__name__)

    try:
        _sebagai(u_admin, lambda: get_audit_trail("HRIS Employee Pay", b1.name))
    except frappe.PermissionError:
        _catat("T21b Payroll Admin DITOLAK membuka Audit Trail baris Bulanan", True)
    except Exception as ex:  # noqa: BLE001
        _catat("T21b Payroll Admin DITOLAK membuka Audit Trail baris Bulanan", False, "galat lain: " + repr(ex)[:150])
    else:
        _catat("T21b Payroll Admin DITOLAK membuka Audit Trail baris Bulanan", False, "TIDAK ditolak, data bocor")

    for kunci, email in (("Payroll Manager", u_manager), ("Direksi", u_direksi)):
        try:
            _sebagai(email, lambda: get_audit_trail("HRIS Employee Pay", b1.name))
        except Exception as ex:  # noqa: BLE001
            _catat("T21 %s boleh membuka Audit Trail baris Bulanan" % kunci, False, repr(ex)[:150])
        else:
            _catat("T21 %s boleh membuka Audit Trail baris Bulanan" % kunci, True)

    # Version adalah DocType Frappe: pastikan Payroll Admin tidak bisa membaca riwayat baris Bulanan langsung.
    try:
        baris = _sebagai(
            u_admin,
            lambda: frappe.get_list(
                "Version",
                filters={"ref_doctype": "HRIS Employee Pay", "docname": b1.name},
                pluck="name",
            ),
        )
    except frappe.PermissionError:
        _catat("T22 Payroll Admin tidak bisa membaca Version baris Bulanan (ditolak)", True)
    except Exception as ex:  # noqa: BLE001
        _catat("T22 Payroll Admin tidak bisa membaca Version baris Bulanan", False, "galat lain: " + repr(ex)[:150])
    else:
        _catat("T22 Payroll Admin tidak bisa membaca Version baris Bulanan (kosong)", not baris, str(baris))


def periksa():
    hasil.clear()
    perusahaan = frappe.get_all("Company", pluck="name", limit=1)[0]
    try:
        _jalankan(perusahaan)
    except Exception as ex:  # noqa: BLE001
        import traceback

        traceback.print_exc()
        _catat("uji berjalan tanpa galat tak terduga", False, repr(ex)[:200])
    finally:
        frappe.set_user("Administrator")
        frappe.db.rollback()
        for email, _peran in USERS.values():
            frappe.clear_cache(user=email)
    print("---")
    ringkas = "OK %d | GAGAL %d" % (hasil.count(True), hasil.count(False))
    print(ringkas)
    return ringkas
