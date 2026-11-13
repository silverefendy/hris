"""Penelusuran komponen gaji per Department (E1 tahap 2). Terpisah dari resolve() pengali lembur.

Naik dari Department ke akar: Berlaku = nilai; Tidak Berlaku = berhenti (0); Ikut Induk atau
tidak ada baris = lanjut. Sampai akar tanpa hasil = tidak berlaku (bukan galat).
"""
import frappe
from frappe.utils import flt, getdate
from frappe.utils.nestedset import get_ancestors_of

DEPT = "HRIS Department"
RULE = "HRIS Department Rule"
ANAK = "HRIS Department Rule Component"


def pilih_komponen(rantai, aturan, baris, tanggal):
    """Fungsi murni. aturan = [{name, department, effective_from, creation}];
    baris = [{parent, component, status, amount}] untuk komponen yang dicari."""
    tanggal = getdate(tanggal)
    for dept in rantai:
        kandidat = [a for a in aturan if a["department"] == dept and getdate(a["effective_from"]) <= tanggal]
        for a in sorted(kandidat, key=lambda x: (getdate(x["effective_from"]), str(x.get("creation") or "")), reverse=True):
            b = next((x for x in baris if x["parent"] == a["name"]), None)
            if not b or b["status"] == "Ikut Induk":
                continue
            if b["status"] == "Tidak Berlaku":
                return {"nilai": 0.0, "berlaku": False, "aturan": a["name"], "department": dept}
            return {"nilai": flt(b["amount"]), "berlaku": True, "aturan": a["name"], "department": dept}
    return {"nilai": 0.0, "berlaku": False, "aturan": None, "department": None}


def resolve_komponen(department, tanggal, kode):
    if not department:
        return {"nilai": 0.0, "berlaku": False, "aturan": None, "department": None}
    rantai = [department] + list(get_ancestors_of(DEPT, department))
    aturan = frappe.get_all(RULE, filters={"department": ["in", rantai], "is_active": 1,
                            "effective_from": ["<=", getdate(tanggal)]},
                            fields=["name", "department", "effective_from", "creation"])
    if not aturan:
        return {"nilai": 0.0, "berlaku": False, "aturan": None, "department": None}
    baris = frappe.get_all(ANAK, filters={"parent": ["in", [a["name"] for a in aturan]], "parenttype": RULE, "component": kode},
                           fields=["parent", "component", "status", "amount"])
    return pilih_komponen(rantai, aturan, baris, tanggal)
