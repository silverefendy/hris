"""K-140 E2: penetapan komponen per Grup atau Department (HCA).

HCA menjawab "siapa yang menerima komponen" untuk seluruh Grup atau Department. HEC karyawan tetap menang
(lihat services/cakupan_komponen.py). Tanpa HCA dan tanpa HEC = tidak dapat.
"""
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, flt, getdate

TABEL = "HRIS Component Assignment"
ID_PENGUBAH = ("date_from", "date_to", "status", "amount", "is_active")


class HRISComponentAssignment(Document):
    def validate(self):
        lama = None if self.is_new() else self.get_doc_before_save()
        self.validate_cakupan()
        self.validate_tanggal()
        self.validate_status_nominal()
        if lama:
            self.validate_terkunci(lama)
        self.validate_alasan(lama)
        self.validate_tumpang_tindih()

    def validate_cakupan(self):
        if self.scope_type == "Department":
            if not self.department:
                frappe.throw(_("Pilih Department."))
            self.employee_group = None
            company = frappe.db.get_value("HRIS Department", self.department, "company")
        elif self.scope_type == "Grup":
            if not self.employee_group:
                frappe.throw(_("Pilih Grup."))
            self.department = None
            self.include_children = 0
            company = frappe.db.get_value("HRIS Employee Group", self.employee_group, "company")
        else:
            frappe.throw(_("Cakupan harus Department atau Grup."))
        if not company:
            frappe.throw(_("Department atau Grup ini belum punya Company. Lengkapi dulu datanya."))
        self.company = company

    def validate_tanggal(self):
        if not self.date_from or not self.date_to:
            frappe.throw(_("Isi Dari dan Sampai. Untuk satu hari saja, isi keduanya dengan tanggal yang sama."))
        if getdate(self.date_to) < getdate(self.date_from):
            frappe.throw(_("Sampai tidak boleh sebelum Dari."))

    def validate_status_nominal(self):
        if self.status == "Tidak Berlaku":
            self.amount = 0
        elif flt(self.amount) < 0:
            frappe.throw(_("Nominal Khusus tidak boleh negatif."))

    def validate_terkunci(self, lama):
        for f in ("scope_type", "department", "employee_group", "component"):
            if cstr(lama.get(f) or "") != cstr(self.get(f) or ""):
                frappe.throw(
                    _("Cakupan dan Komponen tidak dapat diubah. Matikan centang Aktif pada baris ini, lalu buat baris baru.")
                )

    def _berubah(self, lama):
        if not lama:
            return True
        for f in ID_PENGUBAH:
            if f == "amount":
                if abs(flt(self.get(f)) - flt(lama.get(f))) > 0.0001:
                    return True
            elif cstr(self.get(f) or "") != cstr(lama.get(f) or ""):
                return True
        return False

    def validate_alasan(self, lama):
        if not (self.reason or "").strip():
            frappe.throw(_("Alasan wajib diisi."))
        if lama and self._berubah(lama) and cstr(self.reason) == cstr(lama.reason):
            frappe.throw(_("Ada perubahan tanggal, status, nominal, atau Aktif. Ubah juga Alasan agar jelas kenapa berubah."))

    def validate_tumpang_tindih(self):
        if not self.is_active:
            return
        filters = {
            "scope_type": self.scope_type,
            "component": self.component,
            "is_active": 1,
            "name": ["!=", self.name or ""],
            "date_from": ["<=", self.date_to],
            "date_to": [">=", self.date_from],
        }
        if self.scope_type == "Department":
            filters["department"] = self.department
        else:
            filters["employee_group"] = self.employee_group
        ada = frappe.get_all(TABEL, filters=filters, fields=["name", "date_from", "date_to"], limit=1)
        if ada:
            frappe.throw(
                _(
                    "Masalah: rentang tanggal tumpang tindih dengan {0} ({1} sampai {2}). "
                    "Penyebab: satu cakupan dan komponen hanya boleh punya satu penetapan aktif pada satu tanggal. "
                    "Tindakan: ubah rentang baris itu, atau matikan Aktif pada baris itu."
                ).format(ada[0].name, ada[0].date_from, ada[0].date_to)
            )
