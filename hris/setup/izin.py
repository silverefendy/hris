"""Pastikan role HRIS dan role laporan tersedia setelah migrate. Aman dijalankan berulang."""

import frappe

from hris.setup.roles import ensure_roles

# Role laporan di JSON tidak ikut diperbarui oleh migrate, jadi ditambahkan di sini.
ROLE_LAPORAN = {
    "HRIS Working Hour Ringkasan": ["HRIS Payroll Admin", "HRIS Direksi"],
}


def after_migrate():
    ensure_roles()
    ensure_role_laporan()


def ensure_role_laporan():
    """Tambahkan role yang belum ada pada Report. Tidak pernah menghapus role."""
    for laporan, roles in ROLE_LAPORAN.items():
        if not frappe.db.exists("Report", laporan):
            continue
        ada = set(
            frappe.get_all("Has Role", filters={"parenttype": "Report", "parent": laporan}, pluck="role")
        )
        for role in roles:
            if role in ada or not frappe.db.exists("Role", role):
                continue
            frappe.get_doc({
                "doctype": "Has Role",
                "parent": laporan,
                "parenttype": "Report",
                "parentfield": "roles",
                "role": role,
            }).insert(ignore_permissions=True)
        frappe.clear_document_cache("Report", laporan)
    frappe.db.commit()
