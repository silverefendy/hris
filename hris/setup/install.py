"""Setup dan seed data app HRIS (dipanggil dari hooks after_install / after_migrate)."""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

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


def _employee_anchor():
	"""Field Employee tempat Custom Field HRIS disisipkan (setelah department)."""
	meta = frappe.get_meta("Employee")
	if meta.has_field("department"):
		return "department"
	return meta.fields[-1].fieldname


def ensure_custom_fields():
	"""Buat Custom Field HRIS di Employee. Idempoten: yang sudah ada dilewati."""
	if not frappe.db.exists("DocType", "HRIS Employee Group"):
		return
	definitions = [
		{
			"fieldname": "hris_employee_group",
			"fieldtype": "Link",
			"label": "Grup Karyawan HRIS",
			"options": "HRIS Employee Group",
			"in_standard_filter": 1,
		},
		{
			"fieldname": "hris_pay_type",
			"fieldtype": "Select",
			"label": "Jenis Karyawan (Bulanan/Harian)",
			"options": "Bulanan\nHarian",
			"in_standard_filter": 1,
		},
	]
	previous = _employee_anchor()
	missing = []
	for definition in definitions:
		fieldname = definition["fieldname"]
		exists = frappe.db.exists(
			"Custom Field", {"dt": "Employee", "fieldname": fieldname}
		)
		if not exists:
			missing.append(dict(definition, insert_after=previous))
		previous = fieldname
	if missing:
		create_custom_fields({"Employee": missing})


def after_install():
	ensure_roles()
	ensure_custom_fields()


def after_migrate():
	ensure_roles()
	ensure_custom_fields()
