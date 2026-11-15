"""K-140 C2: ukur kecepatan Payroll Summary dan perhitungan tunjangan dengan dan tanpa HCA.

Hanya mengukur (tanpa lulus atau gagal). Baris gaji sintetis dan data uji di-rollback.
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
PAY = "HRIS Employee Pay"
EMP = "HRIS Employee"
TGL = "2026-11-14"
AWAL, AKHIR = "2026-11-01", "2026-11-30"
HADIR = [date(2026, 11, d) for d in range(1, 15)]
N_SLIP, MAKS_DEPT, MAKS_GRUP, MAKS_HEC = 300, 40, 10, 60


def _hitung(fn):
    """Menjalankan fn dan mengembalikan (hasil, detik, jumlah query)."""
    asli = frappe.db.sql
    n = [0]

    def bungkus(*a, **k):
        n[0] += 1
        return asli(*a, **k)

    frappe.db.sql = bungkus
    t = time.perf_counter()
    try:
        h = fn()
    finally:
        frappe.db.sql = asli
    return h, time.perf_counter() - t, n[0]


def _ukur(label, karyawan, kode):
    r1, t1, q1 = _hitung(lambda: ps.ambil_data(mode="Per Tanggal", tanggal=TGL, semua=1))
    n1 = max(r1["jumlah_baris"], 1)
    print("UKUR %-10s Payroll Summary: %6.2f detik, %5d baris, %6.1f ms/baris, %6d query (%5.1f/baris)"
          % (label, t1, r1["jumlah_baris"], 1000 * t1 / n1, q1, q1 / n1))

    def slip():
        for emp, pay_type in karyawan:
            for k in kode:
                hitung_tunjangan_karyawan(emp, k, pay_type, AWAL, AKHIR, HADIR)

    _x, t2, q2 = _hitung(slip)
    n2 = max(len(karyawan), 1)
    print("UKUR %-10s Slip %d karyawan x %d komponen: %6.2f detik, %6.1f ms/karyawan, %6.1f query/karyawan"
          % (label, len(karyawan), len(kode), t2, 1000 * t2 / n2, q2 / n2))
    return {"ps_ms": 1000 * t1 / n1, "ps_q": q1 / n1, "slip_ms": 1000 * t2 / n2, "slip_q": q2 / n2, "baris": r1["jumlah_baris"]}


def _sisipkan_gaji():
    """Gaji sintetis: salin baris gaji yang ada ke setiap karyawan aktif yang belum punya gaji pada TGL."""
    templat = {}
    for jenis in ("Bulanan", "Harian"):
        nama = frappe.db.sql("select name from `tabHRIS Employee Pay` where pay_type = %s and effective_to is null limit 1", (jenis,))
        if nama:
            templat[jenis] = nama[0][0]
    if not templat:
        return 0
    daftar = list(templat.values())
    tanpa = frappe.db.sql(
        "select name from `tabHRIS Employee` where status = 'Aktif' and name not in "
        "(select employee from `tabHRIS Employee Pay` where effective_from <= %s and (effective_to is null or effective_to >= %s))",
        (TGL, TGL),
    )
    n = 0
    for i, (emp,) in enumerate(tanpa):
        d = frappe.get_doc(PAY, daftar[i % len(daftar)])
        d.name = "UJI-KCP-%05d" % i
        d.employee = emp
        d.flags.name_set = True
        d.db_insert()
        n += 1
    return n


def jalankan():
    if not frappe.db.sql("select name from `tabHRIS Employee Pay` limit 1"):
        print("SKIP: tidak ada baris gaji sebagai templat")
        return
    awal = {t: frappe.db.count(t) for t in (HCA, HEC, PAY)}
    try:
        n_gaji = _sisipkan_gaji()
        karyawan = frappe.db.sql(
            "select e.name, p.pay_type from `tabHRIS Employee` e "
            "join `tabHRIS Employee Pay` p on p.employee = e.name and p.effective_to is null "
            "where e.status = 'Aktif' order by e.name limit %d" % N_SLIP
        )
        kode = frappe.get_all(KATALOG, pluck="name", order_by="name")
        for k in kode:
            frappe.db.set_value(KATALOG, k, "is_active", 1)
        for k in ("TJ_MAKAN", "TJ_TRANSPORT"):
            if k in kode:
                frappe.db.set_value(KATALOG, k, "payment_basis", "Per Hari Hadir")
        print("INFO   baris gaji sintetis: %d, sampel slip: %d karyawan, komponen aktif sementara: %d (%s)"
              % (n_gaji, len(karyawan), len(kode), ", ".join(kode)))

        a = _ukur("TANPA HCA", karyawan, kode)

        n_hca = n_hec = 0
        dept = frappe.db.sql(
            "select distinct e.department from `tabHRIS Employee` e join `tabHRIS Department` d on d.name = e.department "
            "where e.status = 'Aktif' and d.company is not null and d.is_group = 0 limit %d" % MAKS_DEPT
        )
        grup = frappe.db.sql("select name from `tabHRIS Employee Group` where company is not null and is_active = 1 limit %d" % MAKS_GRUP)

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
        print("INFO   data sintetis: %d HCA dan %d HEC" % (n_hca, n_hec))

        b = _ukur("DENGAN HCA", karyawan, kode)
        print("RINGKAS Payroll Summary: %.1f -> %.1f ms/baris (%+.1f), query/baris %.1f -> %.1f; proyeksi %d baris = %.1f -> %.1f detik"
              % (a["ps_ms"], b["ps_ms"], b["ps_ms"] - a["ps_ms"], a["ps_q"], b["ps_q"], b["baris"], a["ps_ms"] * b["baris"] / 1000, b["ps_ms"] * b["baris"] / 1000))
        print("RINGKAS Slip: %.1f -> %.1f ms/karyawan (%+.1f), query/karyawan %.1f -> %.1f; proyeksi 1078 karyawan = %.1f -> %.1f detik"
              % (a["slip_ms"], b["slip_ms"], b["slip_ms"] - a["slip_ms"], a["slip_q"], b["slip_q"], a["slip_ms"] * 1.078, b["slip_ms"] * 1.078))
    finally:
        frappe.db.rollback()
    ok = all(frappe.db.count(t) == awal[t] for t in awal)
    print("SELESAI rollback %s (%s)" % ("OK" if ok else "GAGAL", ", ".join("%s %d/%d" % (t.split()[-1], frappe.db.count(t), awal[t]) for t in awal)))
