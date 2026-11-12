"""K-137: uji notifikasi slip Draft saat Department Rule berubah (tanpa tulis permanen).

Jalankan: bench --site hris-uji.local execute hris.hris_payroll.tests.uji_notif_department_rule.jalankan
"""
from datetime import date

import frappe

from hris.hris_payroll.services import department_rule_notify as dn


def jalankan():
    ok = []
    gagal = []

    def cek(nama, kondisi, ket=""):
        (ok if kondisi else gagal).append(nama)
        print("OK    " if kondisi else "GAGAL ", nama, ket)

    sebelum = frappe._dict(department="D1", effective_from="2026-10-01", is_active=1, overtime_multiplier=1.0)
    sama = frappe._dict(department="D1", effective_from=date(2026, 10, 1), is_active=1, overtime_multiplier=1.0)
    cek("N1 rule baru dianggap berubah", dn._berubah(sama, None))
    cek("N2 tanpa perubahan tidak berubah", not dn._berubah(sama, sebelum))
    for kolom, nilai in (("overtime_multiplier", 1.5), ("is_active", 0), ("effective_from", "2026-11-01"), ("department", "D2")):
        ubah = frappe._dict(sama)
        ubah[kolom] = nilai
        cek("N3 perubahan %s terdeteksi" % kolom, dn._berubah(ubah, sebelum))

    akar = "All Departments"
    jauh = dn.hitung_slip_draft([akar], date(2100, 1, 1))
    lama = dn.hitung_slip_draft([akar], date(2000, 1, 1))
    cek("N4 tanggal sangat jauh: 0 slip", jauh == 0, str(jauh))
    cek("N4b jumlah bertipe int dan tidak negatif", isinstance(lama, int) and lama >= 0, str(lama))

    stub = frappe._dict(name="DR-UJI-NOTIF", department=akar)
    frappe.db.savepoint("uji_notif")
    try:
        n = dn.kirim_notifikasi(stub, 3)
        dibuat = frappe.db.count("Notification Log", {"document_type": dn.RULE, "document_name": "DR-UJI-NOTIF"})
        cek("N5 jumlah Notification Log sama dengan jumlah penerima", dibuat == n, "(penerima %d, dibuat %d)" % (n, dibuat))
        if n == 0:
            print("INFO  tidak ada pengguna aktif dengan peran Payroll Manager/Admin selain Administrator di site ini")
    finally:
        frappe.db.rollback(save_point="uji_notif")
    sisa = frappe.db.count("Notification Log", {"document_type": dn.RULE, "document_name": "DR-UJI-NOTIF"})
    cek("N6 uji bersih (rollback)", sisa == 0, str(sisa))

    print("HASIL: OK %d, GAGAL %d" % (len(ok), len(gagal)))
