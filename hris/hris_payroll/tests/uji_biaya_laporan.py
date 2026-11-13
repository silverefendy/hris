import frappe
from frappe.utils import flt
from hris.hris_payroll.report.hris_biaya_tenaga_kerja.hris_biaya_tenaga_kerja import hitung

WH = "HRIS Working Hour"


def jalankan():
    hasil = []

    def cek(nama, kondisi, info=""):
        hasil.append(bool(kondisi))
        print(("OK     " if kondisi else "GAGAL  ") + nama + (" | " + str(info) if info else ""))

    s = frappe.get_all(
        "HRIS Payroll Slip",
        fields=["name", "payroll_period", "erpnext_employee", "department", "employee_group",
                "base_amount", "working_days", "total_earning", "period_start", "period_end"],
        limit_page_length=1,
    )[0]
    hari = frappe.get_all(
        WH,
        filters={"employee": s.erpnext_employee, "work_date": ["between", [str(s.period_start), str(s.period_end)]]},
        fields=["name", "rule_department", "borrowed_for_group"],
        order_by="work_date asc",
        limit_page_length=2,
    )
    dept_lain = frappe.get_all("HRIS Department", filters={"name": ["!=", s.department]}, pluck="name", limit_page_length=1)
    grup_lain = frappe.get_all("HRIS Employee Group", filters={"name": ["!=", s.employee_group]}, pluck="name", limit_page_length=1)
    if len(hari) < 2 or not dept_lain or not grup_lain:
        print("BERHENTI: butuh 2 hari Working Hour, 1 Department lain, 1 Employee Group lain")
        return
    harapan = round(flt(s.base_amount) / flt(s.working_days) * 2)
    total = round(flt(s.total_earning))
    print("slip", s.name, "| harapan porsi:", harapan, "| total_earning:", total)
    try:
        for h in hari:
            frappe.db.set_value(WH, h.name, "rule_department", dept_lain[0], update_modified=False)
        f = frappe._dict(payroll_period=s.payroll_period, group_by="Department", status="Semua")
        data, pesan = hitung(f)
        d = {x["kelompok"]: x for x in data}
        cek("D1 asal: pinjaman keluar", d[s.department]["pinjaman_keluar"] == harapan, d[s.department]["pinjaman_keluar"])
        cek("D2 tujuan: pinjaman masuk", d[dept_lain[0]]["pinjaman_masuk"] == harapan, d[dept_lain[0]]["pinjaman_masuk"])
        cek("D3 total biaya = total_earning", sum(x["total_biaya"] for x in data) == total)
        cek("D4 tanpa peringatan", "PERINGATAN" not in pesan)
        frappe.db.rollback()

        for h in hari:
            frappe.db.set_value(WH, h.name, "borrowed_for_group", grup_lain[0], update_modified=False)
        f.group_by = "Employee Group"
        data, pesan = hitung(f)
        d = {x["kelompok"]: x for x in data}
        cek("G1 asal: pinjaman keluar", d[s.employee_group]["pinjaman_keluar"] == harapan, d[s.employee_group]["pinjaman_keluar"])
        cek("G2 tujuan: pinjaman masuk", d[grup_lain[0]]["pinjaman_masuk"] == harapan, d[grup_lain[0]]["pinjaman_masuk"])
        cek("G3 total biaya = total_earning", sum(x["total_biaya"] for x in data) == total)
        frappe.db.rollback()

        data, pesan = hitung(frappe._dict(payroll_period=s.payroll_period, group_by="Department", status="Semua"))
        cek("Z1 rollback: tanpa pinjaman lagi", sum(x["pinjaman_keluar"] for x in data) == 0)
    finally:
        frappe.db.rollback()
    print("OK %d, GAGAL %d" % (sum(hasil), len(hasil) - sum(hasil)))
