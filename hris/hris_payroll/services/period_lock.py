"""Penguncian data setelah HRIS Payroll Period berstatus Final (K-128).

Semua fungsi aman dipanggil di site yang belum punya tabel terkait: hasilnya "tidak terkunci".
"""

from datetime import timedelta

import frappe
from frappe.utils import getdate

PERIOD = "HRIS Payroll Period"
PAY = "HRIS Employee Pay"
EMP = "HRIS Employee"


def _siap():
    db = frappe.db
    return bool(db.table_exists(PERIOD) and db.table_exists(PAY) and db.table_exists(EMP))


def is_locked(employee, work_date):
    """True bila karyawan ERPNext ini punya baris gaji berlaku pada tanggal itu dan jadwalnya
    punya periode Final yang memuat tanggal tersebut."""
    if not employee or not work_date or not _siap():
        return False
    tanggal = getdate(work_date)
    baris = frappe.db.sql(
        """
        select pp.name
        from `tabHRIS Payroll Period` pp
        inner join `tabHRIS Employee Pay` ep on ep.payroll_schedule = pp.payroll_schedule
        inner join `tabHRIS Employee` he on he.name = ep.employee
        where pp.status = 'Final'
          and pp.period_start <= %(d)s and pp.period_end >= %(d)s
          and ep.effective_from <= %(d)s
          and (ep.effective_to is null or ep.effective_to >= %(d)s)
          and he.erpnext_employee = %(emp)s
        limit 1
        """,
        {"d": tanggal, "emp": employee},
    )
    return bool(baris)


def locked_pairs(employees, start, end):
    """Himpunan (employee, 'YYYY-MM-DD') yang terkunci dalam rentang start..end."""
    names = tuple(e for e in (employees or []) if e)
    if not names or not _siap():
        return set()
    awal, akhir = getdate(start), getdate(end)
    baris = frappe.db.sql(
        """
        select he.erpnext_employee as employee,
               pp.period_start as ps, pp.period_end as pe,
               ep.effective_from as ef, ep.effective_to as et
        from `tabHRIS Payroll Period` pp
        inner join `tabHRIS Employee Pay` ep on ep.payroll_schedule = pp.payroll_schedule
        inner join `tabHRIS Employee` he on he.name = ep.employee
        where pp.status = 'Final'
          and pp.period_start <= %(akhir)s and pp.period_end >= %(awal)s
          and ep.effective_from <= pp.period_end
          and (ep.effective_to is null or ep.effective_to >= pp.period_start)
          and he.erpnext_employee in %(emps)s
        """,
        {"awal": awal, "akhir": akhir, "emps": names},
        as_dict=True,
    )
    hasil = set()
    for r in baris:
        batas_pay = getdate(r.et) if r.et else getdate(r.pe)
        dari = max(awal, getdate(r.ps), getdate(r.ef))
        sampai = min(akhir, getdate(r.pe), batas_pay)
        hari = dari
        while hari <= sampai:
            hasil.add((r.employee, str(hari)))
            hari += timedelta(days=1)
    return hasil
