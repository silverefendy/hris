"""K-6b tahap 1: Hitung dulu (dry run) untuk hapus HRIS Working Hour per batch.

Berkas ini HANYA MEMBACA. Tidak ada INSERT/UPDATE/DELETE.

Aturan penghalang:
- Blokir  : ada slip Final, atau slip di bawah Payroll Period Final, yang mencakup
            karyawan (erpnext_employee) dan work_date dokumen.
- Peringatan (perlu konfirmasi): slip Draft/Ditinjau; Menunggu/Tidak Lengkap belum
            ditinjau milik karyawan ber-gaji; dokumen berisi input manual HR.
- Info    : Hadir tanpa baris gaji berlaku; Raw Log tidak ikut terhapus.
"""

import frappe
from frappe import _
from frappe.utils import cint, getdate

WH = "HRIS Working Hour"
HAK_HAPUS = {"System Manager", "HRIS Direksi"}
MAKS_DAFTAR = 20

# Ada baris gaji yang berlaku pada work_date (logika sama dengan kesiapan periode).
_ADA_GAJI = """select 1 from `tabHRIS Employee` he
    inner join `tabHRIS Employee Pay` ep on ep.employee = he.name
    where he.erpnext_employee = wh.employee
      and ep.effective_from <= wh.work_date
      and (ep.effective_to is null or ep.effective_to >= wh.work_date)"""

# Dokumen yang memuat pekerjaan manual HR (tidak bisa dihitung ulang dari Raw Log).
_INPUT_MANUAL = """(ifnull(wh.absence_class, '') != '' or ifnull(wh.classified_by, '') != ''
    or ifnull(wh.reviewed_by, '') != '' or ifnull(wh.review_note, '') != ''
    or ifnull(wh.adjustment_hours, 0) != 0 or ifnull(wh.adjustment_reason, '') != '')"""

# Belum ditinjau HRD (sama dengan syarat kesiapan periode).
_MENUNGGU = """((wh.status = 'Tidak Lengkap' and ifnull(wh.review_status, '') != 'Sudah Ditinjau')
    or ifnull(wh.review_status, '') = 'Menunggu')"""

_SLIP_JOIN = """from `tabHRIS Working Hour` wh
    inner join `tabHRIS Payroll Slip` s on s.erpnext_employee = wh.employee
        and wh.work_date between s.period_start and s.period_end
    left join `tabHRIS Payroll Period` pp on pp.name = s.payroll_period"""

_FINAL = "(s.status = 'Final' or ifnull(pp.status, '') = 'Final')"
_BELUM_FINAL = "(s.status in ('Draft', 'Ditinjau') and ifnull(pp.status, '') != 'Final')"

# 6b-1b: dua sumber blokir. (1) slip Final / Period Final di bawah slip; (2) kunci periode
# (karyawan punya baris gaji berlaku dan jadwalnya punya Payroll Period Final), sama dengan period_lock.
_SLIP_FINAL_ADA = """exists (select 1 from `tabHRIS Payroll Slip` s
    left join `tabHRIS Payroll Period` pp on pp.name = s.payroll_period
    where s.erpnext_employee = wh.employee
      and wh.work_date between s.period_start and s.period_end
      and (s.status = 'Final' or ifnull(pp.status, '') = 'Final'))"""

_KUNCI_PERIODE = """exists (select 1 from `tabHRIS Payroll Period` kp
    inner join `tabHRIS Employee Pay` kep on kep.payroll_schedule = kp.payroll_schedule
    inner join `tabHRIS Employee` khe on khe.name = kep.employee
    where kp.status = 'Final'
      and kp.period_start <= wh.work_date and kp.period_end >= wh.work_date
      and kep.effective_from <= wh.work_date
      and (kep.effective_to is null or kep.effective_to >= wh.work_date)
      and khe.erpnext_employee = wh.employee)"""

_TERBLOKIR = "(" + _SLIP_FINAL_ADA + " or " + _KUNCI_PERIODE + ")"


def _check_access():
    if not HAK_HAPUS & set(frappe.get_roles()):
        frappe.throw(_("Anda tidak berhak menghapus Working Hour."), frappe.PermissionError)


def _daftar(nilai):
    """Terima list, JSON string, string tunggal, atau kosong. Kembalikan list str."""
    if not nilai:
        return []
    if isinstance(nilai, str):
        try:
            nilai = frappe.parse_json(nilai)
        except Exception:
            nilai = [nilai]
        if isinstance(nilai, str):
            nilai = [nilai]
    return [str(x).strip() for x in nilai if str(x).strip()]


def _siapkan(date_from, date_to, karyawan=None, status=None, tanpa_gaji=0):
    if not date_from or not date_to:
        frappe.throw(_("Dari Tanggal dan Sampai Tanggal wajib diisi."))
    d1, d2 = getdate(date_from), getdate(date_to)
    if d2 < d1:
        frappe.throw(_("Sampai Tanggal tidak boleh lebih awal dari Dari Tanggal."))

    emp = _daftar(karyawan)
    st = _daftar(status)
    opsi = [o.strip() for o in (frappe.get_meta(WH).get_field("status").options or "").split("\n") if o.strip()]
    salah = [s for s in st if s not in opsi]
    if salah:
        frappe.throw(_("Status tidak dikenal: {0}").format(", ".join(salah)))

    cond = ["wh.work_date between %(d1)s and %(d2)s"]
    p = {"d1": d1, "d2": d2}
    if emp:
        cond.append("wh.employee in %(emp)s")
        p["emp"] = tuple(emp)
    if st:
        cond.append("wh.status in %(st)s")
        p["st"] = tuple(st)
    if cint(tanpa_gaji):
        cond.append("not exists (" + _ADA_GAJI + ")")

    flt = {
        "dari_tanggal": str(d1),
        "sampai_tanggal": str(d2),
        "karyawan": emp,
        "status": st,
        "tanpa_gaji": cint(tanpa_gaji),
    }
    return " and ".join(cond), p, flt


def _angka(sql, p):
    return frappe.db.sql(sql, p)[0][0] or 0


def _hitung(where, p):
    total = _angka("select count(*) from `tabHRIS Working Hour` wh where " + where, p)
    per_status = {
        (r[0] or "(kosong)"): r[1]
        for r in frappe.db.sql(
            "select wh.status, count(*) from `tabHRIS Working Hour` wh where " + where + " group by wh.status",
            p,
        )
    }

    # --- Blokir: slip Final / Period Final ---
    n_blokir = _angka(
        "select count(*) from `tabHRIS Working Hour` wh where " + where + " and " + _TERBLOKIR, p
    )
    slip_blokir = frappe.db.sql(
        "select s.name, s.employee_name, s.status, pp.status as status_periode, "
        "s.period_start, s.period_end, count(distinct wh.name) as jumlah "
        + _SLIP_JOIN + " where " + where + " and " + _FINAL
        + " group by s.name, s.employee_name, s.status, pp.status, s.period_start, s.period_end"
        " order by s.period_start, s.name limit " + str(MAKS_DAFTAR),
        p,
        as_dict=True,
    )

    # --- Peringatan ---
    peringatan = []

    r = frappe.db.sql(
        "select count(distinct wh.name), count(distinct s.name) " + _SLIP_JOIN
        + " where " + where + " and " + _BELUM_FINAL,
        p,
    )[0]
    if r[0]:
        slip_draft = frappe.db.sql(
            "select s.name, s.employee_name, s.status, s.period_start, s.period_end, "
            "count(distinct wh.name) as jumlah " + _SLIP_JOIN
            + " where " + where + " and " + _BELUM_FINAL
            + " group by s.name, s.employee_name, s.status, s.period_start, s.period_end"
            " order by s.period_start, s.name limit " + str(MAKS_DAFTAR),
            p,
            as_dict=True,
        )
        peringatan.append({
            "kode": "slip_belum_final",
            "jumlah": r[0],
            "slip": r[1],
            "pesan": _("{0} Working Hour berada di bawah {1} slip yang belum Final (Draft/Ditinjau). "
                       "Angka slip bergantung pada data ini; hitung ulang slip setelah penghapusan.").format(r[0], r[1]),
            "daftar": slip_draft,
            "butuh_konfirmasi": 1,
        })

    n = _angka(
        "select count(*) from `tabHRIS Working Hour` wh where " + where
        + " and " + _MENUNGGU + " and exists (" + _ADA_GAJI + ")",
        p,
    )
    if n:
        peringatan.append({
            "kode": "belum_ditinjau",
            "jumlah": n,
            "pesan": _("{0} hari milik karyawan ber-gaji masih Menunggu atau Tidak Lengkap belum ditinjau. "
                       "Menghapusnya menghilangkan penghalang kesiapan periode tanpa ditinjau.").format(n),
            "butuh_konfirmasi": 1,
        })

    n = _angka("select count(*) from `tabHRIS Working Hour` wh where " + where + " and " + _INPUT_MANUAL, p)
    if n:
        peringatan.append({
            "kode": "input_manual",
            "jumlah": n,
            "pesan": _("{0} dokumen memuat input manual HR (klasifikasi, peninjauan, atau koreksi jam). "
                       "Data ini TIDAK bisa dihitung ulang dari Raw Log.").format(n),
            "butuh_konfirmasi": 1,
        })

    # --- Info ---
    info = []
    n = _angka(
        "select count(*) from `tabHRIS Working Hour` wh where " + where
        + " and wh.status = 'Hadir' and not exists (" + _ADA_GAJI + ")",
        p,
    )
    if n:
        info.append({
            "kode": "hadir_tanpa_gaji",
            "jumlah": n,
            "pesan": _("{0} hari berstatus Hadir milik karyawan tanpa baris gaji berlaku. "
                       "Kesiapan periode biasanya memperingatkan hal ini; setelah dihapus, sinyalnya hilang.").format(n),
        })
    info.append({
        "kode": "raw_log",
        "pesan": _("Raw Log tidak ikut terhapus. Setelah Working Hour hilang, log dapat dihapus lewat Hapus Raw Log."),
    })

    return {
        "total": total,
        "per_status": per_status,
        "blokir": {"jumlah": n_blokir, "slip": slip_blokir},
        "peringatan": peringatan,
        "info": info,
        "boleh": bool(total) and not n_blokir,
    }


@frappe.whitelist()
def check_delete(date_from, date_to, karyawan=None, status=None, tanpa_gaji=0):
    """Cek Dulu: hitung dokumen yang cocok dan penghalangnya. TIDAK mengubah apa pun."""
    _check_access()
    where, p, flt = _siapkan(date_from, date_to, karyawan, status, tanpa_gaji)
    hasil = _hitung(where, p)
    hasil["filter"] = flt
    return hasil


def dokumen_terblokir(employee, work_date):
    """True bila WH karyawan+tanggal ini terkunci (slip Final / periode Final). Dipakai guard on_trash."""
    if not employee or not work_date:
        return False
    baris = frappe.db.sql(
        "select 1 from (select %(e)s as employee, %(d)s as work_date) wh where " + _TERBLOKIR + " limit 1",
        {"e": employee, "d": getdate(work_date)},
    )
    return bool(baris)
