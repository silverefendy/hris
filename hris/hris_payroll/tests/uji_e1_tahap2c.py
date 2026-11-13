import frappe
from hris.hris_payroll.services.department_komponen import resolve_komponen_karyawan


def jalankan():
    ok = g = 0

    def cek(n, k, ket=""):
        nonlocal ok, g
        if k:
            ok += 1
        else:
            g += 1
        print(("OK      " if k else "GAGAL   ") + n, ket)

    frappe.db.savepoint("e1t2c")
    try:
        company = frappe.db.get_value("Company", {}, "name")
        dept = frappe.db.get_value("HRIS Department", {"name": ["!=", "All Departments"]}, "name")
        frappe.get_doc({"doctype": "HRIS Department Rule", "department": dept, "effective_from": "2098-01-01", "is_active": 1,
                        "components": [{"component": "TJ_MAKAN", "status": "Berlaku", "amount": 15000}]}).insert()
        grp = frappe.get_doc({"doctype": "HRIS Employee Group", "group_name": "ZZ Uji E1 2c", "company": company,
                              "schedule_type": "Jadwal Mingguan", "is_active": 1}).insert()
        T = "2098-06-01"
        cek("G1 grup tanpa baris: ikut Department", resolve_komponen_karyawan(dept, grp.name, "Grup", T, "TJ_MAKAN")["nilai"] == 15000)
        grp.reload()
        grp.append("components", {"component": "TJ_MAKAN", "status": "Berlaku", "amount": 20000})
        grp.save()
        cek("G2 rule_follow Grup: Group menimpa", resolve_komponen_karyawan(dept, grp.name, "Grup", T, "TJ_MAKAN")["nilai"] == 20000)
        cek("G3 rule_follow Department: Group diabaikan", resolve_komponen_karyawan(dept, grp.name, "Department", T, "TJ_MAKAN")["nilai"] == 15000)
        grp.reload()
        grp.components[0].status = "Tidak Berlaku"
        grp.save()
        cek("G4 Group Tidak Berlaku: hasil 0", resolve_komponen_karyawan(dept, grp.name, "Grup", T, "TJ_MAKAN")["nilai"] == 0)
        try:
            grp.reload()
            grp.append("components", {"component": "TJ_MAKAN", "status": "Berlaku", "amount": 1})
            grp.save()
            cek("G5 komponen dobel ditolak", False)
        except frappe.ValidationError:
            cek("G5 komponen dobel ditolak", True)
        from hris.hris_attendance.services.audit_trail import get_audit_trail
        rows = get_audit_trail("HRIS Employee Group", grp.name)
        teks = " ".join(r["field"] + " " + r["new"] for r in rows)
        cek("A1 Audit Trail mencatat baris komponen", "baris" in teks.lower(), teks[:160])
    finally:
        frappe.db.rollback(save_point="e1t2c")
    cek("Z1 rollback bersih", not frappe.db.exists("HRIS Employee Group", "ZZ Uji E1 2c"))
    print("HASIL: OK %d, GAGAL %d" % (ok, g))
