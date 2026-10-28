import frappe
from frappe import _

NON_VALUE_FIELDS = ("Section Break", "Column Break", "Tab Break", "HTML", "Button")


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
		when = _format_time(version.creation)
		who = frappe.utils.get_fullname(version.owner)

		changed = data.get("changed") or []
		reason = ""
		for item in changed:
			if item[0] == "change_reason":
				reason = item[2] or ""

		# Perubahan field biasa
		for fieldname, old, new in changed:
			if fieldname == "change_reason":
				continue
			df = meta.get_field(fieldname)
			label = df.label if df else fieldname
			rows.append(_row(when, who, label, old, new, reason))

		# Baris tabel anak yang ditambah
		for table_field, row_data in data.get("added") or []:
			label = _("{0} - baris ditambah").format(_table_label(meta, table_field))
			rows.append(_row(when, who, label, "", _row_summary(meta, table_field, row_data), reason))

		# Baris tabel anak yang dihapus
		for table_field, row_data in data.get("removed") or []:
			label = _("{0} - baris dihapus").format(_table_label(meta, table_field))
			rows.append(_row(when, who, label, _row_summary(meta, table_field, row_data), "", reason))

		# Baris tabel anak yang diubah
		for item in data.get("row_changed") or []:
			if len(item) < 4:
				continue
			table_field, row_index, row_name, row_changes = item[0], item[1], item[2], item[3]
			child_meta = _child_meta(meta, table_field)
			number = _row_number(row_index)
			for fieldname, old, new in row_changes or []:
				child_df = child_meta.get_field(fieldname) if child_meta else None
				child_label = child_df.label if child_df else fieldname
				label = "{0} ({1} {2}): {3}".format(
					_table_label(meta, table_field), _("baris"), number, child_label
				)
				rows.append(_row(when, who, label, old, new, reason))

	rows.reverse()
	rows.append(_row(_format_time(created.creation), frappe.utils.get_fullname(created.owner), _("(dokumen dibuat)"), "", "", ""))
	return rows


def _row(when, who, field, old, new, reason):
	return {
		"time": when,
		"user": who,
		"field": field,
		"old": "" if old is None else str(old),
		"new": "" if new is None else str(new),
		"reason": reason,
	}


def _table_label(meta, table_field):
	df = meta.get_field(table_field)
	return df.label if df else table_field


def _child_meta(meta, table_field):
	df = meta.get_field(table_field)
	if df and df.options:
		return frappe.get_meta(df.options)
	return None


def _row_number(index):
	try:
		return int(index) + 1
	except (TypeError, ValueError):
		return index


def _row_summary(meta, table_field, row_data):
	child_meta = _child_meta(meta, table_field)
	row_data = row_data or {}
	parts = []
	if child_meta:
		for df in child_meta.fields:
			if df.fieldtype in NON_VALUE_FIELDS:
				continue
			value = row_data.get(df.fieldname)
			if value is None or value == "":
				continue
			parts.append("{0}: {1}".format(df.label or df.fieldname, value))
	return "; ".join(parts)


def _format_time(value):
	return frappe.utils.format_datetime(value, "dd-MM-yyyy HH:mm:ss")
