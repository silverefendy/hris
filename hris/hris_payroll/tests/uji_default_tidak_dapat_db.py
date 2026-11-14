"""K-140 uji database (di-rollback): default tidak dapat lewat hitung_tunjangan_karyawan.

Jalankan:
bench --site hris-uji.local execute hris.hris_payroll.tests.uji_default_tidak_dapat_db.jalankan
"""
from datetime import date

import frappe

from hris.hris_payroll.services.komponen_slip import hitung_tunjangan_karyawan

HEC = "HRIS Employee Component"
KATALOG = "HRIS Pay Component"
AWAL, AKHIR = "2030-03-01", "2030-03-31"
HADIR = [date(2030, 3, d) for d in range(1, 11)]


def jalankan():
    hasil = []

    def cek(nama, kondisi, info=""):
        hasil.append(bool(kondisi))
        print(("OK     " if kondisi else "GAGAL  ") + nama + ((" | " + str(info)[:250]) if (not kondisi and info) else ""))

    b = frappe.db.sql("select employee from `tabHRIS Employee Pay` where pay_type='Bulanan' and effective_to is null limit 1")
    if not b:
        print("SKIP: tidak ada karyawan Bulanan")
        return
    B = b[0][0]

    def buat(**kw):
        d = {"doctype": HEC, "status": "Berlaku", "is_active": 1, "reason": "uji K-140", "employee": B, "component": "TJ_MAKAN"}
        d.update(kw)
        doc = frappe.get_doc(d)
        doc.insert(ignore_permissions=True)
        return doc

    try:
        frappe.db.set_value(KATALOG, "TJ_MAKAN", {"payment_basis": "Per Hari Hadir", "is_active": 1})
        r = hitung_tunjangan_karyawan(B, "TJ_MAKAN", "Bulanan", AWAL, AKHIR, HADIR)
        cek("D1 Bulanan Per Hari Hadir tanpa HEC: Rp0 dan tanpa galat", r.get("jumlah") == 0 and not r.get("error"), r)
        h = buat(amount=25000, date_from=AWAL, date_to=AKHIR)
        r = hitung_tunjangan_karyawan(B, "TJ_MAKAN", "Bulanan", AWAL, AKHIR, HADIR)
        cek("D2 HEC Berlaku 25.000: 10 hari Hadir x 25.000", r.get("jumlah") == 250000 and not r.get("error"), r)
        h.status = "Tidak Berlaku"
        h.amount = 0
        h.reason = "uji K-140 diubah"
        h.save(ignore_permissions=True)
        r = hitung_tunjangan_karyawan(B, "TJ_MAKAN", "Bulanan", AWAL, AKHIR, HADIR)
        cek("D3 HEC diubah menjadi Tidak Berlaku: Rp0", r.get("jumlah") == 0 and not r.get("error"), r)
        frappe.db.set_value(KATALOG, "TJ_MAKAN", "payment_basis", "Per Bulan")
        r = hitung_tunjangan_karyawan(B, "TJ_MAKAN", "Bulanan", AWAL, AKHIR, [])
        cek("D4 Per Bulan dengan HEC Tidak Berlaku penuh: Rp0", r.get("jumlah") == 0 and not r.get("error"), r)
    finally:
        frappe.db.rollback()
    print("OK %d, GAGAL %d (data uji di-rollback)" % (sum(hasil), len(hasil) - sum(hasil)))
