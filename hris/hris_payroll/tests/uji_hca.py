"""K-140 E2: uji DocType HRIS Component Assignment (HCA). Semua data di-rollback.

Jalankan:
bench --site hris-uji.local execute hris.hris_payroll.tests.uji_hca.jalankan
"""
import re

import frappe

TABEL = "HRIS Component Assignment"
AWAL, AKHIR = "2030-03-01", "2030-03-31"
ALASAN = "uji K-140 HCA"


def jalankan():
    hasil = []

    def cek(nama, kondisi, info=""):
        hasil.append(bool(kondisi))
        print(("OK     " if kondisi else "GAGAL  ") + nama + ((" | " + str(info)[:250]) if (not kondisi and info != "") else ""))

    def ditolak(nama, fn):
        try:
            fn()
            cek(nama, False, "tidak ditolak")
        except (frappe.ValidationError, frappe.PermissionError):
            cek(nama, True)
            frappe.clear_messages()

    dept = frappe.db.sql("select name, company from `tabHRIS Department` where company is not null and is_group = 0 limit 1")
    grup = frappe.db.sql("select name, company from `tabHRIS Employee Group` where company is not null and is_active = 1 limit 1")
    lain = frappe.db.sql("select name from `tabHRIS Pay Component` where name != 'TJ_MAKAN' limit 1")
    if not (dept and grup):
        print("SKIP: tidak ada Department atau Grup ber-Company untuk uji")
        return
    D, DC = dept[0]
    G, GC = grup[0]
    awal_baris = frappe.db.count(TABEL)

    def buat(**kw):
        d = {"doctype": TABEL, "scope_type": "Grup", "employee_group": G, "component": "TJ_MAKAN", "status": "Berlaku",
             "is_active": 1, "reason": ALASAN, "date_from": AWAL, "date_to": AKHIR}
        d.update(kw)
        doc = frappe.get_doc(d)
        doc.insert(ignore_permissions=True)
        return doc

    try:
        h1 = buat()
        cek("A1 Grup valid: penamaan HCA dan Company dari Grup", re.match(r"^HCA-\d{4}-\d{4}$", h1.name) and h1.company == GC, (h1.name, h1.company))
        h2 = buat(scope_type="Department", department=D, employee_group=None)
        cek("A2 Department valid: Company dari Department dan termasuk anak bawaan aktif",
            h2.company == DC and int(h2.include_children) == 1, (h2.company, h2.include_children))
        ditolak("A3 tumpang tindih Grup dan komponen sama ditolak", lambda: buat(date_from="2030-03-15", date_to="2030-04-15"))
        h3 = buat(date_from="2030-04-01", date_to="2030-04-30")
        cek("A4 rentang tidak bertumpuk diterima", bool(h3.name))
        h4 = buat(is_active=0)
        cek("A5 baris nonaktif tidak memicu tumpang tindih", h4.is_active == 0)
        ditolak("A6 Grup tanpa Grup ditolak", lambda: buat(employee_group=None))
        ditolak("A7 Department tanpa Department ditolak", lambda: buat(scope_type="Department", employee_group=None, department=None))
        h5 = buat(component="TJ_MAKAN", date_from="2031-01-01", date_to="2031-01-31", department=D)
        cek("A8 scope Grup dengan Department terisi: Department dikosongkan", not h5.department and h5.employee_group == G, (h5.department, h5.employee_group))
        h6 = buat(date_from="2031-02-01", date_to="2031-02-28", status="Tidak Berlaku", amount=5000)
        cek("A9 Tidak Berlaku: nominal menjadi 0", h6.amount == 0, h6.amount)
        ditolak("A10 nominal negatif ditolak", lambda: buat(date_from="2031-03-01", date_to="2031-03-31", amount=-1))
        ditolak("A11 Sampai sebelum Dari ditolak", lambda: buat(date_from="2031-05-10", date_to="2031-05-01"))
        ditolak("A12 alasan kosong ditolak", lambda: buat(date_from="2031-06-01", date_to="2031-06-30", reason="  "))
        if lain:
            h1.reload()
            h1.component = lain[0][0]
            h1.reason = "ganti komponen"
            ditolak("A13 komponen tidak boleh diubah setelah disimpan", lambda: h1.save(ignore_permissions=True))
            frappe.clear_messages()
        h1 = frappe.get_doc(TABEL, h1.name)
        h1.date_to = "2030-03-20"
        ditolak("A14 ubah tanggal tanpa alasan baru ditolak", lambda: h1.save(ignore_permissions=True))
        h1 = frappe.get_doc(TABEL, h1.name)
        h1.date_to = "2030-03-20"
        h1.reason = "dipersingkat uji"
        h1.save(ignore_permissions=True)
        cek("A15 ubah tanggal dengan alasan baru diterima", str(frappe.db.get_value(TABEL, h1.name, "date_to")) == "2030-03-20")
    finally:
        frappe.db.rollback()
    cek("A16 rollback: jumlah baris kembali seperti awal", frappe.db.count(TABEL) == awal_baris, (frappe.db.count(TABEL), awal_baris))
    print("OK %d, GAGAL %d (data uji di-rollback)" % (sum(hasil), len(hasil) - sum(hasil)))
