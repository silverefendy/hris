"""Penamaan HRIS Raw Log: {mesin}-{ID pegawai}-{YYMMDD}-{NNNNN}.

Contoh: PLTB_220-6887-261031-00001

- Tanggal di nama diambil dari waktu punch.
- Nomor urut berulang tiap bulan, per kombinasi mesin + ID pegawai + bulan punch.
- punch_key (mesin|ID|waktu sampai detik) adalah penjaga duplikat. Nilainya
  tidak berubah walaupun waktu punch dikoreksi HRD, sehingga tarikan ulang
  tidak membuat salinan.
"""

import re

import frappe
from frappe.model.naming import getseries
from frappe.utils import get_datetime

SERIES_DIGITS = 5


def _part(value):
    return re.sub(r"[\s/]+", "_", str(value or "").strip())


def make_punch_key(device, user_id, punch_time):
    stamp = get_datetime(punch_time).strftime("%Y%m%d%H%M%S")
    return f"{device}|{str(user_id or '').strip()}|{stamp}"


def build_raw_log_name(device, user_id, punch_time):
    """Kembalikan (name, punch_key). Melempar DuplicateEntryError bila punch sudah ada."""
    key = make_punch_key(device, user_id, punch_time)
    if frappe.db.exists("HRIS Raw Log", {"punch_key": key}):
        raise frappe.DuplicateEntryError("HRIS Raw Log", key)

    ts = get_datetime(punch_time)
    prefix = f"{_part(device)}-{_part(user_id)}"
    number = getseries(f"{prefix}-{ts.strftime('%y%m')}", SERIES_DIGITS)
    return f"{prefix}-{ts.strftime('%y%m%d')}-{number}", key
