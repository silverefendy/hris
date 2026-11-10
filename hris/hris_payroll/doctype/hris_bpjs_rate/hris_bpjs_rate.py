import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, getdate

DOCTYPE = "HRIS BPJS Rate"
PROGRAM = ("BPJS Kesehatan", "JHT", "JP", "JKK", "JKM")


class HRISBPJSRate(Document):
    def validate(self):
        # validate jalan sebelum cek field wajib; field kosong dilewati
        self.risk_class = (self.risk_class or "").strip()
        self.validate_program()
        self.validate_nilai()
        self.set_unique_key()

    def validate_program(self):
        if self.program and self.program not in PROGRAM:
            frappe.throw(_("Program tidak dikenal: {0}.").format(self.program))
        if self.program == "JKK":
            if not self.risk_class:
                frappe.throw(_("JKK wajib memakai Kelas Risiko."))
        else:
            self.risk_class = ""

    def validate_nilai(self):
        for fieldname, label in (("employee_rate", "Tarif Karyawan"), ("company_rate", "Tarif Perusahaan")):
            nilai = flt(self.get(fieldname))
            if nilai < 0 or nilai > 100:
                frappe.throw(_("{0} harus antara 0 dan 100 persen.").format(label))
            self.set(fieldname, nilai)
        if flt(self.wage_cap) < 0:
            frappe.throw(_("Batas Upah Tertinggi tidak boleh negatif."))

    def set_unique_key(self):
        if not (self.company and self.program and self.effective_from):
            return
        kunci = "|".join([self.company, self.program, self.risk_class or "", str(getdate(self.effective_from))])
        ada = frappe.db.get_value(DOCTYPE, {"unique_key": kunci, "name": ["!=", self.name or ""]}, "name")
        if ada:
            frappe.throw(
                _("Tarif {0}{1} berlaku mulai {2} untuk {3} sudah ada: {4}. Ubah tanggal berlaku atau edit dokumen itu.").format(
                    self.program,
                    (" kelas " + self.risk_class) if self.risk_class else "",
                    self.effective_from,
                    self.company,
                    ada,
                )
            )
        self.unique_key = kunci
