"""Pencarian tarif TER PPh 21 dan pembuat pesan galat (K-134, langkah 1)."""
import frappe
from frappe.utils import escape_html, flt, getdate, today


def pesan(masalah, penyebab, tindakan, berwenang):
    """Pesan galat berpola Masalah, Penyebab, Tindakan, Berwenang."""
    return (
        f"<b>Masalah:</b> {escape_html(masalah)}<br>"
        f"<b>Penyebab:</b> {escape_html(penyebab)}<br>"
        f"<b>Tindakan:</b> {escape_html(tindakan)}<br>"
        f"<b>Berwenang:</b> {escape_html(berwenang)}"
    )


def find_rate(ter_category, bruto, on_date=None):
    """Kembalikan baris tarif untuk kategori dan bruto, atau None.

    Set tarif yang berlaku = semua baris aktif dengan 'Berlaku Sejak' terbaru
    yang tanggalnya <= on_date. Set itu menggantikan seluruh set yang lebih lama.
    """
    on_date = getdate(on_date or today())
    kategori = (ter_category or "").strip().upper()
    baris = frappe.get_all(
        "HRIS PPh21 TER Rate",
        filters={"ter_category": kategori, "enabled": 1, "effective_from": ["<=", on_date]},
        fields=["name", "ter_category", "effective_from", "bruto_from", "bruto_to",
                "open_ended", "rate_percent"],
        order_by="effective_from desc, bruto_from asc",
    )
    if not baris:
        return None
    set_berlaku = baris[0].effective_from
    bruto = flt(bruto)
    for r in baris:
        if r.effective_from != set_berlaku:
            continue
        atas_ok = bool(r.open_ended) or bruto <= flt(r.bruto_to)
        if bruto >= flt(r.bruto_from) and atas_ok:
            return r
    return None


def set_pasal17(on_date=None):
    """Baris tarif Pasal 17 pada set yang berlaku di on_date (Berlaku Sejak terbaru yang <= on_date), urut bruto_from."""
    on_date = getdate(on_date or today())
    baris = frappe.get_all(
        "HRIS PPh21 Pasal17 Rate",
        filters={"enabled": 1, "effective_from": ["<=", on_date]},
        fields=["name", "effective_from", "bruto_from", "bruto_to", "open_ended", "rate_percent"],
        order_by="effective_from desc, bruto_from asc",
    )
    if not baris:
        return []
    set_berlaku = baris[0].effective_from
    return [x for x in baris if x.effective_from == set_berlaku]


def find_rate17(bruto, on_date=None):
    """Kembalikan baris tarif Pasal 17 yang mencakup bruto setahun pada on_date, atau None."""
    bruto = flt(bruto)
    for x in set_pasal17(on_date):
        atas_ok = bool(x.open_ended) or bruto <= flt(x.bruto_to)
        if bruto >= flt(x.bruto_from) and atas_ok:
            return x
    return None


def kategori_ter_aktif():
    """Himpunan kategori TER (huruf besar) yang punya baris tarif aktif."""
    daftar = frappe.get_all("HRIS PPh21 TER Rate", filters={"enabled": 1}, pluck="ter_category")
    return {(k or "").strip().upper() for k in daftar if (k or "").strip()}
