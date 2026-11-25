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


# --- Kiriman Agen Windows (jenis "Kirim Agen") ---
JENIS_KIRIM_AGEN = "Kirim Agen"
JENDELA_SESI_MENIT = 5


def catat_kirim_agen(device_name, ringkasan):
    """Catat satu panggilan push_punches ke HRIS Pull Run (jenis Kirim Agen).

    Panggilan untuk mesin yang sama dalam JENDELA_SESI_MENIT sejak panggilan
    sebelumnya dijumlahkan ke satu record, sehingga satu pengiriman Device Tool
    (banyak batch) menjadi satu baris. Detak (0 baris) tidak dicatat.
    Aman-gagal: error dicatat ke Error Log dan tidak pernah dilempar ke proses
    penyimpanan punch. Mengembalikan nama record, atau None.
    """
    try:
        ringkasan = ringkasan or {}
        diterima = int(ringkasan.get("received") or 0)
        if diterima <= 0 or not device_name:
            return None
        baru = int(ringkasan.get("created") or 0)
        sudah = int(ringkasan.get("duplicate") or 0)
        gagal_n = int(ringkasan.get("error") or 0)
        pesan = ""
        if gagal_n:
            for r in ringkasan.get("results") or []:
                if r.get("status") == "error":
                    pesan = str(r.get("message") or "")[:1000]
                    break

        from frappe.utils import add_to_date

        sekarang = now_datetime()
        batas = add_to_date(sekarang, minutes=-JENDELA_SESI_MENIT)
        ada = frappe.get_all(
            DOCTYPE,
            filters=[
                ["jenis", "=", JENIS_KIRIM_AGEN],
                ["device", "=", device_name],
                ["finished_at", ">=", batas],
            ],
            pluck="name",
            order_by="finished_at desc",
            limit_page_length=1,
        )
        if ada:
            frappe.db.sql(
                """update `tabHRIS Pull Run`
                set punch_dalam_rentang = ifnull(punch_dalam_rentang, 0) + %s,
                    baru = ifnull(baru, 0) + %s,
                    sudah_ada = ifnull(sudah_ada, 0) + %s,
                    gagal = ifnull(gagal, 0) + %s,
                    finished_at = %s, modified = %s
                where name = %s""",
                (diterima, baru, sudah, gagal_n, sekarang, sekarang, ada[0]),
            )
            if pesan:
                frappe.db.set_value(DOCTYPE, ada[0], "pesan_error", pesan, update_modified=False)
            frappe.db.commit()
            return ada[0]

        company = frappe.db.get_value("HRIS Device", device_name, "company")
        doc = frappe.get_doc(
            {
                "doctype": DOCTYPE,
                "jenis": JENIS_KIRIM_AGEN,
                "device": device_name,
                "company": company,
                "status": "Selesai",
                "mode": "Otomatis",
                "started_at": sekarang,
                "finished_at": sekarang,
                "requested_by": frappe.session.user,
                "punch_dalam_rentang": diterima,
                "baru": baru,
                "sudah_ada": sudah,
                "gagal": gagal_n,
                "pesan_error": pesan,
            }
        ).insert(ignore_permissions=True)
        frappe.db.commit()
        return doc.name
    except Exception:
        frappe.log_error(title="HRIS Pull Run: gagal mencatat kiriman agen")
        return None
