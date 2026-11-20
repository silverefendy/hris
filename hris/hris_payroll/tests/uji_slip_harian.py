"""Uji slip Harian (C2) dengan pembanding Bulanan. Fungsi murni, tanpa database.
  bench --site hris-uji.local execute hris.hris_payroll.tests.uji_slip_harian.jalankan
"""
import frappe

from hris.hris_payroll.services.payroll_slip import hitung_komponen

GAJI_HARIAN = 100000
GAJI_BULANAN = 5000000


def _b(status, tgl, jam=8, telat=0, kelas="", potong=0):
    return {
        "status": status, "scheduled_hours": jam, "late_deduction_hours": telat,
        "early_leave_deduction_hours": 0, "overtime_minutes": 0,
        "absence_deducted": potong, "absence_class": kelas, "work_date": tgl,
    }


def _jml(r, nama):
    for k in r.get("komponen", []):
        if k["nama"] == nama:
            return float(k["jumlah"])
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
    cek = _Cek()
    tgl = ["2026-10-%02d" % i for i in range(1, 11)]

    # H1: 3 Hadir + 2 Tidak Hadir
    r = hitung_komponen("Harian", GAJI_HARIAN, [_b("Hadir", tgl[i]) for i in range(3)] + [_b("Tidak Hadir", tgl[3]), _b("Tidak Hadir", tgl[4])])
    rg = r.get("ringkasan", {})
    cek("H1 tidak ada error", "error" not in r, str(r.get("error")))
    cek("H1 Upah Harian = 3 x gaji", _jml(r, "Upah Harian") == 3 * GAJI_HARIAN, "dapat %s" % _jml(r, "Upah Harian"))
    cek("H1 tanpa Potongan Absen", _jml(r, "Potongan Absen") is None, "dapat %s" % _jml(r, "Potongan Absen"))
    cek("H1 ringkasan 3 hadir, 2 absen, 5 hari kerja",
        (rg.get("present_days"), rg.get("absent_days"), rg.get("working_days")) == (3, 2, 5), str(rg))

    # H2: Tidak Hadir bertanda potong tetap tidak membuat Potongan Absen di Harian
    r = hitung_komponen("Harian", GAJI_HARIAN, [_b("Hadir", tgl[0]), _b("Tidak Hadir", tgl[1], kelas="Mangkir", potong=1)])
    cek("H2 Harian: Tidak Hadir dipotong tetap tanpa Potongan Absen", _jml(r, "Potongan Absen") is None and _jml(r, "Upah Harian") == GAJI_HARIAN,
        "Potongan %s, Upah %s" % (_jml(r, "Potongan Absen"), _jml(r, "Upah Harian")))

    # H3: hanya Tidak Hadir (perilaku sekarang: slip 0, bukan error)
    r = hitung_komponen("Harian", GAJI_HARIAN, [_b("Tidak Hadir", tgl[0]), _b("Tidak Hadir", tgl[1])])
    cek("H3 hanya Tidak Hadir: tanpa error, Upah 0", "error" not in r and _jml(r, "Upah Harian") == 0,
        "error=%s upah=%s" % (r.get("error"), _jml(r, "Upah Harian")))

    # H4: tidak ada hari kerja sama sekali = error (dengan dan tanpa saklar)
    r = hitung_komponen("Harian", GAJI_HARIAN, [])
    cek("H4 tanpa hari kerja: error", "error" in r, str(r))
    asli = frappe.conf.get("hris_skip_harian_absen")
    try:
        frappe.conf["hris_skip_harian_absen"] = 1
        r = hitung_komponen("Harian", GAJI_HARIAN, [])
        cek("H4b tanpa hari kerja + saklar skip harian: error", "error" in r, str(r))
    finally:
        if asli is None:
            frappe.conf.pop("hris_skip_harian_absen", None)
        else:
            frappe.conf["hris_skip_harian_absen"] = asli

    # H5: Tidak Lengkap tidak dibayar dan dicatat
    r = hitung_komponen("Harian", GAJI_HARIAN, [_b("Hadir", tgl[i]) for i in range(3)] + [_b("Tidak Lengkap", tgl[3])])
    rg = r.get("ringkasan", {})
    cek("H5 Tidak Lengkap tidak dibayar (Upah = 3 x gaji)", _jml(r, "Upah Harian") == 3 * GAJI_HARIAN, "dapat %s" % _jml(r, "Upah Harian"))
    cek("H5 catatan 'tidak dibayar' ada", any("tidak dibayar" in c for c in r.get("catatan", [])), str(r.get("catatan")))
    cek("H5 ringkasan incomplete_days = 1", rg.get("incomplete_days") == 1, str(rg))

    # H6: potongan telat Harian = 1 jam x (gaji / 8 jam)
    r = hitung_komponen("Harian", GAJI_HARIAN, [_b("Hadir", tgl[0], telat=1), _b("Hadir", tgl[1]), _b("Hadir", tgl[2])])
    t = _jml(r, "Potongan Telat")
    cek("H6 Potongan Telat 1 jam = 12.500", t is not None and abs(t - 12500) <= 1, "dapat %s" % t)

    # B1: Bulanan pembanding. 5 Hadir, 1 Tidak Hadir dipotong (Mangkir), 1 Tidak Hadir Izin tidak dipotong
    baris = [_b("Hadir", tgl[i]) for i in range(5)] + [_b("Tidak Hadir", tgl[5], kelas="Mangkir", potong=1), _b("Tidak Hadir", tgl[6], kelas="Izin", potong=0)]
    r = hitung_komponen("Bulanan", GAJI_BULANAN, baris)
    p = _jml(r, "Potongan Absen")
    cek("B1 Gaji Pokok penuh 5.000.000", _jml(r, "Gaji Pokok") == GAJI_BULANAN, "dapat %s" % _jml(r, "Gaji Pokok"))
    cek("B1 Potongan Absen = gaji / 7 hari x 1 hari", p is not None and abs(p - GAJI_BULANAN / 7.0) <= 1, "dapat %s" % p)

    # B2: Bulanan, Tidak Lengkap tidak dipotong
    r = hitung_komponen("Bulanan", GAJI_BULANAN, [_b("Hadir", tgl[i]) for i in range(5)] + [_b("Tidak Lengkap", tgl[5])])
    cek("B2 Bulanan Tidak Lengkap: tanpa Potongan Absen + catatan 'tidak dipotong'",
        _jml(r, "Potongan Absen") is None and any("tidak dipotong" in c for c in r.get("catatan", [])), str(r.get("catatan")))

    print("Lulus %d dari %d" % (cek.ok, cek.total))
