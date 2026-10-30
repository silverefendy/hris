"""Penyimpan punch bersama untuk semua jalur data.

Agen Windows, pull pyzk, dan impor file memakai fungsi yang sama supaya hasilnya
seragam. Duplikat ditolak oleh nama dokumen HRIS Raw Log (device-userid-waktu),
sehingga pengiriman ulang aman.

Catatan: insert melewati pemeriksaan izin, jadi pemanggil wajib sudah terautentikasi.
Fungsi ini tidak memanggil commit. Permintaan web di-commit otomatis oleh
Frappe saat selesai tanpa error. Pemanggil di background (job pull) harus commit sendiri.
"""
import json

import frappe
from frappe import _
from frappe.utils import add_days, get_datetime, now_datetime, strip_html

SOURCES = ("Agen Windows", "Pull pyzk", "Impor File")
# source -> (centang jalur di Device, field waktu terakhir di Device)
CHANNELS = {
	"Agen Windows": ("use_agent", "last_agent_at"),
	"Pull pyzk": ("use_pull", "last_pull_at"),
}
MAX_BATCH = 500
MAX_FUTURE_DAYS = 1
SAVEPOINT = "hris_punch_row"


def _text(value):
	if value is None:
		return ""
	return str(value).strip()


def _clean(exc):
	return strip_html(str(exc)).strip()[:200] or type(exc).__name__


def _parse_time(value):
	if value in (None, ""):
		frappe.throw(_("punch_time wajib diisi."))
	try:
		parsed = get_datetime(value)
	except Exception:
		parsed = None
	if parsed is None:
		frappe.throw(_("punch_time tidak valid: {0}").format(str(value)[:40]))
	if parsed.tzinfo is not None:
		frappe.throw(_("punch_time harus waktu WIB tanpa zona waktu."))
	if parsed > add_days(now_datetime(), MAX_FUTURE_DAYS):
		frappe.throw(_("punch_time terlalu jauh di masa depan; periksa jam mesin."))
	return parsed.replace(microsecond=0)


def _payload(value):
	if value in (None, ""):
		return None
	if isinstance(value, str):
		return value
	return json.dumps(value, ensure_ascii=False, default=str)


def _device(name, source):
	row = None
	if name and isinstance(name, str):
		row = frappe.db.get_value(
			"HRIS Device", name, ["name", "is_active", "use_agent", "use_pull"], as_dict=True
		)
	if not row:
		frappe.throw(_("Device {0} tidak terdaftar.").format(name))
	if not row.is_active:
		frappe.throw(_("Device {0} tidak aktif.").format(row.name))
	channel = CHANNELS.get(source)
	if channel and not row.get(channel[0]):
		frappe.throw(_("Device {0} belum diaktifkan untuk jalur {1}.").format(row.name, source))
	return row


def _save_row(device_name, row, source):
	if not isinstance(row, dict):
		frappe.throw(_("Baris punch harus berupa objek."))
	user_id = _text(row.get("device_user_id"))
	if not user_id:
		frappe.throw(_("device_user_id wajib diisi."))
	doc = frappe.get_doc(
		{
			"doctype": "HRIS Raw Log",
			"device": device_name,
			"device_user_id": user_id,
			"punch_time": _parse_time(row.get("punch_time")),
			"verify_mode": _text(row.get("verify_mode")) or None,
			"punch_status_raw": _text(row.get("punch_status_raw")) or None,
			"source": source,
			"raw_payload": _payload(row.get("raw_payload")),
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def _touch(device_name, source):
	channel = CHANNELS.get(source)
	if channel:
		# Tanpa Version: Device memakai track_changes, jadi save() biasa akan memenuhi Audit Trail.
		frappe.db.set_value("HRIS Device", device_name, channel[1], now_datetime(), update_modified=False)


def save_punches(device, punches, source):
	"""Simpan daftar punch milik satu device. Mengembalikan ringkasan dan hasil per baris."""
	if source not in SOURCES:
		frappe.throw(_("Source tidak dikenal: {0}.").format(source))
	if isinstance(punches, str):
		punches = frappe.parse_json(punches)
	if punches is None:
		punches = []
	if not isinstance(punches, (list, tuple)):
		frappe.throw(_("punches harus berupa daftar."))
	if len(punches) > MAX_BATCH:
		frappe.throw(_("Maksimal {0} punch per permintaan; dikirim {1}.").format(MAX_BATCH, len(punches)))

	info = _device(device, source)
	summary = {
		"device": info.name,
		"received": len(punches),
		"created": 0,
		"duplicate": 0,
		"error": 0,
		"results": [],
	}
	for index, row in enumerate(punches):
		frappe.db.savepoint(SAVEPOINT)
		try:
			name = _save_row(info.name, row, source)
			summary["created"] += 1
			summary["results"].append({"index": index, "status": "created", "name": name})
		except frappe.DuplicateEntryError:
			frappe.db.rollback(save_point=SAVEPOINT)
			summary["duplicate"] += 1
			summary["results"].append({"index": index, "status": "duplicate"})
		except Exception as exc:
			frappe.db.rollback(save_point=SAVEPOINT)
			if not isinstance(exc, frappe.ValidationError):
				frappe.log_error(title="HRIS Punch: error tak terduga", message=frappe.get_traceback())
			summary["error"] += 1
			summary["results"].append({"index": index, "status": "error", "message": _clean(exc)})
	_touch(info.name, source)
	return summary
