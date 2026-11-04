import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint

# DocType payroll yang kelak menaut ke jadwal lewat field `payroll_schedule`.
# Selama DocType atau field itu belum ada, pemeriksaan dilewati.
PEMAKAI = (
    ("HRIS Employee Pay", "payroll_schedule"),
    ("HRIS Payroll Period", "payroll_schedule"),
)


class HRISPayrollSchedule(Document):
    def validate(self):
        self.schedule_name = (self.schedule_name or "").strip()
        self.validate_offset()
        self.validate_type_parameters()
        self.validate_locked()
        self.validate_deactivation()

    def validate_offset(self):
        offset = cint(self.pay_date_offset_days)
        if offset < 0 or offset > 60:
            frappe.throw(_("Jeda ke Hari Bayar harus antara 0 dan 60 hari."))
        self.pay_date_offset_days = offset

    def validate_type_parameters(self):
        # validate jalan sebelum cek field wajib, jadi cek bersyarat dilakukan di sini
        tipe = self.schedule_type
        if not tipe:
            return

        if tipe == "Bulanan":
            hari = cint(self.cut_off_day)
            if hari < 1 or hari > 31:
                frappe.throw(_("Tanggal Cut-off harus antara 1 dan 31."))
            self.cut_off_day = hari
            self.week_start_day = None
            self.period_days = 0
            self.anchor_date = None
            self.set("cut_off_dates", [])

        elif tipe == "Mingguan":
            if not self.week_start_day:
                frappe.throw(_("Pilih Hari Awal Minggu."))
            self.cut_off_day = 0
            self.period_days = 0
            self.anchor_date = None
            self.set("cut_off_dates", [])

        elif tipe == "Harian":
            if cint(self.period_days) < 1:
                frappe.throw(_("Panjang Periode minimal 1 hari."))
            if not self.anchor_date:
                frappe.throw(_("Isi Tanggal Acuan."))
            self.cut_off_day = 0
            self.week_start_day = None
            self.set("cut_off_dates", [])

        elif tipe == "Tanggal Tetap":
            rows = self.cut_off_dates or []
            if not rows:
                frappe.throw(_("Isi minimal satu Tanggal Cut-off."))
            hari_list = []
            for nomor, row in enumerate(rows, start=1):
                hari = cint(row.day_of_month)
                if hari < 1 or hari > 31:
                    frappe.throw(_("Baris {0}: tanggal harus antara 1 dan 31.").format(nomor))
                hari_list.append(hari)
            if len(set(hari_list)) != len(hari_list):
                frappe.throw(_("Tanggal Cut-off tidak boleh ganda."))
            self.cut_off_day = 0
            self.week_start_day = None
            self.period_days = 0
            self.anchor_date = None
            self.set("cut_off_dates", [{"day_of_month": h} for h in sorted(hari_list)])

    def _dipakai_oleh(self):
        hasil = []
        for doctype, field in PEMAKAI:
            if frappe.db.exists("DocType", doctype) and frappe.get_meta(doctype).has_field(field):
                if frappe.db.exists(doctype, {field: self.name}):
                    hasil.append(doctype)
        return hasil

    def _snapshot(self, doc):
        return (
            doc.schedule_type,
            doc.company,
            cint(doc.cut_off_day),
            doc.week_start_day or "",
            cint(doc.period_days),
            str(doc.anchor_date or ""),
            tuple(sorted(cint(r.day_of_month) for r in (doc.cut_off_dates or []))),
        )

    def validate_locked(self):
        # Parameter periode yang sudah dipakai tidak boleh berubah: periode lama ikut bergeser.
        sebelum = self.get_doc_before_save()
        if not sebelum:
            return
        dipakai = self._dipakai_oleh()
        if not dipakai:
            return
        if self._snapshot(sebelum) != self._snapshot(self):
            frappe.throw(
                _("Jadwal ini sudah dipakai oleh: {0}. Jenis, Company, dan parameter periode tidak boleh diubah. Buat jadwal baru, lalu pindahkan karyawannya.").format(
                    ", ".join(dipakai)
                )
            )

    def validate_deactivation(self):
        if self.is_active or self.is_new():
            return
        sebelum = self.get_doc_before_save()
        if not sebelum or not sebelum.is_active:
            return
        doctype = "HRIS Employee Pay"
        if not frappe.db.exists("DocType", doctype):
            return
        meta = frappe.get_meta(doctype)
        if not (meta.has_field("payroll_schedule") and meta.has_field("is_active")):
            return
        if frappe.db.exists(doctype, {"payroll_schedule": self.name, "is_active": 1}):
            frappe.throw(_("Jadwal {0} masih dipakai karyawan aktif. Pindahkan karyawannya dulu.").format(self.name))
