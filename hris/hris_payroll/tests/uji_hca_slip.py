"""K-140 E3: uji penyambungan HCA ke perhitungan. Bagian murni, lalu database (di-rollback).

Jalankan:
bench --site hris-uji.local execute hris.hris_payroll.tests.uji_hca_slip.jalankan
"""
from datetime import date

import frappe

from hris.hris_payroll.services import payroll_summary as ps
from hris.hris_payroll.services.cakupan_komponen import gabung_semua, susun_tingkat
from hris.hris_payroll.services.komponen_slip import hitung_tunjangan_karyawan

HEC = "HRIS Employee Component"
HCA = "HRIS Component Assignment"
KATALOG = "HRIS Pay Component"
EMP = "HRIS Employee"
AWAL, AKHIR = "2030-03-01", "2030-03-31"
HADIR = [date(2030, 3, d) for d in range(1, 11)]
ALASAN = "uji K-140 E3"


def b(nama, dari=AWAL, sampai=AKHIR, anak=0, status="Berlaku"):
    return {"name": nama, "status": status, "amount": 0, "date_from": dari, "date_to": sampai, "include_children": anak}


def rentang(daftar):
    return [(x["name"], str(x["date_from"]), str(x["date_to"])) for x in daftar]


def jalankan():
    hasil = []

    def cek(nama, kondisi, info=""):
        hasil.append(bool(kondisi))
        print(("OK     " if kondisi else "GAGAL  ") + nama + ((" | " + str(info)[:250]) if (not kondisi and info != "") else ""))

    bg = [b("G1")]
    t = susun_tingkat("D1", ["D0"], "GRP", "Grup", bg, {"D1": [b("A")]}, True)
    cek("T1 Grup aktif dengan baris: hanya tingkat Grup", t == [bg], t)
    t = susun_tingkat("D1", ["D0"], "GRP", "Grup", [], {"D1": [b("A")]}, True)
    cek("T2 Grup tanpa baris: jatuh ke Department", len(t) == 1 and t[0][0]["name"] == "A", t)
    t = susun_tingkat("D1", ["D0"], "GRP", "Grup", bg, {"D1": [b("A")]}, False)
    cek("T3 Grup tidak aktif: jatuh ke Department", len(t) == 1 and t[0][0]["name"] == "A", t)
    t = susun_tingkat("D1", ["D0"], None, "Department", [], {"D1": [b("A")], "D0": [b("P1", anak=1), b("P2", anak=0)]}, False)
    cek("T4 induk hanya yang include_children", [x["name"] for r in t for x in r] == ["A", "P1"], t)
    t = susun_tingkat("D1", ["D0"], None, "Department", [], {"D1": [b("A")], "D0": [b("P1", anak=1)]}, False)
    cek("T5 anak menang atas induk pada tanggal yang sama", rentang(gabung_semua([], t)) == [("A", AWAL, AKHIR)], rentang(gabung_semua([], t)))
    h = [{"name": "HEC-1", "status": "Tidak Berlaku", "amount": 0, "date_from": "2030-03-05", "date_to": "2030-03-07"}]
    g = gabung_semua(h, t)
    cek("T6 HEC karyawan menang atas semua tingkat", [x[0] for x in rentang(g)] == ["A", "HEC-1", "A"], rentang(g))

    r = frappe.db.sql(
        "select e.name, e.department from `tabHRIS Employee` e "
        "join `tabHRIS Department` d on d.name = e.department "
        "join `tabHRIS Employee Pay` p on p.employee = e.name and p.pay_type = 'Bulanan' and p.effective_to is null "
        "where d.company is not null and e.status = 'Aktif' limit 1"
    )
    g_ = frappe.db.sql("select name from `tabHRIS Employee Group` where company is not null and is_active = 1 limit 1")
    if not r or not g_:
        print("SKIP D1-D6: tidak ada karyawan Bulanan aktif ber-Department atau Grup aktif ber-Company")
        print("OK %d, GAGAL %d (hanya bagian murni)" % (sum(hasil), len(hasil) - sum(hasil)))
        return
    B, DEP = r[0]
    G = g_[0][0]
    awal_hca, awal_hec = frappe.db.count(HCA), frappe.db.count(HEC)

    def hec_baru(status, jumlah, dari, sampai):
        d = frappe.get_doc({"doctype": HEC, "employee": B, "component": "TJ_MAKAN", "status": status, "amount": jumlah,
                            "date_from": dari, "date_to": sampai, "is_active": 1, "reason": ALASAN})
        d.insert(ignore_permissions=True)
        return d

    def hca_baru(**kw):
        d = {"doctype": HCA, "scope_type": "Department", "department": DEP, "component": "TJ_MAKAN", "status": "Berlaku",
             "amount": 25000, "date_from": AWAL, "date_to": AKHIR, "is_active": 1, "reason": ALASAN, "include_children": 1}
        d.update(kw)
        doc = frappe.get_doc(d)
        doc.insert(ignore_permissions=True)
        return doc

    def hitung():
        return hitung_tunjangan_karyawan(B, "TJ_MAKAN", "Bulanan", AWAL, AKHIR, HADIR)

    try:
        frappe.db.set_value(KATALOG, "TJ_MAKAN", {"payment_basis": "Per Hari Hadir", "is_active": 1})
        frappe.db.set_value(EMP, B, "rule_follow", "Department")
        h = hca_baru()
        x = hitung()
        cek("D1 HCA Department saja: 10 hari x 25.000", x.get("jumlah") == 250000 and not x.get("error"), x)
        hec_baru("Tidak Berlaku", 0, "2030-03-05", "2030-03-07")
        x = hitung()
        cek("D2 HEC Tidak Berlaku 3 hari mengalahkan HCA: 7 x 25.000", x.get("jumlah") == 175000, x)
        hec_baru("Berlaku", 10000, "2030-03-08", "2030-03-09")
        x = hitung()
        cek("D3 HEC nominal khusus 2 hari: 5 x 25.000 + 2 x 10.000", x.get("jumlah") == 145000, x)
        s = ps.ambil_data(mode="Per Tanggal", tanggal="2030-03-12", employee=B)
        sel = s["baris"][0]["sel"]["TJ_MAKAN"] if s["baris"] else {}
        cek("D4 Payroll Summary memakai HCA: 25.000", sel.get("jumlah") == 25000, sel)
        frappe.db.set_value(HCA, h.name, "is_active", 0)
        x = hitung()
        cek("D5 HCA dinonaktifkan: tinggal HEC (2 x 10.000)", x.get("jumlah") == 20000, x)
        frappe.db.set_value(EMP, B, {"rule_follow": "Grup", "employee_group": G})
        hca_baru(scope_type="Grup", employee_group=G, department=None, amount=33000)
        x = hitung()
        cek("D6 HCA Grup (rule_follow Grup): 5 x 33.000 + 2 x 10.000", x.get("jumlah") == 185000, x)
    finally:
        frappe.db.rollback()
    cek("D7 rollback: jumlah HCA dan HEC kembali", frappe.db.count(HCA) == awal_hca and frappe.db.count(HEC) == awal_hec,
        (frappe.db.count(HCA), awal_hca, frappe.db.count(HEC), awal_hec))
    print("OK %d, GAGAL %d (data uji di-rollback)" % (sum(hasil), len(hasil) - sum(hasil)))
