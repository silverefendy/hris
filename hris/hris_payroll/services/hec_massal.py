"""K-140 tahap B: tombol massal "Terapkan ke Department atau Grup".

rencanakan_massal() murni (tanpa database). Aturan (R3): karyawan yang sudah punya HEC aktif pada rentang itu
(Berlaku maupun Tidak Berlaku) DILEWATI dan dilaporkan, tidak ditimpa. pratinjau() hanya membaca.
terapkan() membuat HEC Berlaku per karyawan lewat DocType HEC (semua aturan HEC tetap berlaku), satu savepoint
per karyawan, sehingga satu kegagalan tidak membatalkan yang lain.
"""
import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, strip_html_tags
from frappe.utils.nestedset import get_descendants_of

from hris.hris_payroll.doctype.hris_employee_component.hris_employee_component import _baris_gaji
from hris.hris_payroll.doctype.hris_employee_pay.hris_employee_pay import _akses_penuh, boleh_baris

HEC = "HRIS Employee Component"
EMP = "HRIS Employee"
DEPT = "HRIS Department"
GRUP = "HRIS Employee Group"
KATALOG = "HRIS Pay Component"
BATAS = 3000
CONTOH = 50
SP = "hec_massal_"


def rencanakan_massal(karyawan, hec_ada, boleh, dari, sampai):
    """karyawan = [{name, employee_name}]; hec_ada = {employee: [{name, status, date_from, date_to}]} (aktif);
    boleh = {employee: bool} (tidak ada = boleh). Mengembalikan {"buat": [employee], "lewati": [{employee, nama, alasan}]}."""
    dari, sampai = getdate(dari), getdate(sampai)
    buat, lewati = [], []
    for k in karyawan:
        e = k["name"]
        nama = k.get("employee_name")
        if not boleh.get(e, True):
            lewati.append({"employee": e, "nama": nama, "alasan": _("Tidak berhak (jenis gaji karyawan ini)")})
            continue
        bentrok = [h for h in hec_ada.get(e, []) if getdate(h["date_from"]) <= sampai and getdate(h["date_to"]) >= dari]
        if bentrok:
            h = bentrok[0]
            lewati.append({
                "employee": e, "nama": nama,
                "alasan": _("Sudah punya penetapan aktif {0} ({1}, {2} sampai {3})").format(
                    h["name"], h["status"], h["date_from"], h["date_to"]),
            })
            continue
        buat.append(e)
    return {"buat": buat, "lewati": lewati}


def _pilih(department, termasuk_anak, employee_group):
    filters = {"status": "Aktif"}
    if department:
        if not frappe.db.exists(DEPT, department):
            frappe.throw(_("Department tidak ditemukan."))
        daftar = [department]
        if cint(termasuk_anak):
            daftar += list(get_descendants_of(DEPT, department, ignore_permissions=True))
        filters["department"] = ["in", daftar]
    else:
        if not frappe.db.exists(GRUP, employee_group):
            frappe.throw(_("Grup tidak ditemukan."))
        filters["employee_group"] = employee_group
    hasil = frappe.get_all(EMP, filters=filters, fields=["name", "employee_name"], order_by="name asc",
                           limit_page_length=BATAS + 1)
    if len(hasil) > BATAS:
        frappe.throw(_("Terlalu banyak karyawan (lebih dari {0}). Persempit Department atau Grup.").format(BATAS))
    return hasil


def _boleh(employees, dari, sampai):
    """Pemeriksaan hak yang sama dengan controller HEC (jenis gaji pada tanggal awal dan akhir)."""
    if _akses_penuh(frappe.session.user):
        return {}
    hasil = {}
    for e in employees:
        jenis = set()
        for tgl in (dari, sampai):
            b = _baris_gaji(e, tgl)
            jenis.add(b.pay_type if b else "")
        if "Bulanan" in jenis:
            pt = "Bulanan"
        elif jenis == {"Harian"}:
            pt = "Harian"
        else:
            pt = ""
        hasil[e] = boleh_baris(pt)
    return hasil


def _periksa(component, date_from, date_to, department, employee_group):
    frappe.has_permission(HEC, "create", throw=True)
    if bool(department) == bool(employee_group):
        frappe.throw(_("Pilih Department atau Grup, salah satu saja."))
    if not component or not frappe.db.exists(KATALOG, component):
        frappe.throw(_("Komponen tidak ditemukan di katalog."))
    if not cint(frappe.db.get_value(KATALOG, component, "is_active")):
        frappe.throw(_("Komponen ini tidak aktif di katalog."))
    if not date_from or not date_to:
        frappe.throw(_("Isi Dari dan Sampai."))
    dari, sampai = getdate(date_from), getdate(date_to)
    if sampai < dari:
        frappe.throw(_("Sampai tidak boleh sebelum Dari."))
    return dari, sampai


def _susun(component, date_from, date_to, department, termasuk_anak, employee_group):
    dari, sampai = _periksa(component, date_from, date_to, department, employee_group)
    karyawan = _pilih(department, termasuk_anak, employee_group)
    nama = [k["name"] for k in karyawan]
    hec_ada = {}
    if nama:
        for h in frappe.get_all(
            HEC,
            filters={"component": component, "is_active": 1, "employee": ["in", nama],
                     "date_from": ["<=", sampai], "date_to": [">=", dari]},
            fields=["name", "employee", "status", "date_from", "date_to"],
        ):
            hec_ada.setdefault(h["employee"], []).append(h)
    rencana = rencanakan_massal(karyawan, hec_ada, _boleh(nama, dari, sampai), dari, sampai)
    return karyawan, rencana, dari, sampai


@frappe.whitelist()
def pratinjau(component, date_from, date_to, department=None, termasuk_anak=0, employee_group=None):
    karyawan, r, _dari, _sampai = _susun(component, date_from, date_to, department, termasuk_anak, employee_group)
    return {
        "dipilih": len(karyawan), "akan_dibuat": len(r["buat"]), "dilewati": len(r["lewati"]),
        "contoh_lewati": r["lewati"][:CONTOH],
    }


@frappe.whitelist()
def terapkan(component, date_from, date_to, reason, amount=0, department=None, termasuk_anak=0, employee_group=None):
    reason = (reason or "").strip()
    if not reason:
        frappe.throw(_("Alasan wajib diisi."))
    if flt(amount) < 0:
        frappe.throw(_("Nominal Khusus tidak boleh negatif."))
    karyawan, r, dari, sampai = _susun(component, date_from, date_to, department, termasuk_anak, employee_group)
    nama = {k["name"]: k.get("employee_name") for k in karyawan}
    dibuat, gagal = 0, []
    for i, e in enumerate(r["buat"]):
        sp = SP + str(i)
        frappe.db.savepoint(sp)
        try:
            frappe.get_doc({
                "doctype": HEC, "employee": e, "component": component, "status": "Berlaku", "amount": flt(amount),
                "date_from": dari, "date_to": sampai, "is_active": 1, "reason": "Massal: " + reason,
            }).insert()
            dibuat += 1
        except (frappe.ValidationError, frappe.PermissionError) as ex:
            frappe.db.rollback(save_point=sp)
            frappe.clear_messages()
            gagal.append({"employee": e, "nama": nama.get(e), "alasan": strip_html_tags(str(ex))[:300]})
    return {
        "dibuat": dibuat, "dilewati": len(r["lewati"]), "gagal": len(gagal),
        "daftar_lewati": r["lewati"][:CONTOH], "daftar_gagal": gagal[:CONTOH],
        "pesan": _("Selesai: {0} dibuat, {1} dilewati, {2} gagal.").format(dibuat, len(r["lewati"]), len(gagal)),
    }
