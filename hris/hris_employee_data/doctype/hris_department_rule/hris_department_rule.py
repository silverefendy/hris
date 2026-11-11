import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import getseries
from frappe.utils import flt, nowdate

PARAMETER = ("overtime_multiplier",)


class HRISDepartmentRule(Document):
    def autoname(self):
        # Awalan YYMM = bulan pembuatan; nomor urut lanjut terus (kunci penghitung tetap "DR-").
        tgl = nowdate()
        self.name = "DR-{0}{1}-{2}".format(tgl[2:4], tgl[5:7], getseries("DR-", 4))

    def validate(self):
        if flt(self.overtime_multiplier) < 0:
            frappe.throw(_("Pengali Lembur tidak boleh negatif."))
        if not any(flt(self.get(p)) > 0 for p in PARAMETER):
            frappe.throw(_("Isi minimal satu parameter. Aturan tanpa parameter tidak berguna."))
        if self.is_active:
            ada = frappe.db.exists(
                "HRIS Department Rule",
                {
                    "department": self.department,
                    "effective_from": self.effective_from,
                    "is_active": 1,
                    "name": ["!=", self.name or ""],
                },
            )
            if ada:
                frappe.throw(
                    _("Sudah ada aturan aktif {0} untuk Department {1} dengan tanggal berlaku yang sama.").format(
                        ada, self.department
                    )
                )
