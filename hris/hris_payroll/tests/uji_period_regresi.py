"""Regresi K-128: perilaku Working Hour lama tetap utuh tanpa periode Final. Di-rollback.

Jalankan:
bench --site hris-uji.local execute hris.hris_payroll.tests.uji_period_regresi.periksa
"""

import frappe
from frappe.utils import strip_html

hasil = []


def _catat(nama, lulus, info=""):
    hasil.append(bool(lulus))
    print(("OK     " if lulus else "GAGAL  ") + nama + ((" | " + info) if info else ""))


def _jalankan(perusahaan):
    from hris.hris_attendance.services import working_hour_batch as B
    from hris.hris_attendance.services.working_hour import calculate_working_hour

    baris = frappe.db.sql(
        """
        select erpnext_employee from `tabHRIS Employee`
        where ifnull(erpnext_employee, '') != '' and status = 'Aktif' and company = %s
        order by name limit 1
        """,
        perusahaan,
    )
    if not baris:
        _catat("tersedia satu karyawan terhubung", False)
        return
    erp = baris[0][0]

    try:
        hitung = calculate_working_hour(erp, "2026-03-10")
        _catat("R1 hitung ulang tanpa periode Final tetap berhasil", isinstance(hitung, dict) and "status" in hitung, str(hitung))
    except Exception as ex:  # noqa: BLE001
        _catat("R1 hitung ulang tanpa periode Final tetap berhasil", False, strip_html(str(ex))[:160])

    sudah = frappe.get_doc(
        {"doctype": "HRIS Working Hour", "employee": erp, "work_date": "2026-03-11",
         "status": "Hadir", "review_status": "Sudah Ditinjau"}
    )
    sudah.flags.from_calculation = True
    sudah.insert(ignore_permissions=True, ignore_mandatory=True)

    terlindung = B._protected([{"name": erp}], "2026-03-10", "2026-03-12")
    _catat("R2 baris Sudah Ditinjau tetap dilindungi batch", (erp, "2026-03-11") in terlindung, str(sorted(terlindung)))
    _catat("R3 baris yang tidak ditinjau tidak ikut dilindungi", (erp, "2026-03-10") not in terlindung)

    sudah.reload()
    sudah.review_note = "uji regresi"
    try:
        sudah.save(ignore_permissions=True)
        _catat("R4 edit manual tanpa periode Final tetap lolos", True)
    except Exception as ex:  # noqa: BLE001
        _catat("R4 edit manual tanpa periode Final tetap lolos", False, strip_html(str(ex))[:160])


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
