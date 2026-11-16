import frappe
from frappe.model.document import Document
from frappe.utils import flt, getdate

from hris.hris_payroll.services.pph21_rate import pesan

BERWENANG = "HRD (HRIS HR Admin) atau System Manager"


class HRISPPh21Settings(Document):
    def validate(self):
        self._cek_pemetaan()
        self._cek_komponen()
        self._cek_biaya_jabatan()
        self._cek_pasal17()
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
            if flt(row.ptkp_amount) < 0:
                frappe.throw(
                    pesan(f"PTKP Nominal negatif pada status {row.ptkp_status} (baris {row.idx}).",
                          f"Nilai: {row.ptkp_amount}.",
                          "Isi 0 atau lebih, atau kosongkan.", BERWENANG),
                    title="PTKP nominal tidak valid")
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

    def _cek_biaya_jabatan(self):
        persen = flt(self.biaya_jabatan_persen)
        if persen < 0 or persen > 100:
            frappe.throw(
                pesan("Biaya jabatan (%) harus antara 0 dan 100.", f"Nilai: {self.biaya_jabatan_persen}.",
                      "Isi persen, misalnya 5 untuk 5%, atau kosongkan.", BERWENANG),
                title="Biaya jabatan tidak valid")
        if flt(self.biaya_jabatan_maks_tahun) < 0:
            frappe.throw(
                pesan("Batas biaya jabatan setahun negatif.", f"Nilai: {self.biaya_jabatan_maks_tahun}.",
                      "Isi 0 atau lebih, atau kosongkan.", BERWENANG),
                title="Biaya jabatan tidak valid")

    def _cek_pasal17(self):
        per_set = {}
        for row in self.pasal17_rates or []:
            if flt(row.bruto_from) < 0:
                frappe.throw(
                    pesan(f"Bruto Dari negatif pada tarif Pasal 17 (baris {row.idx}).", f"Nilai: {row.bruto_from}.",
                          "Isi 0 atau lebih.", BERWENANG), title="Tarif Pasal 17 tidak valid")
            if row.open_ended:
                row.bruto_to = None
            elif flt(row.bruto_to) < flt(row.bruto_from):
                frappe.throw(
                    pesan(f"Bruto Sampai lebih kecil dari Bruto Dari pada tarif Pasal 17 (baris {row.idx}).",
                          f"Dari {row.bruto_from}, sampai {row.bruto_to}.",
                          "Perbaiki rentang, atau centang Tanpa Batas Atas.", BERWENANG),
                    title="Tarif Pasal 17 tidak valid")
            if flt(row.rate_percent) < 0 or flt(row.rate_percent) > 100:
                frappe.throw(
                    pesan(f"Tarif harus antara 0 dan 100 persen (baris {row.idx}).", f"Nilai: {row.rate_percent}.",
                          "Isi tarif dalam persen, misalnya 5 untuk 5%.", BERWENANG),
                    title="Tarif Pasal 17 tidak valid")
            per_set.setdefault(str(getdate(row.effective_from)), []).append(row)
        tak_hingga = float("inf")
        for tanggal, daftar in per_set.items():
            for i, a in enumerate(daftar):
                a_atas = tak_hingga if a.open_ended else flt(a.bruto_to)
                for b in daftar[i + 1:]:
                    b_atas = tak_hingga if b.open_ended else flt(b.bruto_to)
                    if flt(a.bruto_from) <= b_atas and flt(b.bruto_from) <= a_atas:
                        frappe.throw(
                            pesan(f"Rentang tarif Pasal 17 bertumpang tindih (baris {a.idx} dan {b.idx}, berlaku sejak {tanggal}).",
                                  "Dua baris pada set tanggal yang sama mencakup bruto yang beririsan.",
                                  "Ubah rentang agar tidak beririsan.", BERWENANG),
                            title="Rentang tarif Pasal 17 bertumpang tindih")
