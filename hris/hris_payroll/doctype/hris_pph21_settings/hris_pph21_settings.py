import frappe
from frappe.model.document import Document
from frappe.utils import flt

from hris.hris_payroll.services.pph21_rate import pesan

BERWENANG = "HRD (HRIS HR Admin) atau System Manager"


class HRISPPh21Settings(Document):
    def validate(self):
        self._cek_pemetaan()
        self._cek_komponen()
        if flt(self.no_npwp_multiplier) <= 0:
            frappe.throw(
                pesan("Pengali tarif tanpa NPWP harus lebih dari 0.",
                      f"Nilai yang diisi: {self.no_npwp_multiplier}.",
                      "Isi 1 bila NPWP tidak memengaruhi tarif.", BERWENANG),
                title="Pengaturan PPh 21 tidak valid")

    def _cek_pemetaan(self):
        terlihat = set()
        for row in self.ptkp_map or []:
            row.ptkp_status = (row.ptkp_status or "").strip().upper()
            row.ter_category = (row.ter_category or "").strip().upper()
            if row.ptkp_status in terlihat:
                frappe.throw(
                    pesan(f"Status PTKP {row.ptkp_status} muncul lebih dari sekali (baris {row.idx}).",
                          "Satu status hanya boleh dipetakan ke satu kategori.",
                          "Hapus baris ganda dan simpan lagi.", BERWENANG),
                    title="Pemetaan PTKP ganda")
            terlihat.add(row.ptkp_status)

    def _cek_komponen(self):
        terlihat = set()
        for row in self.exempt_components or []:
            row.component_name = (row.component_name or "").strip()
            kunci = row.component_name.lower()
            if kunci in terlihat:
                frappe.throw(
                    pesan(f"Komponen {row.component_name} muncul lebih dari sekali (baris {row.idx}).",
                          "Daftar komponen tidak kena pajak tidak boleh ganda.",
                          "Hapus baris ganda dan simpan lagi.", BERWENANG),
                    title="Komponen ganda")
            terlihat.add(kunci)
