"""Uji HRIS Department Rule (K-136 tahap 5a).
Jalankan dari folder sites setelah migrate: ../env/bin/python <path ini>.
Data uji memakai tanggal 2099 dan dihapus di akhir. Catatan: nomor DR- yang terpakai uji tidak kembali (ada celah nomor di site uji)."""

import re
import sys

import frappe
from frappe.utils import nowdate
from frappe.utils.nestedset import get_root_of

from hris.hris_payroll.services.department_rule import pilih_nilai, resolve

SITE = "hris-uji.local"
RULE = "HRIS Department Rule"
P = "overtime_multiplier"

frappe.init(site=SITE, sites_path=".")
frappe.connect()
hasil = []
dibuat = []


def cek(nama, kondisi, rinci=""):
    hasil.append(bool(kondisi))
    print(("OK      " if kondisi else "GAGAL   ") + nama + ("" if kondisi or not rinci else "  " + str(rinci)))


def buat(dept, tgl, nilai, aktif=1):
    d = frappe.get_doc({"doctype": RULE, "department": dept, "effective_from": tgl,
                        "is_active": aktif, "overtime_multiplier": nilai}).insert(ignore_permissions=True)
    dibuat.append(d.name)
    return d


def gagal_validasi(fn):
    try:
        fn()
    except frappe.ValidationError:
        return True
    return False


try:
    rantai = ["C", "B", "A"]
    aturan = [
        {"name": "R1", "department": "A", "effective_from": "2026-01-01", P: 1.5},
        {"name": "R2", "department": "B", "effective_from": "2026-12-01", P: 2.0},
        {"name": "R3", "department": "C", "effective_from": "2026-01-01", P: 0},
    ]
    cek("M1 kosong di C, B menimpa", (pilih_nilai(rantai, aturan, "2026-12-05", P) or {}).get("nilai") == 2.0)
    cek("M2 B belum berlaku, naik ke akar", (pilih_nilai(rantai, aturan, "2026-11-20", P) or {}).get("nilai") == 1.5)
    cek("M3 tanpa aturan = None", pilih_nilai(rantai, [], "2026-11-20", P) is None)
    aturan2 = [
        {"name": "R1", "department": "A", "effective_from": "2026-01-01", P: 1.5},
        {"name": "R4", "department": "A", "effective_from": "2026-06-01", P: 1.75},
    ]
    cek("M4 versi terbaru yang berlaku menang", (pilih_nilai(["A"], aturan2, "2026-07-01", P) or {}).get("nilai") == 1.75)

    akar = get_root_of("HRIS Department")
    daun = frappe.get_all("HRIS Department", filters={"is_group": 0}, pluck="name", limit=1)[0]
    r1 = buat(akar, "2099-01-01", 3.5)
    r2 = buat(daun, "2099-06-01", 4.5)
    cek("N1 daun sebelum aturan daun, ikut akar", resolve(daun, "2099-03-01")["nilai"] == 3.5)
    cek("N2 daun setelah aturan daun, menimpa", resolve(daun, "2099-07-01")["nilai"] == 4.5)
    cek("N3 akar tidak terpengaruh aturan daun", resolve(akar, "2099-07-01")["nilai"] == 3.5)
    cek("N4 duplikat aktif ditolak", gagal_validasi(lambda: buat(akar, "2099-01-01", 9)))
    buat(daun, "2099-09-01", 9.0, aktif=0)
    cek("N5 aturan nonaktif diabaikan", resolve(daun, "2099-10-01")["nilai"] == 4.5)
    yymm = nowdate()[2:4] + nowdate()[5:7]
    cek("N6 format nama DR-YYMM-####", re.match(r"^DR-\d{4}-\d{4}$", r1.name) and r1.name[3:7] == yymm, r1.name)
    cek("N7 nomor urut naik", int(r2.name[-4:]) > int(r1.name[-4:]), (r1.name, r2.name))
    cek("N8 parameter tidak dikenal ditolak", gagal_validasi(lambda: resolve(daun, "2099-03-01", "tarif_x")))
    cek("N9 pengali negatif ditolak", gagal_validasi(lambda: buat(daun, "2099-12-01", -1)))
finally:
    for n in dibuat:
        frappe.delete_doc(RULE, n, force=1, ignore_permissions=True)
    frappe.db.commit()
    print("INFO    data uji dihapus: %d; sisa aturan 2099: %d" % (
        len(dibuat), frappe.db.count(RULE, {"effective_from": [">=", "2099-01-01"]})))
    frappe.destroy()

print("HASIL OK %d GAGAL %d" % (sum(hasil), len(hasil) - sum(hasil)))
sys.exit(0 if all(hasil) else 1)
