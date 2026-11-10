import frappe
from frappe.model.document import Document
from frappe.utils import flt, fmt_money

from hris.hris_payroll.services.pph21_rate import pesan

BERWENANG = "HRD (HRIS HR Admin) atau System Manager"
TAK_TERHINGGA = float("inf")


def _batas_atas(open_ended, bruto_to):
    return TAK_TERHINGGA if open_ended else flt(bruto_to)


class HRISPPh21TERRate(Document):
    def validate(self):
        self.ter_category = (self.ter_category or "").strip().upper()
        if self.open_ended:
            self.bruto_to = None
        self._cek_nilai()
        if self.enabled:
            self._cek_tumpang_tindih()

    def _cek_nilai(self):
        if flt(self.bruto_from) < 0:
            frappe.throw(
                pesan("Bruto Dari tidak boleh negatif.", f"Nilai: {self.bruto_from}.",
                      "Isi 0 atau lebih.", BERWENANG), title="Rentang tidak valid")
        if not self.open_ended and flt(self.bruto_to) < flt(self.bruto_from):
            frappe.throw(
                pesan("Bruto Sampai lebih kecil dari Bruto Dari.",
                      f"Dari {self.bruto_from}, sampai {self.bruto_to}.",
                      "Perbaiki rentang, atau centang Tanpa Batas Atas.", BERWENANG),
                title="Rentang tidak valid")
        if flt(self.rate_percent) < 0 or flt(self.rate_percent) > 100:
            frappe.throw(
                pesan("Tarif harus antara 0 dan 100 persen.", f"Nilai: {self.rate_percent}.",
                      "Isi tarif dalam persen, misalnya 1.5 untuk 1,5%.", BERWENANG),
                title="Tarif tidak valid")

    def _cek_tumpang_tindih(self):
        lain = frappe.get_all(
            "HRIS PPh21 TER Rate",
            filters={"ter_category": self.ter_category, "effective_from": self.effective_from,
                     "enabled": 1, "name": ["!=", self.name or ""]},
            fields=["name", "bruto_from", "bruto_to", "open_ended"],
        )
        saya_atas = _batas_atas(self.open_ended, self.bruto_to)
        for r in lain:
            r_atas = _batas_atas(r.open_ended, r.bruto_to)
            if flt(self.bruto_from) <= r_atas and flt(r.bruto_from) <= saya_atas:
                frappe.throw(
                    pesan(f"Rentang bertumpang tindih dengan {r.name} (kategori {self.ter_category}).",
                          f"Baris {r.name} sudah mencakup {fmt_money(r.bruto_from)} sampai "
                          f"{'tanpa batas' if r.open_ended else fmt_money(r.bruto_to)} "
                          "pada kategori dan tanggal berlaku yang sama.",
                          "Ubah rentang agar tidak beririsan, atau nonaktifkan baris lama.", BERWENANG),
                    title="Rentang tarif bertumpang tindih")
