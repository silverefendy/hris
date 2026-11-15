"""Giliran bulan untuk komponen Per Bulan: apakah slip ini slip pertama dan/atau terakhir di bulan bayarnya.

Memakai ulang logika BPJS (slip pertama) dan PPh 21 (slip terakhir). Gagal menghitung = None (komponen Per Bulan
dihitung tiap slip seperti perilaku lama) dan galat dicatat di Error Log.
"""

import frappe

from hris.hris_payroll.services import payroll_bpjs as bp
from hris.hris_payroll.services.payroll_pph21 import _slip_terakhir


def giliran_bulan(period):
    try:
        params, offset, aturan = bp._jadwal(period)
        pertama = bp.pertama_bulan_murni(params, offset, aturan, period.period_start, period.pay_date)
        return {"pertama": bool(pertama), "terakhir": bool(_slip_terakhir(period))}
    except Exception:
        frappe.log_error(title="HRIS Payroll Slip: giliran bulan gagal")
        return None
