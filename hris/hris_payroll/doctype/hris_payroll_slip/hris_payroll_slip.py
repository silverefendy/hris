import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import make_autoname
from frappe.utils import cstr, flt, getdate

TABEL = "HRIS Payroll Slip"
AKSES_PENUH = {"System Manager", "HRIS Payroll Manager", "HRIS Direksi"}
PERAN_ADMIN = "HRIS Payroll Admin"

KUNCI_TEKS = (
    "payroll_period", "employee", "employee_name", "erpnext_employee", "company",
    "payroll_schedule", "period_start", "period_end", "pay_date", "pay_type",
    "employee_pay", "employee_group", "department", "unique_key", "status",
)
KUNCI_ANGKA = (
    "base_amount", "hourly_rate", "overtime_multiplier", "working_days", "present_days",
    "absent_days", "absent_deducted_days", "incomplete_days", "unclassified_absent_days",
    "scheduled_hours_total", "late_deduction_hours", "early_deduction_hours", "overtime_hours",
)


def _peran(user):
    return set(frappe.get_roles(user))


def _akses_penuh(user):
    return user == "Administrator" or bool(_peran(user) & AKSES_PENUH)


def get_permission_query_conditions(user=None, doctype=None):
    """Payroll Admin hanya melihat slip Harian (K-110)."""
    user = user or frappe.session.user
    if _akses_penuh(user):
        return ""
    if PERAN_ADMIN in _peran(user):
        return "`tabHRIS Payroll Slip`.`pay_type` = 'Harian'"
    return "1=0"


def has_permission(doc, ptype=None, user=None, debug=False):
    """Hanya boleh MENOLAK (False); kembalikan True bila tidak menolak (Frappe 16)."""
    user = user or frappe.session.user
    if _akses_penuh(user):
        return True
    if PERAN_ADMIN in _peran(user) and doc.get("pay_type") not in (None, "", "Harian"):
        return False
    return True


class HRISPayrollSlip(Document):
    def before_insert(self):
        if not self.flags.dari_layanan:
            frappe.throw(_("Slip dibuat lewat tombol Buat Slip di Periode Gaji, bukan dari form ini."))

    def autoname(self):
        yymm = getdate(self.period_end).strftime("%y%m")
        self.name = make_autoname("PSL-{0}-.####".format(yymm))

    def validate(self):
        if self.flags.dari_layanan:
            self.hitung_total()
            return
        lama = self.get_doc_before_save()
        if not lama:
            return
        if lama.status != "Draft":
            frappe.throw(
                _("Slip berstatus {0} terkunci. Untuk koreksi, kembalikan atau buka kembali Periode Gaji ke Draft.").format(lama.status)
            )
        self.validate_terkunci(lama)
        self.validate_komponen(lama)
        self.validate_bpjs(lama)
        self.hitung_total()

    def validate_terkunci(self, lama):
        berubah = []
        for fieldname in KUNCI_TEKS:
            if cstr(self.get(fieldname) or "") != cstr(lama.get(fieldname) or ""):
                berubah.append(self.meta.get_label(fieldname))
        for fieldname in KUNCI_ANGKA:
            if abs(flt(self.get(fieldname)) - flt(lama.get(fieldname))) > 0.0001:
                berubah.append(self.meta.get_label(fieldname))
        if berubah:
            frappe.throw(_("Kolom ini terisi otomatis dan tidak dapat diubah: {0}.").format(", ".join(berubah)))

    def validate_komponen(self, lama):
        def otomatis(doc):
            return sorted(
                (cstr(r.component), cstr(r.component_type), int(round(flt(r.amount))), cstr(r.basis), cstr(r.reason).strip())
                for r in doc.components
                if r.source == "Otomatis"
            )

        if otomatis(self) != otomatis(lama):
            frappe.throw(_("Komponen Otomatis tidak dapat diubah atau ditambah dengan tangan. Gunakan Hitung Ulang Slip, atau tambahkan komponen Manual."))
        for r in self.components:
            if r.source != "Manual":
                continue
            if not cstr(r.component).strip():
                frappe.throw(_("Baris {0}: isi nama komponen.").format(r.idx))
            if flt(r.amount) <= 0:
                frappe.throw(_("Baris {0}: jumlah komponen Manual harus lebih dari 0 (jenis menentukan tambah atau kurang).").format(r.idx))
            if not cstr(r.reason).strip():
                frappe.throw(_("Baris {0}: alasan wajib diisi untuk komponen Manual.").format(r.idx))

    def validate_bpjs(self, lama):
        def rincian(doc):
            return sorted(
                (
                    cstr(r.program),
                    cstr(r.risk_class),
                    int(round(flt(r.base_amount))),
                    int(round(flt(r.capped_base))),
                    round(flt(r.employee_rate), 4),
                    round(flt(r.company_rate), 4),
                    int(round(flt(r.employee_amount))),
                    int(round(flt(r.company_amount))),
                )
                for r in (doc.get("bpjs_items") or [])
            )

        if rincian(self) != rincian(lama):
            frappe.throw(_("Rincian BPJS terisi otomatis dan tidak dapat diubah dengan tangan. Gunakan Hitung Ulang Slip."))

    def hitung_total(self):
        pendapatan = sum(flt(r.amount) for r in self.components if r.component_type == "Pendapatan")
        potongan = sum(flt(r.amount) for r in self.components if r.component_type == "Potongan")
        self.total_earning = pendapatan
        self.total_deduction = potongan
        self.net_pay = pendapatan - potongan

    def on_trash(self):
        if self.status != "Draft":
            frappe.throw(_("Hanya slip berstatus Draft yang boleh dihapus."))
