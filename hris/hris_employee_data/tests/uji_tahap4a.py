"""Uji tahap 4a (K-136): Link department di 4 DocType menunjuk HRIS Department.
Jalankan dari folder sites setelah migrate: ../env/bin/python <path ini>."""

import sys

import frappe

SITE = "hris-uji.local"
DOCTYPE = ("HRIS Employee", "HRIS Payroll Slip", "HRIS Working Hour", "HRIS Employee Group")

frappe.init(site=SITE, sites_path=".")
frappe.connect()
hasil = []


def cek(nama, kondisi, rinci=""):
    hasil.append(bool(kondisi))
    print(("OK      " if kondisi else "GAGAL   ") + nama + ("" if kondisi or not rinci else "  " + str(rinci)))


try:
    for dt in DOCTYPE:
        df = frappe.get_meta(dt).get_field("department")
        cek("L %s: department -> HRIS Department" % dt, bool(df) and df.options == "HRIS Department", df and df.options)
        if frappe.db.table_exists(dt):
            hilang = frappe.db.sql(
                "select count(*) from `tab%s` t where ifnull(department,'')<>'' "
                "and not exists (select 1 from `tabHRIS Department` h where h.name=t.department)" % dt
            )[0][0]
            cek("D %s: semua nilai department ada di HRIS Department" % dt, hilang == 0, hilang)
    cek("E erpnext_department tetap menunjuk Department ERPNext",
        frappe.get_meta("HRIS Department").get_field("erpnext_department").options == "Department")

    baca_dept = set(frappe.get_all("DocPerm", filters={"parent": "HRIS Department", "read": 1, "permlevel": 0}, pluck="role"))
    for dt in DOCTYPE:
        peran = set(frappe.get_all("DocPerm", filters={"parent": dt, "read": 1, "permlevel": 0}, pluck="role"))
        kurang = sorted(peran - baca_dept)
        print("INFO    %s: peran bisa baca tetapi tidak bisa baca HRIS Department: %s" % (dt, kurang or "-"))
finally:
    frappe.destroy()

print("HASIL OK %d GAGAL %d" % (sum(hasil), len(hasil) - sum(hasil)))
sys.exit(0 if all(hasil) else 1)
