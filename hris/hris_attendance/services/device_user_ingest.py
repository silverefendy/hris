"""Menyimpan snapshot daftar user dari mesin absensi (dikirim Device Tool).

Satu baris per user per mesin (kunci: mesin|ID), diperbarui bukan ditumpuk.
Tidak ada yang dihapus. Penandaan 'tidak ada di snapshot terakhir' hanya
dilakukan pada batch terakhir.
"""
import json

import frappe
from frappe.utils import cint, get_datetime, now_datetime

BATCH_MAKS = 500
DOCTYPE = "HRIS Device User"


def _bersih(s, panjang=140):
    return str(s or "").replace("\x00", "").strip()[:panjang]


def save_device_users(device=None, users=None, snapshot_at=None, is_last=0):
    if not device or not frappe.db.exists("HRIS Device", device):
        frappe.throw("HRIS Device tidak ditemukan: {0}".format(device))
    if not frappe.db.get_value("HRIS Device", device, "is_active"):
        frappe.throw("HRIS Device tidak aktif: {0}".format(device))

    if isinstance(users, str):
        users = json.loads(users or "[]")
    users = users or []
    if len(users) > BATCH_MAKS:
        frappe.throw("Batch terlalu besar (maks {0} user).".format(BATCH_MAKS))

    snap = get_datetime(snapshot_at) if snapshot_at else now_datetime()
    terakhir = str(is_last).strip().lower() in ("1", "true", "yes")

    hasil = {"device": device, "site": frappe.local.site, "received": len(users), "created": 0, "updated": 0,
             "unchanged": 0, "error": 0, "marked_absent": 0, "results": []}

    for i, u in enumerate(users):
        try:
            uid = _bersih(u.get("device_user_id"), 60)
            if not uid:
                raise ValueError("device_user_id kosong")
            data = {
                "user_name_on_device": _bersih(u.get("name")),
                "privilege": cint(u.get("privilege")),
                "enabled_on_device": 1 if cint(u.get("enabled", 1)) else 0,
                "finger_count": cint(u.get("finger_count")),
            }
            key = "{0}|{1}".format(device, uid)

            if frappe.db.exists(DOCTYPE, key):
                lama = frappe.db.get_value(DOCTYPE, key, list(data.keys()), as_dict=True)
                beda = False
                for k, v in data.items():
                    nilai_lama = lama.get(k)
                    if nilai_lama is None:
                        nilai_lama = "" if isinstance(v, str) else 0
                    if nilai_lama != v:
                        beda = True
                        break
                if beda:
                    frappe.db.set_value(DOCTYPE, key, dict(data, snapshot_at=snap, in_last_snapshot=1))
                    hasil["updated"] += 1
                else:
                    frappe.db.set_value(DOCTYPE, key, {"snapshot_at": snap, "in_last_snapshot": 1},
                                        update_modified=False)
                    hasil["unchanged"] += 1
            else:
                doc = frappe.get_doc(dict(
                    doctype=DOCTYPE, user_key=key, device=device, device_user_id=uid,
                    snapshot_at=snap, in_last_snapshot=1, **data))
                doc.insert(ignore_permissions=True)
                hasil["created"] += 1
        except Exception as e:
            hasil["error"] += 1
            hasil["results"].append({"index": i, "status": "error", "message": str(e)[:200]})

    if terakhir:
        filt = {"device": device, "in_last_snapshot": 1, "snapshot_at": ["<", snap]}
        hasil["marked_absent"] = frappe.db.count(DOCTYPE, filt)
        frappe.db.sql(
            "update `tabHRIS Device User` set in_last_snapshot = 0 "
            "where device = %s and in_last_snapshot = 1 and snapshot_at < %s",
            (device, snap))

    frappe.db.commit()
    return hasil
