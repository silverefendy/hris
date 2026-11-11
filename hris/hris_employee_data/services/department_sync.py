"""Sinkron satu arah: HRIS Department -> Department ERPNext (K-136 tahap 3).

Nama dan Company tidak boleh berubah setelah tersinkron (dijaga di controller).
Pemakaian adopsi 164 Department yang sudah ada (dari folder sites):
  ../env/bin/python ../apps/hris/hris/hris_employee_data/services/department_sync.py coba
  ../env/bin/python ../apps/hris/hris/hris_employee_data/services/department_sync.py adopsi
Variabel SITE menentukan site (bawaan hris-uji.local); site lain ditolak
kecuali IZINKAN_SITE_LAIN=ya.
"""

import os
import sys

import frappe
from frappe import _
from frappe.utils import cstr, now_datetime, strip_html

DT = "HRIS Department"
SAVEPOINT = "sinkron_department"

ROLE_SINKRON_ULANG = {
    "HRIS HR Admin",
    "HRIS Manager",
    "System Manager",
}


def _akar_erpnext():
    baris = frappe.db.sql("select name from `tabDepartment` where ifnull(parent_department, '') = ''")
    if len(baris) != 1:
        frappe.throw(_("Akar Department ERPNext ditemukan {0} (harus 1).").format(len(baris)))
    return baris[0][0]


def _induk_erpnext(doc):
    induk = frappe.db.get_value(DT, doc.parent_department, "erpnext_department")
    if not induk:
        frappe.throw(_("Induk {0} belum tersinkron ke Department ERPNext.").format(doc.parent_department))
    return induk


def _terapkan(doc):
    if not doc.parent_department:
        return "Akar dipetakan ke Department ERPNext", _akar_erpnext()
    nilai = {
        "parent_department": _induk_erpnext(doc),
        "is_group": doc.is_group,
        "disabled": 0 if doc.is_active else 1,
    }
    if not doc.erpnext_department:
        dep = frappe.new_doc("Department")
        dep.update({"department_name": doc.department_name, "company": doc.company})
        dep.update(nilai)
        dep.insert(ignore_permissions=True)
        return "Department ERPNext dibuat: " + dep.name, dep.name
    dep = frappe.get_doc("Department", doc.erpnext_department)
    berubah = {k: v for k, v in nilai.items() if cstr(dep.get(k)) != cstr(v)}
    if not berubah:
        return "Tidak ada perubahan", dep.name
    dep.update(berubah)
    dep.save(ignore_permissions=True)
    return "Department ERPNext diperbarui (%d field)" % len(berubah), dep.name


def _catat(doc, status, pesan, erpnext=None):
    nilai = {"sync_status": status, "last_sync": now_datetime(), "sync_error": pesan}
    if erpnext:
        nilai["erpnext_department"] = erpnext
    # set_value (bukan doc.db_set) agar perubahan ini tidak masuk Audit Trail
    frappe.db.set_value(DT, doc.name, nilai, update_modified=False)


def sinkron_dokumen(doc):
    """Sinkronkan satu dokumen. Galat sinkron tidak dilempar; dicatat di sync_error."""
    jumlah_pesan = len(frappe.local.message_log)
    frappe.db.savepoint(SAVEPOINT)
    try:
        hasil, nama = _terapkan(doc)
    except Exception as e:
        frappe.db.rollback(save_point=SAVEPOINT)
        frappe.local.message_log = frappe.local.message_log[:jumlah_pesan]
        pesan = strip_html(cstr(e))[:500]
        _catat(doc, "Gagal", pesan)
        return "Gagal: " + pesan
    _catat(doc, "Berhasil", None, nama)
    return hasil


@frappe.whitelist()
def sinkron_ulang(nama):
    """Dipanggil tombol Sinkron Ulang. Hanya role tertentu."""
    if not (set(frappe.get_roles()) & ROLE_SINKRON_ULANG):
        frappe.throw(_("Anda tidak berhak menjalankan Sinkron Ulang."), frappe.PermissionError)
    frappe.has_permission(DT, "write", doc=nama, throw=True)
    return sinkron_dokumen(frappe.get_doc(DT, nama))


def _adopsi():
    """Cocokkan HRIS Department yang belum tertaut dengan Department ERPNext bernama sama."""
    laporan = {"diadopsi": 0, "beda": []}
    namanama = frappe.get_all(
        DT, filters={"erpnext_department": ["is", "not set"]}, order_by="lft asc", pluck="name"
    )
    for nama in namanama:
        doc = frappe.get_doc(DT, nama)
        if not doc.parent_department:
            erp = _akar_erpnext()
        else:
            erp = nama
            ada = frappe.db.get_value(
                "Department", erp, ["company", "parent_department", "is_group", "disabled"], as_dict=True
            )
            induk = frappe.db.get_value(DT, doc.parent_department, "erpnext_department")
            if not ada:
                laporan["beda"].append((nama, "tidak ada di ERPNext"))
                continue
            salah = []
            if cstr(ada.company) != cstr(doc.company):
                salah.append("company")
            if cstr(ada.parent_department) != cstr(induk):
                salah.append("induk")
            if bool(ada.is_group) != bool(doc.is_group):
                salah.append("is_group")
            if bool(ada.disabled) != (not doc.is_active):
                salah.append("disabled")
            if salah:
                laporan["beda"].append((nama, ",".join(salah)))
                continue
        _catat(doc, "Berhasil", None, erp)
        laporan["diadopsi"] += 1
    return laporan


def jalankan(mode):
    site = os.environ.get("SITE", "hris-uji.local")
    if site != "hris-uji.local" and os.environ.get("IZINKAN_SITE_LAIN") != "ya":
        raise SystemExit("BERHENTI: site %s ditolak (set IZINKAN_SITE_LAIN=ya bila sengaja)" % site)
    frappe.init(site=site, sites_path=".")
    frappe.connect()
    frappe.set_user("Administrator")
    ok = False
    try:
        lap = _adopsi()
        total = frappe.db.count(DT)
        tertaut = frappe.db.count(DT, {"erpnext_department": ["is", "set"]})
        print("Site                : %s (mode %s)" % (site, mode))
        print("HRIS Department     : %d" % total)
        print("Diadopsi            : %d" % lap["diadopsi"])
        print("Tidak cocok         : %d %s" % (len(lap["beda"]), lap["beda"][:10]))
        print("Tertaut seluruhnya  : %d dari %d" % (tertaut, total))
        ok = not lap["beda"] and tertaut == total
        print("HASIL: " + ("OK" if ok else "GAGAL"))
        if mode == "adopsi" and ok:
            frappe.db.commit()
            print("DISIMPAN (commit)")
        else:
            frappe.db.rollback()
            print("DI-ROLLBACK (tidak ada yang tersimpan)")
    finally:
        frappe.destroy()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("coba", "adopsi"):
        raise SystemExit("Pemakaian: department_sync.py coba|adopsi")
    jalankan(sys.argv[1])
