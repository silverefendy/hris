"""Pencatatan riwayat tarik dan hapus Raw Log ke HRIS Pull Run.

Semua fungsi aman-gagal: error dicatat ke Error Log dan tidak pernah
dilempar ke proses utama.
"""

import frappe
from frappe.utils import now_datetime

DOCTYPE = "HRIS Pull Run"


def buat(jenis, device_name, date_from=None, date_to=None, user=None):
    """Buat record Antre. Kembalikan nama record, atau None bila gagal."""
    try:
        company = frappe.db.get_value("HRIS Device", device_name, "company")
        doc = frappe.get_doc(
            {
                "doctype": DOCTYPE,
                "jenis": jenis,
                "device": device_name,
                "company": company,
                "status": "Antre",
                "mode": "Rentang Tanggal" if date_from else "Otomatis",
                "date_from": date_from,
                "date_to": date_to,
                "requested_by": user or frappe.session.user,
            }
        ).insert(ignore_permissions=True)
        frappe.db.commit()
        return doc.name
    except Exception:
        frappe.log_error(title="HRIS Pull Run: gagal membuat record")
        return None


def _update(run_name, values):
    if not run_name:
        return
    try:
        frappe.db.set_value(DOCTYPE, run_name, values, update_modified=True)
        frappe.db.commit()
    except Exception:
        frappe.log_error(title=f"HRIS Pull Run: gagal memperbarui {run_name}")


def mulai(run_name):
    _update(run_name, {"status": "Berjalan", "started_at": now_datetime()})


def selesai_tarik(run_name, result):
    _update(
        run_name,
        {
            "status": "Selesai",
            "finished_at": now_datetime(),
            "punch_dalam_rentang": result.get("punch_dalam_rentang") or 0,
            "baru": result.get("baru") or 0,
            "sudah_ada": result.get("sudah_ada") or 0,
            "gagal": result.get("gagal") or 0,
            "last_pull_at_diperbarui": 1 if result.get("last_pull_at_diperbarui") else 0,
        },
    )


def selesai_hapus(run_name, terhapus):
    _update(
        run_name,
        {"status": "Selesai", "finished_at": now_datetime(), "jumlah_dihapus": terhapus or 0},
    )


def gagal(run_name, pesan):
    _update(
        run_name,
        {"status": "Gagal", "finished_at": now_datetime(), "pesan_error": str(pesan)[:1000]},
    )
