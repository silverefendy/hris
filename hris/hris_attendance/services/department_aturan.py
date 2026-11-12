"""K-138 P9 tahap 2: Department aturan per hari untuk HRIS Working Hour.

Department dibaca dari HRIS Employee. Bila tabel HRIS Employee belum ada (site sebelum K-102)
atau karyawan belum punya barisnya, dipakai Department Employee ERPNext. Cabang itu boleh
dihapus setelah K-102 selesai di produksi.
"""

import frappe
from frappe import _
from frappe.utils import getdate

from hris.hris_attendance.services.department_tujuan import tentukan_department

WH = "HRIS Working Hour"
HE = "HRIS Employee"
SA = "HRIS Shift Assignment"
# Perubahan pada kolom ini (pada penugasan yang punya peminjaman) memicu hitung ulang.
KOLOM_PEMICU = (
    "employee", "from_date", "to_date", "is_active",
    "borrowed_for_group", "borrowed_for_department",
)


def _gabung(dept_erpnext, he, pinjam_dept, pinjam_grup_dept):
    """Logika murni. he = (department, rule_follow) atau None."""
    if he is None:
        dept_karyawan, ikut = dept_erpnext, "Department"
    else:
        dept_karyawan, ikut = he[0] or None, he[1] or "Department"
    dept, _sumber = tentukan_department(dept_karyawan, pinjam_dept, pinjam_grup_dept, ikut)
    return dept or None


def _data_he(employee):
    if not frappe.db.table_exists(HE):
        return None
    baris = frappe.db.get_value(HE, {"erpnext_employee": employee}, ["department", "rule_follow"])
    return tuple(baris) if baris else None


def tentukan_rule_department(employee, dept_erpnext, sched):
    pinjam_grup = sched.get("borrowed_for_group")
    grup_dept = frappe.db.get_value("HRIS Employee Group", pinjam_grup, "department") if pinjam_grup else None
    return _gabung(dept_erpnext, _data_he(employee), sched.get("borrowed_for_department"), grup_dept)


def _punya_pinjam(d):
    return bool(d is not None and (d.get("borrowed_for_group") or d.get("borrowed_for_department")))


def _tandai(name, dept_baru, dept_lama, alasan):
    """Hanya menandai perlu ditinjau; tidak mengubah hasil hitung."""
    teks = _("Department aturan seharusnya {0}, tersimpan {1} ({2}).").format(
        dept_baru or "-", dept_lama or "-", alasan
    )
    lama = frappe.db.get_value(WH, name, "review_reason")
    frappe.db.set_value(
        WH, name,
        {
            "needs_review": 1,
            "review_reason": "{0}; {1}".format(lama, teks) if lama else teks,
            "review_status": "Menunggu",
        },
        update_modified=False,
    )


def hitung_ulang_hari_terdampak(employee, dari, sampai):
    """Proses baris Working Hour yang sudah ada pada rentang. Mengembalikan ringkasan."""
    from hris.hris_attendance.services.shift_schedule import get_schedule_for_date
    from hris.hris_attendance.services.working_hour import calculate_working_hour
    from hris.hris_payroll.services.period_lock import is_locked

    hasil = {"sama": 0, "dihitung": 0, "ditandai": 0, "gagal": 0}
    if not (employee and dari and sampai):
        return hasil
    dept_erp = frappe.db.get_value("Employee", employee, "department")
    baris = frappe.get_all(
        WH,
        filters={"employee": employee, "work_date": ["between", [getdate(dari), getdate(sampai)]]},
        fields=["name", "work_date", "rule_department", "review_status", "adjustment_hours"],
        order_by="work_date",
    )
    for b in baris:
        try:
            baru = tentukan_rule_department(employee, dept_erp, get_schedule_for_date(employee, b.work_date))
            if b.rule_department and baru == b.rule_department:
                hasil["sama"] += 1
                continue
            if is_locked(employee, b.work_date):
                _tandai(b.name, baru, b.rule_department, _("periode gaji sudah Final"))
                hasil["ditandai"] += 1
            elif b.review_status == "Sudah Ditinjau" or (b.adjustment_hours or 0) != 0:
                _tandai(b.name, baru, b.rule_department, _("sudah ditinjau atau ada penyesuaian HRD"))
                hasil["ditandai"] += 1
            else:
                calculate_working_hour(employee, b.work_date)
                hasil["dihitung"] += 1
        except Exception:
            hasil["gagal"] += 1
            frappe.log_error(title="K-138 hitung ulang peminjaman: %s %s" % (employee, b.work_date))
    return hasil


def _rentang(doc):
    return (doc.get("employee"), doc.get("from_date"), doc.get("to_date"))


def setelah_simpan_penugasan(doc, method=None):
    lama = doc.get_doc_before_save()
    if not (_punya_pinjam(doc) or _punya_pinjam(lama)):
        return
    if lama is not None and all(str(doc.get(k)) == str(lama.get(k)) for k in KOLOM_PEMICU):
        return
    rentang = {_rentang(doc)}
    if lama is not None:
        rentang.add(_rentang(lama))
    for emp, dari, sampai in rentang:
        hitung_ulang_hari_terdampak(emp, dari, sampai)


def setelah_hapus_penugasan(doc, method=None):
    if _punya_pinjam(doc):
        hitung_ulang_hari_terdampak(*_rentang(doc))
