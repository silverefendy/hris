"""Uji pembuatan slip massal (K-130): cakupan Semua, Department, Grup, Karyawan, mode background, idempotensi.
Semua data di-rollback. Jalankan dari folder sites: ../env/bin/python <path ini>."""

import os

import frappe

ok = 0
gagal = 0


def cek(nama, kondisi, info=""):
    global ok, gagal
    if kondisi:
        ok += 1
        print("OK     ", nama)
    else:
        gagal += 1
        print("GAGAL  ", nama, info)


def harus_gagal(nama, fn):
    try:
        fn()
    except frappe.ValidationError:
        cek(nama, True)
        return
    except Exception as exc:
        cek(nama, False, "galat lain: %r" % (exc,))
        return
    cek(nama, False, "tidak ditolak")


def uji():
    from hris.hris_payroll.doctype.hris_payroll_period.hris_payroll_period import kembalikan, tinjau
    from hris.hris_payroll.services import payroll_slip as ps
    from hris.hris_payroll.services.payroll_schedule import get_period_for_date

    company = frappe.db.get_value("Company", {}, "name")
    sch = frappe.get_doc({
        "doctype": "HRIS Payroll Schedule", "schedule_name": "ZZ Uji Massal", "company": company,
        "schedule_type": "Bulanan", "is_active": 1, "pay_date_offset_days": 3,
        "sunday_rule": "Maju ke Senin", "cut_off_day": 26,
    }).insert(ignore_permissions=True)
    rentang = get_period_for_date(sch.name, "2026-10-17")
    awal, akhir = str(rentang["start"]), str(rentang["end"])

    kand = frappe.db.sql(
        """
        select he.name as he, he.department as dep, he.employee_group as grp
        from `tabHRIS Employee` he
        inner join `tabHRIS Working Hour` wh on wh.employee = he.erpnext_employee
        where wh.work_date between %(a)s and %(b)s
          and he.company = %(co)s
          and he.date_of_joining <= %(a)s
          and (he.resign_date is null or he.resign_date > %(b)s)
          and wh.status in ('Hadir', 'Tidak Lengkap', 'Tidak Hadir')
          and ifnull(wh.scheduled_hours, 0) > 0
          and not exists (select 1 from `tabHRIS Employee Pay` ep where ep.employee = he.name)
        group by he.name, he.department, he.employee_group
        having sum(wh.status = 'Hadir') > 0
        order by he.name limit 12
        """,
        {"a": awal, "b": akhir, "co": company},
        as_dict=True,
    )
    n = len(kand)
    cek("D0 ada minimal 3 karyawan kandidat dengan hari Hadir (%d)" % n, n >= 3, "periode %s s/d %s" % (awal, akhir))
    if n < 3:
        return
    tanpa_wh = frappe.db.sql_list(
        """
        select he.name from `tabHRIS Employee` he
        where he.company = %(co)s and ifnull(he.erpnext_employee, '') != '' and he.date_of_joining <= %(a)s
          and not exists (select 1 from `tabHRIS Working Hour` wh
                          where wh.employee = he.erpnext_employee and wh.work_date between %(a)s and %(b)s)
          and not exists (select 1 from `tabHRIS Employee Pay` ep where ep.employee = he.name)
        limit 1
        """,
        {"a": awal, "b": akhir, "co": company},
    )
    pilihan = [k.he for k in kand]
    semua = pilihan + tanpa_wh
    for nama in semua:
        frappe.get_doc({
            "doctype": "HRIS Employee Pay", "employee": nama, "pay_type": "Harian", "amount": 100000,
            "payroll_schedule": sch.name, "effective_from": "2026-01-01",
        }).insert(ignore_permissions=True)
    period = frappe.get_doc({
        "doctype": "HRIS Payroll Period", "payroll_schedule": sch.name, "reference_date": "2026-10-17",
    }).insert(ignore_permissions=True)

    def jml_slip():
        return frappe.db.count("HRIS Payroll Slip", {"payroll_period": period.name})

    # S1 Semua
    r = ps.buat_slip(period.name, "Semua")
    cek("S1 Semua: mode sync dan total = jumlah karyawan berbaris gaji", r["mode"] == "sync" and r["total"] == len(semua), r)
    cek("S1 Semua: tanpa gagal dan hitungan konsisten", r["gagal"] == 0 and r["dibuat"] + r["diperbarui"] + r["dilewati"] == r["total"], r)
    cek("S1 Semua: dibuat = jumlah kandidat berhari Hadir (%d)" % n, r["dibuat"] == n, r)
    if tanpa_wh:
        cek("S1 Semua: karyawan tanpa Working Hour dilewati dengan alasan jelas",
            r["dilewati"] == 1 and any("Working Hour" in k for k in r["alasan"]), r["alasan"])
    else:
        print("INFO    tidak ada karyawan tanpa Working Hour; pemeriksaan alasan dilewati")
    cek("S1 Semua: jumlah slip di database = dibuat", jml_slip() == r["dibuat"], jml_slip())

    # S2 ulang
    r2 = ps.buat_slip(period.name, "Semua")
    cek("S2 ulang Semua: diperbarui = dibuat sebelumnya, tanpa slip baru", r2["diperbarui"] == r["dibuat"] and r2["dibuat"] == 0, r2)
    cek("S2 ulang Semua: jumlah slip tidak berubah", jml_slip() == r["dibuat"], jml_slip())

    # S3 Department
    dep = next((k.dep for k in kand if k.dep), None)
    if dep:
        harap = len(frappe.get_all("HRIS Employee", filters={"name": ["in", semua], "department": dep}, pluck="name"))
        rd = ps.buat_slip(period.name, "Department", department=dep)
        cek("S3 Department: total = hitungan SQL (%d)" % harap, rd["total"] == harap and rd["gagal"] == 0, rd)
    else:
        print("INFO    tidak ada kandidat ber-Department; S3 dilewati")

    # S4 Grup
    grp = next((k.grp for k in kand if k.grp), None)
    if grp:
        harap = len(frappe.get_all("HRIS Employee", filters={"name": ["in", semua], "employee_group": grp}, pluck="name"))
        rg = ps.buat_slip(period.name, "Grup", employee_group=grp)
        cek("S4 Grup: total = hitungan SQL (%d)" % harap, rg["total"] == harap and rg["gagal"] == 0, rg)
    else:
        print("INFO    tidak ada kandidat ber-Grup; S4 dilewati")

    # S5 penolakan
    luar = frappe.db.sql_list("select name from `tabHRIS Employee` where name not in %s limit 1", (tuple(semua),))
    if luar:
        harus_gagal("S5 Karyawan tanpa baris gaji ditolak", lambda: ps.buat_slip(period.name, "Karyawan", employee=luar[0]))
    harus_gagal("S5 Department tanpa nilai ditolak", lambda: ps.buat_slip(period.name, "Department"))
    harus_gagal("S5 cakupan tidak dikenal ditolak", lambda: ps.buat_slip(period.name, "Ngawur"))

    # S6 background
    tertangkap = {}
    asli_enqueue, asli_limit = frappe.enqueue, ps.SYNC_LIMIT
    frappe.enqueue = lambda *a, **kw: tertangkap.update(kw)
    ps.SYNC_LIMIT = 2
    try:
        rb = ps.buat_slip(period.name, "Semua")
        cek("S6 background: mode background dan total benar", rb.get("mode") == "background" and rb.get("total") == len(semua), rb)
        cek("S6 background: daftar nama yang dikirim ke antrean benar", tertangkap.get("names") == sorted(semua), tertangkap.get("names"))
        if rb.get("run_id"):
            ps.run_batch(rb["run_id"], period.name, tertangkap.get("names", []), commit=False)
            st = ps.get_status(rb["run_id"])
            cek("S6 background: status akhir Selesai dan hitungan cocok",
                st.get("state") == "Selesai" and st.get("done") == len(semua)
                and st.get("diperbarui") == r["dibuat"] and st.get("gagal") == 0, st)
    finally:
        frappe.enqueue, ps.SYNC_LIMIT = asli_enqueue, asli_limit

    # S7 periode terkunci
    try:
        tinjau(period.name)
        harus_gagal("S7 Periode Ditinjau menolak pembuatan slip", lambda: ps.buat_slip(period.name, "Semua"))
        kembalikan(period.name)
        r3 = ps.buat_slip(period.name, "Semua")
        cek("S7 setelah dikembalikan ke Draft, slip bisa dibuat lagi", r3["gagal"] == 0 and r3["total"] == len(semua), r3)
    except Exception as exc:
        cek("S7 tinjau dan kembalikan Periode", False, repr(exc)[:200])


def periksa():
    from hris.hris_payroll.services import payroll_slip as ps

    n_awal = frappe.db.count("HRIS Payroll Slip")
    try:
        uji()
    finally:
        frappe.db.rollback()
        ps._cache().delete_value(ps.ACTIVE_KEY)
    cek("Z1 tidak ada sisa slip uji", frappe.db.count("HRIS Payroll Slip") == n_awal)
    cek("Z1 tidak ada sisa jadwal uji", not frappe.db.exists("HRIS Payroll Schedule", "ZZ Uji Massal"))
    print("HASIL: OK %d, GAGAL %d" % (ok, gagal))
    return gagal


if __name__ == "__main__":
    os.chdir("/home/it/erp/sites")
    frappe.init(site="hris-uji.local", sites_path=".")
    frappe.connect()
    frappe.set_user("Administrator")
    try:
        sisa = periksa()
    finally:
        frappe.db.rollback()
        frappe.destroy()
    raise SystemExit(1 if sisa else 0)
