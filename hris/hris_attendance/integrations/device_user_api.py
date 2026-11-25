"""Endpoint penerima snapshot user mesin dari Device Tool."""
import frappe

from hris.hris_attendance.services.agent_auth import verify_agent_request
from hris.hris_attendance.services.device_user_ingest import save_device_users


@frappe.whitelist(allow_guest=True, methods=["POST"])
def push_device_users(device=None, users=None, snapshot_at=None, is_last=0):
    """Terima snapshot user satu mesin (batch maks 500).

    Autentikasi: header X-HRIS-Token (sama dengan push_punches).
    Body JSON: device (nama HRIS Device), users (daftar objek dengan kunci
    device_user_id, name, privilege, enabled, finger_count), snapshot_at
    (WIB, sama untuk semua batch), is_last (1 pada batch terakhir).
    """
    verify_agent_request()
    return save_device_users(device, users, snapshot_at, is_last)
