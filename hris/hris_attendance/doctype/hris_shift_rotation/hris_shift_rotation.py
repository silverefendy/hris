import frappe
from frappe import _
from frappe.model.document import Document


class HRISShiftRotation(Document):
	def validate(self):
		self.rotation_name = (self.rotation_name or "").strip()
		self.validate_pattern()

	def validate_pattern(self):
		# validate jalan SEBELUM cek field wajib, jadi kosong dilewati dulu
		rows = self.pattern or []
		if not rows:
			return

		for number, row in enumerate(rows, start=1):
			row.day_number = number
			if row.is_off:
				row.shift = None
				continue
			if not row.shift:
				frappe.throw(_("Hari ke-{0}: pilih Shift, atau centang Libur.").format(number))
			shift_company = frappe.db.get_value("HRIS Shift", row.shift, "company")
			if self.company and shift_company and shift_company != self.company:
				frappe.throw(
					_("Hari ke-{0}: Shift {1} milik company {2}, bukan {3}.").format(
						number, row.shift, shift_company, self.company
					)
				)

		if all(row.is_off for row in rows):
			frappe.throw(_("Pola tidak boleh libur semua. Minimal satu hari berisi Shift."))

		self.cycle_days = len(rows)
