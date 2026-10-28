import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate


class HRISShiftAssignment(Document):
	def validate(self):
		self.reason = (self.reason or "").strip()
		self.validate_dates()
		self.validate_employee()
		self.validate_shift()
		self.validate_borrowed_group()
		self.validate_overlap()

	def validate_dates(self):
		# validate jalan SEBELUM cek field wajib, jadi kosong dilewati dulu
		if self.from_date and self.to_date and getdate(self.to_date) < getdate(self.from_date):
			frappe.throw(_("Tanggal Sampai tidak boleh sebelum Tanggal Dari."))

	def validate_employee(self):
		if not self.employee:
			return
		emp = frappe.db.get_value("Employee", self.employee, ["employee_name", "company", "status"], as_dict=True)
		if not emp:
			frappe.throw(_("Karyawan {0} tidak ditemukan.").format(self.employee))
		if emp.status != "Active":
			frappe.throw(_("Karyawan {0} tidak berstatus Active.").format(self.employee))
		# diisi dari server supaya tidak bergantung pada browser
		self.employee_name = emp.employee_name
		self.company = emp.company

	def validate_shift(self):
		if not self.shift:
			return
		shift = frappe.db.get_value("HRIS Shift", self.shift, ["company", "is_active"], as_dict=True)
		if not shift:
			frappe.throw(_("Shift {0} tidak ditemukan.").format(self.shift))
		if not shift.is_active:
			frappe.throw(_("Shift {0} tidak aktif.").format(self.shift))
		if self.company and shift.company != self.company:
			frappe.throw(
				_("Shift {0} milik company {1}, sedangkan karyawan di company {2}.").format(
					self.shift, shift.company, self.company
				)
			)

	def validate_borrowed_group(self):
		if not self.borrowed_for_group:
			return
		if not frappe.db.get_value("HRIS Employee Group", self.borrowed_for_group, "is_active"):
			frappe.throw(_("Grup {0} tidak aktif.").format(self.borrowed_for_group))

	def validate_overlap(self):
		if not (self.is_active and self.employee and self.from_date and self.to_date):
			return
		rows = frappe.get_all(
			"HRIS Shift Assignment",
			filters={
				"employee": self.employee,
				"is_active": 1,
				"name": ["!=", self.name or ""],
				"from_date": ["<=", self.to_date],
				"to_date": [">=", self.from_date],
			},
			fields=["name", "from_date", "to_date"],
		)
		if rows:
			r = rows[0]
			frappe.throw(
				_("Karyawan {0} sudah punya Shift Assignment aktif {1} ({2} sampai {3}) yang tumpang tindih.").format(
					self.employee, r.name, r.from_date, r.to_date
				)
			)
