"""Endpoint baca-saja jadwal shift untuk Device Tool (tahap F).

Autentikasi: header X-HRIS-Token (sama dengan endpoint agen). Tidak menulis apa pun dan tidak
mengembalikan nama atau data pribadi: hanya ID Finger, tanggal, nama shift, dan aturan jamnya.

Aturan jadwal sama dengan shift_schedule.get_schedule_for_date (prioritas: Shift Assignment,
Rotasi grup, Jadwal Mingguan grup, lalu hari libur), tetapi dihitung massal supaya cepat.
Sumber grup mengikuti perhitungan resmi: custom field grup di Employee ERPNext.
"""
import frappe
from frappe import _
from frappe.utils import add_days, date_diff, getdate

from hris.hris_attendance.services import shift_schedule as ss
from hris.hris_attendance.services.agent_auth import verify_agent_request

KOLOM = ["id", "tanggal", "shift", "wajib", "works", "libur", "off", "sumber"]
SHIFT_FIELDS = [
    "name", "start_time", "end_time", "crosses_midnight", "duration_minutes", "break_minutes",
    "late_tolerance_min", "early_leave_tolerance_min", "window_before_min", "late_limit_min",
    "window_after_min", "min_out_after_in_min", "overtime_min_minutes",
]
FIELD_JAM = ("start_time", "end_time")


def _hms(value):
    if value is None:
        return ""
    if hasattr(value, "total_seconds"):
        detik = int(value.total_seconds())
        return "%02d:%02d:%02d" % (detik // 3600 % 24, detik % 3600 // 60, detik % 60)
    if hasattr(value, "strftime"):
        return value.strftime("%H:%M:%S")
    return str(value)


def _detail_shift():
    hasil = {}
    for s in frappe.get_all("HRIS Shift", fields=SHIFT_FIELDS):
        d = {}
        for f in SHIFT_FIELDS:
            if f == "name":
                continue
            v = s.get(f)
            d[f] = _hms(v) if f in FIELD_JAM else int(v or 0)
        hasil[s.name] = d
    return hasil


def bangun_jadwal(dari, sampai):
    """Logika inti tanpa autentikasi (dipakai uji)."""
    start, end = getdate(dari), getdate(sampai)
    if end < start:
        frappe.throw(_("Tanggal Sampai tidak boleh sebelum Tanggal Dari."))
    if date_diff(end, start) + 1 > ss.MAX_RANGE_DAYS:
        frappe.throw(_("Rentang maksimal {0} hari.").format(ss.MAX_RANGE_DAYS))
    hari = [add_days(start, i) for i in range(date_diff(end, start) + 1)]

    hris = frappe.get_all(
        "HRIS Employee",
        filters={"status": "Aktif", "attendance_device_id": ["is", "set"]},
        fields=["name", "attendance_device_id", "employee_group", "erpnext_employee"],
        order_by="name asc",
    )
    per_id = {}
    for r in hris:
        kode = (r.attendance_device_id or "").strip()
        if kode:
            per_id.setdefault(kode, []).append(r)
    ganda = sorted(k for k, v in per_id.items() if len(v) > 1)
    terpakai = [(k, v[0]) for k, v in per_id.items() if len(v) == 1]

    group_field = ss._group_fieldname()
    nama_erp = [r.erpnext_employee for _k, r in terpakai if r.erpnext_employee]
    emp_rows = {}
    for i in range(0, len(nama_erp), 500):
        for e in frappe.get_all(
            "Employee",
            filters={"name": ["in", nama_erp[i:i + 500]]},
            fields=["name", "company", group_field],
        ):
            emp_rows[e.name] = e

    asg_by_emp = {}
    for a in frappe.get_all(
        "HRIS Shift Assignment",
        filters={"is_active": 1, "from_date": ["<=", end], "to_date": [">=", start]},
        fields=["employee", "shift", "from_date", "to_date"],
    ):
        asg_by_emp.setdefault(a.employee, []).append(a)

    libur_by_hari = {}
    for h in frappe.get_all(
        "HRIS Holiday",
        filters={"holiday_date": ["between", [start, end]]},
        fields=["holiday_date", "holiday_name", "applies_to_all_companies", "company"],
    ):
        libur_by_hari.setdefault(getdate(h.holiday_date), []).append(h)

    cache_grup = {}
    cache_rotasi = {}

    def ambil_grup(nama):
        if nama not in cache_grup:
            cache_grup[nama] = frappe.get_doc("HRIS Employee Group", nama) if frappe.db.exists("HRIS Employee Group", nama) else None
        return cache_grup[nama]

    def ambil_rotasi(nama):
        if nama not in cache_rotasi:
            cache_rotasi[nama] = frappe.get_doc("HRIS Shift Rotation", nama) if frappe.db.exists("HRIS Shift Rotation", nama) else None
        return cache_rotasi[nama]

    def libur(day, company):
        for h in libur_by_hari.get(day, []):
            if h.applies_to_all_companies or h.company == company:
                return 1
        return 0

    def resolusi(emp, day):
        # Kembali: (shift, wajib, off, sumber). Urutan prioritas sama dengan get_schedule_for_date.
        for a in asg_by_emp.get(emp.name, []):
            if a.from_date <= day <= a.to_date:
                return a.shift, 1, 0, "Shift Assignment"
        nama_grup = emp.get(group_field)
        if not nama_grup:
            return None, 0, 0, "Tidak ada"
        g = ambil_grup(nama_grup)
        if not g or not g.is_active:
            return None, 0, 0, "Tidak ada"
        if g.schedule_type == "Rotasi":
            if g.rotation and g.rotation_start_date:
                delta = date_diff(day, g.rotation_start_date)
                if delta >= 0:
                    rot = ambil_rotasi(g.rotation)
                    if rot and rot.is_active and rot.pattern:
                        row = rot.pattern[delta % len(rot.pattern)]
                        if row.is_off:
                            return None, 0, 1, "Rotasi"
                        return row.shift, 1, 0, "Rotasi"
            return None, 0, 0, "Tidak ada"
        row = ss._weekly_row(g, day)
        if row:
            return row.shift, 1 if row.is_required else 0, 0, "Jadwal Mingguan"
        return None, 0, 0, "Tidak ada"

    baris = []
    tanpa_tautan = 0
    beda_grup = 0
    diproses = 0
    for kode, r in terpakai:
        emp = emp_rows.get(r.erpnext_employee) if r.erpnext_employee else None
        if not emp:
            tanpa_tautan += 1
            continue
        diproses += 1
        if (r.employee_group or None) != (emp.get(group_field) or None):
            beda_grup += 1
        for day in hari:
            shift, wajib, off, sumber = resolusi(emp, day)
            ada_libur = libur(day, emp.company)
            if not shift and not off and not ada_libur:
                continue
            works = 1 if (shift and (sumber == "Shift Assignment" or not ada_libur)) else 0
            baris.append([kode, str(day), shift or "", wajib, works, ada_libur, off, sumber])

    peringatan = []
    if ganda:
        peringatan.append("ID Finger ganda di karyawan Aktif (dilewati): " + ", ".join(ganda[:20]))
    if tanpa_tautan:
        peringatan.append("%d karyawan Aktif tanpa tautan Employee ERPNext (dilewati)" % tanpa_tautan)
    if beda_grup:
        peringatan.append("%d karyawan grupnya berbeda antara HRIS Employee dan Employee ERPNext (dipakai: Employee ERPNext)" % beda_grup)

    return {
        "dari": str(start),
        "sampai": str(end),
        "kolom": KOLOM,
        "baris": baris,
        "shift": _detail_shift(),
        "diproses": diproses,
        "peringatan": peringatan,
    }


@frappe.whitelist(allow_guest=True, methods=["POST"])
def get_jadwal_shift(dari=None, sampai=None):
    verify_agent_request()
    if not dari or not sampai:
        frappe.throw(_("Parameter dari dan sampai wajib diisi."))
    return bangun_jadwal(dari, sampai)
