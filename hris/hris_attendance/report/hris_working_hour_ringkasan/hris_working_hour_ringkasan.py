import frappe
from frappe import _
from frappe.utils import date_diff, flt, getdate

ALLOWED_ROLES = {"HRIS HR Admin", "HRIS Manager", "System Manager"}
MAX_DAYS = 93


def execute(filters=None):
	filters = frappe._dict(filters or {})
	_check(filters)
	return get_columns(), get_data(filters)


def _check(filters):
	if not (ALLOWED_ROLES & set(frappe.get_roles())):
		frappe.throw(
			_("Hanya HRIS HR Admin, HRIS Manager, atau System Manager yang boleh membuka laporan ini."),
			frappe.PermissionError,
		)
	if not filters.get("from_date") or not filters.get("to_date"):
		frappe.throw(_("Dari Tanggal dan Sampai Tanggal wajib diisi."))
	start, end = getdate(filters.from_date), getdate(filters.to_date)
	if end < start:
		frappe.throw(_("Sampai Tanggal tidak boleh sebelum Dari Tanggal."))
	if date_diff(end, start) + 1 > MAX_DAYS:
		frappe.throw(_("Rentang maksimal {0} hari.").format(MAX_DAYS))


def get_columns():
	return [
		{"fieldname": "employee", "label": _("Karyawan"), "fieldtype": "Link", "options": "Employee", "width": 120},
		{"fieldname": "employee_name", "label": _("Nama"), "fieldtype": "Data", "width": 180},
		{"fieldname": "department", "label": _("Department"), "fieldtype": "Link", "options": "Department", "width": 150},
		{"fieldname": "scheduled_days", "label": _("Hari Terjadwal"), "fieldtype": "Int", "width": 100},
		{"fieldname": "present_days", "label": _("Hadir"), "fieldtype": "Int", "width": 70},
		{"fieldname": "incomplete_days", "label": _("Tidak Lengkap"), "fieldtype": "Int", "width": 100},
		{"fieldname": "absent_days", "label": _("Tidak Hadir"), "fieldtype": "Int", "width": 90},
		{"fieldname": "off_days", "label": _("Libur"), "fieldtype": "Int", "width": 70},
		{"fieldname": "late_minutes", "label": _("Telat (menit)"), "fieldtype": "Int", "width": 100},
		{"fieldname": "early_leave_minutes", "label": _("Pulang Cepat (menit)"), "fieldtype": "Int", "width": 130},
		{"fieldname": "deduction_hours", "label": _("Potongan (jam)"), "fieldtype": "Float", "precision": 2, "width": 110},
		{"fieldname": "overtime_minutes", "label": _("Lembur (menit)"), "fieldtype": "Int", "width": 110},
		{"fieldname": "effective_hours", "label": _("Jam Efektif"), "fieldtype": "Float", "precision": 2, "width": 100},
		{"fieldname": "adjustment_hours", "label": _("Penyesuaian HRD (jam)"), "fieldtype": "Float", "precision": 2, "width": 140},
		{"fieldname": "final_effective_hours", "label": _("Jam Final"), "fieldtype": "Float", "precision": 2, "width": 100},
		{"fieldname": "pending_review", "label": _("Perlu Ditinjau"), "fieldtype": "Int", "width": 110},
	]


def get_data(filters):
	conditions = ["work_date between %(from_date)s and %(to_date)s"]
	values = {"from_date": getdate(filters.from_date), "to_date": getdate(filters.to_date)}
	for key in ("company", "department", "employee_group", "employee"):
		if filters.get(key):
			conditions.append("{0} = %({0})s".format(key))
			values[key] = filters[key]

	rows = frappe.db.sql(
		"""
		select
			employee,
			max(employee_name) as employee_name,
			max(department) as department,
			sum(status in ('Hadir', 'Tidak Lengkap', 'Tidak Hadir')) as scheduled_days,
			sum(status = 'Hadir') as present_days,
			sum(status = 'Tidak Lengkap') as incomplete_days,
			sum(status = 'Tidak Hadir') as absent_days,
			sum(status = 'Libur') as off_days,
			sum(late_minutes) as late_minutes,
			sum(early_leave_minutes) as early_leave_minutes,
			sum(ifnull(late_deduction_hours, 0) + ifnull(early_leave_deduction_hours, 0)) as deduction_hours,
			sum(overtime_minutes) as overtime_minutes,
			sum(effective_hours) as effective_hours,
			sum(adjustment_hours) as adjustment_hours,
			sum(final_effective_hours) as final_effective_hours,
			sum(review_status = 'Menunggu') as pending_review
		from `tabHRIS Working Hour`
		where {where}
		group by employee
		order by employee_name, employee
		""".format(where=" and ".join(conditions)),
		values,
		as_dict=True,
	)

	int_keys = (
		"scheduled_days", "present_days", "incomplete_days", "absent_days", "off_days",
		"late_minutes", "early_leave_minutes", "overtime_minutes", "pending_review",
	)
	float_keys = ("deduction_hours", "effective_hours", "adjustment_hours", "final_effective_hours")
	for row in rows:
		for k in int_keys:
			row[k] = int(row[k] or 0)
		for k in float_keys:
			row[k] = flt(row[k], 2)
	return rows
