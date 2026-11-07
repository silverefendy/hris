"""Uji K-127 lanjutan: penjaga jadwal gaji (T18 sampai T20). Semua di-rollback.

Jalankan:
bench --site hris-uji.local execute hris.hris_payroll.tests.uji_employee_pay_jadwal.periksa
"""

import frappe
from frappe.utils import strip_html

hasil = []


def _catat(nama, lulus, info=""):
    hasil.append(bool(lulus))
    print(("OK     " if lulus else "GAGAL  ") + nama + ((" | " + info) if info else ""))


def _info(nama, info=""):
    print("INFO   " + nama + ((" | " + info) if info else ""))


def _jadwal(perusahaan, nama):
    return frappe.get_doc(
        {
            "doctype": "HRIS Payroll Schedule",
            "schedule_name": nama,
            "company": perusahaan,
            "schedule_type": "Bulanan",
            "cut_off_day": 26,
            "is_active": 1,
        }
    ).insert(ignore_permissions=True)


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


def _nonaktifkan(nama_jadwal):
    doc = frappe.get_doc("HRIS Payroll Schedule", nama_jadwal)
    doc.is_active = 0
    doc.save(ignore_permissions=True)


def _jalankan(perusahaan):
    j1 = _jadwal(perusahaan, "ZZ Uji Jadwal 127a")
    j2 = _jadwal(perusahaan, "ZZ Uji Jadwal 127b")
    e = _karyawan(perusahaan, "ZZ Uji K127 Jadwal")
    frappe.get_doc(
        {
            "doctype": "HRIS Employee Pay",
            "employee": e.name,
            "pay_type": "Harian",
            "amount": 100000,
            "payroll_schedule": j1.name,
            "effective_from": "2026-01-01",
        }
    ).insert(ignore_permissions=True)

    try:
        _nonaktifkan(j1.name)
    except frappe.ValidationError as ex:
        pesan = strip_html(str(ex))
        _catat("T18a jadwal yang dipakai karyawan aktif tidak bisa dinonaktifkan", "masih dipakai" in pesan.lower(), pesan[:120])
    else:
        _catat("T18a jadwal yang dipakai karyawan aktif tidak bisa dinonaktifkan", False, "TIDAK ditolak")

    try:
        _nonaktifkan(j2.name)
    except Exception as ex:  # noqa: BLE001
        _catat("T18b jadwal tanpa pemakai boleh dinonaktifkan", False, strip_html(str(ex))[:120])
    else:
        _catat("T18b jadwal tanpa pemakai boleh dinonaktifkan", True)

    doc = frappe.get_doc("HRIS Payroll Schedule", j1.name)
    doc.cut_off_day = 27
    try:
        doc.save(ignore_permissions=True)
    except frappe.ValidationError as ex:
        pesan = strip_html(str(ex))
        _catat("T19 parameter periode jadwal yang dipakai terkunci", "sudah dipakai" in pesan.lower(), pesan[:120])
    else:
        _catat("T19 parameter periode jadwal yang dipakai terkunci", False, "TIDAK ditolak")

    e.reload()
    e.status = "Resign"
    e.resign_date = "2026-11-01"
    e.flags.skip_sync = True
    try:
        e.save(ignore_permissions=True)
    except Exception as ex:  # noqa: BLE001
        _info("T20 dilewati: karyawan tidak bisa di-resign-kan di uji", strip_html(str(ex))[:120])
        return
    try:
        _nonaktifkan(j1.name)
    except Exception as ex:  # noqa: BLE001
        _catat("T20 setelah karyawan Resign, jadwal boleh dinonaktifkan", False, strip_html(str(ex))[:120])
    else:
        _catat("T20 setelah karyawan Resign, jadwal boleh dinonaktifkan", True)


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
    print("---")
    ringkas = "OK %d | GAGAL %d" % (hasil.count(True), hasil.count(False))
    print(ringkas)
    return ringkas
