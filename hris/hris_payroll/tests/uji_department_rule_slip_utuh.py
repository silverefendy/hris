"""Uji K-136 tahap 4b pada slip utuh. Hanya hris-uji.local; semua data uji di-rollback."""

import os

import frappe
from frappe.utils import flt

SITE = "hris-uji.local"
os.chdir("/home/it/erp/sites")
frappe.init(site=SITE, sites_path=".")
frappe.connect()
frappe.set_user("Administrator")

RULE = "HRIS Department Rule"
ok = 0
gagal = 0


def cek(kode, kondisi, ket=""):
    global ok, gagal
    if kondisi:
        ok += 1
        print("OK      {0} {1}".format(kode, ket))
    else:
        gagal += 1
        print("GAGAL   {0} {1}".format(kode, ket))


def baca_slip(he, period):
    nama = frappe.db.get_value("HRIS Payroll Slip", {"unique_key": period + "|" + he}, "name")
    if not nama:
        return None, None
    doc = frappe.get_doc("HRIS Payroll Slip", nama)
    oto = {r.component: flt(r.amount) for r in doc.components if r.source == "Otomatis"}
    return doc, oto.get("Lembur")


def periksa_slip(kode, he, period, pengali):
    doc, lembur = baca_slip(he, period)
    if not doc:
        cek(kode, False, "slip tidak ditemukan")
        return
    cek(kode + " pengali", abs(flt(doc.overtime_multiplier) - pengali) < 0.0001, "slip={0} harapan={1}".format(doc.overtime_multiplier, pengali))
    harapan = flt(doc.hourly_rate) * 2 * pengali
    cek(kode + " Lembur", lembur is not None and abs(lembur - harapan) <= 1, "lembur={0} harapan={1:.2f}".format(lembur, harapan))


def utama():
    from hris.hris_payroll.services import payroll_slip as ps
    from hris.hris_payroll.services.payroll_schedule import get_period_for_date

    semua = frappe.get_all(RULE, fields=["name", "department", "overtime_multiplier"])
    if not (len(semua) == 1 and semua[0].department == ps.DEPT_AKAR and flt(semua[0].overtime_multiplier) == 1.0):
        print("BERHENTI: uji butuh tepat 1 aturan (akar, 1.0). Ada:", semua)
        return
    cek("S0", True, "hanya aturan akar: " + semua[0].name)

    company = frappe.db.get_value("Company", {}, "name")
    sch = frappe.get_doc({
        "doctype": "HRIS Payroll Schedule", "schedule_name": "ZZ Uji Pengali", "company": company,
        "schedule_type": "Bulanan", "is_active": 1, "pay_date_offset_days": 3,
        "sunday_rule": "Maju ke Senin", "cut_off_day": 26,
    }).insert(ignore_permissions=True)
    rentang = get_period_for_date(sch.name, "2026-10-17")
    awal, akhir = str(rentang["start"]), str(rentang["end"])
    kand = frappe.db.sql(
        """
        select he.name as he, he.erpnext_employee as emp, he.department as dept, count(*) as n
        from `tabHRIS Employee` he
        inner join `tabHRIS Department` d on d.name = he.department
        inner join `tabHRIS Working Hour` wh on wh.employee = he.erpnext_employee
        where wh.work_date between %(a)s and %(b)s
          and he.company = %(co)s and he.department != 'All Departments'
          and he.date_of_joining <= %(a)s
          and (he.resign_date is null or he.resign_date > %(b)s)
          and wh.status in ('Hadir', 'Tidak Lengkap', 'Tidak Hadir')
          and ifnull(wh.scheduled_hours, 0) > 0
          and not exists (select 1 from `tabHRIS Employee Pay` ep where ep.employee = he.name)
        group by he.name, he.erpnext_employee, he.department
        having sum(wh.status = 'Hadir') > 0
        order by n desc limit 1
        """,
        {"a": awal, "b": akhir, "co": company},
        as_dict=True,
    )
    cek("D0", bool(kand), "kandidat dengan Department dan Working Hour, periode {0} s/d {1}".format(awal, akhir))
    if not kand:
        return
    he, emp, dept = kand[0].he, kand[0].emp, kand[0].dept
    print("INFO    karyawan {0}, Department {1}".format(he, dept))

    baris = frappe.get_all("HRIS Working Hour", filters={"employee": emp, "work_date": ["between", [awal, akhir]]}, fields=["name", "status"])
    for r in baris:
        frappe.db.set_value("HRIS Working Hour", r.name, "overtime_minutes", 0, update_modified=False)
    hadir = [r for r in baris if r.status == "Hadir"]
    frappe.db.set_value("HRIS Working Hour", hadir[0].name, "overtime_minutes", 120, update_modified=False)

    frappe.get_doc({
        "doctype": "HRIS Employee Pay", "employee": he, "pay_type": "Bulanan", "amount": 3000000,
        "payroll_schedule": sch.name, "effective_from": "2026-01-01",
    }).insert(ignore_permissions=True)
    period = frappe.get_doc({
        "doctype": "HRIS Payroll Period", "payroll_schedule": sch.name, "reference_date": "2026-10-17",
    }).insert(ignore_permissions=True)

    h = ps.buat_slip(period.name, "Karyawan", employee=he)
    cek("U1 slip dibuat", h.get("dibuat") == 1, str(h))
    if h.get("dibuat") != 1:
        return
    periksa_slip("U1", he, period.name, 1.0)

    frappe.get_doc({"doctype": RULE, "department": dept, "effective_from": "2099-01-01",
                    "is_active": 1, "overtime_multiplier": 3.0}).insert(ignore_permissions=True)
    h = ps.buat_slip(period.name, "Karyawan", employee=he)
    cek("U2 diperbarui", h.get("diperbarui") == 1, str(h))
    periksa_slip("U2", he, period.name, 1.0)

    aturan = frappe.get_doc({"doctype": RULE, "department": dept, "effective_from": "2026-01-01",
                             "is_active": 1, "overtime_multiplier": 1.75}).insert(ignore_permissions=True)
    h = ps.buat_slip(period.name, "Karyawan", employee=he)
    cek("U3 diperbarui", h.get("diperbarui") == 1, str(h))
    periksa_slip("U3", he, period.name, 1.75)

    aturan.reload()
    aturan.overtime_multiplier = 2.0
    aturan.save(ignore_permissions=True)
    h = ps.buat_slip(period.name, "Karyawan", employee=he)
    cek("U4 diperbarui", h.get("diperbarui") == 1, str(h))
    periksa_slip("U4", he, period.name, 2.0)


try:
    utama()
finally:
    frappe.db.rollback()

cek("Z1 aturan kembali 1", frappe.db.count(RULE) == 1, str(frappe.db.count(RULE)))
cek("Z1 jadwal uji tidak tersisa", not frappe.db.exists("HRIS Payroll Schedule", "ZZ Uji Pengali"))
print("HASIL: OK {0}, GAGAL {1}".format(ok, gagal))
frappe.destroy()
raise SystemExit(1 if gagal else 0)
