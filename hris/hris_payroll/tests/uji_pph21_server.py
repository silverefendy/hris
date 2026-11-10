"""Uji BACA-SAJA: apakah server menegakkan wajib ptkp_status bila pph21_enrolled dicentang
(mandatory_depends_on). Tidak menyimpan apa pun. Jalankan dari folder sites."""

import frappe

SITE = "hris-uji.local"
frappe.init(site=SITE, sites_path=".")
frappe.connect()
frappe.set_user("Administrator")

try:
    if frappe.local.site != SITE:
        raise SystemExit("Site bukan %s; berhenti." % SITE)
    nama = frappe.db.get_value("HRIS Employee", {}, "name")
    if not nama:
        print("LEWATI  tidak ada HRIS Employee di site uji")
    else:
        d = frappe.get_doc("HRIS Employee", nama)
        d.pph21_enrolled = 1
        d.ptkp_status = ""
        hilang = [str(x) for x in d._get_missing_mandatory_fields()]
        server_wajib = any("ptkp_status" in x or "PTKP" in x for x in hilang)
        print("INFO    kosong + dicentang: server %s wajib PTKP" % ("MENEGAKKAN" if server_wajib else "TIDAK menegakkan"))
        d.pph21_enrolled = 0
        hilang0 = [str(x) for x in d._get_missing_mandatory_fields()]
        print("INFO    tidak dicentang: PTKP %s dianggap kurang" % ("TETAP" if any("PTKP" in x or "ptkp_status" in x for x in hilang0) else "tidak"))
        print("INFO    (tidak ada data yang disimpan)")
finally:
    frappe.destroy()
