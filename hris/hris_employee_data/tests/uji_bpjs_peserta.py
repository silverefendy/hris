"""Uji field kepesertaan BPJS di HRIS Employee (K-133 langkah 2). Tidak menulis data.
Jalankan dari folder sites: ../env/bin/python <path ini>."""

import frappe

SITE = "hris-uji.local"
DT = "HRIS Employee"
CENTANG = ["bpjs_kes_enrolled", "bpjs_jht_enrolled", "bpjs_jp_enrolled", "bpjs_jkk_enrolled", "bpjs_jkm_enrolled", "pph21_enrolled"]
SEMUA = CENTANG + ["bpjs_jkk_risk_class", "bpjs_wage_basis"]

frappe.init(site=SITE, sites_path=".")
frappe.connect()
frappe.set_user("Administrator")

hasil = []


def cek(nama, kondisi, rinci=""):
    hasil.append(bool(kondisi))
    print(("OK      " if kondisi else "GAGAL   ") + nama + ("" if kondisi or not rinci else "  " + str(rinci)))


try:
    if frappe.local.site != SITE:
        raise SystemExit("Site bukan %s; berhenti." % SITE)
    frappe.clear_cache(doctype=DT)
    meta = frappe.get_meta(DT)
    urut = [f.fieldname for f in meta.fields]

    cek("S1 delapan field kepesertaan ada", all(meta.get_field(n) for n in SEMUA))
    cek(
        "S2 tipe field sesuai",
        all(meta.get_field(n) and meta.get_field(n).fieldtype == "Check" for n in CENTANG)
        and meta.get_field("bpjs_jkk_risk_class").fieldtype == "Data"
        and meta.get_field("bpjs_wage_basis").fieldtype == "Select",
    )
    cek(
        "S3 semua permlevel 1",
        all(int(meta.get_field(n).permlevel or 0) == 1 for n in SEMUA + ["sec_bpjs_peserta", "col_bpjs_peserta"]),
    )
    cek(
        "S4 letak: setelah bank_account_number, sebelum sec_sinkron",
        urut.index("bank_account_number") < urut.index("sec_bpjs_peserta") < urut.index("pph21_enrolled") < urut.index("sec_sinkron"),
    )
    cek("S5 centang bawaan mati", all(str(meta.get_field(n).default) == "0" for n in CENTANG))
    cek(
        "S6 dasar upah: opsi dan bawaan",
        meta.get_field("bpjs_wage_basis").options.split("\n") == ["Gaji Final", "Gaji Penuh"]
        and meta.get_field("bpjs_wage_basis").default == "Gaji Final",
    )
    cek("S7 nama field unik", len(urut) == len(set(urut)))
    cek("S8 tab Audit Trail tetap di akhir", urut[-2:] == ["audit_trail_tab", "audit_trail_html"], urut[-2:])
    cek("S9 kolom ada di basis data", all(frappe.db.has_column(DT, n) for n in SEMUA))
    ada = frappe.db.sql(
        "select count(*) from `tabHRIS Employee` where " + " or ".join("`%s` = 1" % n for n in CENTANG)
    )[0][0]
    cek("S10 baris lama: tidak ada centang menyala", ada == 0, ada)
    kosong = frappe.db.sql("select count(*) from `tabHRIS Employee` where bpjs_wage_basis is null or bpjs_wage_basis = ''")[0][0]
    print("INFO    baris lama dengan dasar upah kosong: %s (slip memperlakukan kosong sebagai Gaji Final)" % kosong)
finally:
    if hasil:
        print("HASIL: OK %d, GAGAL %d" % (hasil.count(True), hasil.count(False)))
    frappe.destroy()
