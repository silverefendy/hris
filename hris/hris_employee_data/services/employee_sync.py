"""Sinkron satu arah: HRIS Employee -> Employee ERPNext (K-101).

Data Sensitif dan field user tidak pernah dikirim. Nilai kosong di HRIS
tidak menimpa isi Employee ERPNext, kecuali status dan relieving_date.
"""

import frappe
from frappe import _
from frappe.utils import cstr, now_datetime, strip_html

SAVEPOINT = "sinkron_employee"

GENDER = {
    "Laki-laki": "Male",
    "Perempuan": "Female",
    "Tidak Disebutkan": "Prefer not to say",
}
STATUS = {"Aktif": "Active", "Resign": "Left"}
PERKAWINAN = {
    "Belum Menikah": "Single",
    "Menikah": "Married",
    "Cerai Hidup": "Divorced",
    "Cerai Mati": "Widowed",
}

# (field HRIS, field Employee ERPNext)
PEMETAAN_LANGSUNG = (
    ("employee_name", "first_name"),
    ("birth_date", "date_of_birth"),
    ("date_of_joining", "date_of_joining"),
    ("company", "company"),
    ("branch", "branch"),
    ("department", "department"),
    ("attendance_device_id", "attendance_device_id"),
    ("employee_group", "hris_employee_group"),
    ("legacy_payroll_code", "hris_payroll_code"),
    ("contract_end_date", "contract_end_date"),
    ("phone", "cell_number"),
    ("email", "personal_email"),
    ("address", "current_address"),
)


def _ambil(tabel, kunci, label):
    if kunci not in tabel:
        frappe.throw(
            _("{0} '{1}' belum bisa dipetakan ke Employee ERPNext.").format(label, kunci)
        )
    return tabel[kunci]


def bangun_nilai(doc):
    """Nilai yang akan dikirim ke Employee ERPNext."""
    nilai = {}
    for sumber, tujuan in PEMETAAN_LANGSUNG:
        isi = doc.get(sumber)
        if isi not in (None, ""):
            nilai[tujuan] = isi
    nilai["gender"] = _ambil(GENDER, doc.gender, "Jenis kelamin")
    nilai["status"] = _ambil(STATUS, doc.status, "Status")
    nilai["relieving_date"] = doc.resign_date if doc.status == "Resign" else None
    # HRIS menyimpan nama lengkap; bagian nama lain di ERPNext dikosongkan agar tidak ganda.
    nilai["middle_name"] = None
    nilai["last_name"] = None
    if doc.marital_status:
        nilai["marital_status"] = _ambil(PERKAWINAN, doc.marital_status, "Status perkawinan")
    return nilai


def _seri_awal():
    opsi = frappe.get_meta("Employee").get_field("naming_series").options or ""
    for baris in opsi.split("\n"):
        if baris.strip():
            return baris.strip()
    return None


def _terapkan(doc):
    nilai = bangun_nilai(doc)
    if not doc.erpnext_employee:
        emp = frappe.new_doc("Employee")
        emp.update(nilai)
        if not emp.get("naming_series"):
            emp.naming_series = _seri_awal()
        emp.insert(ignore_permissions=True)
        return "Employee ERPNext dibuat: " + emp.name, emp.name
    emp = frappe.get_doc("Employee", doc.erpnext_employee)
    berubah = {k: v for k, v in nilai.items() if cstr(emp.get(k)) != cstr(v)}
    if not berubah:
        return "Tidak ada perubahan", emp.name
    emp.update(berubah)
    emp.save(ignore_permissions=True)
    return "Employee ERPNext diperbarui (%d field)" % len(berubah), emp.name


def _catat(doc, status, pesan, employee=None):
    nilai = {"sync_status": status, "last_sync": now_datetime(), "sync_error": pesan}
    if employee:
        nilai["erpnext_employee"] = employee
    # set_value (bukan doc.db_set) agar perubahan ini tidak masuk Audit Trail
    frappe.db.set_value("HRIS Employee", doc.name, nilai, update_modified=False)


def sinkron_dokumen(doc):
    """Sinkronkan satu dokumen. Galat sinkron tidak dilempar; dicatat di sync_error."""
    jumlah_pesan = len(frappe.local.message_log)
    frappe.db.savepoint(SAVEPOINT)
    try:
        hasil, nama_employee = _terapkan(doc)
    except Exception as e:
        frappe.db.rollback(save_point=SAVEPOINT)
        # buang pesan popup yang dibuat frappe.throw di dalam sinkron
        frappe.local.message_log = frappe.local.message_log[:jumlah_pesan]
        pesan = strip_html(cstr(e))[:500]
        _catat(doc, "Gagal", pesan)
        return "Gagal: " + pesan
    _catat(doc, "Berhasil", None, nama_employee)
    return hasil


def sinkron_employee(nama):
    return sinkron_dokumen(frappe.get_doc("HRIS Employee", nama))


def periksa_pemetaan():
    """Daftar masalah pemetaan terhadap Employee ERPNext (kosong = aman)."""
    masalah = []
    meta = frappe.get_meta("Employee")
    tujuan = [t for s, t in PEMETAAN_LANGSUNG]
    tujuan += ["gender", "status", "relieving_date", "marital_status"]
    tujuan += ["middle_name", "last_name"]
    for t in tujuan:
        if not meta.has_field(t):
            masalah.append("field tidak ada di Employee: " + t)
    for v in GENDER.values():
        if not frappe.db.exists("Gender", v):
            masalah.append("Gender tidak ada: " + v)
    for nama_field, tabel in (("status", STATUS), ("marital_status", PERKAWINAN)):
        df = meta.get_field(nama_field)
        opsi = [o.strip() for o in (df.options or "").split("\n")]
        for v in tabel.values():
            if v not in opsi:
                masalah.append("opsi %s tidak ada: %s" % (nama_field, v))
    return masalah
