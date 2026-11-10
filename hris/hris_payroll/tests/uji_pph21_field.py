"""Uji field PPh 21 (K-134 langkah 2 dan 3): ptkp_status di HRIS Employee, taxable di HRIS Payroll Slip Item.
Tidak menulis data. Jalankan dari folder sites: ../env/bin/python <path ini>."""

import frappe

SITE = "hris-uji.local"
frappe.init(site=SITE, sites_path=".")
frappe.connect()
frappe.set_user("Administrator")

hasil = []


def cek(nama, kondisi, rinci=""):
    hasil.append(bool(kondisi))
    print(("OK      " if kondisi else "GAGAL   ") + nama + ("" if kondisi or not rinci else "  " + str(rinci)))


def hak(meta, role, jenis, level):
    return any(p.role == role and int(p.permlevel or 0) == level and getattr(p, jenis, 0) for p in meta.permissions)


try:
    if frappe.local.site != SITE:
        raise SystemExit("Site bukan %s; berhenti." % SITE)
    for dt in ("HRIS Employee", "HRIS Payroll Slip Item"):
        frappe.clear_cache(doctype=dt)

    emp = frappe.get_meta("HRIS Employee")
    urut = [f.fieldname for f in emp.fields]
    f = emp.get_field("ptkp_status")
    cek("P1 ptkp_status ada", f)
    cek("P2 Select dengan kosong + 8 pilihan",
        f and f.fieldtype == "Select"
        and f.options.split("\n") == ["", "TK/0", "TK/1", "TK/2", "TK/3", "K/0", "K/1", "K/2", "K/3"],
        f and f.options)
    cek("P3 permlevel 1", f and int(f.permlevel or 0) == 1)
    cek("P4 tampil dan wajib bergantung pph21_enrolled",
        f and "pph21_enrolled" in (f.depends_on or "") and "pph21_enrolled" in (f.mandatory_depends_on or ""))
    cek("P5 letak: setelah pph21_enrolled, sebelum col_bpjs_peserta",
        urut.index("pph21_enrolled") < urut.index("ptkp_status") < urut.index("col_bpjs_peserta"))
    cek("P6 kolom DB ptkp_status ada", frappe.db.has_column("HRIS Employee", "ptkp_status"))
    cek("P7 HR Admin dan Employee Admin tulis permlevel 1",
        hak(emp, "HRIS HR Admin", "write", 1) and hak(emp, "HRIS Employee Admin", "write", 1))
    cek("P8 Payroll Admin dan Direksi tidak tulis permlevel 1",
        not hak(emp, "HRIS Payroll Admin", "write", 1) and not hak(emp, "HRIS Direksi", "write", 1))

    item = frappe.get_meta("HRIS Payroll Slip Item")
    uf = [x.fieldname for x in item.fields]
    t = item.get_field("taxable")
    cek("T1 taxable ada, Check, bawaan 1", t and t.fieldtype == "Check" and str(t.default) == "1")
    cek("T2 terkunci untuk baris Otomatis", t and "Otomatis" in (t.read_only_depends_on or ""))
    cek("T3 letak setelah reason", uf.index("reason") < uf.index("taxable"))
    cek("T4 kolom DB taxable ada", frappe.db.has_column("HRIS Payroll Slip Item", "taxable"))
    kosong = frappe.db.sql("select count(*) from `tabHRIS Payroll Slip Item` where taxable is null")[0][0]
    total, satu = frappe.db.sql("select count(*), coalesce(sum(taxable),0) from `tabHRIS Payroll Slip Item`")[0]
    cek("T5 tidak ada baris lama bernilai NULL", kosong == 0, kosong)
    print("INFO    baris slip item: %s, bernilai 1: %s" % (total, satu))
finally:
    frappe.destroy()
    print("\nHASIL: OK %d, GAGAL %d" % (sum(hasil), len(hasil) - sum(hasil)))
