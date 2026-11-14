"""K-140 E4: pratinjau karyawan yang terkena satu penetapan HCA (hanya membaca).

klasifikasi() murni. Aturannya meniru susun_tingkat() di cakupan_komponen.py:
- HCA Grup berlaku untuk anggota Grup ber-rule_follow Grup; anggota ber-rule_follow Department ikut Department.
- HCA Department berlaku untuk karyawan di Department itu (dan di bawahnya bila include_children), kecuali yang
  ber-rule_follow Grup dan Grupnya punya HCA sendiri untuk komponen itu (tertutup HCA Grup).
- HEC karyawan tetap menang atas HCA (dilaporkan sebagai "punya penetapan sendiri").
"""
import frappe
from frappe import _
from frappe.utils.nestedset import get_descendants_of

HCA = "HRIS Component Assignment"
EMP = "HRIS Employee"
HEC = "HRIS Employee Component"
DEPT = "HRIS Department"
GRP = "HRIS Employee Group"
CONTOH = 40
BATAS = 5000


def klasifikasi(scope_type, karyawan, grup_dengan_hca):
    """karyawan = [{name, employee_name, employee_group, rule_follow}] (sudah dalam cakupan dan aktif)."""
    dapat, ikut_department, tertutup = [], [], []
    for k in karyawan:
        rf = k.get("rule_follow")
        if scope_type == "Grup":
            (dapat if rf == "Grup" else ikut_department).append(k)
        elif rf == "Grup" and k.get("employee_group") in grup_dengan_hca:
            tertutup.append(k)
        else:
            dapat.append(k)
    return {"dapat": dapat, "ikut_department": ikut_department, "tertutup_grup": tertutup}


def _ringkas(daftar, punya_hec=()):
    return [{"name": k["name"], "employee_name": k.get("employee_name"), "punya_hec": k["name"] in punya_hec}
            for k in daftar[:CONTOH]]


@frappe.whitelist()
def pratinjau(name):
    frappe.has_permission(HCA, "read", doc=name, throw=True)
    h = frappe.get_doc(HCA, name)
    filters = {"status": "Aktif"}
    if h.scope_type == "Grup":
        filters["employee_group"] = h.employee_group
    else:
        daftar = [h.department]
        if h.include_children:
            daftar += list(get_descendants_of(DEPT, h.department, ignore_permissions=True))
        filters["department"] = ["in", daftar]
    karyawan = frappe.get_all(EMP, filters=filters, fields=["name", "employee_name", "employee_group", "rule_follow"],
                              order_by="name asc", limit_page_length=BATAS + 1)
    peringatan = []
    if len(karyawan) > BATAS:
        karyawan = karyawan[:BATAS]
        peringatan.append(_("Cakupan melebihi {0} karyawan; hanya {0} pertama yang dihitung dalam pratinjau.").format(BATAS))
    tumpang = {"component": h.component, "is_active": 1, "date_from": ["<=", h.date_to], "date_to": [">=", h.date_from]}
    grup_hca = set(frappe.get_all(HCA, filters=dict(tumpang, scope_type="Grup"), pluck="employee_group"))
    if grup_hca:
        grup_hca &= set(frappe.get_all(GRP, filters={"name": ["in", list(grup_hca)], "is_active": 1}, pluck="name"))
    punya_hec = set()
    if karyawan:
        punya_hec = set(frappe.get_all(HEC, filters=dict(tumpang, employee=["in", [k["name"] for k in karyawan]]), pluck="employee"))
    r = klasifikasi(h.scope_type, karyawan, grup_hca)
    if not h.is_active:
        peringatan.append(_("Penetapan ini nonaktif, jadi tidak berpengaruh pada gaji."))
    if h.status == "Tidak Berlaku":
        peringatan.append(_("Status Tidak Berlaku: karyawan di bawah ini tidak menerima komponen dari penetapan ini."))
    if h.scope_type == "Grup" and not frappe.db.get_value(GRP, h.employee_group, "is_active"):
        peringatan.append(_("Grup ini nonaktif; penetapan Grup tidak dipakai."))
    return {
        "scope": h.scope_type, "komponen": h.component,
        "jumlah": {"dapat": len(r["dapat"]), "ikut_department": len(r["ikut_department"]),
                   "tertutup_grup": len(r["tertutup_grup"]), "punya_hec": len([k for k in r["dapat"] if k["name"] in punya_hec]),
                   "total_cakupan": len(karyawan)},
        "contoh": {"dapat": _ringkas(r["dapat"], punya_hec), "ikut_department": _ringkas(r["ikut_department"]),
                   "tertutup_grup": _ringkas(r["tertutup_grup"])},
        "peringatan": peringatan,
    }
