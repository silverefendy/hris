import math
from datetime import datetime, timedelta

import frappe
from frappe import _
from frappe.utils import cint, flt, get_datetime, get_time, getdate, now_datetime

from hris.hris_attendance.services.shift_schedule import get_schedule_for_date

DT = "HRIS Working Hour"
COUNTED = ["Menunggu", "Disetujui", "Terkirim"]
SOURCES = ("Shift Assignment", "Rotasi", "Jadwal Mingguan")
RULE_FIELDS = [
	"name", "start_time", "end_time", "crosses_midnight", "duration_minutes", "break_minutes",
	"window_before_min", "late_limit_min", "window_after_min", "min_out_after_in_min",
	"overtime_min_minutes", "late_tolerance_min", "early_leave_tolerance_min",
	"deduction_block_min", "deduction_hours_per_block",
]
RESET = {
	"schedule_source": None, "shift": None, "is_holiday": 0, "employee_group": None,
	"department": None, "borrowed_for_group": None, "shift_start": None, "shift_end": None,
	"crosses_midnight": 0, "break_minutes": 0, "scheduled_minutes": 0, "late_tolerance_min": 0,
	"early_leave_tolerance_min": 0, "window_before_min": 0, "late_limit_min": 0,
	"window_after_min": 0, "min_out_after_in_min": 0, "overtime_min_minutes": 0,
	"deduction_block_min": 0, "deduction_hours_per_block": 0, "check_in": None, "check_out": None,
	"check_in_log": None, "check_out_log": None, "punch_count": 0, "status": None,
	"late_minutes": 0, "early_leave_minutes": 0, "late_deduction_hours": 0,
	"early_leave_deduction_hours": 0, "scheduled_hours": 0, "effective_hours": 0,
	"overtime_minutes": 0, "has_overtime": 0, "overtime_type": None, "needs_review": 0,
	"review_reason": None,
}


def _hms(value):
	return get_time(value).strftime("%H:%M:%S")


def _floor_minute(value):
	return value.replace(second=0, microsecond=0)


def _minutes_between(later, earlier):
	return int((later - earlier).total_seconds() // 60)


def _deduction_hours(minutes, block, per_block):
	block = block if block and block > 0 else 60
	return int(math.ceil(minutes / float(block))) * flt(per_block)


def compute_day(rule, day, punches, is_holiday=0):
	"""Hitung satu hari kerja. Murni (tanpa database) supaya mudah diuji.

	rule: dict aturan shift (start_time bertipe time). punches: list dict
	{name, time (datetime), review_status} terurut naik, sudah di dalam jendela.
	"""
	start = datetime.combine(day, rule["start_time"])
	end = start + timedelta(minutes=rule["duration_minutes"])
	masuk_to = start + timedelta(minutes=rule["late_limit_min"])
	pulang_to = end + timedelta(minutes=rule["window_after_min"])
	masuk_from = start - timedelta(minutes=rule["window_before_min"])

	roles = {p["name"]: "Diabaikan Otomatis" for p in punches}

	masuk = None
	for p in punches:
		if masuk_from <= p["time"] <= masuk_to:
			masuk = p
			break

	if masuk:
		earliest_out = masuk["time"] + timedelta(minutes=rule["min_out_after_in_min"])
		candidates = [p for p in punches if p is not masuk and earliest_out <= p["time"] <= pulang_to]
	else:
		candidates = [p for p in punches if masuk_to < p["time"] <= pulang_to]
	pulang = candidates[-1] if candidates else None

	if masuk:
		roles[masuk["name"]] = "Masuk"
	if pulang:
		roles[pulang["name"]] = "Pulang"

	if masuk and pulang:
		status = "Hadir"
	elif masuk or pulang:
		status = "Tidak Lengkap"
	else:
		status = "Tidak Hadir"

	late_minutes = 0
	late_hours = 0.0
	if masuk:
		diff = _minutes_between(_floor_minute(masuk["time"]), start)
		if diff > rule["late_tolerance_min"]:
			late_minutes = diff
			late_hours = _deduction_hours(diff, rule["deduction_block_min"], rule["deduction_hours_per_block"])

	early_minutes = 0
	early_hours = 0.0
	overtime = 0
	if pulang:
		diff = _minutes_between(end, _floor_minute(pulang["time"]))
		if diff > rule["early_leave_tolerance_min"]:
			early_minutes = diff
			early_hours = _deduction_hours(diff, rule["deduction_block_min"], rule["deduction_hours_per_block"])
		over = _minutes_between(_floor_minute(pulang["time"]), end)
		step = rule["overtime_min_minutes"] or 1
		if over > 0 and over >= step:
			overtime = (min(over, rule["window_after_min"]) // step) * step

	scheduled_minutes = max(0, rule["duration_minutes"] - rule["break_minutes"])
	scheduled_hours = round(scheduled_minutes / 60.0, 2)
	if status == "Hadir":
		effective = max(0.0, scheduled_hours - late_hours - early_hours)
	else:
		# K-41: tidak lengkap atau tidak hadir = 0 jam, HRD menyesuaikan.
		effective = 0.0
		late_hours = 0.0
		early_hours = 0.0

	reasons = []
	if status == "Tidak Lengkap":
		reasons.append("Punch tidak lengkap (hanya {0})".format("masuk" if masuk else "pulang"))
	if any(p and p.get("review_status") == "Menunggu" for p in (masuk, pulang)):
		reasons.append("Memakai log berstatus Menunggu")
	ignored = sum(1 for r in roles.values() if r == "Diabaikan Otomatis")
	if ignored:
		reasons.append("{0} punch diabaikan otomatis".format(ignored))

	return {
		"roles": roles,
		"reasons": reasons,
		"fields": {
			"check_in": masuk["time"] if masuk else None,
			"check_out": pulang["time"] if pulang else None,
			"check_in_log": masuk["name"] if masuk else None,
			"check_out_log": pulang["name"] if pulang else None,
			"punch_count": len(punches),
			"status": status,
			"late_minutes": late_minutes,
			"early_leave_minutes": early_minutes,
			"late_deduction_hours": late_hours,
			"early_leave_deduction_hours": early_hours,
			"scheduled_hours": scheduled_hours,
			"effective_hours": effective,
			"overtime_minutes": overtime,
			"has_overtime": 1 if overtime else 0,
			"overtime_type": ("Hari Libur" if is_holiday else "Hari Kerja") if overtime else None,
		},
	}


def _punch_filters(employee, start, end, inclusive_end):
	return [
		["employee", "=", employee],
		["review_status", "in", COUNTED],
		["punch_time", ">=", start],
		["punch_time", "<=" if inclusive_end else "<", end],
	]


def _window_punches(employee, start, end):
	rows = frappe.get_all(
		"HRIS Raw Log",
		filters=_punch_filters(employee, start, end, True),
		fields=["name", "punch_time", "review_status"],
		order_by="punch_time asc",
	)
	return [{"name": r["name"], "time": get_datetime(r["punch_time"]), "review_status": r["review_status"]} for r in rows]


def _day_punch_count(employee, day):
	start = datetime.combine(day, datetime.min.time())
	rows = frappe.get_all("HRIS Raw Log", filters=_punch_filters(employee, start, start + timedelta(days=1), False), pluck="name")
	return len(rows)


def _signature(doc):
	return (str(doc.check_in), str(doc.check_out), str(doc.status))


def calculate_working_hour(employee, work_date):
	day = getdate(work_date)
	sched = get_schedule_for_date(employee, day)
	emp = frappe.db.get_value("Employee", employee, ["company", "department"], as_dict=True)
	if not emp:
		frappe.throw(_("Karyawan {0} tidak ditemukan.").format(employee))

	key = "{0}|{1}".format(employee, day)
	name = frappe.db.get_value(DT, {"unique_key": key}, "name")
	if name:
		doc = frappe.get_doc(DT, name)
		previous_logs = [doc.check_in_log, doc.check_out_log]
		previous_review = doc.review_status
		previous_sig = _signature(doc)
	else:
		doc = frappe.new_doc(DT)
		doc.employee = employee
		doc.work_date = day
		previous_logs = []
		previous_review = None
		previous_sig = ("None", "None", "None")

	for fieldname, value in RESET.items():
		doc.set(fieldname, value)

	doc.employee_group = sched.get("group")
	doc.borrowed_for_group = sched.get("borrowed_for_group")
	doc.department = emp.department
	doc.schedule_source = sched["source"] if sched["source"] in SOURCES else "Tidak Terjadwal"
	doc.is_holiday = 1 if sched.get("is_holiday") else 0

	shift = None
	if sched.get("shift"):
		shift = frappe.db.get_value("HRIS Shift", sched["shift"], RULE_FIELDS, as_dict=True)

	roles = {}
	reasons = []

	if not shift:
		doc.status = "Libur" if (sched.get("is_off") or doc.is_holiday) else "Tidak Terjadwal"
		count = _day_punch_count(employee, day)
		doc.punch_count = count
		if count:
			reasons.append("Ada {0} punch pada hari libur atau tanpa jadwal".format(count))
	elif not sched.get("works"):
		doc.shift = shift["name"]
		doc.status = "Libur"
		count = _day_punch_count(employee, day)
		doc.punch_count = count
		if count:
			reasons.append("Ada {0} punch pada hari libur atau tanpa jadwal".format(count))
	else:
		rule = {
			"start_time": get_time(shift["start_time"]),
			"duration_minutes": cint(shift["duration_minutes"]),
			"break_minutes": cint(shift["break_minutes"]),
			"window_before_min": cint(shift["window_before_min"]),
			"late_limit_min": cint(shift["late_limit_min"]),
			"window_after_min": cint(shift["window_after_min"]),
			"min_out_after_in_min": cint(shift["min_out_after_in_min"]),
			"overtime_min_minutes": cint(shift["overtime_min_minutes"]),
			"late_tolerance_min": cint(shift["late_tolerance_min"]),
			"early_leave_tolerance_min": cint(shift["early_leave_tolerance_min"]),
			"deduction_block_min": cint(shift["deduction_block_min"]),
			"deduction_hours_per_block": flt(shift["deduction_hours_per_block"]),
		}
		start = datetime.combine(day, rule["start_time"])
		end = start + timedelta(minutes=rule["duration_minutes"])
		punches = _window_punches(
			employee,
			start - timedelta(minutes=rule["window_before_min"]),
			end + timedelta(minutes=rule["window_after_min"]),
		)

		doc.shift = shift["name"]
		doc.shift_start = _hms(shift["start_time"])
		doc.shift_end = _hms(shift["end_time"])
		doc.crosses_midnight = 1 if shift["crosses_midnight"] else 0
		doc.break_minutes = rule["break_minutes"]
		doc.scheduled_minutes = max(0, rule["duration_minutes"] - rule["break_minutes"])
		for fieldname in (
			"late_tolerance_min", "early_leave_tolerance_min", "window_before_min", "late_limit_min",
			"window_after_min", "min_out_after_in_min", "overtime_min_minutes",
			"deduction_block_min", "deduction_hours_per_block",
		):
			doc.set(fieldname, rule[fieldname])

		if not punches and not sched.get("is_required"):
			# Hari tidak wajib dan tidak ada punch: dianggap libur.
			doc.status = "Libur"
		else:
			result = compute_day(rule, day, punches, doc.is_holiday)
			for fieldname, value in result["fields"].items():
				doc.set(fieldname, value)
			roles = result["roles"]
			reasons = result["reasons"]

	doc.needs_review = 1 if reasons else 0
	doc.review_reason = "; ".join(reasons) if reasons else None
	if doc.needs_review:
		keep = previous_review == "Sudah Ditinjau" and previous_sig == _signature(doc)
		doc.review_status = "Sudah Ditinjau" if keep else "Menunggu"
	else:
		doc.review_status = "Sudah Ditinjau" if previous_review == "Sudah Ditinjau" else "Tidak Perlu"

	doc.calculated_on = now_datetime()
	doc.calculated_by = frappe.session.user
	doc.flags.from_calculation = True
	if name:
		doc.save(ignore_permissions=True)
	else:
		doc.insert(ignore_permissions=True)

	# K-18 d: layanan menulis punch_role (bukan field sumber, tanpa Version).
	for log in set(previous_logs) - set(roles):
		if log:
			frappe.db.set_value("HRIS Raw Log", log, "punch_role", "", update_modified=False)
	for log, role in roles.items():
		frappe.db.set_value("HRIS Raw Log", log, "punch_role", role, update_modified=False)

	return {"name": doc.name, "status": doc.status}
