"""Uji 6b-3b: on_trash menolak hapus bawaan WH yang terkunci periode Final.
  bench --site hris-uji.local execute hris.hris_payroll.tests.uji_wh_hapus_on_trash.jalankan
"""
import frappe

JADWAL = "Uji Slip Browser 01"
DT = "HRIS Working Hour"


def jalankan():
    ok = 0
    total = 0

    def cek(nama, kondisi):
        nonlocal ok, total
        total += 1
        if kondisi:
            ok += 1
            print("OK", nama)
        else:
            print("GAGAL", nama)

    k = frappe.db.sql(
        """
        select wh.name, pp.name as periode, pp.status as status_periode
        from `tabHRIS Working Hour` wh
        inner join `tabHRIS Employee` he on he.erpnext_employee = wh.employee
        inner join `tabHRIS Employee Pay` ep on ep.employee = he.name
            and ep.effective_from <= wh.work_date
            and (ep.effective_to is null or ep.effective_to >= wh.work_date)
        inner join `tabHRIS Payroll Period` pp on pp.payroll_schedule = ep.payroll_schedule
            and wh.work_date between pp.period_start and pp.period_end
        where ep.payroll_schedule = %s and ifnull(pp.status, '') != 'Final'
        limit 1
        """,
        JADWAL,
        as_dict=True,
    )
    if not k:
        print("SKIP tidak ada WH ber-gaji pada periode jadwal", JADWAL)
        print("\nLulus 0 dari 0 (SKIP)")
        return
    k = k[0]

    try:
        doc = frappe.get_doc(DT, k.name)
        try:
            doc.on_trash()
            cek("sebelum Final: on_trash tidak menolak", True)
        except Exception:
            cek("sebelum Final: on_trash tidak menolak", False)

        frappe.db.set_value("HRIS Payroll Period", k.periode, "status", "Final", update_modified=False)

        try:
            doc.on_trash()
            cek("periode Final: on_trash menolak", False)
        except frappe.ValidationError:
            cek("periode Final: on_trash menolak", True)

        try:
            frappe.delete_doc(DT, k.name, force=False)
            cek("periode Final: delete_doc menolak", False)
        except frappe.ValidationError:
            cek("periode Final: delete_doc menolak", True)
        cek("dokumen masih ada setelah ditolak", bool(frappe.db.exists(DT, k.name)))
    finally:
        frappe.db.rollback()

    status = frappe.db.get_value("HRIS Payroll Period", k.periode, "status")
    cek("status periode kembali semula", (status or "") == (k.status_periode or ""))
    cek("dokumen tetap ada setelah rollback", bool(frappe.db.exists(DT, k.name)))
    print("\nLulus %d dari %d" % (ok, total))
