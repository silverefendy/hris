"""Tunjangan dan potongan komponen pada HRIS Payroll Slip (3b).

Memakai hitung_tunjangan_karyawan (komponen_slip.py) untuk tiap komponen aktif di katalog HRIS Pay Component.
Saklar K1: kunci hris_tunjangan_ikut_pajak di site_config.json (bawaan mati). Mati: tunjangan tidak ikut bruto PPh 21.
"""

from decimal import ROUND_HALF_UP, Decimal

import frappe
from frappe import _
from frappe.utils import cint, cstr, getdate

from hris.hris_payroll.services.komponen_slip import hitung_tunjangan_karyawan

KATALOG = "HRIS Pay Component"
PERIOD = "HRIS Payroll Period"
SAKLAR = "hris_tunjangan_ikut_pajak"
PERAN_PEMERIKSA = "HRIS Payroll Manager"
KUNCI = "hris_slip_tunjangan"
CONTOH_MAKS = 5
BERWENANG = "HRD (HRIS HR Admin atau HRIS Employee Admin)"


def saklar_pajak_hidup():
    """True bila tunjangan boleh ikut dasar PPh 21 (kunci site_config hris_tunjangan_ikut_pajak bernilai 1)."""
    return bool(cint(frappe.conf.get(SAKLAR)))


def _rupiah(nilai):
    return int(Decimal(str(nilai or 0)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _teks(x):
    return x if isinstance(x, str) else frappe.as_json(x)


def susun_tunjangan(he, pay_type, awal, akhir, baris_hitung):
    """Menghitung semua komponen aktif untuk satu karyawan.

    Mengembalikan {"komponen": [dict seperti keluaran hitung_komponen + kunci taxable],
                   "catatan": [teks untuk calc_notes], "galat": [(kode, pesan)], "periksa": bool}.
    """
    hasil = {"komponen": [], "catatan": [], "galat": [], "periksa": False}
    daftar = frappe.get_all(KATALOG, filters={"is_active": 1}, fields=["name", "component_type", "is_taxable"], order_by="name")
    if not daftar:
        return hasil
    tanggal_hadir = sorted({
        getdate(b["work_date"]) for b in baris_hitung if b.get("status") == "Hadir" and b.get("work_date")
    })
    ikut_pajak = saklar_pajak_hidup()
    for k in daftar:
        r = hitung_tunjangan_karyawan(he.name, k.name, pay_type, str(awal), str(akhir), tanggal_hadir)
        if r.get("error"):
            hasil["galat"].append((k.name, cstr(r["error"])))
            continue
        for p in r.get("janggal") or []:
            hasil["catatan"].append(_("Komponen {0} janggal: {1}").format(k.name, _teks(p)))
            hasil["periksa"] = True
        for p in r.get("peringatan") or []:
            hasil["catatan"].append(_("Komponen {0}: {1}").format(k.name, _teks(p)))
            hasil["periksa"] = True
        jumlah = _rupiah(r.get("jumlah"))
        if jumlah <= 0:
            continue
        tipe = r.get("tipe") or k.component_type
        taxable = 1 if (tipe == "Pendapatan" and ikut_pajak and cint(k.is_taxable)) else 0
        hasil["komponen"].append({
            "nama": r.get("nama") or k.name, "tipe": tipe, "jumlah": jumlah,
            "dasar": cstr(r.get("dasar")), "taxable": taxable,
        })
    return hasil


def pesan_galat(galat):
    """Pesan karyawan dilewati (D1): bentuk Masalah, Penyebab, Tindakan, Berwenang."""
    rinci = "; ".join("{0}: {1}".format(kode, teks) for kode, teks in galat)
    return _(
        "Masalah: komponen gaji tidak dapat dihitung untuk karyawan ini ({0}). "
        "Penyebab: aturan komponen tidak cocok dengan jenis gaji karyawan, atau nilai dasar komponen belum lengkap. "
        "Tindakan: HRD memperbaiki katalog komponen atau nilai dasarnya, atau menonaktifkan komponen itu, "
        "lalu slip dibuat atau dihitung ulang. Berwenang: {1}."
    ).format(rinci, BERWENANG)


def nama_ganda(komponen, baris_slip):
    """K7: peringatan bila ada baris Manual dengan nama dan jenis sama dengan komponen otomatis (risiko terbayar dua kali)."""
    manual = {((r.component or "").strip().lower(), r.component_type) for r in baris_slip if r.source == "Manual"}
    catatan = []
    for k in komponen:
        if ((k["nama"] or "").strip().lower(), k["tipe"]) in manual:
            catatan.append(_("Peringatan: ada baris Manual {0} dan komponen otomatis {0} dengan nama dan jenis sama; periksa agar tidak terbayar dua kali.").format(k["nama"]))
    return catatan


# ---------- ringkasan untuk notifikasi (D2) ----------
def mulai_ringkasan():
    frappe.flags[KUNCI] = {"periksa": [], "galat": []}


def catat(jenis, nama, pesan=None):
    """jenis = "periksa" (nama slip) atau "galat" (nama karyawan, pesan). Tidak berbuat apa pun di luar proses massal."""
    s = frappe.flags.get(KUNCI)
    if s is None:
        return
    s[jenis].append((nama, pesan) if jenis == "galat" else nama)


def _kirim(nama_periode, isi):
    from hris.hris_payroll.doctype.hris_payroll_period.hris_payroll_period import _penerima

    try:
        frappe.db.savepoint("tunj_notif")
        penerima = set(_penerima(PERAN_PEMERIKSA))
        if frappe.session.user not in ("Administrator", "Guest"):
            penerima.add(frappe.session.user)
        for user in sorted(penerima):
            frappe.get_doc({
                "doctype": "Notification Log", "subject": isi, "for_user": user,
                "from_user": frappe.session.user, "type": "Alert",
                "document_type": PERIOD, "document_name": nama_periode,
            }).insert(ignore_permissions=True)
    except Exception:
        frappe.db.rollback(save_point="tunj_notif")
        frappe.log_error(title="HRIS Payroll Slip: notifikasi ringkasan gagal")


def kirim_ringkasan(period):
    """Satu notifikasi per proses massal. Tidak pernah menggagalkan proses slip."""
    s = frappe.flags.get(KUNCI)
    frappe.flags[KUNCI] = None
    if not s or not (s["periksa"] or s["galat"]):
        return
    try:
        bagian = []
        if s["periksa"]:
            bagian.append(_("{0} slip memuat tunjangan yang perlu diperiksa (lihat Catatan Perhitungan di slip; contoh: {1}).").format(
                len(s["periksa"]), ", ".join(s["periksa"][:CONTOH_MAKS])))
        if s["galat"]:
            contoh = ", ".join(n for n, _p in s["galat"][:CONTOH_MAKS])
            bagian.append(_("{0} karyawan dilewati karena komponen gaji bermasalah (contoh: {1}). Alasan pertama: {2}").format(
                len(s["galat"]), contoh, cstr(s["galat"][0][1])[:300]))
        isi = _("Proses slip {0}: ").format(period.name) + " ".join(bagian)
        _kirim(period.name, isi)
    except Exception:
        frappe.log_error(title="HRIS Payroll Slip: ringkasan tunjangan gagal")
