"""Giliran bulan untuk komponen Per Bulan: apakah slip ini slip pertama dan/atau terakhir di bulan bayarnya.

Memakai ulang logika BPJS (slip pertama) dan PPh 21 (slip terakhir). Hasil ditembolok per periode selama satu
proses (frappe.flags), karena jadwal yang sama dihitung untuk setiap karyawan. Gagal menghitung = None (komponen
Per Bulan dihitung tiap slip seperti perilaku lama) dan galat dicatat di Error Log.
"""

import frappe

from hris.hris_payroll.services import payroll_bpjs as bp
from hris.hris_payroll.services.payroll_pph21 import _slip_terakhir

TEMBOLOK = "hris_giliran_bulan"


def giliran_bulan(period):
    kunci = (period.name, str(period.payroll_schedule), str(period.period_start), str(period.period_end), str(period.pay_date))
    tembolok = frappe.flags.get(TEMBOLOK)
    if tembolok is None:
        tembolok = {}
        frappe.flags[TEMBOLOK] = tembolok
    if kunci in tembolok:
        return tembolok[kunci]
    try:
        params, offset, aturan = bp._jadwal(period)
        pertama = bp.pertama_bulan_murni(params, offset, aturan, period.period_start, period.pay_date)
        hasil = {"pertama": bool(pertama), "terakhir": bool(_slip_terakhir(period))}
    except Exception:
        frappe.log_error(title="HRIS Payroll Slip: giliran bulan gagal")
        hasil = None
    tembolok[kunci] = hasil
    return hasil
