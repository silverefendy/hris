import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, get_time


def _minutes(value):
	t = get_time(value)
	return t.hour * 60 + t.minute


class HRISShift(Document):
	def validate(self):
		self.shift_name = (self.shift_name or "").strip()
		self.round_seconds()
		self.validate_times()
		self.validate_numbers()
		self.validate_out_rules()
		self.validate_deduction()

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
			"late_limit_min": "Batas Terlambat",
			"min_out_after_in_min": "Jarak Minimum Masuk ke Pulang",
			"overtime_min_minutes": "Lembur Minimal",
			"break_minutes": "Istirahat",
		}
		for fieldname, label in labels.items():
			if (self.get(fieldname) or 0) < 0:
				frappe.throw(_("{0} tidak boleh negatif.").format(label))
		duration = self.duration_minutes or 0
		if duration and (self.break_minutes or 0) >= duration:
			frappe.throw(_("Istirahat harus lebih kecil dari durasi shift."))

	def validate_out_rules(self):
		# K-36 (revisi): pulang = punch minimal X menit setelah masuk, sampai batas lembur.
		duration = self.duration_minutes or 0
		min_out = self.min_out_after_in_min or 0
		if duration and min_out >= duration:
			frappe.throw(
				_("Jarak Minimum Masuk ke Pulang ({0} menit) harus lebih kecil dari durasi shift ({1} menit).").format(
					min_out, duration
				)
			)
		window_after = self.window_after_min or 0
		overtime_min = self.overtime_min_minutes or 0
		if overtime_min > window_after:
			frappe.throw(
				_("Lembur Minimal ({0} menit) tidak boleh melebihi Jendela Sesudah Selesai ({1} menit).").format(
					overtime_min, window_after
				)
			)

	def validate_deduction(self):
		# K-37: potongan dihitung per blok menit, kelipatan jam.
		if (self.deduction_block_min or 0) <= 0:
			frappe.throw(_("Blok Potongan harus lebih dari 0 menit."))
		if flt(self.deduction_hours_per_block) < 0:
			frappe.throw(_("Jam Dipotong per Blok tidak boleh negatif."))
