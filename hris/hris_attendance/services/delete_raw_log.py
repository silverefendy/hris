"""Hapus massal HRIS Raw Log per mesin dan rentang tanggal.

Hanya menghapus data di database HRIS. Tidak menghubungi mesin absensi.
Pengaman: role, mesin + dua tanggal wajib, konfirmasi nama mesin, tolak bila
ada log berstatus Disetujui/Terkirim atau dipakai HRIS Working Hour.
"""

import frappe
from frappe import _
from frappe.utils import add_days, get_datetime, getdate, now_datetime

DELETE_ROLES = {"System Manager", "HRIS Manager"}
PROTECTED_STATUS = ("Disetujui", "Terkirim")
BATCH = 500
STATUS_TTL = 3600
STALE_SECONDS = 1800


def _cache():
    cache = frappe.cache
    return cache() if callable(cache) else cache


def _status_key(device_name):
    return f"hris_rawlog_delete_status::{device_name}"


def _set_status(device_name, data):
    try:
        data = dict(data, at=str(now_datetime()))
        _cache().set_value(_status_key(device_name), data, expires_in_sec=STATUS_TTL)
    except Exception:
        frappe.log_error(title="HRIS Hapus Raw Log: gagal menyimpan status")


def _check_access():
    if not DELETE_ROLES & set(frappe.get_roles()):
        frappe.throw(_("Anda tidak berhak menghapus Raw Log."), frappe.PermissionError)


def _range(device_name, date_from, date_to):
    if not device_name or not frappe.db.exists("HRIS Device", device_name):
        frappe.throw(_("Mesin wajib dipilih dan harus ada."))
    if not date_from or not date_to:
        frappe.throw(_("Dari Tanggal dan Sampai Tanggal wajib diisi."))
    d1, d2 = getdate(date_from), getdate(date_to)
    if d2 < d1:
        frappe.throw(_("Sampai Tanggal tidak boleh lebih awal dari Dari Tanggal."))
    return d1, d2, f"{d1} 00:00:00", f"{add_days(d2, 1)} 00:00:00"


def _analyze(device_name, d1, d2, start, end):
    params = {"d": device_name, "s": start, "e": end}
    rows = frappe.db.sql(
        """select review_status, count(*) from `tabHRIS Raw Log`
           where device=%(d)s and punch_time>=%(s)s and punch_time<%(e)s
           group by review_status""",
        params,
    )
    per_status = {(r[0] or "(kosong)"): r[1] for r in rows}
    total = sum(per_status.values())
    protected = sum(per_status.get(s, 0) for s in PROTECTED_STATUS)
    used = frappe.db.sql(
        """select count(*) from `tabHRIS Working Hour` wh
           where wh.check_in_log in (select name from `tabHRIS Raw Log`
                   where device=%(d)s and punch_time>=%(s)s and punch_time<%(e)s)
              or wh.check_out_log in (select name from `tabHRIS Raw Log`
                   where device=%(d)s and punch_time>=%(s)s and punch_time<%(e)s)""",
        params,
    )[0][0]

    masalah = []
    if total == 0:
        masalah.append("Tidak ada Raw Log di mesin dan rentang ini.")
    if protected:
        masalah.append(f"{protected} log berstatus Disetujui/Terkirim. Hapus ditolak seluruhnya.")
    if used:
        masalah.append(f"{used} Working Hour memakai log di rentang ini. Hapus ditolak seluruhnya.")

    return {
        "mesin": device_name,
        "dari_tanggal": str(d1),
        "sampai_tanggal": str(d2),
        "total": total,
        "per_status": per_status,
        "dipakai_working_hour": used,
        "masalah": masalah,
        "boleh": not masalah,
    }


@frappe.whitelist()
def check_delete(device_name, date_from, date_to):
    """Cek Dulu: hitung baris yang akan terhapus. Tidak mengubah apa pun."""
    _check_access()
    d1, d2, start, end = _range(device_name, date_from, date_to)
    return _analyze(device_name, d1, d2, start, end)


@frappe.whitelist()
def enqueue_delete(device_name, date_from, date_to, confirm_name):
    """Validasi ulang, lalu antrekan job hapus."""
    _check_access()
    d1, d2, start, end = _range(device_name, date_from, date_to)
    if (confirm_name or "").strip() != device_name:
        frappe.throw(_("Nama mesin pada konfirmasi tidak cocok."))

    info = _analyze(device_name, d1, d2, start, end)
    if not info["boleh"]:
        return {"queued": False, "message": " ".join(info["masalah"])}

    cur = _cache().get_value(_status_key(device_name)) or {}
    if cur.get("status") in ("Antre", "Berjalan") and cur.get("at"):
        age = (now_datetime() - get_datetime(cur["at"])).total_seconds()
        if age < STALE_SECONDS:
            return {"queued": False, "message": "Masih ada penghapusan yang berjalan untuk mesin ini."}

    _set_status(device_name, {"status": "Antre", "user": frappe.session.user, "total": info["total"]})
    frappe.enqueue(
        "hris.hris_attendance.services.delete_raw_log.run_delete_job",
        queue="long",
        timeout=3600,
        device_name=device_name,
        date_from=str(d1),
        date_to=str(d2),
        notify_user=frappe.session.user,
    )
    return {"queued": True, "total": info["total"]}


def run_delete_job(device_name, date_from, date_to, notify_user=None):
    d1, d2, start, end = _range(device_name, date_from, date_to)
    try:
        info = _analyze(device_name, d1, d2, start, end)
        total = info["total"]
        _set_status(device_name, {"status": "Berjalan", "user": notify_user, "total": total, "terhapus": 0})
        if not info["boleh"]:
            raise frappe.ValidationError(" ".join(info["masalah"]))

        filters = [
            ["device", "=", device_name],
            ["punch_time", ">=", start],
            ["punch_time", "<", end],
        ]
        terhapus = 0
        while True:
            names = frappe.get_all("HRIS Raw Log", filters=filters, pluck="name", limit_page_length=BATCH)
            if not names:
                break
            frappe.db.delete("HRIS Raw Log", {"name": ["in", names]})
            frappe.db.commit()
            terhapus += len(names)
            _set_status(
                device_name,
                {"status": "Berjalan", "user": notify_user, "total": total, "terhapus": terhapus},
            )

        frappe.get_doc("HRIS Device", device_name).add_comment(
            "Comment",
            f"Hapus Raw Log oleh {notify_user}: rentang {d1} s/d {d2}, {terhapus} baris dihapus "
            "(hanya data di HRIS; data di mesin tidak disentuh).",
        )
        frappe.db.commit()
        _set_status(
            device_name,
            {
                "status": "Selesai",
                "user": notify_user,
                "total": total,
                "terhapus": terhapus,
                "dari_tanggal": str(d1),
                "sampai_tanggal": str(d2),
            },
        )
        return terhapus
    except Exception as exc:
        frappe.db.rollback()
        _set_status(device_name, {"status": "Gagal", "user": notify_user, "message": str(exc)})
        frappe.log_error(title="HRIS Hapus Raw Log gagal")
        raise


@frappe.whitelist()
def delete_status(device_name):
    """Status penghapusan terakhir (Antre, Berjalan, Selesai, Gagal); kosong bila lewat 1 jam."""
    _check_access()
    status = _cache().get_value(_status_key(device_name)) or {}
    if status.get("at"):
        status["detik"] = int((now_datetime() - get_datetime(status["at"])).total_seconds())
    return status
