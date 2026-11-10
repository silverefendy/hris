"""Uji HRIS BPJS Rate (K-133 langkah 1). Tarif di sini hanya CONTOH FIKTIF untuk uji.
Jalankan dari folder sites: ../env/bin/python <path ini>. Semua perubahan di-rollback."""

import frappe
from frappe.utils import flt

SITE = "hris-uji.local"
DT = "HRIS BPJS Rate"
CATATAN = "TARIF CONTOH UJI, BUKAN TARIF RESMI"

frappe.init(site=SITE, sites_path=".")
frappe.connect()
frappe.set_user("Administrator")

hasil = []


def cek(nama, kondisi, rinci=""):
    hasil.append(bool(kondisi))
    print(("OK      " if kondisi else "GAGAL   ") + nama + ("" if kondisi or not rinci else "  " + str(rinci)))


def buat(company, **nilai):
    data = {"doctype": DT, "company": company, "notes": CATATAN}
    data.update(nilai)
    return frappe.get_doc(data)


def harus_gagal(doc):
    try:
        doc.insert()
    except frappe.ValidationError:
        return True
    return False


def user_uji(email, peran):
    frappe.get_doc(
        {
            "doctype": "User",
            "email": email,
            "first_name": "ZZ Uji",
            "enabled": 1,
            "send_welcome_email": 0,
            "roles": [{"role": r} for r in peran],
        }
    ).insert(ignore_permissions=True)
    return email


EMAILS = ["zz-uji-bpjs-mgr@example.com", "zz-uji-bpjs-adm@example.com", "zz-uji-bpjs-lain@example.com"]

try:
    if frappe.local.site != SITE:
        raise SystemExit("Site bukan %s; berhenti." % SITE)

    company = frappe.get_all("Company", pluck="name", limit=1)[0]
    n_awal = frappe.db.count(DT)

    a = buat(company, program="JHT", employee_rate=2, company_rate=3.7, effective_from="2026-01-01")
    a.insert()
    cek("R1 JHT valid disimpan", bool(a.name))
    cek("R2 penomoran BPR-YYMM-NNNN", a.name.startswith("BPR-") and a.name[4:8].isdigit(), a.name)
    cek("R3 kunci unik terisi", a.unique_key == "%s|JHT||2026-01-01" % company, a.unique_key)
    cek("R4 tarif tersimpan", abs(flt(a.employee_rate) - 2) < 1e-6 and abs(flt(a.company_rate) - 3.7) < 1e-6)
    cek(
        "R5 kunci ganda ditolak",
        harus_gagal(buat(company, program="JHT", employee_rate=2, company_rate=3.7, effective_from="2026-01-01")),
    )
    b = buat(company, program="JHT", employee_rate=2, company_rate=3.7, effective_from="2026-07-01")
    b.insert()
    cek("R6 tanggal berlaku lain boleh", bool(b.name))
    cek(
        "R7 JKK tanpa kelas risiko ditolak",
        harus_gagal(buat(company, program="JKK", employee_rate=0, company_rate=0.24, effective_from="2026-01-01")),
    )
    k1 = buat(company, program="JKK", risk_class="I", employee_rate=0, company_rate=0.24, effective_from="2026-01-01")
    k1.insert()
    k2 = buat(company, program="JKK", risk_class="II", employee_rate=0, company_rate=0.54, effective_from="2026-01-01")
    k2.insert()
    cek("R8 JKK per kelas risiko pada tanggal sama boleh", bool(k1.name) and bool(k2.name))
    cek(
        "R8b JKK kelas risiko ganda ditolak",
        harus_gagal(
            buat(company, program="JKK", risk_class="I", employee_rate=0, company_rate=0.24, effective_from="2026-01-01")
        ),
    )
    c = buat(
        company, program="JP", risk_class="X", employee_rate=1, company_rate=2, wage_cap=1000000, effective_from="2026-01-01"
    )
    c.insert()
    cek("R9 program non-JKK: kelas risiko dikosongkan", not c.risk_class and c.unique_key == "%s|JP||2026-01-01" % company, c.unique_key)
    cek("R9b batas upah tersimpan", flt(c.wage_cap) == 1000000)
    cek(
        "R10 tarif negatif ditolak",
        harus_gagal(buat(company, program="BPJS Kesehatan", employee_rate=-1, company_rate=4, effective_from="2026-01-01")),
    )
    cek(
        "R11 tarif di atas 100 ditolak",
        harus_gagal(buat(company, program="BPJS Kesehatan", employee_rate=1, company_rate=101, effective_from="2026-01-01")),
    )
    cek(
        "R12 batas upah negatif ditolak",
        harus_gagal(
            buat(company, program="BPJS Kesehatan", employee_rate=1, company_rate=4, wage_cap=-1, effective_from="2026-01-01")
        ),
    )

    mgr = user_uji(EMAILS[0], ["HRIS Payroll Manager"])
    adm = user_uji(EMAILS[1], ["HRIS Payroll Admin"])
    lain = user_uji(EMAILS[2], ["HRIS Attendance Operator"])
    cek("I1 Payroll Manager: baca, tulis, buat", all(frappe.has_permission(DT, p, user=mgr) for p in ("read", "write", "create")))
    cek("I1 Payroll Manager: tidak boleh hapus", not frappe.has_permission(DT, "delete", user=mgr))
    cek(
        "I2 Payroll Admin: hanya baca",
        frappe.has_permission(DT, "read", user=adm)
        and not any(frappe.has_permission(DT, p, user=adm) for p in ("write", "create", "delete")),
    )
    cek("I3 peran lain: tidak melihat", not frappe.has_permission(DT, "read", user=lain))
finally:
    frappe.db.rollback()
    if hasil:
        cek("Z1 tidak ada sisa tarif uji", frappe.db.count(DT) == n_awal)
        cek("Z1 tidak ada sisa user uji", not any(frappe.db.exists("User", e) for e in EMAILS))
        print("HASIL: OK %d, GAGAL %d" % (hasil.count(True), hasil.count(False)))
    frappe.destroy()
