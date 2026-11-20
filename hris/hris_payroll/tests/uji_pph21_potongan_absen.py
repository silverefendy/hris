"""Uji C3: Potongan Absen tidak mengurangi bruto kena pajak; PPh 21 tetap atas gaji penuh sebulan.
Bagian 1 murni. Bagian 2 mengaktifkan HRIS PPh21 Settings dan tarif FIKTIF di dalam transaksi, lalu rollback.
  bench --site hris-uji.local execute hris.hris_payroll.tests.uji_pph21_potongan_absen.jalankan
"""
from decimal import Decimal

import frappe

from hris.hris_payroll.services import payroll_pph21 as pp
from hris.hris_payroll.services.payroll_slip import hitung_komponen

SITE = "hris-uji.local"
GAJI = 5000000
KAT = "UJIC"


def _b(status, tgl, telat=0, kelas="", potong=0):
    return {
        "status": status, "scheduled_hours": 8, "late_deduction_hours": telat,
        "early_leave_deduction_hours": 0, "overtime_minutes": 0,
        "absence_deducted": potong, "absence_class": kelas, "work_date": tgl,
    }


def _jml(h, nama):
    for k in h.get("komponen", []):
        if k["nama"] == nama:
            return k["jumlah"]
    return None


class _Cek:
    def __init__(self):
        self.ok = 0
        self.total = 0

    def __call__(self, nama, kondisi, detail=""):
        self.total += 1
        if kondisi:
            self.ok += 1
            print("OK    %s" % nama)
        else:
            print("GAGAL %s | %s" % (nama, detail))


def jalankan():
    if frappe.local.site != SITE:
        print("Site bukan %s; berhenti." % SITE)
        return
    cek = _Cek()
    tgl = ["2026-10-%02d" % i for i in range(1, 11)]

    # ---- Bagian 1: murni ----
    a = hitung_komponen("Bulanan", GAJI, [_b("Hadir", t) for t in tgl[:7]])
    b = hitung_komponen(
        "Bulanan", GAJI,
        [_b("Hadir", tgl[0], telat=1)] + [_b("Hadir", t) for t in tgl[1:5]]
        + [_b("Tidak Hadir", tgl[5], kelas="Mangkir", potong=1), _b("Tidak Hadir", tgl[6], kelas="Mangkir", potong=1)],
    )
    cek("P1 slip A (semua hadir) tanpa Potongan Absen", _jml(a, "Potongan Absen") is None)
    cek("P2 slip B punya Potongan Absen > 0", (_jml(b, "Potongan Absen") or 0) > 0, str(_jml(b, "Potongan Absen")))
    cek("P3 slip B punya Potongan Telat > 0", (_jml(b, "Potongan Telat") or 0) > 0, str(_jml(b, "Potongan Telat")))
    bruto_a = pp._bruto_sendiri(a["komponen"], set())
    bruto_b = pp._bruto_sendiri(b["komponen"], set())
    cek("P4 bruto kena pajak A = gaji penuh", bruto_a == Decimal(GAJI), str(bruto_a))
    cek("P5 bruto kena pajak B = gaji penuh (potongan tidak mengurangi)", bruto_b == Decimal(GAJI), str(bruto_b))

    # ---- Bagian 2: jalur penuh hitung_pph21_slip, di dalam transaksi lalu rollback ----
    if frappe.db.count("HRIS PPh21 TER Rate", {"ter_category": KAT}):
        print("Ada sisa tarif %s di situs uji; hapus dulu, lalu ulangi." % KAT)
        return
    nama_fungsi = ("_data_karyawan", "_slip_saat_ini", "_slip_lain", "_slip_terakhir")
    asli = {n: getattr(pp, n) for n in nama_fungsi}
    try:
        pp._data_karyawan = lambda he: {"pph21_enrolled": 1, "ptkp_status": "TK/0", "npwp": "123"}
        pp._slip_saat_ini = lambda he, period: (None, Decimal(0))
        pp._slip_lain = lambda he, period, nama_ada, bebas: (0, Decimal(0), None)
        pp._slip_terakhir = lambda period: True

        frappe.get_doc({
            "doctype": "HRIS PPh21 TER Rate", "ter_category": KAT, "bruto_from": 0, "bruto_to": None,
            "open_ended": 1, "rate_percent": 1.5, "effective_from": "2026-01-01", "enabled": 1,
        }).insert()
        s = frappe.get_doc("HRIS PPh21 Settings")
        s.enabled = 1
        s.set("ptkp_map", [])
        s.append("ptkp_map", {"ptkp_status": "TK/0", "ter_category": KAT})
        s.set("exempt_components", [])
        s.no_npwp_multiplier = 1
        s.rounding = "Ke Bawah"
        s.save()

        he = frappe._dict(name="UJI-C3-HE")
        periode = frappe._dict(name="UJI-C3-PERIODE", pay_date="2026-10-29", period_start="2026-10-27", period_end="2026-11-26")
        ha = pp.hitung_pph21_slip(he, periode, None, a)
        hb = pp.hitung_pph21_slip(he, periode, None, b)
        pa, pb = _jml(ha, pp.NAMA), _jml(hb, pp.NAMA)
        cek("P6 slip A tidak dilewati dan ada PPh 21", "dilewati" not in ha and pa is not None, str(ha)[:200])
        cek("P7 slip B tidak dilewati dan ada PPh 21", "dilewati" not in hb and pb is not None, str(hb)[:200])
        cek("P8 PPh 21 A = 1,5% x gaji penuh = 75.000", pa == 75000, "dapat %s" % pa)
        cek("P9 PPh 21 B sama dengan A (potongan tidak mengubah pajak)", pa is not None and pa == pb, "A=%s B=%s" % (pa, pb))
    finally:
        for n, f in asli.items():
            setattr(pp, n, f)
        frappe.db.rollback()

    print("Lulus %d dari %d" % (cek.ok, cek.total))
