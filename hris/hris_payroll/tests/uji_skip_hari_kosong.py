"""Uji skip hari kosong HRIS Working Hour. Tidak meninggalkan data (rollback).
  bench --site hris-uji.local execute hris.hris_payroll.tests.uji_skip_hari_kosong.jalankan
"""
import frappe
from frappe.utils import add_days, getdate

from hris.hris_attendance.services.working_hour import calculate_working_hour


def jalankan():
    print("Saklar hris_skip_hari_kosong =", frappe.conf.get("hris_skip_hari_kosong", 1))
    baris = frappe.db.sql(
        """select employee, max(work_date) as terakhir, count(*) as n
           from `tabHRIS Working Hour` group by employee order by n desc limit 1""",
        as_dict=True,
    )
    if not baris:
        print("Tidak ada data Working Hour untuk diuji.")
        return
    emp = baris[0]["employee"]
    awal = add_days(getdate(baris[0]["terakhir"]), 1)
    print("Karyawan:", emp, "| mulai:", awal)
    ringkas = {}
    try:
        for i in range(14):
            hari = add_days(awal, i)
            try:
                hasil = calculate_working_hour(emp, hari)
            except Exception as exc:
                print(hari, "ERROR:", str(exc)[:120])
                continue
            aksi = "dilewati" if hasil.get("skipped") else "dibuat"
            ringkas[(hasil["status"], aksi)] = ringkas.get((hasil["status"], aksi), 0) + 1
            rinci = ""
            if hasil.get("name"):
                d = frappe.db.get_value(
                    "HRIS Working Hour", hasil["name"],
                    ["punch_count", "needs_review", "review_reason", "schedule_source"], as_dict=True,
                )
                rinci = " | punch=%s review=%s sumber=%s alasan=%s" % (
                    d.punch_count, d.needs_review, d.schedule_source, (d.review_reason or "-")[:60])
            print(hari, hasil["status"], "->", aksi.upper(), rinci)
    finally:
        frappe.db.rollback()
    print("\nRingkasan:")
    for (status, aksi), n in sorted(ringkas.items()):
        print("  %-16s %-9s %d" % (status, aksi, n))
    print("\nSemua perubahan di-rollback; tidak ada dokumen tersisa.")
