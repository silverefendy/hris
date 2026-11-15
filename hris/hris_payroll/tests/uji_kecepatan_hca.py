"""K-140 C: ukur kecepatan Payroll Summary dan perhitungan tunjangan dengan dan tanpa HCA.

Hanya mengukur (tanpa lulus atau gagal). Semua data uji di-rollback.
Jalankan:
bench --site hris-uji.local execute hris.hris_payroll.tests.uji_kecepatan_hca.jalankan
"""
import time
from datetime import date

import frappe

from hris.hris_payroll.services import payroll_summary as ps
from hris.hris_payroll.services.komponen_slip import hitung_tunjangan_karyawan

HEC = "HRIS Employee Component"
HCA = "HRIS Component Assignment"
KATALOG = "HRIS Pay Component"
TGL = "2026-11-14"
AWAL, AKHIR = "2026-11-01", "2026-11-30"
HADIR = [date(2026, 11, d) for d in range(1, 15)]
N_SLIP, MAKS_DEPT, MAKS_GRUP, MAKS_HEC = 100, 40, 10, 60
TOTAL_KARYAWAN = 1078


def _waktu(fn):
    t = time.perf_counter()
    h = fn()
    return h, time.perf_counter() - t


def _ukur(label, karyawan, kode):
    r1, t1 = _waktu(lambda: ps.ambil_data(mode="Per Tanggal", tanggal=TGL, semua=1))
    n1 = r1["jumlah_baris"]
    print("UKUR %-10s Payroll Summary (punya gaji)    : %6.2f detik, %5d baris, %6.1f ms/baris" % (label, t1, n1, 1000 * t1 / max(n1, 1)))
    r2, t2 = _waktu(lambda: ps.ambil_data(mode="Per Tanggal", tanggal=TGL, semua=1, tampilkan_tanpa_gaji=1))
    n2 = r2["jumlah_baris"]
    print("UKUR %-10s Payroll Summary (termasuk tanpa): %6.2f detik, %5d baris, %6.1f ms/baris" % (label, t2, n2, 1000 * t2 / max(n2, 1)))

    def slip():
        for emp, pay_type in karyawan:
            for k in kode:
                hitung_tunjangan_karyawan(emp, k, pay_type, AWAL, AKHIR, HADIR)

    _x, t3 = _waktu(slip)
    per_emp = t3 / max(len(karyawan), 1)
    print("UKUR %-10s Slip: %d karyawan x %d komponen   : %6.2f detik, %6.1f ms/karyawan, proyeksi %d karyawan = %.1f detik"
          % (label, len(karyawan), len(kode), t3, 1000 * per_emp, TOTAL_KARYAWAN, per_emp * TOTAL_KARYAWAN))


def jalankan():
    karyawan = frappe.db.sql(
        "select e.name, p.pay_type from `tabHRIS Employee` e "
        "join `tabHRIS Employee Pay` p on p.employee = e.name and p.effective_to is null "
        "where e.status = 'Aktif' limit %d" % N_SLIP
    )
    if not karyawan:
        print("SKIP: tidak ada karyawan aktif ber-gaji")
        return
    awal_hca, awal_hec = frappe.db.count(HCA), frappe.db.count(HEC)
    try:
        kode = frappe.get_all(KATALOG, pluck="name", order_by="name")
        for k in kode:
            frappe.db.set_value(KATALOG, k, "is_active", 1)
        for k in ("TJ_MAKAN", "TJ_TRANSPORT"):
            if k in kode:
                frappe.db.set_value(KATALOG, k, "payment_basis", "Per Hari Hadir")
        print("INFO   karyawan diukur untuk slip: %d, komponen aktif sementara: %s" % (len(karyawan), ", ".join(kode)))
        print("INFO   karyawan aktif di Payroll Summary diukur dari semua karyawan ber-gaji pada %s" % TGL)

        _ukur("TANPA HCA", karyawan, kode)

        n_hca = n_hec = 0
        dept = frappe.db.sql(
            "select distinct e.department from `tabHRIS Employee` e join `tabHRIS Department` d on d.name = e.department "
            "where e.status = 'Aktif' and d.company is not null and d.is_group = 0 limit %d" % MAKS_DEPT
        )
        grup = frappe.db.sql(
            "select name from `tabHRIS Employee Group` where company is not null and is_active = 1 limit %d" % MAKS_GRUP
        )

        def buat(tabel, **kw):
            d = {"doctype": tabel, "status": "Berlaku", "amount": 1000, "date_from": "2026-01-01", "date_to": "2026-12-31",
                 "is_active": 1, "reason": "uji kecepatan K-140"}
            d.update(kw)
            frappe.get_doc(d).insert(ignore_permissions=True)

        for (dep,) in dept:
            for k in ("TJ_MAKAN", "TJ_TRANSPORT"):
                if k in kode:
                    try:
                        buat(HCA, scope_type="Department", department=dep, component=k, include_children=1)
                        n_hca += 1
                    except frappe.ValidationError:
                        frappe.clear_messages()
        for (g,) in grup:
            if "TJ_MAKAN" in kode:
                try:
                    buat(HCA, scope_type="Grup", employee_group=g, component="TJ_MAKAN")
                    n_hca += 1
                except frappe.ValidationError:
                    frappe.clear_messages()
        for emp, _p in karyawan[:MAKS_HEC]:
            try:
                buat(HEC, employee=emp, component="TJ_MAKAN", status="Tidak Berlaku", amount=0, date_from="2026-11-05", date_to="2026-11-07")
                n_hec += 1
            except (frappe.ValidationError, frappe.PermissionError):
                frappe.clear_messages()
        print("INFO   data sintetis: %d HCA dan %d HEC (di-rollback)" % (n_hca, n_hec))

        _ukur("DENGAN HCA", karyawan, kode)
    finally:
        frappe.db.rollback()
    ok = frappe.db.count(HCA) == awal_hca and frappe.db.count(HEC) == awal_hec
    print("SELESAI rollback %s (HCA %d/%d, HEC %d/%d)" % ("OK" if ok else "GAGAL", frappe.db.count(HCA), awal_hca, frappe.db.count(HEC), awal_hec))
