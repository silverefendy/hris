import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today

FIELD_SENSITIF = ("ktp_number", "npwp", "bpjs_tk_no", "bpjs_kes_no", "bank_account_number")


class HRISEmployee(Document):
    def validate(self):
        self._normalisasi()
        self._cek_ktp()
        self._cek_tanggal()
        self._cek_status()

    def _normalisasi(self):
        # Kosong disimpan sebagai NULL agar aturan unik tidak menganggap dua kosong sama.
        for fieldname in FIELD_SENSITIF:
            nilai = (self.get(fieldname) or "").strip()
            self.set(fieldname, nilai or None)

    def _cek_ktp(self):
        if not self.ktp_number:
            return
        if not re.fullmatch(r"\d{16}", self.ktp_number):
            frappe.throw(_("No KTP harus 16 digit angka."))
        ada = frappe.db.get_value(
            "HRIS Employee",
            {"ktp_number": self.ktp_number, "name": ["!=", self.name or ""]},
            "name",
        )
        if ada:
            frappe.throw(_("No KTP sudah dipakai oleh dokumen {0}.").format(ada))

    def _cek_tanggal(self):
        if self.date_of_joining and self.contract_end_date:
            if getdate(self.contract_end_date) < getdate(self.date_of_joining):
                frappe.throw(_("Akhir perjanjian kerja tidak boleh sebelum tanggal bergabung."))
        if self.birth_date and getdate(self.birth_date) > getdate(today()):
            frappe.throw(_("Tanggal lahir tidak boleh di masa depan."))

    def _cek_status(self):
        if self.status == "Resign" and not self.resign_date:
            frappe.throw(_("Status Resign wajib mengisi Tanggal Resign."))
        if self.status == "Aktif":
            self.resign_date = None
            self.resign_reason = None
