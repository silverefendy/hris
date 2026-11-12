"""K-138 tahap 3: slip memakai rule_department per hari. Hanya hris-uji.local; di-rollback."""
import os

import frappe
from frappe.utils import flt

os.chdir("/home/it/erp/sites")
frappe.init(site="hris-uji.local", sites_path=".")
frappe.connect()
frappe.set_user("Administrator")

RULE = "HRIS Department Rule"
ok = 0
gagal = 0


def cek(kode, kondisi, ket=""):
    global ok, gagal
    if kondisi:
        ok += 1
    else:
        gagal += 1
    print(("OK      " if kondisi else "GAGAL   ") + kode + " " + str(ket))


def lembur_slip(he, period):
    nama = frappe.db.get_value("HRIS Payroll Slip", {"unique_key": period + "|" + he}, "name")
    doc = frappe.get_doc("HRIS Payroll Slip", nama)
    oto = {r.component: flt(r.amount) for r in doc.components if r.source == "Otomatis"}
    return doc, oto.get("Lembur"), flt(doc.hourly_rate)


def utama():
    from hris.hris_payroll.services import payroll_slip as ps
    from hris.hris_payroll.services.payroll_schedule import get_period_for_date

    semua = frappe.get_all(RULE, fields=["department", "overtime_multiplier"])
    if not (len(semua) == 1 and semua[0].department == ps.DEPT_AKAR):
        print("BERHENTI: uji butuh tepat 1 aturan akar. Ada:", semua)
        return
    company = frappe.db.get_value("Company", {}, "name")
    sch = frappe.get_doc({
        "doctype": "HRIS Payroll Schedule", "schedule_name": "ZZ Uji P9 Slip", "company": company,
        "schedule_type": "Bulanan", "is_active": 1, "pay_date_offset_days": 3,
        "sunday_rule": "Maju ke Senin", "cut_off_day": 26,
    }).insert(ignore_permissions=True)
    r = get_period_for_date(sch.name, "2026-10-17")
    awal, akhir = str(r["start"]), str(r["end"])
    kand = frappe.db.sql(
        """
        select he.name as he, he.erpnext_employee as emp, he.department as dept
        from `tabHRIS Employee` he
        inner join `tabHRIS Working Hour` wh on wh.employee = he.erpnext_employee
        where wh.work_date between %(a)s and %(b)s and he.company = %(co)s
          and he.department is not null and he.department not in ('', 'All Departments')
          and he.date_of_joining <= %(a)s and (he.resign_date is null or he.resign_date > %(b)s)
          and wh.status in ('Hadir', 'Tidak Lengkap', 'Tidak Hadir') and ifnull(wh.scheduled_hours, 0) > 0
          and not exists (select 1 from `tabHRIS Employee Pay` ep where ep.employee = he.name)
        group by he.name, he.erpnext_employee, he.department
        having sum(wh.status = 'Hadir') >= 2
        order by count(*) desc limit 1
        """,
        {"a": awal, "b": akhir, "co": company}, as_dict=True)
    cek("D0 kandidat (>=2 hari Hadir)", bool(kand))
    if not kand:
        return
    he, emp, dept = kand[0].he, kand[0].emp, kand[0].dept
    lain = frappe.db.get_value("HRIS Department", {"name": ["not in", [dept, ps.DEPT_AKAR]]}, "name")
    cek("D0 Department lain", bool(lain), lain)
    if not lain:
        return
    baris = frappe.get_all("HRIS Working Hour", filters={"employee": emp, "work_date": ["between", [awal, akhir]]},
                           fields=["name", "status"], order_by="work_date")
    for b in baris:
        frappe.db.set_value("HRIS Working Hour", b.name, {"overtime_minutes": 0, "rule_department": None}, update_modified=False)
    hadir = [b for b in baris if b.status == "Hadir"]
    for b in hadir[:2]:
        frappe.db.set_value("HRIS Working Hour", b.name, "overtime_minutes", 120, update_modified=False)
    frappe.get_doc({"doctype": RULE, "department": dept, "effective_from": "2026-01-01",
                    "is_active": 1, "overtime_multiplier": 1.75}).insert(ignore_permissions=True)
    frappe.get_doc({"doctype": RULE, "department": lain, "effective_from": "2026-01-01",
                    "is_active": 1, "overtime_multiplier": 2.0}).insert(ignore_permissions=True)
    frappe.get_doc({"doctype": "HRIS Employee Pay", "employee": he, "pay_type": "Bulanan", "amount": 3000000,
                    "payroll_schedule": sch.name, "effective_from": "2026-01-01"}).insert(ignore_permissions=True)
    period = frappe.get_doc({"doctype": "HRIS Payroll Period", "payroll_schedule": sch.name,
                             "reference_date": "2026-10-17"}).insert(ignore_permissions=True)

    # S2: semua kosong
    ps.buat_slip(period.name, "Karyawan", employee=he)
    doc, lembur, tarif = lembur_slip(he, period.name)
    harap2 = tarif * 4 * 1.75
    cek("S2 rule_department kosong", lembur is not None and abs(lembur - harap2) <= 1, "lembur=%s harapan=%.2f" % (lembur, harap2))

    # S3: sama dengan Department karyawan
    for b in hadir[:2]:
        frappe.db.set_value("HRIS Working Hour", b.name, "rule_department", dept, update_modified=False)
    ps.buat_slip(period.name, "Karyawan", employee=he)
    doc, lembur, tarif = lembur_slip(he, period.name)
    cek("S3 rule_department = Department karyawan", lembur is not None and abs(lembur - harap2) <= 1, "lembur=%s" % lembur)

    # S1: satu hari dipinjam
    frappe.db.set_value("HRIS Working Hour", hadir[1].name, "rule_department", lain, update_modified=False)
    ps.buat_slip(period.name, "Karyawan", employee=he)
    doc, lembur, tarif = lembur_slip(he, period.name)
    harap1 = tarif * 2 * 1.75 + tarif * 2 * 2.0
    cek("S1 satu hari dipinjam", lembur is not None and abs(lembur - harap1) <= 1, "lembur=%s harapan=%.2f" % (lembur, harap1))
    catatan = " ".join(str(getattr(doc, f, "") or "") for f in ("notes", "catatan", "remarks"))
    print("INFO    catatan slip:", catatan[:200])


try:
    utama()
finally:
    frappe.db.rollback()
cek("Z1 aturan kembali 1", frappe.db.count(RULE) == 1, frappe.db.count(RULE))
print("HASIL: OK %d, GAGAL %d" % (ok, gagal))
frappe.destroy()
raise SystemExit(1 if gagal else 0)
