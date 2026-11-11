"""K-136 tahap 5a: aturan akar HRIS Department Rule (pengali lembur 1.0 = nilai konstanta lama PENGALI_LEMBUR)."""

import frappe
from frappe.utils.nestedset import get_root_of

RULE = "HRIS Department Rule"
TANGGAL = "2000-01-01"
NILAI = 1.0


def execute():
    akar = get_root_of("HRIS Department")
    if not akar:
        print("Patch aturan akar dilewati: HRIS Department akar belum ada.")
        return
    ada = frappe.db.exists(RULE, {"department": akar, "is_active": 1, "overtime_multiplier": [">", 0]})
    if ada:
        print("Patch aturan akar dilewati: sudah ada {0}.".format(ada))
        return
    doc = frappe.get_doc({
        "doctype": RULE,
        "department": akar,
        "effective_from": TANGGAL,
        "is_active": 1,
        "overtime_multiplier": NILAI,
    }).insert(ignore_permissions=True)
    print("Aturan akar dibuat: {0} ({1}, pengali {2})".format(doc.name, akar, NILAI))
