"""Uji Per Bulan langkah 2: giliran bulan tersambung ke slip dan Payroll Summary. Semua perubahan di-rollback.

bench --site hris-uji.local execute hris.hris_payroll.tests.uji_per_bulan_slip.jalankan
"""

import frappe

from hris.hris_payroll.services import payroll_slip as ps
from hris.hris_payroll.services import payroll_summary as su
from hris.hris_payroll.services.giliran_bulan import giliran_bulan
from hris.hris_payroll.tests.uji_tunjangan_slip_integrasi import foto, pilih_pasangan


def cek(nama, kondisi, info=""):
    print(("OK     " if kondisi else "GAGAL  ") + nama + (" | " + str(info) if info else ""))


def uji_inti(period, karyawan):
    tangkap = []

    def palsu_susun(he, pay_type, awal, akhir, baris_hitung, giliran=None):
        tangkap.append(giliran)
        return {"komponen": [], "catatan": [], "galat": [], "periksa": False}

    ps.susun_tunjangan = palsu_susun
    for nomor, g in (("S2", {"pertama": False, "terakhir": True}), ("S3", {"pertama": True, "terakhir": False})):
        ps.giliran_bulan = lambda p, g=g: g
        tangkap.clear()
        jenis, info = ps.proses_karyawan(period, karyawan)
        cek("%s slip meneruskan giliran %s ke susun_tunjangan" % (nomor, g), len(tangkap) == 1 and tangkap[0] == g, (jenis, tangkap))

    panggilan = []

    def palsu_hitung(*a, **k):
        panggilan.append(a)
        return {"jumlah": 0, "dasar": "", "janggal": [], "peringatan": []}

    su.hitung_tunjangan = palsu_hitung
    G = {"pertama": False, "terakhir": False}
    su.giliran_bulan = lambda p: G
    su.ambil_data(mode="Per Periode", periode=period.name, employee=karyawan, tampilkan_nonaktif=1, tampilkan_tanpa_gaji=1)
    cek("S4 Summary Per Periode meneruskan giliran ke semua komponen",
        len(panggilan) > 0 and all(len(a) > 8 and a[7] == G for a in panggilan), "%d panggilan" % len(panggilan))
    cek("S5 Summary meneruskan Waktu Bayar dari katalog",
        len(panggilan) > 0 and all(len(a) > 8 and a[8] in ("Slip Pertama", "Slip Terakhir") for a in panggilan),
        sorted({a[8] for a in panggilan if len(a) > 8}))
    panggilan.clear()
    su.ambil_data(mode="Per Tanggal", tanggal=str(period.period_end), employee=karyawan, tampilkan_nonaktif=1, tampilkan_tanpa_gaji=1)
    cek("S6 Summary Per Tanggal tanpa giliran (perilaku lama)",
        len(panggilan) > 0 and all(len(a) > 8 and a[7] is None for a in panggilan), "%d panggilan" % len(panggilan))
    g = giliran_bulan(period)
    cek("S7 giliran_bulan nyata mengembalikan kunci pertama dan terakhir", isinstance(g, dict) and set(g) == {"pertama", "terakhir"}, g)


def jalankan():
    sebelum = foto()
    asli = (ps.susun_tunjangan, ps.giliran_bulan, su.hitung_tunjangan, su.giliran_bulan)
    try:
        period, karyawan, _nama, _tipe, alasan = pilih_pasangan()
        if period is None:
            cek("S1 pasangan periode Draft dan karyawan ditemukan", False, alasan)
        else:
            cek("S1 pasangan periode Draft dan karyawan ditemukan", True, "%s / %s" % (period.name, karyawan))
            uji_inti(period, karyawan)
    finally:
        ps.susun_tunjangan, ps.giliran_bulan, su.hitung_tunjangan, su.giliran_bulan = asli
        frappe.db.rollback()
    cek("S8 rollback: data kembali seperti semula", foto() == sebelum)
