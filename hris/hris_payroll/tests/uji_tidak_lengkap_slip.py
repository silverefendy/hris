"""Uji C1: hasil tinjauan Tidak Lengkap pada slip. Fungsi murni, tanpa database.
  bench --site hris-uji.local execute hris.hris_payroll.tests.uji_tidak_lengkap_slip.jalankan
"""
from hris.hris_payroll.services.payroll_slip import hitung_komponen

GAJI_H = 100000
GAJI_B = 5000000
HADIR = "Dihitung Hadir"
ABSEN = "Dihitung Tidak Hadir"


def _b(status, tgl, hasil=None):
    d = {
        "status": status, "scheduled_hours": 8, "late_deduction_hours": 0,
        "early_leave_deduction_hours": 0, "overtime_minutes": 0,
        "absence_deducted": 0, "absence_class": "", "work_date": tgl,
    }
    if hasil is not None:
        d["incomplete_outcome"] = hasil
    return d


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

    # Harian: 3 Hadir + TL Dihitung Hadir + TL Dihitung Tidak Hadir + TL belum ditinjau
    baris = [_b("Hadir", tgl[i]) for i in range(3)] + [
        _b("Tidak Lengkap", tgl[3], HADIR), _b("Tidak Lengkap", tgl[4], ABSEN), _b("Tidak Lengkap", tgl[5], "")]
    r = hitung_komponen("Harian", GAJI_H, baris)
    rg = r.get("ringkasan", {})
    cat = " | ".join(r.get("catatan", []))
    cek("T1 Harian: Upah = 4 hari x gaji (3 Hadir + 1 Dihitung Hadir)", _jml(r, "Upah Harian") == 4 * GAJI_H, "dapat %s" % _jml(r, "Upah Harian"))
    cek("T2 Harian: present_days = 4", rg.get("present_days") == 4, str(rg))
    cek("T3 Harian: absent_days = 1", rg.get("absent_days") == 1, str(rg))
    cek("T4 Harian: incomplete_days = 1 (hanya yang belum ditinjau)", rg.get("incomplete_days") == 1, str(rg))
    cek("T5 Harian: tanpa Potongan Absen", _jml(r, "Potongan Absen") is None)
    cek("T6 Harian: catatan menyebut kedua hasil tinjauan", "Dihitung Hadir" in cat and "Dihitung Tidak Hadir" in cat, cat)
    cek("T7 Harian: yang belum ditinjau tetap 'tidak dibayar'", "tidak dibayar" in cat, cat)

    # Bulanan: 5 Hadir + 3 TL (8 hari kerja)
    baris = [_b("Hadir", tgl[i]) for i in range(5)] + [
        _b("Tidak Lengkap", tgl[5], HADIR), _b("Tidak Lengkap", tgl[6], ABSEN), _b("Tidak Lengkap", tgl[7], "")]
    r = hitung_komponen("Bulanan", GAJI_B, baris)
    rg = r.get("ringkasan", {})
    cat = " | ".join(r.get("catatan", []))
    p = _jml(r, "Potongan Absen")
    cek("B1 Bulanan: Potongan Absen = gaji / 8 x 1 hari", p is not None and abs(p - GAJI_B / 8.0) <= 1, "dapat %s" % p)
    cek("B2 Bulanan: ringkasan present 6, absent 1, dipotong 1, incomplete 1",
        (rg.get("present_days"), rg.get("absent_days"), rg.get("absent_deducted_days"), rg.get("incomplete_days")) == (6, 1, 1, 1), str(rg))
    r = hitung_komponen("Bulanan", GAJI_B, [_b("Hadir", tgl[i]) for i in range(5)] + [_b("Tidak Lengkap", tgl[5], HADIR), _b("Tidak Lengkap", tgl[6], "")])
    cek("B3 Bulanan: hanya Dihitung Hadir dan belum ditinjau: tanpa Potongan Absen", _jml(r, "Potongan Absen") is None)
    cek("B4 Bulanan: yang belum ditinjau tetap 'tidak dipotong'", "tidak dipotong" in " | ".join(r.get("catatan", [])), str(r.get("catatan")))

    # Kasus tepi
    baris = [_b("Hadir", tgl[i]) for i in range(4)] + [_b("Hadir", tgl[4], ABSEN)]
    r = hitung_komponen("Bulanan", GAJI_B, baris)
    cek("K1 hasil pada hari bukan Tidak Lengkap diabaikan", _jml(r, "Potongan Absen") is None)
    r = hitung_komponen("Bulanan", GAJI_B, [_b("Hadir", tgl[i]) for i in range(5)] + [_b("Tidak Lengkap", tgl[5])])
    cek("K2 baris tanpa kunci hasil = belum ditinjau (perilaku lama)",
        r.get("ringkasan", {}).get("incomplete_days") == 1 and _jml(r, "Potongan Absen") is None, str(r.get("ringkasan")))

    print("Lulus %d dari %d" % (cek.ok, cek.total))
