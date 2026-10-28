import frappe
from frappe import _


@frappe.whitelist()
def get_audit_trail(doctype, name):
	if not str(doctype).startswith("HRIS "):
		frappe.throw(
			_("Audit trail hanya tersedia untuk DocType HRIS."),
			frappe.PermissionError,
		)
	frappe.has_permission(doctype, "read", doc=name, throw=True)

	meta = frappe.get_meta(doctype)
	created = frappe.db.get_value(doctype, name, ["creation", "owner"], as_dict=True)
	if not created:
		return []

	rows = []
	versions = frappe.get_all(
		"Version",
		filters={"ref_doctype": doctype, "docname": name},
		fields=["creation", "owner", "data"],
		order_by="creation asc",
	)
	for version in versions:
		data = frappe.parse_json(version.data) or {}
		changed = data.get("changed") or []
		reason = ""
		for item in changed:
			if item[0] == "change_reason":
				reason = item[2] or ""
		for fieldname, old, new in changed:
			if fieldname == "change_reason":
				continue
			df = meta.get_field(fieldname)
			rows.append(
				{
					"time": _format_time(version.creation),
					"user": frappe.utils.get_fullname(version.owner),
					"field": df.label if df else fieldname,
					"old": "" if old is None else str(old),
					"new": "" if new is None else str(new),
					"reason": reason,
				}
			)

	rows.reverse()
	rows.append(
		{
			"time": _format_time(created.creation),
			"user": frappe.utils.get_fullname(created.owner),
			"field": _("(dokumen dibuat)"),
			"old": "",
			"new": "",
			"reason": "",
		}
	)
	return rows


def _format_time(value):
	return frappe.utils.format_datetime(value, "dd-MM-yyyy HH:mm:ss")
