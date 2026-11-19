"""Uji 6a pada hitung_komponen (fungsi murni, tanpa database).
  bench --site hris-uji.local execute hris.hris_payroll.tests.uji_absen_6a.jalankan
"""
import frappe

from hris.hris_payroll.services.payroll_slip import hitung_komponen

K_KLAS = "hris_absen_belum_klas_dipotong"
K_HARIAN = "hris_skip_harian_absen"


def _b(status, kelas="", potong=0):
    return {
        "status": status, "scheduled_hours": 8, "late_deduction_hours": 0,
        "early_leave_deduction_hours": 0, "overtime_minutes": 0,
        "absence_deducted": potong, "absence_class": kelas, "work_date": "2026-10-01",
    }


def _potongan_absen(hasil):
    for k in hasil.get("komponen", []):
        if k["nama"] == "Potongan Absen":
            return float(k["jumlah"])
    return None


def jalankan():
    asli = {k: frappe.conf.get(k) for k in (K_KLAS, K_HARIAN)}
    hasil_uji = []

    def cek(nama, kondisi):
        hasil_uji.append(bool(kondisi))
        print(("PASS  " if kondisi else "FAIL  ") + nama)

    try:
        empat_hadir = [_b("Hadir") for _i in range(4)]
        frappe.conf[K_KLAS] = 0
        r = hitung_komponen("Bulanan", 5000000, empat_hadir + [_b("Tidak Hadir")])
        cek("Bulanan, saklar mati: belum klasifikasi tidak dipotong", _potongan_absen(r) is None)

        frappe.conf[K_KLAS] = 1
        r = hitung_komponen("Bulanan", 5000000, empat_hadir + [_b("Tidak Hadir")])
        cek("Bulanan, saklar hidup: belum klasifikasi dipotong 1/5 gaji (1.000.000)", _potongan_absen(r) == 1000000.0)

        r = hitung_komponen("Bulanan", 5000000, empat_hadir + [_b("Tidak Hadir", "Sakit", 0)])
        cek("Bulanan, Sakit berklasifikasi tidak dipotong", _potongan_absen(r) is None)

        r = hitung_komponen("Bulanan", 5000000, empat_hadir + [_b("Tidak Hadir", "Mangkir", 1)])
        cek("Bulanan, Mangkir dipotong 1.000.000", _potongan_absen(r) == 1000000.0)

        frappe.conf[K_HARIAN] = 0
        r = hitung_komponen("Harian", 150000, [])
        cek("Harian tanpa hari kerja, saklar mati: pesan lama",
            "error" in r and "tidak ada upah" not in r["error"])

        frappe.conf[K_HARIAN] = 1
        r = hitung_komponen("Harian", 150000, [])
        cek("Harian tanpa hari kerja, saklar hidup: dilewati dengan pesan jelas",
            "error" in r and "tidak ada upah, slip tidak dibuat" in r["error"])

        r = hitung_komponen("Harian", 150000, [_b("Hadir"), _b("Hadir")])
        upah = [k for k in r.get("komponen", []) if k["nama"] == "Upah Harian"]
        cek("Harian 2 hari Hadir: upah 300.000", upah and float(upah[0]["jumlah"]) == 300000.0)

        r = hitung_komponen("Bulanan", 5000000, [])
        cek("Bulanan tanpa hari kerja: tetap error", "error" in r)
    finally:
        for k, v in asli.items():
            if v is None:
                frappe.conf.pop(k, None)
            else:
                frappe.conf[k] = v
    print("\nLulus %d dari %d" % (sum(hasil_uji), len(hasil_uji)))
