import re

import frappe
from frappe import _
from frappe.model.document import Document

POLA_KODE = re.compile(r"^[A-Z][A-Z0-9_]*$")


class HRISPayComponent(Document):
    def validate(self):
        self.component_code = (self.component_code or "").strip()
        self.component_name = (self.component_name or "").strip()
        if self.component_code and not POLA_KODE.match(self.component_code):
            frappe.throw(_("Kode harus UPPER_SNAKE_CASE (huruf besar, angka, garis bawah), contoh TJ_JABATAN."))
        if not self.is_new():
            lama = self.get_doc_before_save()
            if lama and lama.component_code != self.component_code:
                frappe.throw(_("Kode komponen tidak dapat diubah setelah disimpan."))
