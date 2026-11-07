import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cstr, getdate, now_datetime, today

from hris.hris_payroll.services.payroll_schedule import get_period_for_date

TABEL = "HRIS Payroll Period"
PERAN_MANAGER = "HRIS Payroll Manager"
PERAN_ADMIN = "HRIS Payroll Admin"
BOLEH_TINJAU = {PERAN_MANAGER, PERAN_ADMIN}

# (fieldname, label, tanggal?)
KUNCI = (
    ("payroll_schedule", "Jadwal Gaji", False),
    ("company", "Company", False),
    ("reference_date", "Tanggal Acuan Periode", True),
    ("period_start", "Awal Periode", True),
    ("period_end", "Akhir Periode", True),
    ("pay_date", "Hari Bayar", True),
    ("unique_key", "Kunci Unik", False),
)
JEJAK = ("reviewed_by", "reviewed_on", "finalized_by", "finalized_on", "reopen_reason")


def _nilai(nilai, tanggal=False):
    if tanggal and nilai:
        return str(getdate(nilai))
    return cstr(nilai or "")


def _wajib_peran(peran, tindakan):
    user = frappe.session.user
    if user == "Administrator" or set(frappe.get_roles(user)) & set(peran):
        return
    frappe.throw(_("Anda tidak berhak {0} periode gaji.").format(tindakan), frappe.PermissionError)


class HRISPayrollPeriod(Document):
    def validate(self):
        if self.is_new():
            self.validate_baru()
        else:
            self.validate_terkunci()

    def validate_baru(self):
        jadwal = frappe.db.get_value(
            "HRIS Payroll Schedule", self.payroll_schedule, ["is_active", "company"], as_dict=True
        )
        if not jadwal:
            frappe.throw(_("Jadwal Gaji tidak ditemukan."))
        if not jadwal.is_active:
            frappe.throw(_("Jadwal Gaji tidak aktif."))
        if not self.reference_date:
            frappe.throw(_("Isi Tanggal Acuan Periode."))

        hasil = get_period_for_date(self.payroll_schedule, self.reference_date)
        self.company = jadwal.company
        self.period_start = hasil["start"]
        self.period_end = hasil["end"]
        self.pay_date = hasil["pay_date"]
        self.status = "Draft"
        for fieldname in JEJAK:
            self.set(fieldname, None)

        self.unique_key = "{0}|{1}".format(self.payroll_schedule, self.period_start)
        ada = frappe.db.get_value(TABEL, {"unique_key": self.unique_key}, "name")
        if ada:
            frappe.throw(
                _("Periode {0} sampai {1} untuk jadwal ini sudah ada: {2}.").format(
                    self.period_start, self.period_end, ada
                )
            )

    def validate_terkunci(self):
        lama = self.get_doc_before_save()
        if not lama:
            return
        berubah = [
            label
            for fieldname, label, tanggal in KUNCI
            if _nilai(self.get(fieldname), tanggal) != _nilai(lama.get(fieldname), tanggal)
        ]
        if berubah:
            frappe.throw(_("Kolom ini tidak dapat diubah setelah periode dibuat: {0}.").format(", ".join(berubah)))
        if self.flags.dari_transisi:
            return
        if self.status != lama.status:
            frappe.throw(_("Status hanya berubah lewat tombol Tinjau, Finalkan, Kembalikan, atau Buka Kembali."))
        for fieldname in JEJAK:
            if _nilai(self.get(fieldname)) != _nilai(lama.get(fieldname)):
                frappe.throw(_("Jejak persetujuan terisi otomatis dan tidak dapat diubah."))

    def on_trash(self):
        if self.status != "Draft":
            frappe.throw(_("Hanya periode berstatus Draft yang boleh dihapus."))


def _pindah(doc, baru, **jejak):
    doc.flags.dari_transisi = True
    doc.status = baru
    for fieldname, nilai in jejak.items():
        doc.set(fieldname, nilai)
    doc.save(ignore_permissions=True)
    return doc.status


def hitung_kesiapan(doc):
    """Daftar kekurangan yang menghalangi Final. ok=True bila tidak ada."""
    param = {
        "jadwal": doc.payroll_schedule,
        "awal": getdate(doc.period_start),
        "akhir": getdate(doc.period_end),
    }
    items = []

    if getdate(doc.period_end) >= getdate(today()):
        items.append(
            {
                "kode": "belum_berakhir",
                "jumlah": 1,
                "contoh": [],
                "pesan": _("Periode belum berakhir (akhir periode {0}).").format(doc.period_end),
            }
        )

    belum = frappe.db.sql(
        """
        select wh.name, wh.work_date
        from `tabHRIS Working Hour` wh
        inner join `tabHRIS Employee` he on he.erpnext_employee = wh.employee
        inner join `tabHRIS Employee Pay` ep on ep.employee = he.name
            and ep.payroll_schedule = %(jadwal)s
            and ep.effective_from <= wh.work_date
            and (ep.effective_to is null or ep.effective_to >= wh.work_date)
        where wh.work_date between %(awal)s and %(akhir)s
          and wh.status in ('Tidak Lengkap', 'Tidak Hadir')
          and ifnull(wh.review_status, '') != 'Sudah Ditinjau'
        order by wh.work_date, wh.name
        """,
        param,
        as_dict=True,
    )
    if belum:
        items.append(
            {
                "kode": "belum_ditinjau",
                "jumlah": len(belum),
                "contoh": ["{0} ({1})".format(r.name, r.work_date) for r in belum[:10]],
                "pesan": _("Ada {0} hari Tidak Lengkap atau Tidak Hadir yang belum ditinjau HRD.").format(len(belum)),
            }
        )

    tanpa = frappe.db.sql(
        """
        select wh.employee, count(*) as hari
        from `tabHRIS Working Hour` wh
        left join `tabHRIS Employee` he on he.erpnext_employee = wh.employee
        left join `tabHRIS Employee Pay` ep on ep.employee = he.name
            and ep.effective_from <= wh.work_date
            and (ep.effective_to is null or ep.effective_to >= wh.work_date)
        where wh.work_date between %(awal)s and %(akhir)s
          and wh.status = 'Hadir'
          and ep.name is null
        group by wh.employee
        order by wh.employee
        """,
        param,
        as_dict=True,
    )
    if tanpa:
        items.append(
            {
                "kode": "tanpa_gaji",
                "jumlah": len(tanpa),
                "contoh": ["{0} ({1} hari)".format(r.employee, r.hari) for r in tanpa[:10]],
                "pesan": _("Ada {0} karyawan berstatus Hadir tanpa baris gaji berlaku pada tanggal kerjanya.").format(
                    len(tanpa)
                ),
            }
        )
    return {"ok": not items, "items": items}


@frappe.whitelist()
def get_readiness(name):
    _wajib_peran(BOLEH_TINJAU, "memeriksa kesiapan")
    return hitung_kesiapan(frappe.get_doc(TABEL, name))


@frappe.whitelist()
def tinjau(name):
    _wajib_peran(BOLEH_TINJAU, "meninjau")
    doc = frappe.get_doc(TABEL, name)
    if doc.status != "Draft":
        frappe.throw(_("Hanya periode Draft yang dapat ditinjau."))
    return _pindah(doc, "Ditinjau", reviewed_by=frappe.session.user, reviewed_on=now_datetime())


@frappe.whitelist()
def kembalikan(name):
    _wajib_peran(BOLEH_TINJAU, "mengembalikan")
    doc = frappe.get_doc(TABEL, name)
    if doc.status != "Ditinjau":
        frappe.throw(_("Hanya periode Ditinjau yang dapat dikembalikan ke Draft."))
    return _pindah(doc, "Draft", reviewed_by=None, reviewed_on=None)


@frappe.whitelist()
def finalkan(name):
    _wajib_peran({PERAN_MANAGER}, "memfinalkan")
    doc = frappe.get_doc(TABEL, name)
    if doc.status != "Ditinjau":
        frappe.throw(_("Hanya periode Ditinjau yang dapat difinalkan."))
    kesiapan = hitung_kesiapan(doc)
    if not kesiapan["ok"]:
        baris = []
        for item in kesiapan["items"]:
            teks = item["pesan"]
            if item["contoh"]:
                teks += " " + _("Contoh: {0}.").format(", ".join(item["contoh"][:3]))
            baris.append("&bull; " + teks)
        frappe.throw("<br>".join(baris), title=_("Periode belum dapat difinalkan"))
    return _pindah(doc, "Final", finalized_by=frappe.session.user, finalized_on=now_datetime())


@frappe.whitelist()
def buka_kembali(name, alasan=None):
    _wajib_peran({PERAN_MANAGER}, "membuka kembali")
    if not (alasan or "").strip():
        frappe.throw(_("Alasan wajib diisi untuk membuka kembali periode."))
    doc = frappe.get_doc(TABEL, name)
    if doc.status != "Final":
        frappe.throw(_("Hanya periode Final yang dapat dibuka kembali."))
    return _pindah(
        doc,
        "Draft",
        reopen_reason=alasan.strip(),
        reviewed_by=None,
        reviewed_on=None,
        finalized_by=None,
        finalized_on=None,
    )
