"""Tarik log absensi dari mesin lewat pyzk (jalur Pull).

Alur: konek -> verifikasi serial -> baca punch -> simpan sebagai HRIS Raw Log.
Aturan:
- Tidak pernah menulis, menghapus, atau menonaktifkan apa pun di mesin.
- Tidak pernah menghapus data di Frappe.
- Duplikat dicegah oleh punch_key (mesin|ID|waktu) di HRIS Raw Log,
  sehingga tarikan ulang dengan rentang tumpang tindih aman.
- last_pull_at hanya maju bila tarikan tanpa batas akhir (date_to kosong).
"""

import json
from collections import Counter

import frappe
from frappe import _
from frappe.utils import add_days, add_to_date, get_datetime, getdate, now_datetime
from frappe.utils.password import get_decrypted_password

from hris.hris_attendance.services.raw_log_naming import make_punch_key

FIRST_PULL_FROM = "2026-10-01"
CONNECT_TIMEOUT = 10
COMMIT_EVERY = 200
SAMPLE_SIZE = 5
SAVEPOINT = "hris_pull_punch"


# ------------------------------------------------------------------ util

def _clean(value):
    return str(value or "").replace("\x00", "").strip()


def _safe(fn):
    try:
        return _clean(fn())
    except Exception:
        return ""


def _connect(doc):
    """Buka koneksi pyzk. Comm Key dibaca dari field Password, tidak pernah dicetak."""
    try:
        from zk import ZK
    except ImportError:
        frappe.throw(_("Paket pyzk belum terpasang di env bench."))

    host = _clean(doc.ip_address)
    if not host or not doc.port:
        frappe.throw(_("IP Address dan Port Device wajib diisi."))

    raw_key = get_decrypted_password("HRIS Device", doc.name, "comm_key", raise_exception=False)
    key = int(raw_key) if raw_key and str(raw_key).strip().isdigit() else 0

    try:
        zk = ZK(host, port=int(doc.port), timeout=CONNECT_TIMEOUT, password=key, ommit_ping=True)
        return zk.connect()
    except Exception as exc:
        frappe.log_error(title=f"HRIS Pull: gagal konek {doc.name}", message=frappe.get_traceback())
        frappe.throw(_("Gagal menghubungi mesin {0} ({1}:{2}): {3}").format(doc.name, host, doc.port, exc))


def _close(conn):
    try:
        if conn:
            conn.disconnect()
    except Exception:
        pass


def _normalize_serial(value):
    return _clean(value).upper()


def _range(doc, date_from=None, date_to=None):
    """Kembalikan (dari, sampai). sampai = None berarti sampai sekarang."""
    until = getdate(date_to) if date_to else None
    if date_from:
        since = getdate(date_from)
    elif until:
        since = until
    elif doc.last_pull_at:
        since = getdate(add_days(doc.last_pull_at, -1))
    else:
        since = getdate(FIRST_PULL_FROM)
    if until and until < since:
        frappe.throw(_("Tanggal sampai tidak boleh lebih awal dari tanggal dari."))
    return since, until


def _read_records(conn, since, until=None):
    records = conn.get_attendance() or []
    start = get_datetime(f"{since} 00:00:00")
    end = get_datetime(f"{until} 23:59:59") if until else None
    picked = []
    for rec in records:
        if not rec.timestamp:
            continue
        ts = get_datetime(rec.timestamp)
        if ts >= start and (end is None or ts <= end):
            picked.append(rec)
    picked.sort(key=lambda r: get_datetime(r.timestamp))
    return len(records), picked


def _existing_keys(device, records):
    if not records:
        return set()
    times = [get_datetime(r.timestamp) for r in records]
    rows = frappe.get_all(
        "HRIS Raw Log",
        filters={"device": device, "punch_time": ["between", [min(times), max(times)]]},
        pluck="punch_key",
    )
    return {k for k in rows if k}


def _legacy_rows(device):
    """Baris Pull lama tanpa punch_key (tidak terlindungi dari duplikat)."""
    return frappe.db.count(
        "HRIS Raw Log",
        {"device": device, "source": "Pull pyzk", "punch_key": ["is", "not set"]},
    )


def _ensure_ready(doc):
    if not doc.is_active:
        frappe.throw(_("Device {0} tidak aktif.").format(doc.name))
    if not doc.use_pull:
        frappe.throw(_("Device {0} belum mencentang Via Pull (pyzk).").format(doc.name))
    legacy = _legacy_rows(doc.name)
    if legacy:
        frappe.throw(
            _("Ada {0} baris Raw Log Pull lama tanpa punch_key pada Device {1}. Hapus baris itu dulu agar tidak terjadi duplikat.").format(
                legacy, doc.name
            )
        )


# ------------------------------------------------------------------ tombol A

@frappe.whitelist()
def fetch_device_info(device_name):
    """Baca-saja: ambil serial, firmware, model, jam mesin. Tidak menyimpan apa pun."""
    frappe.has_permission("HRIS Device", "write", doc=device_name, throw=True)
    doc = frappe.get_doc("HRIS Device", device_name)
    conn = _connect(doc)
    try:
        return {
            "serial_number": _clean(conn.get_serialnumber()),
            "firmware_version": _safe(conn.get_firmware_version),
            "device_model": _safe(conn.get_device_name) or _safe(conn.get_platform),
            "device_time": str(conn.get_time()),
        }
    finally:
        _close(conn)


# ------------------------------------------------------------------ dry-run (console)

def dry_run(device_name, date_from=None, date_to=None):
    """Tarik lalu tampilkan ringkasan. TIDAK menyimpan apa pun."""
    doc = frappe.get_doc("HRIS Device", device_name)
    since, until = _range(doc, date_from, date_to)
    conn = _connect(doc)
    try:
        serial_mesin = _clean(conn.get_serialnumber())
        total, records = _read_records(conn, since, until)
    finally:
        _close(conn)

    seen = _existing_keys(doc.name, records)
    limit = add_to_date(now_datetime(), days=1)

    sudah_ada = masa_depan = 0
    for rec in records:
        ts = get_datetime(rec.timestamp)
        if ts > limit:
            masa_depan += 1
            continue
        key = make_punch_key(doc.name, _clean(rec.user_id), ts)
        if key in seen:
            sudah_ada += 1
        else:
            seen.add(key)

    def _row(rec):
        return {"user_id": _clean(rec.user_id), "waktu": str(rec.timestamp), "status": rec.status, "punch": rec.punch}

    return {
        "mode": "DRY-RUN (tidak ada yang disimpan)",
        "device": doc.name,
        "serial_mesin": serial_mesin,
        "serial_device": doc.serial_number,
        "serial_cocok": _normalize_serial(serial_mesin) == _normalize_serial(doc.serial_number),
        "dari_tanggal": str(since),
        "sampai_tanggal": str(until) if until else None,
        "total_punch_di_mesin": total,
        "punch_dalam_rentang": len(records),
        "waktu_tertua": str(records[0].timestamp) if records else None,
        "waktu_terbaru": str(records[-1].timestamp) if records else None,
        "user_id_unik": len({_clean(r.user_id) for r in records}),
        "sudah_ada_di_raw_log": sudah_ada,
        "ditolak_waktu_masa_depan": masa_depan,
        "akan_masuk_sebagai_baru": len(records) - sudah_ada - masa_depan,
        "baris_pull_lama_tanpa_punch_key": _legacy_rows(doc.name),
        "sebaran_status_punch": {
            f"status={s}, punch={p}": n for (s, p), n in Counter((r.status, r.punch) for r in records).items()
        },
        "contoh_terbaru": [_row(r) for r in records[-SAMPLE_SIZE:]],
    }


# ------------------------------------------------------------------ tarikan sungguhan

@frappe.whitelist()
def enqueue_pull(device_name, date_from=None, date_to=None):
    """Antrekan tarikan sungguhan. Satu Device hanya satu job pada satu waktu."""
    frappe.has_permission("HRIS Device", "write", doc=device_name, throw=True)
    frappe.enqueue(
        "hris.hris_attendance.services.pull_device.pull",
        queue="long",
        timeout=1800,
        job_id=f"hris_pull::{device_name}",
        deduplicate=True,
        device_name=device_name,
        date_from=date_from or None,
        date_to=date_to or None,
    )
    return {"queued": True}


def pull(device_name, date_from=None, date_to=None):
    """Tarik dan simpan sebagai HRIS Raw Log. Serial wajib cocok dengan Device."""
    doc = frappe.get_doc("HRIS Device", device_name)
    _ensure_ready(doc)
    since, until = _range(doc, date_from, date_to)

    conn = _connect(doc)
    try:
        serial_mesin = _clean(conn.get_serialnumber())
        if _normalize_serial(serial_mesin) != _normalize_serial(doc.serial_number):
            msg = _("Serial mesin ({0}) berbeda dari Serial Number Device ({1}). Tarikan dihentikan.").format(
                serial_mesin, doc.serial_number
            )
            doc.add_comment("Info", msg)
            frappe.db.commit()
            frappe.throw(msg)
        total, records = _read_records(conn, since, until)
    finally:
        _close(conn)

    counts = Counter()
    errors = []
    limit = add_to_date(now_datetime(), days=1)
    existing = _existing_keys(doc.name, records)

    for rec in records:
        ts = get_datetime(rec.timestamp)
        user_id = _clean(rec.user_id)
        if ts > limit:
            counts["ditolak_masa_depan"] += 1
            continue
        if not user_id:
            counts["gagal"] += 1
            continue
        key = make_punch_key(doc.name, user_id, ts)
        if key in existing:
            counts["sudah_ada"] += 1
            continue

        frappe.db.savepoint(SAVEPOINT)
        try:
            frappe.get_doc(
                {
                    "doctype": "HRIS Raw Log",
                    "device": doc.name,
                    "device_user_id": user_id,
                    "punch_time": ts,
                    "verify_mode": str(rec.status),
                    "punch_status_raw": str(rec.punch),
                    "source": "Pull pyzk",
                    "raw_payload": json.dumps(
                        {"uid": rec.uid, "user_id": user_id, "timestamp": str(ts), "status": rec.status, "punch": rec.punch}
                    ),
                }
            ).insert(ignore_permissions=True)
            existing.add(key)
            counts["baru"] += 1
            if counts["baru"] % COMMIT_EVERY == 0:
                frappe.db.commit()
        except frappe.DuplicateEntryError:
            frappe.db.rollback(save_point=SAVEPOINT)
            existing.add(key)
            counts["sudah_ada"] += 1
        except Exception as exc:
            frappe.db.rollback(save_point=SAVEPOINT)
            counts["gagal"] += 1
            if len(errors) < 3:
                errors.append(f"{key}: {exc}")

    update_last = not counts["gagal"] and not until
    if update_last:
        frappe.db.set_value("HRIS Device", doc.name, "last_pull_at", now_datetime(), update_modified=False)

    result = {
        "device": doc.name,
        "dari_tanggal": str(since),
        "sampai_tanggal": str(until) if until else None,
        "total_punch_di_mesin": total,
        "punch_dalam_rentang": len(records),
        "baru": counts["baru"],
        "sudah_ada": counts["sudah_ada"],
        "gagal": counts["gagal"],
        "ditolak_masa_depan": counts["ditolak_masa_depan"],
        "last_pull_at_diperbarui": update_last,
        "contoh_error": errors,
    }
    doc.add_comment(
        "Info",
        "Tarikan Pull selesai: baru {baru}, sudah ada {sudah_ada}, gagal {gagal}, "
        "ditolak masa depan {ditolak_masa_depan} (dari {dari_tanggal} sampai {sampai_tanggal}).".format(**result),
    )
    if errors:
        frappe.log_error(title=f"HRIS Pull: {doc.name} ada yang gagal", message="\n".join(errors))
    frappe.db.commit()
    return result
