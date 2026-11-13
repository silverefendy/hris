"""E1 tahap 3a: penelusuran nilai tunjangan per komponen, termasuk pengecualian HRIS Employee Component (HEC).

BELUM disambung ke slip (proses_karyawan). hitung_tunjangan() murni (tanpa database).

Aturan (keputusan 13 Nov 2026):
- Per Hari Hadir (Harian): dihitung per hari Hadir. HEC Tidak Berlaku = 0 hari itu; HEC Berlaku + nominal =
  nominal; HEC Berlaku tanpa nominal = nilai dasar, dan bila nilai dasar nol = 0 ditandai janggal.
- Per Bulan / Per Slip: satu nilai per periode, tetap penuh. Hanya HEC yang menutup seluruh periode yang
  mengubah nilai; HEC sebagian hari hanya menghasilkan peringatan.
- Bulanan + Per Hari Hadir: belum didukung (mengembalikan error).
"""
from decimal import ROUND_HALF_UP, Decimal

import frappe
from frappe import _
from frappe.utils import getdate

HEC = "HRIS Employee Component"
KATALOG = "HRIS Pay Component"


def _d(x):
    return Decimal(str(x or 0))


def _rp(n):
    return "Rp{0}".format("{:,.0f}".format(n).replace(",", "."))


def _rupiah(x):
    return int(x.quantize(Decimal(1), rounding=ROUND_HALF_UP))


def _hari_tumpang(dari, sampai, awal, akhir):
    return max((min(sampai, akhir) - max(dari, awal)).days + 1, 0)


def _per_hari(dasar, hec, tanggal_hadir):
    total = Decimal(0)
    n_dasar = n_khusus = n_tidak = n_janggal = 0
    nama_janggal = set()
    for tgl in sorted(set(getdate(t) for t in tanggal_hadir)):
        h = next((x for x in hec if x["dari"] <= tgl <= x["sampai"]), None)
        if h is None:
            if dasar > 0:
                total += dasar
                n_dasar += 1
        elif h["status"] == "Tidak Berlaku":
            n_tidak += 1
        elif h["amount"] > 0:
            total += h["amount"]
            n_khusus += 1
        elif dasar > 0:
            total += dasar
            n_dasar += 1
        else:
            n_janggal += 1
            nama_janggal.add(h["name"])
    bagian = []
    if n_dasar:
        bagian.append(_("{0} hari x {1}").format(n_dasar, _rp(dasar)))
    if n_khusus:
        bagian.append(_("{0} hari nominal khusus").format(n_khusus))
    if n_tidak:
        bagian.append(_("{0} hari Tidak Berlaku (pengecualian)").format(n_tidak))
    janggal = []
    if n_janggal:
        janggal.append(
            _("Berlaku tanpa nominal dan nilai dasar nol ({0}): {1} hari dihitung Rp0.").format(
                ", ".join(sorted(str(n) for n in nama_janggal)), n_janggal
            )
        )
    return {"jumlah": _rupiah(total), "dasar": "; ".join(bagian) or _("Tidak ada hari yang dihitung"),
            "janggal": janggal, "peringatan": []}


def _per_periode(dasar, hec, awal, akhir):
    penuh = [x for x in hec if x["dari"] <= awal and x["sampai"] >= akhir]
    sebagian = [x for x in hec if x not in penuh and _hari_tumpang(x["dari"], x["sampai"], awal, akhir) > 0]
    janggal, peringatan = [], []
    if penuh:
        h = penuh[0]
        if h["status"] == "Tidak Berlaku":
            jumlah = Decimal(0)
            teks = _("Pengecualian {0}: Tidak Berlaku seluruh periode").format(h["name"])
        elif h["amount"] > 0:
            jumlah = h["amount"]
            teks = _("Nominal khusus {0} seluruh periode").format(h["name"])
        elif dasar > 0:
            jumlah = dasar
            teks = _("Nilai dasar (pengecualian {0} Berlaku tanpa nominal)").format(h["name"])
        else:
            jumlah = Decimal(0)
            teks = _("Pengecualian {0} Berlaku tanpa nominal, nilai dasar nol").format(h["name"])
            janggal.append(_("Berlaku tanpa nominal dan nilai dasar nol ({0}): dihitung Rp0.").format(h["name"]))
    else:
        jumlah = dasar
        teks = _("Nilai dasar per periode") if dasar > 0 else _("Tidak berlaku (tidak ada nilai dasar)")
    for x in sebagian:
        hari = _hari_tumpang(x["dari"], x["sampai"], awal, akhir)
        if x["status"] == "Tidak Berlaku":
            if dasar > 0:
                peringatan.append(
                    _("{0}: {1} hari Tidak Berlaku, tetapi nilai per periode tetap penuh.").format(x["name"], hari)
                )
        elif x["amount"] > 0:
            peringatan.append(
                _("{0}: nominal khusus {1} untuk {2} hari tidak menggantikan nilai per periode.").format(
                    x["name"], _rp(x["amount"]), hari
                )
            )
        elif dasar <= 0:
            janggal.append(_("Berlaku tanpa nominal dan nilai dasar nol ({0}): tidak ada nilai.").format(x["name"]))
    return {"jumlah": _rupiah(jumlah), "dasar": teks, "janggal": janggal, "peringatan": peringatan}


def hitung_tunjangan(pay_type, payment_basis, nilai_dasar, pengecualian, awal, akhir, tanggal_hadir):
    """Fungsi murni.
    nilai_dasar = {"nilai": angka, "berlaku": bool}
    pengecualian = [{name, status, amount, date_from, date_to}]
    tanggal_hadir = daftar tanggal berstatus Hadir (dipakai hanya untuk Per Hari Hadir).
    Mengembalikan {"error"} atau {"jumlah" (rupiah bulat), "dasar", "janggal": [], "peringatan": []}.
    """
    if pay_type not in ("Bulanan", "Harian"):
        return {"error": _("Jenis gaji tidak dikenal: {0}.").format(pay_type)}
    if pay_type == "Bulanan" and payment_basis == "Per Hari Hadir":
        return {"error": _("Komponen Per Hari Hadir untuk karyawan Bulanan belum didukung (perlu keputusan).")}
    awal, akhir = getdate(awal), getdate(akhir)
    dasar = _d(nilai_dasar.get("nilai")) if nilai_dasar.get("berlaku") else Decimal(0)
    hec = sorted(
        (
            {"name": p.get("name"), "status": p.get("status"), "amount": _d(p.get("amount")),
             "dari": getdate(p["date_from"]), "sampai": getdate(p["date_to"])}
            for p in pengecualian
        ),
        key=lambda x: (x["dari"], str(x["name"] or "")),
    )
    if payment_basis == "Per Hari Hadir":
        return _per_hari(dasar, hec, tanggal_hadir)
    return _per_periode(dasar, hec, awal, akhir)


def ambil_pengecualian(employee, kode, awal, akhir):
    """HEC aktif milik karyawan dan komponen yang rentangnya menyentuh periode."""
    return frappe.get_all(
        HEC,
        filters={
            "employee": employee, "component": kode, "is_active": 1,
            "date_from": ["<=", getdate(akhir)], "date_to": [">=", getdate(awal)],
        },
        fields=["name", "status", "amount", "date_from", "date_to"],
        order_by="date_from asc",
    )


def hitung_tunjangan_karyawan(employee, kode, pay_type, awal, akhir, tanggal_hadir):
    """Membungkus: baca katalog, nilai dasar (Grup atau Department), dan HEC, lalu hitung."""
    from hris.hris_payroll.services.department_komponen import resolve_komponen_karyawan

    komp = frappe.db.get_value(KATALOG, kode, ["component_name", "component_type", "payment_basis"], as_dict=True)
    if not komp:
        return {"error": _("Komponen {0} tidak ada di katalog.").format(kode)}
    he = frappe.db.get_value("HRIS Employee", employee, ["department", "employee_group", "rule_follow"], as_dict=True)
    if not he:
        return {"error": _("Karyawan {0} tidak ditemukan.").format(employee)}
    dasar = resolve_komponen_karyawan(he.department, he.employee_group, he.rule_follow, getdate(akhir), kode)
    hasil = hitung_tunjangan(
        pay_type, komp.payment_basis, dasar, ambil_pengecualian(employee, kode, awal, akhir),
        awal, akhir, tanggal_hadir,
    )
    if not hasil.get("error"):
        hasil.update({"kode": kode, "nama": komp.component_name or kode,
                      "tipe": komp.component_type, "sumber": dasar.get("sumber")})
    return hasil
