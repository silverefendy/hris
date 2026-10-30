import ipaddress
import secrets

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime

from hris.hris_attendance.services.agent_auth import hash_token

MANAGE_ROLES = {"System Manager", "HRIS Manager"}
TOKEN_PREFIX = "hris_"


class HRISAttendanceSettings(Document):
	def validate(self):
		self.normalize_allowed_ips()
		if self.agent_enabled and not self.agent_token_hash:
			frappe.throw(_("Buat token dulu (tombol Generate / Rotate Token) sebelum mengaktifkan agen."))

	def normalize_allowed_ips(self):
		lines = []
		for raw in (self.allowed_ips or "").splitlines():
			value = raw.strip()
			if not value:
				continue
			try:
				ipaddress.ip_network(value, strict=False)
			except ValueError:
				frappe.throw(_("Alamat IP tidak valid: {0}").format(value))
			if value not in lines:
				lines.append(value)
		self.allowed_ips = "\n".join(lines)


@frappe.whitelist(methods=["POST"])
def generate_agent_token():
	"""Buat token agen baru. Token lama langsung tidak berlaku. Token hanya dikembalikan sekali."""
	if not (MANAGE_ROLES & set(frappe.get_roles())):
		frappe.throw(
			_("Hanya System Manager atau HRIS Manager yang boleh membuat token agen."),
			frappe.PermissionError,
		)
	token = TOKEN_PREFIX + secrets.token_urlsafe(32)
	settings = frappe.get_doc("HRIS Attendance Settings")
	settings.agent_token_hash = hash_token(token)
	settings.agent_token_prefix = token[:9]
	settings.token_generated_on = now_datetime()
	settings.token_generated_by = frappe.session.user
	settings.save()
	return {"token": token, "prefix": settings.agent_token_prefix}
