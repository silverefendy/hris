"""Payroll Summary fase 2a: menyimpan pengecualian tunjangan (HEC) dari halaman.

rencanakan() murni (tanpa database): menghitung baris HEC mana yang dinonaktifkan, dipersempit atau
diperluas, dan dibuat, agar pengecualian baru MENGGANTIKAN isi rentangnya dan rentang bersambung
bernilai sama digabung. simpan_pengecualian() menjalankan rencana lewat DocType HEC (semua aturan HEC
tetap berlaku) dalam satu transaksi.
"""
import frappe
from frappe import _
from frappe.utils import add_days, cstr, flt, getdate

HEC = "HRIS Employee Component"
EMP = "HRIS Employee"
KATALOG = "HRIS Pay Component"
AKSI = ("Berlaku", "Tidak Berlaku", "Hapus")
SP = "hec_pengecualian"


def _sama(a, b):
    return a["status"] == b["status"] and abs(flt(a["amount"]) - flt(b["amount"])) < 0.0001


def _hari(d, n):
    return getdate(add_days(d, n))


def rencanakan(existing, aksi, dari, sampai, amount=0, gabung_tetangga=True):
    """existing = baris HEC AKTIF (satu karyawan dan komponen): [{name, status, amount, date_from, date_to}].
    Mengembalikan {"nonaktif": [nama], "ubah": [{name, date_from, date_to, menyusut, utama}],
    "buat": [{status, amount, date_from, date_to, utama}]}. 'ubah' berurut: yang menyusut dulu."""
    o_dari, o_sampai = getdate(dari), getdate(sampai)
    if o_sampai < o_dari:
        raise ValueError("sampai sebelum dari")
    nilai_n = {"status": aksi, "amount": 0.0 if aksi == "Tidak Berlaku" else flt(amount)}

    u_dari, u_sampai = o_dari, o_sampai
    asli, diserap = {}, []
    for e in existing:
        ef, et = getdate(e["date_from"]), getdate(e["date_to"])
        asli[e["name"]] = {"dari": ef, "sampai": et}
        menyentuh = not (et < o_dari or ef > o_sampai)
        if aksi != "Hapus" and menyentuh and _sama({"status": e["status"], "amount": flt(e["amount"])}, nilai_n):
            diserap.append(e["name"])
            u_dari, u_sampai = min(u_dari, ef), max(u_sampai, et)

    segmen = []
    for e in existing:
        if e["name"] in diserap:
            continue
        ef, et = asli[e["name"]]["dari"], asli[e["name"]]["sampai"]
        dasar = {"status": e["status"], "amount": flt(e["amount"]), "utama": False}
        if et < u_dari or ef > u_sampai:
            segmen.append(dict(dasar, name=e["name"], dari=ef, sampai=et, disentuh=False))
            continue
        kiri, kanan = ef < u_dari, et > u_sampai
        if kiri:
            segmen.append(dict(dasar, name=e["name"], dari=ef, sampai=_hari(u_dari, -1), disentuh=True))
        if kanan:
            segmen.append(dict(dasar, name=None if kiri else e["name"], dari=_hari(u_sampai, 1), sampai=et, disentuh=True))
        # tidak kiri dan tidak kanan: tertutup penuh, tidak ada segmen (akan dinonaktifkan)
    if aksi != "Hapus":
        segmen.append(dict(nilai_n, name=diserap[0] if diserap else None, dari=u_dari, sampai=u_sampai,
                           disentuh=True, utama=True))

    segmen.sort(key=lambda s: (s["dari"], s["sampai"]))
    hasil = []
    for s in segmen:
        p = hasil[-1] if hasil else None
        if p and _sama(p, s) and s["dari"] == _hari(p["sampai"], 1):
            syarat = (p["disentuh"] or s["disentuh"]) if gabung_tetangga else (p["disentuh"] and s["disentuh"])
            if syarat:
                p["sampai"] = s["sampai"]
                p["disentuh"] = True
                p["utama"] = p["utama"] or s["utama"]
                if not p["name"]:
                    p["name"] = s["name"]
                continue
        hasil.append(dict(s))

    ada, ubah, buat = set(), [], []
    for s in hasil:
        if s["name"]:
            ada.add(s["name"])
            a = asli[s["name"]]
            if a["dari"] != s["dari"] or a["sampai"] != s["sampai"]:
                ubah.append({
                    "name": s["name"], "date_from": s["dari"], "date_to": s["sampai"], "utama": s["utama"],
                    "menyusut": s["dari"] >= a["dari"] and s["sampai"] <= a["sampai"],
                })
        else:
            buat.append({"status": s["status"], "amount": s["amount"], "date_from": s["dari"],
                         "date_to": s["sampai"], "utama": s["utama"]})
    nonaktif = [n for n in asli if n not in ada]
    ubah.sort(key=lambda u: (not u["menyusut"], u["date_from"]))
    return {"nonaktif": nonaktif, "ubah": ubah, "buat": buat}


def _alasan(lama, baru):
    return baru if cstr(lama) != baru else baru + " (ulang)"


def _ambil(employee, component):
    return frappe.get_all(
        HEC,
        filters={"employee": employee, "component": component, "is_active": 1},
        fields=["name", "status", "amount", "date_from", "date_to"],
        order_by="date_from asc",
    )


def _jalankan(rencana, employee, component, reason):
    n_off = n_ubah = n_buat = 0
    for nama in rencana["nonaktif"]:
        d = frappe.get_doc(HEC, nama)
        d.is_active = 0
        d.reason = _alasan(d.reason, "Diganti: " + reason)
        d.save()
        n_off += 1
    for u in rencana["ubah"]:
        d = frappe.get_doc(HEC, u["name"])
        d.date_from, d.date_to = u["date_from"], u["date_to"]
        d.reason = _alasan(d.reason, reason if u["utama"] else "Disesuaikan: " + reason)
        d.save()
        n_ubah += 1
    for b in rencana["buat"]:
        frappe.get_doc({
            "doctype": HEC, "employee": employee, "component": component, "status": b["status"],
            "amount": b["amount"], "date_from": b["date_from"], "date_to": b["date_to"], "is_active": 1,
            "reason": reason if b["utama"] else "Disesuaikan: " + reason,
        }).insert()
        n_buat += 1
    return {"dibuat": n_buat, "diubah": n_ubah, "dinonaktifkan": n_off}


@frappe.whitelist()
def simpan_pengecualian(employee, component, aksi, date_from, date_to, reason, amount=0):
    frappe.has_permission(HEC, "create", throw=True)
    if aksi not in AKSI:
        frappe.throw(_("Aksi harus Berlaku, Tidak Berlaku, atau Hapus."))
    reason = (reason or "").strip()
    if not reason:
        frappe.throw(_("Alasan wajib diisi."))
    if flt(amount) < 0:
        frappe.throw(_("Nominal Khusus tidak boleh negatif."))
    dari, sampai = getdate(date_from), getdate(date_to)
    if sampai < dari:
        frappe.throw(_("Sampai tidak boleh sebelum Dari."))
    if not frappe.db.exists(EMP, employee):
        frappe.throw(_("Karyawan tidak ditemukan."))
    if not frappe.db.exists(KATALOG, component):
        frappe.throw(_("Komponen tidak ditemukan di katalog."))

    existing = _ambil(employee, component)
    rencana = rencanakan(existing, aksi, dari, sampai, amount, True)
    alternatif = rencanakan(existing, aksi, dari, sampai, amount, False)
    if not (rencana["nonaktif"] or rencana["ubah"] or rencana["buat"]):
        return {"dibuat": 0, "diubah": 0, "dinonaktifkan": 0,
                "pesan": _("Tidak ada perubahan: pengecualian yang sama sudah ada.")}

    frappe.db.savepoint(SP)
    try:
        hasil = _jalankan(rencana, employee, component, reason)
    except frappe.PermissionError:
        raise
    except frappe.ValidationError:
        if alternatif == rencana:
            raise
        # Penggabungan mengenai baris yang terkunci (misalnya periode Final): coba tanpa menggabung.
        frappe.db.rollback(save_point=SP)
        frappe.clear_messages()
        hasil = _jalankan(alternatif, employee, component, reason)
        hasil["catatan"] = _("Rentang bersambung tidak digabung karena baris lama tidak dapat diubah.")
    hasil["pesan"] = _("Tersimpan: {0} baris dibuat, {1} diubah, {2} dinonaktifkan.").format(
        hasil["dibuat"], hasil["diubah"], hasil["dinonaktifkan"])
    return hasil
