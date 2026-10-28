import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import get_time


def _minutes(value):
	t = get_time(value)
	return t.hour * 60 + t.minute


class HRISShift(Document):
	def validate(self):
		self.shift_name = (self.shift_name or "").strip()
		self.round_seconds()
		self.validate_times()
		self.validate_numbers()

	def round_seconds(self):
		# Field Time menerima detik; shift hanya dihitung sampai menit.
		for fieldname in ("start_time", "end_time"):
			value = self.get(fieldname)
			if value:
				t = get_time(value)
				self.set(fieldname, "{:02d}:{:02d}:00".format(t.hour, t.minute))

	def validate_times(self):
		# validate jalan SEBELUM cek field wajib, jadi kosong dilewati dulu
		if not self.start_time or not self.end_time:
			return
		start = _minutes(self.start_time)
		end = _minutes(self.end_time)
		if start == end:
			frappe.throw(_("Jam mulai dan jam selesai tidak boleh sama."))
		self.crosses_midnight = 1 if end < start else 0
		self.duration_minutes = (end - start) % 1440

	def validate_numbers(self):
		labels = {
			"late_tolerance_min": "Toleransi Telat",
			"early_leave_tolerance_min": "Toleransi Pulang Cepat",
			"window_before_min": "Jendela Sebelum Mulai",
			"window_after_min": "Jendela Sesudah Selesai",
			"break_minutes": "Istirahat",
		}
		for fieldname, label in labels.items():
			if (self.get(fieldname) or 0) < 0:
				frappe.throw(_("{0} tidak boleh negatif.").format(label))
		duration = self.duration_minutes or 0
		if duration and (self.break_minutes or 0) >= duration:
			frappe.throw(_("Istirahat harus lebih kecil dari durasi shift."))
