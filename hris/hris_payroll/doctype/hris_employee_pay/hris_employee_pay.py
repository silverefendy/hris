import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, cstr, flt, getdate

TABEL = "HRIS Employee Pay"
AKSES_PENUH = {"System Manager", "HRIS Payroll Manager", "HRIS Direksi"}
PERAN_ADMIN = "HRIS Payroll Admin"
PESAN_HAK = "Anda tidak berhak mengubah data gaji karyawan ini."

TERKUNCI = (
    ("employee", "Karyawan"),
    ("pay_type", "Jenis Gaji"),
    ("amount", "Nominal"),
    ("payroll_schedule", "Jadwal Gaji"),
    ("effective_from", "Berlaku Dari"),
    ("effective_to", "Berlaku Sampai"),
    ("change_reason", "Alasan Perubahan"),
)


def _peran(user):
    return set(frappe.get_roles(user))


def periode_final_sejak(jadwal, tanggal):
    """Nama periode Final milik salah satu jadwal yang berakhir pada atau setelah tanggal. None bila tidak ada."""
    daftar = tuple(j for j in jadwal if j)
    if not daftar or not frappe.db.table_exists("HRIS Payroll Period"):
        return None
    baris = frappe.db.sql(
        """
        select name from `tabHRIS Payroll Period`
        where status = 'Final' and payroll_schedule in %(jadwal)s and period_end >= %(tanggal)s
        limit 1
        """,
        {"jadwal": daftar, "tanggal": getdate(tanggal)},
    )
    return baris[0][0] if baris else None


def _akses_penuh(user):
    return user == "Administrator" or bool(_peran(user) & AKSES_PENUH)


def boleh_baris(pay_type, user=None):
    """True bila user boleh memegang baris dengan jenis gaji ini (K-110)."""
    user = user or frappe.session.user
    if _akses_penuh(user):
        return True
    if PERAN_ADMIN in _peran(user):
        return pay_type == "Harian"
    return False


def get_permission_query_conditions(user=None, doctype=None):
    """Penyaring baris untuk list view, Link, dan laporan."""
    user = user or frappe.session.user
    if _akses_penuh(user):
        return ""
    if PERAN_ADMIN in _peran(user):
        return "`tabHRIS Employee Pay`.`pay_type` = 'Harian'"
    return "1=0"


def has_permission(doc, ptype=None, user=None, debug=False):
    """Hanya boleh MENOLAK (False). Mengembalikan True bila tidak menolak.

    Frappe 16 memakai `if not hasil`, sehingga None dianggap menolak.
    """
    user = user or frappe.session.user
    if _akses_penuh(user):
        return True
    if PERAN_ADMIN in _peran(user) and doc.get("pay_type") not in (None, "", "Harian"):
        return False
    return True


class HRISEmployeePay(Document):
    def validate(self):
        if self.flags.get("hris_tutup"):
            self.validate_tutup()
            return
        if not self.is_new():
            self.validate_terkunci()
            return
        self.validate_baru()

    # ---- baris baru ----
    def validate_baru(self):
        if flt(self.amount) <= 0:
            frappe.throw(_("Nominal harus lebih dari 0."))

        emp = frappe.db.get_value(
            "HRIS Employee", self.employee, ["employee_name", "company"], as_dict=True
        )
        if not emp:
            frappe.throw(_("Karyawan tidak ditemukan."))
        if not emp.company:
            frappe.throw(_("Karyawan belum punya Company. Lengkapi dulu di HRIS Employee."))
        self.employee_name = emp.employee_name
        self.company = emp.company

        if not self.effective_from:
            frappe.throw(_("Isi Berlaku Dari."))

        self.validate_jadwal()
        self.validate_hak()
        self.validate_urutan()
        self.validate_periode_final()

    def validate_jadwal(self):
        jadwal = frappe.db.get_value(
            "HRIS Payroll Schedule", self.payroll_schedule, ["is_active", "company"], as_dict=True
        )
        if not jadwal:
            frappe.throw(_("Jadwal Gaji tidak ditemukan."))
        if not jadwal.is_active:
            frappe.throw(_("Jadwal Gaji tidak aktif."))
        if jadwal.company != self.company:
            frappe.throw(_("Jadwal Gaji harus satu Company dengan karyawan."))

    def validate_hak(self):
        if not boleh_baris(self.pay_type):
            frappe.throw(_(PESAN_HAK), frappe.PermissionError)
        terbuka = self._baris_terbuka()
        if terbuka and not boleh_baris(terbuka.pay_type):
            frappe.throw(_(PESAN_HAK), frappe.PermissionError)

    def validate_urutan(self):
        # get_all mengabaikan izin: pemeriksaan ini harus melihat semua baris
        terakhir = frappe.get_all(
            TABEL,
            filters={"employee": self.employee},
            fields=["name", "effective_from", "effective_to"],
            order_by="effective_from desc, creation desc",
            limit=1,
        )
        if not terakhir:
            return
        if not (self.change_reason or "").strip():
            frappe.throw(_("Alasan Perubahan wajib diisi karena karyawan ini sudah punya baris gaji."))
        batas = getdate(terakhir[0].effective_to or terakhir[0].effective_from)
        if getdate(self.effective_from) <= batas:
            frappe.throw(
                _("Berlaku Dari harus setelah {0} (baris gaji terakhir karyawan ini).").format(
                    frappe.format(batas, {"fieldtype": "Date"})
                )
            )

    def validate_periode_final(self):
        jadwal = {self.payroll_schedule}
        terbuka = self._baris_terbuka()
        if terbuka:
            jadwal.add(frappe.db.get_value(TABEL, terbuka.name, "payroll_schedule"))
        final = periode_final_sejak(jadwal, self.effective_from)
        if final:
            frappe.throw(
                _("Berlaku Dari jatuh pada atau sebelum akhir periode gaji yang sudah Final ({0}). Buka kembali periodenya (Payroll Manager) atau pilih tanggal setelahnya.").format(final)
            )

    def _baris_terbuka(self, selain=None):
        filters = {"employee": self.employee, "effective_to": ["is", "not set"]}
        if selain:
            filters["name"] = ["!=", selain]
        baris = frappe.get_all(
            TABEL,
            filters=filters,
            fields=["name", "pay_type", "effective_from"],
            order_by="effective_from desc, creation desc",
            limit=1,
        )
        return baris[0] if baris else None

    # ---- baris tersimpan: dikunci ----
    def validate_terkunci(self):
        lama = self.get_doc_before_save()
        if not lama:
            return
        berubah = []
        for fieldname, label in TERKUNCI:
            if fieldname == "amount":
                beda = abs(flt(self.get(fieldname)) - flt(lama.get(fieldname))) > 0.0001
            else:
                beda = cstr(self.get(fieldname) or "") != cstr(lama.get(fieldname) or "")
            if beda:
                berubah.append(label)
        if berubah:
            frappe.throw(
                _("Baris gaji tidak dapat diubah (kolom: {0}). Buat baris baru dengan Berlaku Dari yang baru.").format(
                    ", ".join(berubah)
                )
            )

    # ---- penutupan otomatis oleh sistem ----
    def validate_tutup(self):
        if self.effective_to and getdate(self.effective_to) < getdate(self.effective_from):
            frappe.throw(_("Berlaku Sampai tidak boleh sebelum Berlaku Dari."))

    def after_insert(self):
        akhir = add_days(self.effective_from, -1)
        for nama in frappe.get_all(
            TABEL,
            filters={
                "employee": self.employee,
                "effective_to": ["is", "not set"],
                "name": ["!=", self.name],
            },
            pluck="name",
        ):
            lama = frappe.get_doc(TABEL, nama)
            lama.flags.hris_tutup = True
            lama.effective_to = akhir
            lama.save(ignore_permissions=True)

    def on_trash(self):
        final = periode_final_sejak({self.payroll_schedule}, self.effective_from)
        if final:
            frappe.throw(_("Baris gaji ini berada pada atau sebelum periode gaji yang sudah Final ({0}); tidak boleh dihapus.").format(final))
        if self.effective_to:
            frappe.throw(_("Baris yang sudah ditutup tidak boleh dihapus. Hapus dulu baris yang lebih baru."))
        sebelumnya = frappe.get_all(
            TABEL,
            filters={"employee": self.employee, "name": ["!=", self.name]},
            fields=["name"],
            order_by="effective_from desc, creation desc",
            limit=1,
        )
        if sebelumnya:
            lama = frappe.get_doc(TABEL, sebelumnya[0].name)
            lama.flags.hris_tutup = True
            lama.effective_to = None
            lama.save(ignore_permissions=True)
