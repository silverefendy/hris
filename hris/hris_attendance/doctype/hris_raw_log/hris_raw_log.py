import frappe
from frappe import _
from frappe.model.document import Document

from hris.hris_attendance.services.raw_log_naming import build_raw_log_name

EDIT_ROLES = {"HRIS HR Admin", "HRIS Manager", "System Manager"}
SOURCE_FIELDS = (
	"device",
	"device_user_id",
	"punch_time",
	"verify_mode",
	"punch_status_raw",
	"employee",
)
REVIEW_FINAL = ("Disetujui", "Ditolak")


class HRISRawLog(Document):
	def autoname(self):
		self.name, self.punch_key = build_raw_log_name(self.device, self.device_user_id, self.punch_time)

	def before_validate(self):
		self.company = frappe.db.get_value("HRIS Device", self.device, "company")
		if self.is_new():
			self.match_employee()
			self.review_status = "Menunggu" if self.employee else "Tidak Cocok"

	def match_employee(self):
		if self.employee or not self.device_user_id:
			return
		rows = frappe.get_all(
			"Employee",
			filters={
				"attendance_device_id": self.device_user_id,
				"company": self.company,
				"status": "Active",
			},
			pluck="name",
			limit=2,
		)
		if len(rows) == 1:
			self.employee = rows[0]

	def validate(self):
		if self.is_new():
			return
		self.validate_source_edit()
		self.sync_status_after_edit()
		self.stamp_review()

	def validate_source_edit(self):
		changed = [f for f in SOURCE_FIELDS if self.has_value_changed(f)]
		if not changed:
			return
		if self.review_status == "Terkirim":
			frappe.throw(_("Log berstatus Terkirim tidak dapat diubah."))
		if not (EDIT_ROLES & set(frappe.get_roles())):
			frappe.throw(
				_("Hanya HRIS HR Admin atau HRIS Manager yang boleh mengubah data log."),
				frappe.PermissionError,
			)
		reason = (self.change_reason or "").strip()
		if not reason or not self.has_value_changed("change_reason"):
			labels = ", ".join(self.meta.get_label(f) for f in changed)
			frappe.throw(
				_("Alasan perubahan baru wajib diisi saat mengubah: {0}").format(labels)
			)

	def sync_status_after_edit(self):
		if not any(self.has_value_changed(f) for f in SOURCE_FIELDS):
			return
		if self.has_value_changed("review_status"):
			return
		self.review_status = "Menunggu" if self.employee else "Tidak Cocok"

	def stamp_review(self):
		if not self.has_value_changed("review_status"):
			return
		if self.review_status in REVIEW_FINAL:
			if not (EDIT_ROLES & set(frappe.get_roles())):
				frappe.throw(
					_("Hanya HRIS HR Admin atau HRIS Manager yang boleh menyetujui atau menolak log."),
					frappe.PermissionError,
				)
			self.reviewed_by = frappe.session.user
			self.reviewed_on = frappe.utils.now_datetime()
		else:
			self.reviewed_by = None
			self.reviewed_on = None
