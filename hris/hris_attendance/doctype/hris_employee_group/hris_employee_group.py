import frappe
from frappe import _
from frappe.model.document import Document

DAYS = ("Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu")


class HRISEmployeeGroup(Document):
	def validate(self):
		self.validate_schedule_type()
		self.group_name = (self.group_name or "").strip()
		self.validate_department()
		self.validate_weekly_schedule()

	def validate_department(self):
		if not (self.department and self.company):
			return
		dept_company = frappe.db.get_value("Department", self.department, "company")
		if dept_company and dept_company != self.company:
			frappe.throw(
				_("Department {0} milik company {1}, bukan {2}.").format(
					self.department, dept_company, self.company
				)
			)

	def validate_weekly_schedule(self):
		used = {}
		for row in self.get("weekly_schedule") or []:
			if not row.day_from:
				continue
			row.day_to = row.day_to or row.day_from
			if row.day_from not in DAYS or row.day_to not in DAYS:
				frappe.throw(_("Baris {0}: nama hari tidak valid.").format(row.idx))
			start = DAYS.index(row.day_from)
			end = DAYS.index(row.day_to)
			if end < start:
				frappe.throw(
					_("Baris {0}: 'Sampai Hari' tidak boleh sebelum 'Dari Hari'. Pisahkan menjadi dua baris bila melewati hari Minggu.").format(row.idx)
				)
			for i in range(start, end + 1):
				if i in used:
					frappe.throw(
						_("Baris {0} dan {1} sama-sama memuat hari {2}.").format(
							used[i], row.idx, DAYS[i]
						)
					)
				used[i] = row.idx
			if row.shift:
				self.validate_shift(row)
			else:
				row.is_required = 0

	def validate_shift(self, row):
		shift = frappe.db.get_value(
			"HRIS Shift", row.shift, ["company", "is_active"], as_dict=True
		)
		if not shift:
			frappe.throw(_("Baris {0}: shift {1} tidak ditemukan.").format(row.idx, row.shift))
		if self.company and shift.company != self.company:
			frappe.throw(
				_("Baris {0}: shift {1} milik company {2}, bukan {3}.").format(
					row.idx, row.shift, shift.company, self.company
				)
			)
		if not shift.is_active:
			frappe.throw(_("Baris {0}: shift {1} tidak aktif.").format(row.idx, row.shift))

	def validate_schedule_type(self):
		# Jadwal Mingguan atau Rotasi, tidak boleh bercampur. Kosong dianggap Jadwal Mingguan.
		if not self.schedule_type:
			self.schedule_type = "Jadwal Mingguan"

		if self.schedule_type == "Rotasi":
			self.set("weekly_schedule", [])
			if not self.rotation:
				frappe.throw(_("Pilih Rotasi untuk grup bertipe Rotasi."))
			if not self.rotation_start_date:
				frappe.throw(_("Isi Tanggal Mulai Rotasi (tanggal hari ke-1 siklus)."))
			rot = frappe.db.get_value("HRIS Shift Rotation", self.rotation, ["company", "is_active"], as_dict=True)
			if not rot:
				frappe.throw(_("Rotasi {0} tidak ditemukan.").format(self.rotation))
			if not rot.is_active:
				frappe.throw(_("Rotasi {0} tidak aktif.").format(self.rotation))
			if self.company and rot.company != self.company:
				frappe.throw(_("Rotasi {0} milik company {1}, bukan {2}.").format(self.rotation, rot.company, self.company))
		else:
			self.rotation = None
			self.rotation_start_date = None
