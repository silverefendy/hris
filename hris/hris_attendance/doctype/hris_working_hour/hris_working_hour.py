import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import flt, get_datetime, getdate, now_datetime

EDIT_ROLES = {"HRIS HR Admin", "HRIS Manager", "System Manager"}
# Hanya ini yang boleh diubah manusia (K-42). Sisanya hasil layanan hitung.
EDITABLE = {"review_status", "review_note", "adjustment_hours", "adjustment_reason"}
# Diisi controller sendiri.
DERIVED = {"final_effective_hours", "reviewed_by", "reviewed_on", "employee_name", "company"}
LOCKED = ("employee", "work_date")
LAYOUT = ("Section Break", "Column Break", "Tab Break", "HTML", "Button")
NON_NEGATIVE = (
	"break_minutes", "scheduled_minutes", "late_tolerance_min", "early_leave_tolerance_min",
	"window_before_min", "late_limit_min", "window_after_min", "min_out_after_in_min",
	"overtime_min_minutes", "deduction_block_min", "deduction_hours_per_block", "punch_count",
	"late_minutes", "early_leave_minutes", "late_deduction_hours", "early_leave_deduction_hours",
	"scheduled_hours", "effective_hours", "overtime_minutes",
)


class HRISWorkingHour(Document):
	def autoname(self):
		# K-40: nomor dari TANGGAL KERJA, bukan tanggal dibuat.
		if not self.employee or not self.work_date:
			frappe.throw(_("Karyawan dan Tanggal Kerja wajib diisi."))
		day = getdate(self.work_date)
		self.unique_key = "{0}|{1}".format(self.employee, day)
		existing = frappe.db.get_value("HRIS Working Hour", {"unique_key": self.unique_key}, "name")
		if existing:
			frappe.throw(
				_("Working Hour karyawan {0} tanggal {1} sudah ada: {2}.").format(self.employee, day, existing)
			)
		self.name = make_autoname("WH-{0}-.####".format(day.strftime("%y%m%d")))

	def before_validate(self):
		if not self.employee:
			return
		emp = frappe.db.get_value("Employee", self.employee, ["employee_name", "company"], as_dict=True)
		if not emp:
			frappe.throw(_("Karyawan {0} tidak ditemukan.").format(self.employee))
		self.employee_name = emp.employee_name
		self.company = emp.company

	def validate(self):
		self.guard_edits()
		self.validate_punch()
		self.validate_numbers()
		self.apply_adjustment()
		self.stamp_review()

	def guard_edits(self):
		if self.is_new():
			return
		for fieldname in LOCKED:
			if self.has_value_changed(fieldname):
				frappe.throw(_("Karyawan dan Tanggal Kerja tidak dapat diubah. Buat ulang barisnya bila salah."))
		if self.flags.from_calculation:
			return
		blocked = []
		edited = []
		for df in self.meta.fields:
			name = df.fieldname
			if df.fieldtype in LAYOUT or name in DERIVED or name in LOCKED:
				continue
			if not self.has_value_changed(name):
				continue
			if name in EDITABLE:
				edited.append(name)
			else:
				blocked.append(df.label or name)
		if blocked:
			frappe.throw(
				_("Field hasil hitung tidak dapat diubah langsung: {0}. Ubah lewat Penyesuaian HRD atau hitung ulang.").format(
					", ".join(blocked)
				)
			)
		if edited and not (EDIT_ROLES & set(frappe.get_roles())):
			frappe.throw(
				_("Hanya HRIS HR Admin, HRIS Manager, atau System Manager yang boleh mengubah tinjauan dan penyesuaian."),
				frappe.PermissionError,
			)

	def validate_punch(self):
		if self.check_in and self.check_out and get_datetime(self.check_out) < get_datetime(self.check_in):
			frappe.throw(_("Jam pulang tidak boleh sebelum jam masuk."))

	def validate_numbers(self):
		for fieldname in NON_NEGATIVE:
			if flt(self.get(fieldname)) < 0:
				frappe.throw(_("{0} tidak boleh negatif.").format(self.meta.get_label(fieldname)))

	def apply_adjustment(self):
		adjustment = flt(self.adjustment_hours)
		if adjustment and not (self.adjustment_reason or "").strip():
			frappe.throw(_("Alasan Penyesuaian wajib diisi bila ada penyesuaian jam."))
		self.final_effective_hours = max(0.0, flt(self.effective_hours) + adjustment)

	def stamp_review(self):
		if self.is_new() or not self.has_value_changed("review_status"):
			return
		if self.review_status == "Sudah Ditinjau":
			self.reviewed_by = frappe.session.user
			self.reviewed_on = now_datetime()
		else:
			self.reviewed_by = None
			self.reviewed_on = None
