import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, flt, getdate

from hris.hris_payroll.doctype.hris_employee_pay.hris_employee_pay import (
    PERAN_ADMIN,
    PESAN_HAK,
    _akses_penuh,
    _peran,
    boleh_baris,
    periode_final_sejak,
)

TABEL = "HRIS Employee Component"
ID_PENGUBAH = ("date_from", "date_to", "status", "amount", "is_active")


def _baris_gaji(employee, tanggal):
    """Baris HRIS Employee Pay yang berlaku pada tanggal itu: {pay_type, payroll_schedule} atau None."""
    baris = frappe.db.sql(
        """
        select pay_type, payroll_schedule from `tabHRIS Employee Pay`
        where employee = %(e)s and effective_from <= %(d)s
          and (effective_to is null or effective_to >= %(d)s)
        order by effective_from desc limit 1
        """,
        {"e": employee, "d": getdate(tanggal)},
        as_dict=True,
    )
    return baris[0] if baris else None


class HRISEmployeeComponent(Document):
    def validate(self):
        lama = None if self.is_new() else self.get_doc_before_save()
        self.isi_karyawan()
        self.validate_tanggal()
        self.validate_status_nominal()
        if lama:
            self.validate_terkunci(lama)
        self.isi_pay_type()
        self.validate_hak(lama)
        self.validate_alasan(lama)
        self.validate_periode_final(lama)
        self.validate_tumpang_tindih()

    def isi_karyawan(self):
        emp = frappe.db.get_value(
            "HRIS Employee", self.employee,
            ["employee_name", "company", "department", "employee_group"], as_dict=True,
        )
        if not emp:
            frappe.throw(_("Karyawan tidak ditemukan."))
        if not emp.company:
            frappe.throw(_("Karyawan belum punya Company. Lengkapi dulu di HRIS Employee."))
        self.employee_name = emp.employee_name
        self.company = emp.company
        self.department = emp.department
        self.employee_group = emp.employee_group

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
        if lama.employee != self.employee or lama.component != self.component:
            frappe.throw(
                _("Karyawan dan Komponen tidak dapat diubah. Matikan centang Aktif pada baris ini, lalu buat baris baru.")
            )

    def isi_pay_type(self):
        jenis = set()
        for tgl in (self.date_from, self.date_to):
            baris = _baris_gaji(self.employee, tgl)
            jenis.add(baris.pay_type if baris else "")
        if "Bulanan" in jenis:
            self.pay_type = "Bulanan"
        elif jenis == {"Harian"}:
            self.pay_type = "Harian"
        else:
            self.pay_type = ""

    def validate_hak(self, lama):
        if not boleh_baris(self.pay_type):
            frappe.throw(_(PESAN_HAK), frappe.PermissionError)
        if lama and lama.pay_type and not boleh_baris(lama.pay_type):
            frappe.throw(_(PESAN_HAK), frappe.PermissionError)

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

    def validate_periode_final(self, lama):
        if not self._berubah(lama):
            return
        jadwal = set()
        tanggal = [getdate(self.date_from), getdate(self.date_to)]
        if lama:
            tanggal += [getdate(lama.date_from), getdate(lama.date_to)]
        for tgl in tanggal:
            baris = _baris_gaji(self.employee, tgl)
            if baris:
                jadwal.add(baris.payroll_schedule)
        final = periode_final_sejak(jadwal, min(tanggal))
        if final:
            frappe.throw(
                _(
                    "Masalah: tanggal pengecualian jatuh pada atau sebelum akhir periode gaji yang sudah Final ({0}). "
                    "Penyebab: periode Final terkunci (K-128). "
                    "Tindakan: buka kembali periodenya, atau pakai tanggal setelah periode itu. "
                    "Berwenang: HRIS Payroll Manager."
                ).format(final)
            )

    def validate_tumpang_tindih(self):
        if not self.is_active:
            return
        ada = frappe.get_all(
            TABEL,
            filters={
                "employee": self.employee,
                "component": self.component,
                "is_active": 1,
                "name": ["!=", self.name or ""],
                "date_from": ["<=", self.date_to],
                "date_to": [">=", self.date_from],
            },
            fields=["name", "date_from", "date_to"],
            limit=1,
        )
        if ada:
            frappe.throw(
                _(
                    "Masalah: rentang tanggal tumpang tindih dengan {0} ({1} sampai {2}). "
                    "Penyebab: satu karyawan dan komponen hanya boleh punya satu pengecualian aktif pada satu tanggal. "
                    "Tindakan: ubah rentang baris itu, atau matikan Aktif pada baris itu."
                ).format(ada[0].name, ada[0].date_from, ada[0].date_to)
            )


def get_permission_query_conditions(user=None, doctype=None):
    """Penyaring baris untuk list view, Link, dan laporan (mengikuti K-127)."""
    user = user or frappe.session.user
    if _akses_penuh(user):
        return ""
    if PERAN_ADMIN in _peran(user):
        return "`tabHRIS Employee Component`.`pay_type` = 'Harian'"
    return "1=0"


def has_permission(doc, ptype=None, user=None, debug=False):
    """Hanya boleh MENOLAK (False). Mengembalikan True bila tidak menolak (Frappe 16: None dianggap menolak)."""
    user = user or frappe.session.user
    if _akses_penuh(user):
        return True
    nama = doc.get("name") or ""
    baru = (not nama) or nama.startswith("new-")
    if PERAN_ADMIN in _peran(user) and not baru and doc.get("pay_type") != "Harian":
        return False
    return True
