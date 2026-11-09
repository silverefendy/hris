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
        if frappe.db.table_exists("HRIS Payroll Slip") and frappe.db.exists("HRIS Payroll Slip", {"payroll_period": self.name}):
            frappe.throw(_("Periode ini sudah memiliki slip gaji; hapus slipnya dulu."))


def _sinkron_status_slip(doc):
    """Status slip mengikuti status periode (K-130). Aman bila tabel slip belum ada."""
    if frappe.db.table_exists("HRIS Payroll Slip"):
        frappe.db.sql(
            "update `tabHRIS Payroll Slip` set status = %s where payroll_period = %s",
            (doc.status, doc.name),
        )


def _pindah(doc, baru, **jejak):
    doc.flags.dari_transisi = True
    doc.status = baru
    for fieldname, nilai in jejak.items():
        doc.set(fieldname, nilai)
    doc.save(ignore_permissions=True)
    _sinkron_status_slip(doc)
    return doc.status


MAKS_DAFTAR = 1500


def _penerima(peran):
    """User aktif pemegang peran, tanpa Administrator dan pengguna yang sedang bertindak."""
    pemegang = frappe.get_all("Has Role", filters={"role": peran, "parenttype": "User"}, pluck="parent")
    if not pemegang:
        return []
    aktif = frappe.get_all("User", filters={"name": ["in", list(set(pemegang))], "enabled": 1}, pluck="name")
    return sorted(u for u in aktif if u not in ("Administrator", "Guest", frappe.session.user))


def _beritahu(doc, peran, isi):
    """Notifikasi in-app (lonceng). Kegagalan tidak boleh membatalkan perpindahan status."""
    try:
        frappe.db.savepoint("hpp_notif")
        for user in _penerima(peran):
            frappe.get_doc(
                {
                    "doctype": "Notification Log",
                    "subject": isi,
                    "for_user": user,
                    "from_user": frappe.session.user,
                    "type": "Alert",
                    "document_type": TABEL,
                    "document_name": doc.name,
                }
            ).insert(ignore_permissions=True)
    except Exception:
        frappe.db.rollback(save_point="hpp_notif")
        frappe.log_error(title="HRIS Payroll Period: notifikasi gagal")


def hitung_kesiapan(doc):
    """Daftar kekurangan yang menghalangi Final. ok=True bila tidak ada.

    Aturan campuran (K-128): Tidak Lengkap wajib Sudah Ditinjau; baris Menunggu menghalangi
    apa pun statusnya; Tidak Hadir berstatus Tidak Perlu tidak menghalangi.
    """
    awal = getdate(doc.period_start)
    akhir = getdate(doc.period_end)
    param = {"jadwal": doc.payroll_schedule, "awal": awal, "akhir": akhir}
    rentang = [str(awal), str(akhir)]
    items = []

    if akhir >= getdate(today()):
        items.append(
            {
                "kode": "belum_berakhir",
                "jumlah": 1,
                "contoh": [],
                "daftar": [],
                "tautan": [],
                "terpotong": False,
                "pesan": _("Periode belum berakhir (akhir periode {0}).").format(doc.period_end),
                "penyebab": _("Data hari-hari terakhir periode masih dapat berubah."),
                "tindakan": _("Tunggu sampai akhir periode lewat, lalu periksa kesiapan lagi."),
                "berwenang": "",
            }
        )

    belum = frappe.db.sql(
        """
        select wh.name, wh.work_date, wh.status, wh.review_status, wh.employee_name
        from `tabHRIS Working Hour` wh
        inner join `tabHRIS Employee` he on he.erpnext_employee = wh.employee
        inner join `tabHRIS Employee Pay` ep on ep.employee = he.name
            and ep.payroll_schedule = %(jadwal)s
            and ep.effective_from <= wh.work_date
            and (ep.effective_to is null or ep.effective_to >= wh.work_date)
        where wh.work_date between %(awal)s and %(akhir)s
          and (
                (wh.status = 'Tidak Lengkap' and ifnull(wh.review_status, '') != 'Sudah Ditinjau')
                or ifnull(wh.review_status, '') = 'Menunggu'
              )
        order by wh.work_date, wh.name
        """,
        param,
        as_dict=True,
    )
    if belum:
        n = len(belum)
        items.append(
            {
                "kode": "belum_ditinjau",
                "jumlah": n,
                "contoh": ["{0} ({1})".format(r.name, r.work_date) for r in belum[:10]],
                "daftar": [
                    {
                        "doctype": "HRIS Working Hour",
                        "name": r.name,
                        "label": r.name,
                        "info": "{0} - {1} - {2} - {3}".format(r.employee_name or "-", r.work_date, r.status, r.review_status or "-"),
                    }
                    for r in belum[:MAKS_DAFTAR]
                ],
                "terpotong": n > MAKS_DAFTAR,
                "tautan": [
                    {
                        "label": _("Lihat semua Tidak Lengkap yang belum Sudah Ditinjau"),
                        "doctype": "HRIS Working Hour",
                        "filters": {
                            "work_date": ["Between", rentang],
                            "status": "Tidak Lengkap",
                            "review_status": ["!=", "Sudah Ditinjau"],
                        },
                    },
                    {
                        "label": _("Lihat semua yang berstatus Menunggu"),
                        "doctype": "HRIS Working Hour",
                        "filters": {"work_date": ["Between", rentang], "review_status": "Menunggu"},
                    },
                ],
                "pesan": _(
                    "Ada {0} hari yang belum ditinjau HRD: Tidak Lengkap yang belum berstatus Sudah Ditinjau, atau baris berstatus Menunggu."
                ).format(n),
                "penyebab": _("Data scan hari itu ambigu atau menunggu keputusan HRD, sehingga jam kerja yang dibayar belum pasti."),
                "tindakan": _(
                    "Buka tiap hari, periksa scan, lalu ubah Status Tinjauan menjadi Sudah Ditinjau (isi penyesuaian bila perlu)."
                ),
                "berwenang": _("HRIS HR Admin, HRIS Manager, atau System Manager"),
            }
        )

    tanpa = frappe.db.sql(
        """
        select wh.employee, he.name as he_name, max(wh.employee_name) as nama, count(*) as hari, min(wh.work_date) as pertama
        from `tabHRIS Working Hour` wh
        left join `tabHRIS Employee` he on he.erpnext_employee = wh.employee
        left join `tabHRIS Employee Pay` ep on ep.employee = he.name
            and ep.effective_from <= wh.work_date
            and (ep.effective_to is null or ep.effective_to >= wh.work_date)
        where wh.work_date between %(awal)s and %(akhir)s
          and wh.status = 'Hadir'
          and ep.name is null
        group by wh.employee, he.name
        order by wh.employee
        """,
        param,
        as_dict=True,
    )
    if tanpa:
        n = len(tanpa)
        items.append(
            {
                "kode": "tanpa_gaji",
                "jumlah": n,
                "contoh": ["{0} ({1} hari)".format(r.employee, r.hari) for r in tanpa[:10]],
                "daftar": [
                    {
                        "doctype": "HRIS Employee" if r.he_name else None,
                        "name": r.he_name,
                        "label": r.nama or r.employee,
                        "info": _("{0} - {1} hari Hadir, mulai {2}").format(r.employee, r.hari, r.pertama),
                        "aksi": "buat_gaji" if r.he_name else None,
                    }
                    for r in tanpa[:MAKS_DAFTAR]
                ],
                "terpotong": n > MAKS_DAFTAR,
                "tautan": [{"label": _("Buka daftar Baris Gaji"), "doctype": "HRIS Employee Pay", "filters": {}}],
                "pesan": _("Ada {0} karyawan berstatus Hadir tanpa baris gaji berlaku pada tanggal kerjanya.").format(n),
                "penyebab": _("Karyawan itu belum punya baris HRIS Employee Pay yang berlaku pada tanggal kerjanya."),
                "tindakan": _(
                    "Buat baris HRIS Employee Pay dengan Berlaku Dari pada atau sebelum tanggal kerja pertama yang tertera."
                ),
                "berwenang": _("HRIS Payroll Manager (semua jenis) atau HRIS Payroll Admin (hanya upah Harian)"),
            }
        )
    return {"ok": not items, "items": items, "awal": rentang[0], "akhir": rentang[1]}


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
    status = _pindah(doc, "Ditinjau", reviewed_by=frappe.session.user, reviewed_on=now_datetime())
    _beritahu(
        doc,
        PERAN_MANAGER,
        _("Periode gaji {0} ({1} s/d {2}) ditinjau oleh {3} dan menunggu difinalkan.").format(
            doc.name, doc.period_start, doc.period_end, frappe.session.user
        ),
    )
    return status


@frappe.whitelist()
def kembalikan(name):
    _wajib_peran(BOLEH_TINJAU, "mengembalikan")
    doc = frappe.get_doc(TABEL, name)
    if doc.status != "Ditinjau":
        frappe.throw(_("Hanya periode Ditinjau yang dapat dikembalikan ke Draft."))
    status = _pindah(doc, "Draft", reviewed_by=None, reviewed_on=None)
    _beritahu(
        doc,
        PERAN_ADMIN,
        _("Periode gaji {0} ({1} s/d {2}) dikembalikan ke Draft oleh {3}. Periksa kesiapan, lalu tinjau kembali.").format(
            doc.name, doc.period_start, doc.period_end, frappe.session.user
        ),
    )
    return status


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
            if item.get("contoh"):
                teks += " " + _("Contoh: {0}.").format(", ".join(item["contoh"][:3]))
            if item.get("tindakan"):
                teks += "<br>&nbsp;&nbsp;" + _("Tindakan: {0}").format(item["tindakan"])
            if item.get("berwenang"):
                teks += "<br>&nbsp;&nbsp;" + _("Berwenang: {0}").format(item["berwenang"])
            baris.append("&bull; " + teks)
        baris.append(_("Gunakan tombol Periksa Kesiapan untuk daftar lengkap beserta tautannya."))
        frappe.throw("<br>".join(baris), title=_("Periode belum dapat difinalkan"))
    status = _pindah(doc, "Final", finalized_by=frappe.session.user, finalized_on=now_datetime())
    _beritahu(
        doc,
        PERAN_ADMIN,
        _("Periode gaji {0} ({1} s/d {2}) difinalkan oleh {3}. Working Hour dan gaji pada rentang ini kini terkunci.").format(
            doc.name, doc.period_start, doc.period_end, frappe.session.user
        ),
    )
    return status


@frappe.whitelist()
def buka_kembali(name, alasan=None):
    _wajib_peran({PERAN_MANAGER}, "membuka kembali")
    if not (alasan or "").strip():
        frappe.throw(_("Alasan wajib diisi untuk membuka kembali periode."))
    doc = frappe.get_doc(TABEL, name)
    if doc.status != "Final":
        frappe.throw(_("Hanya periode Final yang dapat dibuka kembali."))
    status = _pindah(
        doc,
        "Draft",
        reopen_reason=alasan.strip(),
        reviewed_by=None,
        reviewed_on=None,
        finalized_by=None,
        finalized_on=None,
    )
    _beritahu(
        doc,
        PERAN_ADMIN,
        _("Periode gaji {0} ({1} s/d {2}) dibuka kembali oleh {3}. Alasan: {4}. Koreksi diperbolehkan lagi; tinjau ulang sesudahnya.").format(
            doc.name, doc.period_start, doc.period_end, frappe.session.user, alasan.strip()
        ),
    )
    return status
