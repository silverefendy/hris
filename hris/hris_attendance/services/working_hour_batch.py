import time
import uuid

import frappe
from frappe import _
from frappe.utils import add_days, date_diff, flt, getdate, nowdate

from hris.hris_attendance.services.shift_schedule import _group_fieldname
from hris.hris_attendance.services.working_hour import DT, calculate_working_hour

ALLOWED_ROLES = {"HRIS HR Admin", "HRIS Manager", "System Manager"}
SCOPES = ("Semua", "Karyawan", "Department", "Grup")
MAX_DAYS = 31
SYNC_LIMIT = 300
STATUS_TTL = 3600
QUEUE_STALE_AFTER = 60
RUN_STALE_AFTER = 120
ACTIVE_STALE_AFTER = 180
ERROR_LIMIT = 20
HEARTBEAT_EVERY = 5
ACTIVE_KEY = "hris_wh_recalc_active"
SAVEPOINT = "hris_wh_item"


def _cache():
	# Bentuk akses cache berbeda antar versi Frappe: objek langsung atau fungsi.
	c = frappe.cache
	if hasattr(c, "set_value"):
		return c
	return c()


def _status_key(run_id):
	return "hris_wh_recalc:" + str(run_id)


def _last_key(user):
	return "hris_wh_recalc_last:" + str(user)


def _save(run_id, status, touch=True):
	if touch:
		status["updated"] = time.time()
	_cache().set_value(_status_key(run_id), status, expires_in_sec=STATUS_TTL)


def _load(run_id):
	return _cache().get_value(_status_key(run_id))


def _assert_allowed():
	if not (ALLOWED_ROLES & set(frappe.get_roles())):
		frappe.throw(
			_("Hanya HRIS HR Admin, HRIS Manager, atau System Manager yang boleh menghitung working hour."),
			frappe.PermissionError,
		)


def _normalize(from_date, to_date, scope, employee, department, employee_group, company, skip_reviewed):
	start, end = getdate(from_date), getdate(to_date)
	yesterday = add_days(getdate(nowdate()), -1)
	if end < start:
		frappe.throw(_("Tanggal Sampai tidak boleh sebelum Tanggal Dari."))
	if end > yesterday:
		frappe.throw(_("Tanggal Sampai paling lambat kemarin ({0}). Hari yang belum selesai tidak dihitung.").format(yesterday))
	if date_diff(end, start) + 1 > MAX_DAYS:
		frappe.throw(_("Rentang maksimal {0} hari per proses.").format(MAX_DAYS))
	scope = scope or "Semua"
	if scope not in SCOPES:
		frappe.throw(_("Cakupan tidak dikenal: {0}.").format(scope))
	needed = {"Karyawan": employee, "Department": department, "Grup": employee_group}
	if scope in needed and not needed[scope]:
		frappe.throw(_("Pilih {0} untuk cakupan {0}.").format(scope))
	return {
		"from_date": str(start),
		"to_date": str(end),
		"scope": scope,
		"employee": employee or None,
		"department": department or None,
		"employee_group": employee_group or None,
		"company": company or None,
		"skip_reviewed": 1 if (str(skip_reviewed) not in ("0", "", "None", "False", "false")) else 0,
	}


def _employees(params):
	filters = {"status": "Active"}
	if params.get("company"):
		filters["company"] = params["company"]
	scope = params["scope"]
	if scope == "Karyawan":
		filters["name"] = params["employee"]
	elif scope == "Department":
		filters["department"] = params["department"]
	elif scope == "Grup":
		filters[_group_fieldname()] = params["employee_group"]
	rows = frappe.get_all("Employee", filters=filters, fields=["name", "date_of_joining"], order_by="name")
	if scope == "Karyawan" and not rows:
		frappe.throw(_("Karyawan {0} tidak ditemukan atau tidak berstatus Active.").format(params["employee"]))
	return rows


def _protected(employees, start, end):
	if not employees:
		return set()
	rows = frappe.get_all(
		DT,
		filters={"employee": ["in", [e["name"] for e in employees]], "work_date": ["between", [start, end]]},
		fields=["employee", "work_date", "review_status", "adjustment_hours"],
	)
	return {
		(r["employee"], str(r["work_date"]))
		for r in rows
		if r["review_status"] == "Sudah Ditinjau" or flt(r["adjustment_hours"]) != 0
	}


def _process(employees, params, run_id=None, status=None, commit=False):
	start, end = getdate(params["from_date"]), getdate(params["to_date"])
	days = [add_days(start, i) for i in range(date_diff(end, start) + 1)]
	protected = _protected(employees, start, end) if params["skip_reviewed"] else set()
	result = {
		"total": len(employees) * len(days),
		"ok": 0,
		"skipped_reviewed": 0,
		"skipped_joining": 0,
		"failed": 0,
		"errors": [],
	}
	done = 0
	for emp in employees:
		joined = getdate(emp["date_of_joining"]) if emp.get("date_of_joining") else None
		for day in days:
			if joined and day < joined:
				result["skipped_joining"] += 1
			elif (emp["name"], str(day)) in protected:
				result["skipped_reviewed"] += 1
			else:
				frappe.db.savepoint(SAVEPOINT)
				try:
					calculate_working_hour(emp["name"], day)
					result["ok"] += 1
				except Exception as exc:
					frappe.db.rollback(save_point=SAVEPOINT)
					result["failed"] += 1
					if len(result["errors"]) < ERROR_LIMIT:
						result["errors"].append("{0} {1}: {2}".format(emp["name"], day, str(exc)[:150]))
					frappe.log_error(
						title="HRIS Working Hour: gagal hitung {0} {1}".format(emp["name"], day),
						message=frappe.get_traceback(),
					)
			done += 1
			if status is not None and (done % HEARTBEAT_EVERY == 0 or done == result["total"]):
				status.update(
					done=done,
					ok=result["ok"],
					skipped_reviewed=result["skipped_reviewed"],
					skipped_joining=result["skipped_joining"],
					failed=result["failed"],
					errors=list(result["errors"]),
				)
				_save(run_id, status)
		if commit:
			frappe.db.commit()
	return result


def _init_status(run_id, total, user, params):
	status = {
		"run_id": run_id,
		"state": "Antre",
		"user": user,
		"total": total,
		"done": 0,
		"ok": 0,
		"skipped_reviewed": 0,
		"skipped_joining": 0,
		"failed": 0,
		"errors": [],
		"started_on": frappe.utils.now(),
		"params": params,
		"message": None,
	}
	_save(run_id, status)
	_cache().set_value(ACTIVE_KEY, run_id, expires_in_sec=STATUS_TTL)
	_cache().set_value(_last_key(user), run_id, expires_in_sec=STATUS_TTL)
	return status


def _release_active(run_id):
	if _cache().get_value(ACTIVE_KEY) == run_id:
		_cache().delete_value(ACTIVE_KEY)


def _assert_no_active_run():
	active = _cache().get_value(ACTIVE_KEY)
	if not active:
		return
	status = _load(active)
	if status and status.get("state") in ("Antre", "Berjalan") and time.time() - status.get("updated", 0) < ACTIVE_STALE_AFTER:
		frappe.throw(
			_("Sudah ada proses hitung berjalan (oleh {0}, {1} dari {2}). Tunggu selesai atau buka Status Hitung.").format(
				status.get("user"), status.get("done"), status.get("total")
			)
		)


@frappe.whitelist()
def recalculate_working_hours(
	from_date, to_date, scope="Semua", employee=None, department=None, employee_group=None, company=None, skip_reviewed=1
):
	_assert_allowed()
	params = _normalize(from_date, to_date, scope, employee, department, employee_group, company, skip_reviewed)
	_assert_no_active_run()
	employees = _employees(params)
	total = len(employees) * (date_diff(getdate(params["to_date"]), getdate(params["from_date"])) + 1)
	run_id = uuid.uuid4().hex[:12]

	if total == 0:
		return {
			"mode": "sync", "run_id": run_id, "total": 0, "ok": 0, "skipped_reviewed": 0,
			"skipped_joining": 0, "failed": 0, "errors": [],
			"message": _("Tidak ada karyawan Active yang cocok dengan pilihan ini."),
		}

	if total <= SYNC_LIMIT:
		result = _process(employees, params)
		result.update({"mode": "sync", "run_id": run_id})
		return result

	_init_status(run_id, total, frappe.session.user, params)
	frappe.enqueue(
		"hris.hris_attendance.services.working_hour_batch.run_batch",
		queue="long",
		timeout=3600,
		run_id=run_id,
		params=params,
	)
	return {"mode": "background", "run_id": run_id, "total": total}


def run_batch(run_id, params, commit=True):
	status = _load(run_id) or {"run_id": run_id, "user": frappe.session.user}
	status["state"] = "Berjalan"
	_save(run_id, status)
	try:
		employees = _employees(params)
		result = _process(employees, params, run_id=run_id, status=status, commit=commit)
		status.update(
			state="Selesai",
			done=result["total"],
			ok=result["ok"],
			skipped_reviewed=result["skipped_reviewed"],
			skipped_joining=result["skipped_joining"],
			failed=result["failed"],
			errors=list(result["errors"]),
		)
		_save(run_id, status)
	except Exception:
		if commit:
			frappe.db.rollback()
		frappe.log_error(title="HRIS Working Hour: proses hitung background gagal", message=frappe.get_traceback())
		if commit:
			frappe.db.commit()
		status.update(state="Gagal", message=_("Proses berhenti karena error. Lihat Error Log."))
		_save(run_id, status)
		raise
	finally:
		_release_active(run_id)


@frappe.whitelist()
def get_recalc_status(run_id=None):
	_assert_allowed()
	if not run_id:
		run_id = _cache().get_value(_last_key(frappe.session.user))
	if not run_id:
		return {"state": "Tidak Ada", "message": _("Belum ada proses hitung terbaru.")}
	status = _load(run_id)
	if not status:
		return {"state": "Tidak Ada", "run_id": run_id, "message": _("Status tidak ditemukan atau sudah kedaluwarsa (lebih dari 1 jam).")}
	age = int(time.time() - status.get("updated", time.time()))
	status["age_seconds"] = age
	status["warning"] = None
	if status.get("state") == "Antre" and age > QUEUE_STALE_AFTER:
		status["warning"] = _(
			"Belum diambil worker selama {0} detik. Worker background kemungkinan mati; periksa proses bench/supervisor."
		).format(age)
	elif status.get("state") == "Berjalan" and age > RUN_STALE_AFTER:
		status["warning"] = _(
			"Tidak ada kemajuan selama {0} detik. Proses kemungkinan terhenti; periksa Error Log dan worker."
		).format(age)
	return status


def ping_job(token):
	# Dipakai uji kesehatan worker.
	_cache().set_value("hris_wh_ping:" + str(token), time.time(), expires_in_sec=60)
