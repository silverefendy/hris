"""Cetak catatan dan dasar potongan 6a. Tanpa database.
  bench --site hris-uji.local execute hris.hris_payroll.tests.uji_catatan_6a.jalankan
"""
import frappe

from hris.hris_payroll.services.payroll_slip import hitung_komponen


def _b(status, tgl, kelas="", potong=0):
    return {
        "status": status, "scheduled_hours": 8, "late_deduction_hours": 0,
        "early_leave_deduction_hours": 0, "overtime_minutes": 0,
        "absence_deducted": potong, "absence_class": kelas, "work_date": tgl,
    }


def jalankan():
    asli = frappe.conf.get("hris_absen_belum_klas_dipotong")
    frappe.conf["hris_absen_belum_klas_dipotong"] = 1
    try:
        baris = [_b("Hadir", "2026-10-0%d" % i) for i in range(1, 6)]
        baris += [
            _b("Tidak Hadir", "2026-10-10"),
            _b("Tidak Hadir", "2026-10-11"),
            _b("Tidak Hadir", "2026-10-12", "Mangkir", 1),
        ]
        r = hitung_komponen("Bulanan", 5000000, baris)
        for k in r["komponen"]:
            if k["nama"] == "Potongan Absen":
                print("Dasar  :", k["dasar"])
                print("Jumlah :", k["jumlah"])
        for c in r["catatan"]:
            print("Catatan:", c)
    finally:
        if asli is None:
            frappe.conf.pop("hris_absen_belum_klas_dipotong", None)
        else:
            frappe.conf["hris_absen_belum_klas_dipotong"] = asli
