import frappe

ROLES_DIBUTUHKAN = [
    "HRIS Payroll Admin",
    "HRIS Payroll Manager",
]


def ensure_roles():
    """Buat role yang belum ada. Aman dijalankan berulang."""
    hasil = []
    for nama in ROLES_DIBUTUHKAN:
        if frappe.db.exists("Role", nama):
            hasil.append("ada: %s" % nama)
            continue
        frappe.get_doc({"doctype": "Role", "role_name": nama, "desk_access": 1}).insert(
            ignore_permissions=True
        )
        hasil.append("dibuat: %s" % nama)
    frappe.db.commit()
    print("\n".join(hasil))
    return hasil
