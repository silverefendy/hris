import frappe
from frappe import _


def validate_employee_group(doc, method=None):
	"""Hook Employee.validate: company grup harus sama dengan company karyawan."""
	group = doc.get("hris_employee_group")
	if not group:
		return
	group_company = frappe.db.get_value("HRIS Employee Group", group, "company")
	if group_company and doc.company and group_company != doc.company:
		frappe.throw(
			_("Grup {0} milik company {1}, sedangkan karyawan ini milik company {2}.").format(
				group, group_company, doc.company
			)
		)
