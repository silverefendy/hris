import frappe
from frappe.utils import flt
from hris.hris_payroll.services.payroll_slip import hitung_komponen
from hris.hris_payroll.report.hris_biaya_tenaga_kerja.hris_biaya_tenaga_kerja import _nilai_hari

KALI = 1.5


def _b(status="Hadir", jam=8, lembur=0, pengali=None):
    b = {
        "status": status, "scheduled_hours": jam, "late_deduction_hours": 0,
        "early_leave_deduction_hours": 0, "overtime_minutes": lembur,
        "absence_deducted": 0, "absence_class": "", "work_date": "2026-10-01",
    }
    if pengali:
        b["pengali"] = pengali
    return b


def jalankan():
    hasil = []

    def cek(nama, kondisi, info=""):
        hasil.append(bool(kondisi))
        print(("OK     " if kondisi else "GAGAL  ") + nama + (" | " + str(info) if info else ""))

    kasus = {
        "Bulanan": (3000000, [_b(lembur=90), _b(lembur=60, pengali=2), _b(jam=7),
                              _b("Tidak Hadir"), _b("Tidak Lengkap"), _b("Libur", jam=0)]),
        "Harian": (150000, [_b(lembur=120), _b(jam=7, lembur=30, pengali=2), _b(jam=0, lembur=60),
                            _b("Tidak Hadir"), _b("Tidak Lengkap"), _b("Libur", jam=0)]),
    }
    for tipe, (gaji, baris) in kasus.items():
        h = hitung_komponen(tipe, gaji, [dict(x) for x in baris], pengali=KALI)
        if h.get("error"):
            cek(tipe + ": hitung_komponen", False, h["error"])
            continue
        pend = sum(flt(k["jumlah"]) for k in h["komponen"] if k["tipe"] == "Pendapatan")
        ring = h["ringkasan"]
        s = frappe._dict(pay_type=tipe, base_amount=gaji, working_days=ring["working_days"])
        jam_total = flt(ring["scheduled_hours_total"])
        tarif = gaji / jam_total if jam_total > 0 else 0.0
        jml = 0.0
        for b in baris:
            r = frappe._dict(b)
            jml += _nilai_hari(s, r, tarif, flt(r.get("pengali")) or KALI)
        cek(tipe + ": jumlah per hari = Pendapatan slip", abs(jml - pend) <= 2,
            "per hari %.2f vs slip %.2f" % (jml, pend))

    sh = frappe._dict(pay_type="Harian", base_amount=150000, working_days=0)
    cek("H1 Harian hari 1 = 206250", abs(_nilai_hari(sh, frappe._dict(_b(lembur=120)), 0, KALI) - 206250) < 0.01)
    sb = frappe._dict(pay_type="Bulanan", base_amount=3000000, working_days=5)
    cek("B1 Bulanan hari Libur = 0", _nilai_hari(sb, frappe._dict(_b("Libur", jam=0)), 0, KALI) == 0)
    cek("B2 Bulanan hari kerja tanpa lembur = 600000", abs(_nilai_hari(sb, frappe._dict(_b()), 0, KALI) - 600000) < 0.01)
    print("OK %d, GAGAL %d" % (sum(hasil), len(hasil) - sum(hasil)))
