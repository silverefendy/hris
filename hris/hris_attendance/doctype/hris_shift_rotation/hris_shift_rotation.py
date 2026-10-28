import frappe
from frappe import _
from frappe.model.document import Document


class HRISShiftRotation(Document):
	def validate(self):
		self.rotation_name = (self.rotation_name or "").strip()
		self.validate_pattern()
		self.validate_not_locked()
		self.validate_deactivation()

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

	def validate_not_locked(self):
		# Pola yang sudah dipakai grup tidak boleh berubah: jadwal lama ikut bergeser.
		before = self.get_doc_before_save()
		if not before:
			return
		used_by = frappe.get_all("HRIS Employee Group", filters={"rotation": self.name}, pluck="name")
		if not used_by:
			return
		old = [(1 if r.is_off else 0, r.shift or "") for r in before.pattern]
		new = [(1 if r.is_off else 0, r.shift or "") for r in self.pattern]
		if old != new or before.company != self.company:
			frappe.throw(
				_("Rotasi ini sudah dipakai grup: {0}. Pola dan Company tidak boleh diubah. Buat Rotation baru, lalu pindahkan grupnya.").format(
					", ".join(used_by)
				)
			)

	def validate_deactivation(self):
		# Rotasi tidak boleh dinonaktifkan selama masih dipakai grup aktif (K-34).
		if self.is_active or self.is_new():
			return
		before = self.get_doc_before_save()
		if not before or not before.is_active:
			return
		groups = frappe.get_all(
			"HRIS Employee Group",
			filters={"rotation": self.name, "is_active": 1},
			pluck="name",
		)
		if groups:
			frappe.throw(
				_("Rotasi {0} masih dipakai grup aktif: {1}. Nonaktifkan atau pindahkan grupnya dulu.").format(
					self.name, ", ".join(groups)
				)
			)
