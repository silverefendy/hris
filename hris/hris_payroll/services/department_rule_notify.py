"""K-137 (E8): pemberitahuan slip Draft saat HRIS Department Rule berubah.

Slip Ditinjau/Final tidak disentuh. Slip Draft tidak berubah sendiri; pemberitahuan hanya
memberi tahu bahwa Hitung Ulang diperlukan bila ingin pengali baru.
"""

import frappe
from frappe import _
from frappe.utils import cint, flt, getdate

DEPT = "HRIS Department"
SLIP = "HRIS Payroll Slip"
RULE = "HRIS Department Rule"
PERAN_PENERIMA = ("HRIS Payroll Manager", "HRIS Payroll Admin")


def _berubah(doc, sebelum):
    """True bila rule baru atau salah satu field yang memengaruhi hitungan berubah."""
    if sebelum is None:
        return True
    return (
        doc.department != sebelum.department
        or getdate(doc.effective_from) != getdate(sebelum.effective_from)
        or cint(doc.is_active) != cint(sebelum.is_active)
        or flt(doc.overtime_multiplier) != flt(sebelum.overtime_multiplier)
    )


def hitung_slip_draft(daftar_department, tanggal_awal):
    """Jumlah slip Draft pada subtree Department (inklusif) dengan period_end >= tanggal_awal."""
    if not (frappe.db.table_exists(SLIP) and frappe.db.table_exists(DEPT)):
        return 0
    nama = set()
    for d in daftar_department:
        batas = frappe.db.get_value(DEPT, d, ["lft", "rgt"])
        if not batas or batas[0] is None:
            nama.add(d)
            continue
        nama.update(frappe.get_all(DEPT, filters={"lft": [">=", batas[0]], "rgt": ["<=", batas[1]]}, pluck="name"))
    if not nama:
        return 0
    filters = {"status": "Draft", "department": ["in", sorted(nama)], "period_end": [">=", getdate(tanggal_awal)]}
    if frappe.get_meta(SLIP).has_field("overtime_hours"):
        filters["overtime_hours"] = [">", 0]
    return frappe.db.count(SLIP, filters)


def kirim_notifikasi(doc, jumlah):
    """Notification Log in-app ke pemegang peran Payroll. Mengembalikan jumlah penerima."""
    from hris.hris_payroll.doctype.hris_payroll_period.hris_payroll_period import _penerima

    isi = _("{0} slip Draft mungkin memakai pengali lama (aturan {1}, Department {2}). Pakai Hitung Ulang bila ingin pengali baru.").format(
        jumlah, doc.name, doc.department
    )
    penerima = set()
    for peran in PERAN_PENERIMA:
        if frappe.db.exists("Role", peran):
            penerima.update(_penerima(peran))
    frappe.db.savepoint("hdr_notif")
    try:
        for user in sorted(penerima):
            frappe.get_doc(
                {
                    "doctype": "Notification Log",
                    "subject": isi,
                    "for_user": user,
                    "from_user": frappe.session.user,
                    "type": "Alert",
                    "document_type": RULE,
                    "document_name": doc.name,
                }
            ).insert(ignore_permissions=True)
    except Exception:
        frappe.db.rollback(save_point="hdr_notif")
        frappe.log_error(title="HRIS Department Rule: notifikasi slip Draft gagal")
        return 0
    return len(penerima)


def setelah_simpan(doc):
    """Dipanggil dari on_update controller. Tidak boleh membatalkan penyimpanan Rule."""
    try:
        sebelum = doc.get_doc_before_save()
        if not _berubah(doc, sebelum):
            return
        awal = getdate(doc.effective_from)
        daftar = {doc.department}
        if sebelum is not None:
            awal = min(awal, getdate(sebelum.effective_from))
            daftar.add(sebelum.department)
        jumlah = hitung_slip_draft(sorted(daftar), awal)
        if jumlah <= 0:
            return
        kirim_notifikasi(doc, jumlah)
        frappe.msgprint(
            _("{0} slip Draft pada Department ini (dan cabangnya) mungkin memakai pengali lama. Gunakan Hitung Ulang bila ingin pengali baru. Slip Ditinjau atau Final tidak berubah.").format(jumlah),
            title=_("Slip Draft terpengaruh"),
            indicator="orange",
        )
    except Exception:
        frappe.log_error(title="HRIS Department Rule: pemberitahuan slip Draft gagal")
