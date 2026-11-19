"""Penyedia data sintetis untuk mencoba dialog Hapus Massal lewat browser. Bukan uji regresi.
  siapkan  : bench --site hris-uji.local execute hris.hris_payroll.tests.siapkan_data_uji_hapus_ui.siapkan
  bersihkan: bench --site hris-uji.local execute hris.hris_payroll.tests.siapkan_data_uji_hapus_ui.bersihkan
Data: 1200 dokumen, karyawan UJIWHD-EMP, tanggal 2099-04-01 s/d 2099-04-28, nama UJIWHD-U*.
"""
import frappe
from frappe.utils import add_days, now_datetime

DT = "HRIS Working Hour"
KOLOM = [
    "name", "creation", "modified", "modified_by", "owner", "docstatus", "idx",
    "employee", "employee_name", "work_date", "unique_key", "status",
]


def bersihkan():
    frappe.db.delete(DT, {"name": ["like", "UJIWHD-U%"]})
    frappe.db.commit()
    print("Sisa data uji UI:", frappe.db.count(DT, {"name": ["like", "UJIWHD-U%"]}))


def siapkan():
    frappe.db.delete(DT, {"name": ["like", "UJIWHD-U%"]})
    now = now_datetime()
    nilai = []
    for i in range(1200):
        nm = "UJIWHD-U%05d" % (i + 1)
        nilai.append((nm, now, now, "Administrator", "Administrator", 0, 0,
                      "UJIWHD-EMP", "Uji WHD UI", str(add_days("2099-04-01", i % 28)), nm, "Tidak Hadir"))
    frappe.db.bulk_insert(DT, KOLOM, nilai)
    frappe.db.commit()
    print("Data uji UI dibuat:", frappe.db.count(DT, {"name": ["like", "UJIWHD-U%"]}), "dokumen (2099-04-01 s/d 2099-04-28)")
