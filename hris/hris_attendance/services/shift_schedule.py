import frappe
from frappe import _
from frappe.utils import add_days, date_diff, getdate

DAYS = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
MAX_RANGE_DAYS = 62


def _group_fieldname():
	# Nama custom field grup di Employee dicari dari meta, bukan ditebak.
	meta = frappe.get_meta("Employee")
	names = [df.fieldname for df in meta.get_link_fields() if df.options == "HRIS Employee Group"]
	if not names:
		frappe.throw(_("Field grup HRIS di Employee tidak ditemukan."))
	return names[0]


def _shift_detail(name):
	if not name:
		return None
	d = frappe.db.get_value(
		"HRIS Shift", name, ["name", "start_time", "end_time", "crosses_midnight"], as_dict=True
	)
	if not d:
		return None
	return {
		"name": d.name,
		"start_time": str(d.start_time or ""),
		"end_time": str(d.end_time or ""),
		"crosses_midnight": 1 if d.crosses_midnight else 0,
	}


def _weekly_row(group, day):
	index = day.weekday()
	for row in group.weekly_schedule or []:
		try:
			start = DAYS.index(row.day_from)
			end = DAYS.index(row.day_to) if row.day_to else start
		except ValueError:
			continue
		covered = list(range(start, end + 1)) if start <= end else list(range(start, 7)) + list(range(0, end + 1))
		if index in covered:
			return row
	return None


def _holiday(day, company):
	rows = frappe.get_all(
		"HRIS Holiday",
		filters={"holiday_date": day},
		fields=["holiday_name", "applies_to_all_companies", "company"],
	)
	for r in rows:
		if r.applies_to_all_companies or r.company == company:
			return r.holiday_name
	return None


def get_schedule_for_date(employee, date):
	day = getdate(date)
	group_field = _group_fieldname()
	emp = frappe.db.get_value("Employee", employee, ["company", group_field], as_dict=True)
	if not emp:
		frappe.throw(_("Karyawan {0} tidak ditemukan.").format(employee))

	result = {
		"employee": employee,
		"date": str(day),
		"source": "Tidak ada",
		"shift": None,
		"shift_detail": None,
		"is_off": 0,
		"is_required": 0,
		"group": emp.get(group_field),
		"rotation": None,
		"day_number": None,
		"assignment": None,
		"borrowed_for_group": None,
	}

	# 1. Shift Assignment aktif
	assignment = frappe.get_all(
		"HRIS Shift Assignment",
		filters={"employee": employee, "is_active": 1, "from_date": ["<=", day], "to_date": [">=", day]},
		fields=["name", "shift", "borrowed_for_group"],
		limit=1,
	)
	if assignment:
		a = assignment[0]
		result.update({"source": "Shift Assignment", "shift": a.shift, "assignment": a.name,
					   "borrowed_for_group": a.borrowed_for_group, "is_required": 1})
	elif result["group"]:
		group = frappe.get_doc("HRIS Employee Group", result["group"])
		if group.is_active:
			if group.schedule_type == "Rotasi":
				# 2. Rotasi grup
				if group.rotation and group.rotation_start_date:
					delta = date_diff(day, group.rotation_start_date)
					if delta >= 0:
						rotation = frappe.get_doc("HRIS Shift Rotation", group.rotation)
						if rotation.pattern:
							row = rotation.pattern[delta % len(rotation.pattern)]
							result.update({
								"source": "Rotasi",
								"rotation": rotation.name,
								"day_number": row.day_number,
								"shift": None if row.is_off else row.shift,
								"is_off": 1 if row.is_off else 0,
								"is_required": 0 if row.is_off else 1,
							})
			else:
				# 3. Jadwal mingguan grup
				row = _weekly_row(group, day)
				if row:
					result.update({"source": "Jadwal Mingguan", "shift": row.shift,
								   "is_required": 1 if row.is_required else 0})

	result["shift_detail"] = _shift_detail(result["shift"])
	holiday_name = _holiday(day, emp.company)
	result["is_holiday"] = 1 if holiday_name else 0
	result["holiday_name"] = holiday_name
	# Assignment pada tanggal libur dianggap masuk kerja; jadwal otomatis tidak.
	result["works"] = 1 if (result["shift"] and (result["source"] == "Shift Assignment" or not holiday_name)) else 0
	return result


@frappe.whitelist()
def get_employee_schedule(employee, from_date, to_date):
	frappe.has_permission("Employee", "read", doc=employee, throw=True)
	start, end = getdate(from_date), getdate(to_date)
	if end < start:
		frappe.throw(_("Tanggal Sampai tidak boleh sebelum Tanggal Dari."))
	if date_diff(end, start) + 1 > MAX_RANGE_DAYS:
		frappe.throw(_("Rentang maksimal {0} hari.").format(MAX_RANGE_DAYS))
	return [get_schedule_for_date(employee, add_days(start, i)) for i in range(date_diff(end, start) + 1)]
