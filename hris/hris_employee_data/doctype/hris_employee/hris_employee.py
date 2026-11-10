import re

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import getdate, today

FIELD_SENSITIF = ("ktp_number", "npwp", "bpjs_tk_no", "bpjs_kes_no", "bank_account_number")


class HRISEmployee(Document):
    def validate(self):
        self._cek_pph21()
        self._normalisasi()
        self._cek_ktp()
        self._cek_id_finger()
        self._cek_tanggal()
        self._cek_status()

    def _cek_pph21(self):
        """K-134: Status PTKP wajib bila Peserta PPh 21 dicentang (mandatory_depends_on hanya berlaku di form)."""
        if self.get("pph21_enrolled") and not (self.get("ptkp_status") or "").strip():
            frappe.throw(
                _("Masalah: Peserta PPh 21 dicentang tetapi Status PTKP kosong. "
                  "Penyebab: Status PTKP menentukan kategori tarif TER. "
                  "Tindakan: isi Status PTKP, atau hilangkan centang Peserta PPh 21. "
                  "Berwenang: HRD (HRIS HR Admin atau HRIS Employee Admin)."),
                title=_("Status PTKP wajib"),
            )

    def on_update(self):
        if self.flags.skip_sync:
            return
        from hris.hris_employee_data.services.employee_sync import sinkron_dokumen

        sinkron_dokumen(self)

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

    def _cek_id_finger(self):
        nilai = (self.attendance_device_id or "").strip()
        self.attendance_device_id = nilai or None
        if not nilai:
            return

        # 1) Antar HRIS Employee: aturan lama, hanya yang Aktif.
        if self.status == "Aktif":
            ada = frappe.db.get_value(
                "HRIS Employee",
                {
                    "attendance_device_id": nilai,
                    "status": "Aktif",
                    "name": ["!=", self.name or ""],
                },
                "name",
            )
            if ada:
                frappe.throw(
                    _("ID Finger {0} sudah dipakai oleh dokumen {1} yang masih Aktif.").format(
                        nilai, ada
                    )
                )

        # 2) K-126 (V2): terhadap Employee ERPNext. Kolom attendance_device_id di sana
        #    unik untuk SEMUA status (termasuk Left), jadi diperiksa tanpa melihat
        #    status HRIS. Employee yang tertaut ke dokumen ini dikecualikan.
        pemegang = frappe.db.get_value(
            "Employee",
            {"attendance_device_id": nilai, "name": ["!=", self.erpnext_employee or ""]},
            ["name", "employee_name", "status"],
            as_dict=True,
        )
        if pemegang:
            frappe.throw(
                _(
                    "ID Finger {0} sudah dipakai Employee ERPNext {1} ({2}, status {3}). "
                    "Gunakan ID lain."
                ).format(nilai, pemegang.name, pemegang.employee_name, pemegang.status)
            )

    def _cek_tanggal(self):
        # K-126 (V1): aturan yang sama dengan Employee ERPNext, ditolak di sumbernya.
        if self.birth_date and self.date_of_joining:
            if getdate(self.birth_date) >= getdate(self.date_of_joining):
                frappe.throw(_("Tanggal Bergabung harus setelah Tanggal Lahir."))
        # K-126 (V1b): hanya untuk status Resign, karena status Aktif mengosongkan
        # resign_date di _cek_status yang berjalan sesudah fungsi ini.
        if self.status == "Resign" and self.resign_date and self.date_of_joining:
            if getdate(self.resign_date) < getdate(self.date_of_joining):
                frappe.throw(_("Tanggal Resign tidak boleh sebelum Tanggal Bergabung."))
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
