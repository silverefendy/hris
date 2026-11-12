"""Uji K-136 tahap 4b: _pengali_lembur di payroll_slip. Hanya untuk site uji."""

from unittest import mock

import frappe
from frappe.utils import flt

SITE = "hris-uji.local"
frappe.init(site=SITE, sites_path=".")
frappe.connect()
frappe.set_user("Administrator")

from hris.hris_payroll.services import payroll_slip as ps  # noqa: E402

RULE = "HRIS Department Rule"
RESOLVE = "hris.hris_payroll.services.department_rule.resolve"
ok = 0
gagal = 0
dibuat = []


def cek(kode, kondisi, ket):
    global ok, gagal
    if kondisi:
        ok += 1
        print("OK      {0} {1}".format(kode, ket))
    else:
        gagal += 1
        print("GAGAL   {0} {1}".format(kode, ket))


def ditolak(hasil):
    return hasil[0] is None and bool(hasil[1])


def utama():
    semua = frappe.get_all(RULE, fields=["name", "department", "overtime_multiplier"])
    if not (len(semua) == 1 and semua[0].department == ps.DEPT_AKAR and flt(semua[0].overtime_multiplier) == 1.0):
        print("BERHENTI: uji butuh tepat 1 aturan (akar, 1.0). Ada:", semua)
        return
    cek("S0", True, "hanya aturan akar: {0}".format(semua[0].name))

    kandidat = frappe.get_all("HRIS Department", filters={"name": ["!=", ps.DEPT_AKAR]}, pluck="name", limit=1)
    if not kandidat:
        print("BERHENTI: tidak ada Department selain akar")
        return
    dept = kandidat[0]
    print("INFO    Department uji:", dept)

    nilai, galat = ps._pengali_lembur(None, "2026-11-30")
    cek("T1", galat is None and nilai == 1.0, "tanpa Department memakai akar: {0}, {1}".format(nilai, galat))

    doc = frappe.get_doc({
        "doctype": RULE, "department": dept, "effective_from": "2099-01-01",
        "is_active": 1, "overtime_multiplier": 1.5,
    }).insert(ignore_permissions=True)
    dibuat.append(doc.name)

    nilai, galat = ps._pengali_lembur(dept, "2099-06-30")
    cek("T2", galat is None and nilai == 1.5, "aturan Department berlaku: {0}, {1}".format(nilai, galat))

    nilai, galat = ps._pengali_lembur(dept, "2026-11-30")
    cek("T3", galat is None and nilai == 1.0, "sebelum tanggal berlaku ikut akar: {0}, {1}".format(nilai, galat))

    hasil = ps._pengali_lembur(dept, None)
    cek("T4", ditolak(hasil), "period_end kosong dilewati: {0}".format(hasil))

    hasil = ps._pengali_lembur("DEPARTMENT-TIDAK-ADA-XYZ", "2026-11-30")
    cek("T5", ditolak(hasil), "Department tidak dikenal dilewati: {0}".format(hasil))

    with mock.patch.object(frappe.db, "table_exists", return_value=False):
        hasil = ps._pengali_lembur(dept, None)
    cek("T6", hasil == (ps.PENGALI_LEMBUR, None), "tabel tidak ada memakai konstanta: {0}".format(hasil))

    src = open(ps.__file__, encoding="utf-8").read()
    cek("T7a", "_pengali_lembur(he.department, period.period_end)" in src, "pemanggil terpasang")
    cek("T7b", "pengali=pengali_lembur_slip" in src, "hitung_komponen memakai pengali")
    cek("T7c", "doc.overtime_multiplier = pengali_lembur_slip" in src, "salinan ke slip memakai pengali")
    cek("T7d", "doc.overtime_multiplier = PENGALI_LEMBUR" not in src, "tidak ada lagi salinan konstanta")

    with mock.patch(RESOLVE, return_value={"nilai": 0}):
        hasil = ps._pengali_lembur(dept, "2026-11-30")
    cek("T8a", ditolak(hasil), "nilai 0 dari resolve ditolak: {0}".format(hasil))
    with mock.patch(RESOLVE, return_value=1.5):
        hasil = ps._pengali_lembur(dept, "2026-11-30")
    cek("T8b", ditolak(hasil), "nilai balik bukan dict ditolak: {0}".format(hasil))

    with mock.patch(RESOLVE, side_effect=frappe.ValidationError("tidak ada aturan")):
        hasil = ps._pengali_lembur(dept, "2026-11-30")
    cek("T9a", ditolak(hasil), "ValidationError dari resolve dilewati: {0}".format(hasil))
    with mock.patch(RESOLVE, side_effect=TypeError("contoh")):
        hasil = ps._pengali_lembur(dept, "2026-11-30")
    cek("T9b", ditolak(hasil) and "TypeError" in hasil[1], "galat lain dilewati dengan pesan: {0}".format(hasil))


try:
    utama()
finally:
    for n in dibuat:
        frappe.delete_doc(RULE, n, force=1, ignore_permissions=True)
    frappe.db.commit()
    print("INFO    aturan uji dihapus: {0}; sisa aturan: {1}".format(len(dibuat), frappe.get_all(RULE, pluck="name")))
    frappe.destroy()
print("HASIL OK {0} GAGAL {1}".format(ok, gagal))
