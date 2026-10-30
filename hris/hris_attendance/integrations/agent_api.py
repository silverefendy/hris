"""Endpoint penerima punch untuk agen Windows (middleware)."""
import frappe

from hris.hris_attendance.services.agent_auth import verify_agent_request
from hris.hris_attendance.services.punch_ingest import save_punches


@frappe.whitelist(allow_guest=True, methods=["POST"])
def push_punches(device=None, punches=None):
	"""Terima punch milik satu device dari agen Windows.

	Autentikasi: header X-HRIS-Token (token dari HRIS Attendance Settings).
	Body JSON: device (nama HRIS Device) dan punches (daftar objek dengan kunci
	device_user_id, punch_time WIB, verify_mode, punch_status_raw, raw_payload).
	Daftar kosong dianggap detak (heartbeat) dan hanya memperbarui last_agent_at.
	"""
	verify_agent_request()
	return save_punches(device, punches, "Agen Windows")
