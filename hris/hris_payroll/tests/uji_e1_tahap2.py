import frappe
from hris.hris_payroll.services.department_komponen import pilih_komponen, resolve_komponen


def jalankan():
    ok = g = 0
    def cek(n, k, ket=""):
        nonlocal ok, g
        if k: ok += 1
        else: g += 1
        print(("OK      " if k else "GAGAL   ") + n, ket)
    rantai = ["C", "B", "A"]
    ar = [{"name": "R-A", "department": "A", "effective_from": "2026-01-01", "creation": ""},
          {"name": "R-C", "department": "C", "effective_from": "2026-01-01", "creation": ""}]
    cek("L1 tanpa baris: tidak berlaku", pilih_komponen(rantai, ar, [], "2026-10-01")["berlaku"] is False)
    cek("L2 mewarisi induk", pilih_komponen(rantai, ar, [{"parent": "R-A", "component": "X", "status": "Berlaku", "amount": 15000}], "2026-10-01")["nilai"] == 15000)
    b = [{"parent": "R-A", "component": "X", "status": "Berlaku", "amount": 15000}, {"parent": "R-C", "component": "X", "status": "Tidak Berlaku", "amount": 0}]
    cek("L3 Tidak Berlaku menimpa induk", pilih_komponen(rantai, ar, b, "2026-10-01")["nilai"] == 0)
    b = [{"parent": "R-A", "component": "X", "status": "Berlaku", "amount": 15000}, {"parent": "R-C", "component": "X", "status": "Ikut Induk", "amount": 0}]
    cek("L4 Ikut Induk lanjut ke atas", pilih_komponen(rantai, ar, b, "2026-10-01")["nilai"] == 15000)
    cek("L5 sebelum tanggal berlaku: tidak berlaku", pilih_komponen(rantai, ar, b, "2025-12-31")["berlaku"] is False)
    frappe.db.savepoint("e1t2")
    try:
        dept = frappe.db.get_value("HRIS Department", {"name": ["!=", "All Departments"]}, "name")
        d = frappe.get_doc({"doctype": "HRIS Department Rule", "department": dept, "effective_from": "2098-01-01", "is_active": 1,
                            "components": [{"component": "TJ_MAKAN", "status": "Berlaku", "amount": 15000}]}).insert()
        cek("D1 aturan hanya komponen lolos", bool(d.name))
        cek("D2 resolve_komponen membaca nilai", resolve_komponen(dept, "2098-06-01", "TJ_MAKAN")["nilai"] == 15000)
        try:
            frappe.get_doc({"doctype": "HRIS Department Rule", "department": dept, "effective_from": "2098-02-01", "is_active": 1,
                            "components": [{"component": "TJ_MAKAN", "status": "Berlaku", "amount": 0}]}).insert()
            cek("D3 Berlaku tanpa nilai ditolak", False)
        except frappe.ValidationError:
            cek("D3 Berlaku tanpa nilai ditolak", True)
        try:
            frappe.get_doc({"doctype": "HRIS Department Rule", "department": dept, "effective_from": "2098-03-01", "is_active": 1}).insert()
            cek("D4 aturan kosong ditolak", False)
        except frappe.ValidationError:
            cek("D4 aturan kosong ditolak", True)
    finally:
        frappe.db.rollback(save_point="e1t2")
    print("HASIL: OK %d, GAGAL %d" % (ok, g))
