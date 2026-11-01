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

# Definisi disalin dari server yang sudah berjalan (bukan ditebak).
# attendance_device_id adalah field standar HRMS, jadi tidak dibuat di sini.
EMPLOYEE_FIELDS = [
	{
		"fieldname": "hris_employee_group",
		"fieldtype": "Link",
		"label": "Grup Karyawan HRIS",
		"options": "HRIS Employee Group",
		"insert_after": "department",
		"in_standard_filter": 1,
	},
	{
		"fieldname": "hris_pay_type",
		"fieldtype": "Select",
		"label": "Jenis Karyawan (Bulanan/Harian)",
		"options": "Bulanan\nHarian",
		"insert_after": "hris_employee_group",
		"in_standard_filter": 1,
	},
	{
		"fieldname": "hris_data_status",
		"fieldtype": "Select",
		"label": "Status Data HRIS",
		"options": "\nLengkap\nPerlu Dilengkapi",
		"insert_after": "attendance_device_id",
		"in_standard_filter": 1,
		"no_copy": 1,
	},
	{
		"fieldname": "hris_data_note",
		"fieldtype": "Small Text",
		"label": "Catatan Data HRIS",
		"insert_after": "hris_data_status",
		"no_copy": 1,
	},
	{
		"fieldname": "hris_payroll_code",
		"fieldtype": "Data",
		"label": "Kode di Aplikasi Gaji",
		"insert_after": "hris_data_note",
		"read_only": 1,
		"no_copy": 1,
	},
	{
		"fieldname": "hris_payroll_code_alt",
		"fieldtype": "Data",
		"label": "Kode Alt di Aplikasi Gaji (referensi)",
		"insert_after": "hris_payroll_code",
		"read_only": 1,
		"no_copy": 1,
	},
]

DEPARTMENT_FIELDS = [
	{
		"fieldname": "hris_device_dept_id",
		"fieldtype": "Data",
		"label": "HRIS Device Dept ID",
		"insert_after": "company",
		"unique": 1,
		"read_only": 1,
		"no_copy": 1,
	},
]

# (fieldname, property, value) pada Employee; semuanya bertipe Check.
EMPLOYEE_PROPERTY_SETTERS = [
	("employee_number", "hidden", "1"),
	("employee_number", "reqd", "0"),
	("naming_series", "reqd", "1"),
	("naming_series", "hidden", "0"),
]


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


def _missing_fields(doctype, definitions):
	"""Kembalikan definisi yang belum ada di site. Yang sudah ada tidak disentuh."""
	if not frappe.db.exists("DocType", doctype):
		return []
	meta = frappe.get_meta(doctype)
	fallback = meta.fields[-1].fieldname
	added = set()
	missing = []
	for definition in definitions:
		fieldname = definition["fieldname"]
		if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": fieldname}):
			continue
		if definition["fieldtype"] == "Link" and not frappe.db.exists(
			"DocType", definition["options"]
		):
			continue
		item = dict(definition)
		anchor = item["insert_after"]
		if not (meta.has_field(anchor) or anchor in added):
			item["insert_after"] = fallback
		added.add(fieldname)
		missing.append(item)
	return missing


def ensure_custom_fields():
	"""Buat Custom Field HRIS di Employee dan Department. Idempoten."""
	to_create = {}
	employee = _missing_fields("Employee", EMPLOYEE_FIELDS)
	if employee:
		to_create["Employee"] = employee
	department = _missing_fields("Department", DEPARTMENT_FIELDS)
	if department:
		to_create["Department"] = department
	if to_create:
		create_custom_fields(to_create)


def ensure_property_setters():
	"""Buat Property Setter Employee yang belum ada. Yang sudah ada tidak ditimpa."""
	for fieldname, prop, value in EMPLOYEE_PROPERTY_SETTERS:
		exists = frappe.db.exists(
			"Property Setter",
			{"doc_type": "Employee", "field_name": fieldname, "property": prop},
		)
		if exists:
			continue
		frappe.make_property_setter(
			{
				"doctype": "Employee",
				"fieldname": fieldname,
				"property": prop,
				"value": value,
				"property_type": "Check",
			}
		)


def after_install():
	ensure_roles()
	ensure_custom_fields()
	ensure_property_setters()


def after_migrate():
	ensure_roles()
	ensure_custom_fields()
	ensure_property_setters()
