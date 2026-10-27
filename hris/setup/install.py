"""Setup dan seed data app HRIS (dipanggil dari hooks after_install / after_migrate)."""

import frappe

HRIS_ROLES = (
    "HRIS Attendance Operator",
    "HRIS Attendance Supervisor",
    "HRIS HR Admin",
    "HRIS Payroll User",
    "HRIS Payroll Admin",
    "HRIS Manager",
)


def ensure_roles():
    """Buat role HRIS yang belum ada. Idempoten: role yang sudah ada dilewati."""
    for role_name in HRIS_ROLES:
        if frappe.db.exists("Role", role_name):
            continue
        frappe.get_doc(
            {
                "doctype": "Role",
                "role_name": role_name,
                "desk_access": 1,
            }
        ).insert(ignore_permissions=True)


def after_install():
    ensure_roles()


def after_migrate():
    ensure_roles()
