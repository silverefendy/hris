"""Penelusuran HRIS Department Rule (K-136 tahap 5a).

Pewarisan per parameter: nilai kosong/0 ikut Department induk (naik sampai akar);
nilai terisi menimpa. Tanpa nilai sampai akar = error (P10), bukan nilai bawaan diam-diam.
"""

import frappe
from frappe import _
from frappe.utils import flt, getdate
from frappe.utils.nestedset import get_ancestors_of

DEPT = "HRIS Department"
RULE = "HRIS Department Rule"
PARAMETER = ("overtime_multiplier",)


def pilih_nilai(rantai, aturan, tanggal, parameter):
    """Fungsi murni. rantai = [department, induk, ..., akar]; aturan = daftar dict
    (name, department, effective_from, creation, <parameter>). Mengembalikan dict atau None."""
    tanggal = getdate(tanggal)
    for dept in rantai:
        kandidat = [
            a for a in aturan
            if a["department"] == dept
            and getdate(a["effective_from"]) <= tanggal
            and flt(a.get(parameter)) > 0
        ]
        if kandidat:
            terbaik = max(kandidat, key=lambda a: (getdate(a["effective_from"]), str(a.get("creation") or "")))
            return {"nilai": flt(terbaik[parameter]), "aturan": terbaik.get("name"), "department": dept}
    return None


def resolve(department, tanggal, parameter="overtime_multiplier"):
    """Nilai efektif parameter untuk Department pada tanggal tertentu."""
    if parameter not in PARAMETER:
        frappe.throw(_("Parameter {0} tidak dikenal.").format(parameter))
    if not department:
        frappe.throw(_("Department wajib diisi untuk mencari aturan."))
    rantai = [department] + list(get_ancestors_of(DEPT, department))
    aturan = frappe.get_all(
        RULE,
        filters={
            "department": ["in", rantai],
            "is_active": 1,
            "effective_from": ["<=", getdate(tanggal)],
            parameter: [">", 0],
        },
        fields=["name", "department", "effective_from", "creation", parameter],
    )
    hasil = pilih_nilai(rantai, aturan, tanggal, parameter)
    if not hasil:
        frappe.throw(
            _("Tidak ada aturan {0} untuk Department {1} (sampai akar) pada {2}. Buat HRIS Department Rule dahulu.").format(
                parameter, department, getdate(tanggal)
            )
        )
    return hasil
