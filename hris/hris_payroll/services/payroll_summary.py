"""Payroll Summary fase 1 (hanya membaca): data tabel per tanggal atau per periode.

Pembacaan massal (karyawan, gaji, pengecualian HEC, Working Hour), lalu hitung_tunjangan() per sel.
Hak akses disaring di sini (server): akses penuh, atau Payroll Admin hanya Harian.
"""
import frappe
from frappe import _
from frappe.utils import cint, flt, getdate

from hris.hris_payroll.doctype.hris_employee_pay.hris_employee_pay import PERAN_ADMIN, _akses_penuh, _peran
from hris.hris_payroll.services.department_komponen import resolve_komponen_karyawan
from hris.hris_payroll.services.komponen_slip import hitung_tunjangan

EMP = "HRIS Employee"
PERIODE = "HRIS Payroll Period"
WH = "HRIS Working Hour"
HEC = "HRIS Employee Component"
KATALOG = "HRIS Pay Component"
HARI_KERJA = ("Hadir", "Tidak Lengkap", "Tidak Hadir")

KOLOM_EMP = [
    "name", "employee_name", "company", "department", "employee_group", "rule_follow", "erpnext_employee",
    "pph21_enrolled",
    "bpjs_kes_enrolled", "bpjs_kes_amount", "bpjs_tk_enrolled", "bpjs_tk_amount",
    "bpjs_jht_enrolled", "bpjs_jht_amount", "bpjs_jp_enrolled", "bpjs_jp_amount",
    "bpjs_jkk_enrolled", "bpjs_jkk_amount", "bpjs_jkm_enrolled", "bpjs_jkm_amount",
]


def _rupiah(x):
    return int(round(flt(x)))


def _jenis_diizinkan():
    """None = semua jenis; 'Harian' = hanya Harian (Payroll Admin); selain itu ditolak."""
    user = frappe.session.user
    if _akses_penuh(user):
        return None
    if PERAN_ADMIN in _peran(user):
        return "Harian"
    frappe.throw(_("Anda tidak berhak melihat data gaji."), frappe.PermissionError)


def _komponen(tampilkan_nonaktif):
    filters = {} if tampilkan_nonaktif else {"is_active": 1}
    return frappe.get_all(
        KATALOG, filters=filters,
        fields=["name", "component_name", "component_type", "payment_basis", "is_active"],
        order_by="name asc",
    )


def _karyawan(company, department, grup, employee, resign):
    f = {}
    for k, v in (("company", company), ("department", department), ("employee_group", grup), ("name", employee)):
        if v:
            f[k] = v
    if not resign:
        f["status"] = "Aktif"
    return frappe.get_all(EMP, filters=f, fields=KOLOM_EMP, order_by="employee_name asc")


def _baris_gaji(emps, awal, akhir, jadwal):
    sql = (
        "select employee, pay_type, amount, payroll_schedule, effective_from from `tabHRIS Employee Pay` "
        "where employee in %(e)s and effective_from <= %(akhir)s "
        "and (effective_to is null or effective_to >= %(awal)s)"
    )
    p = {"e": tuple(emps), "awal": awal, "akhir": akhir}
    if jadwal:
        sql += " and payroll_schedule = %(j)s"
        p["j"] = jadwal
    sql += " order by effective_from desc"
    hasil = {}
    for r in frappe.db.sql(sql, p, as_dict=True):
        hasil.setdefault(r.employee, []).append(r)
    return hasil


def _iuran_bpjs(he):
    total = 0.0
    if he.get("bpjs_kes_enrolled"):
        total += flt(he.get("bpjs_kes_amount"))
    if he.get("bpjs_tk_enrolled"):
        total += flt(he.get("bpjs_tk_amount"))
    else:
        for p in ("jht", "jp", "jkk", "jkm"):
            if he.get("bpjs_%s_enrolled" % p):
                total += flt(he.get("bpjs_%s_amount" % p))
    return _rupiah(total)


def _sumber(dasar, daftar_hec):
    if daftar_hec:
        return "Pengecualian " + ", ".join(str(h["name"]) for h in daftar_hec)
    if dasar.get("berlaku"):
        teks = dasar.get("sumber") or ""
        if dasar.get("aturan"):
            teks += " ({0})".format(dasar["aturan"])
        return teks
    return "Tidak ada nilai"


def _satu_baris(he, rows, whr, komponen, hec, dasar_fn, per_periode, awal, akhir):
    masalah, peringatan = [], []
    pay = rows[0] if rows else None
    pay_type = pay.pay_type if pay else ""
    if not pay:
        masalah.append(_("Belum ada baris gaji"))
    elif len(rows) > 1:
        peringatan.append(
            _("Ada {0} baris gaji pada {1} ini; memakai yang terbaru ({2}).").format(
                len(rows), _("periode") if per_periode else _("tanggal"), pay.payroll_schedule)
        )

    tgl_hadir = [getdate(r.work_date) for r in whr if r.status == "Hadir"]
    n_tl = sum(1 for r in whr if r.status == "Tidak Lengkap")
    hari_kerja = [r for r in whr if r.status in HARI_KERJA]
    if per_periode and not whr:
        masalah.append(_("Working Hour belum ada pada periode ini"))
    if n_tl:
        peringatan.append(_("{0} hari Tidak Lengkap").format(n_tl))

    gaji_pokok = per_hari = per_jam = None
    kehadiran = None
    hari_hadir = len(tgl_hadir) if per_periode else None
    if not per_periode:
        kehadiran = whr[0].status if whr else "-"
    if pay:
        gaji_pokok = _rupiah(pay.amount)
        if pay_type == "Harian":
            per_hari = gaji_pokok
            if not per_periode and whr and flt(whr[0].scheduled_hours) > 0:
                per_jam = _rupiah(flt(pay.amount) / flt(whr[0].scheduled_hours))
        elif pay_type == "Bulanan" and per_periode and hari_kerja:
            per_hari = _rupiah(flt(pay.amount) / len(hari_kerja))
            jam_total = sum(flt(r.scheduled_hours) for r in hari_kerja)
            if jam_total > 0:
                per_jam = _rupiah(flt(pay.amount) / jam_total)

    sel = {}
    tot_p = tot_k = 0
    for k in komponen:
        kode = k.name
        if not pay:
            sel[kode] = {"jumlah": None, "sumber": "", "dasar": "", "janggal": [], "peringatan": []}
            continue
        dasar = dasar_fn(he, kode)
        daftar = hec.get((he.name, kode), [])
        hasil = hitung_tunjangan(
            pay_type, k.payment_basis, dasar, daftar, awal, akhir,
            tgl_hadir if per_periode else [akhir],
        )
        if hasil.get("error"):
            sel[kode] = {"error": hasil["error"]}
            masalah.append("{0}: {1}".format(k.component_name or kode, hasil["error"]))
            continue
        sel[kode] = {
            "jumlah": hasil["jumlah"], "sumber": _sumber(dasar, daftar), "dasar": hasil["dasar"],
            "janggal": hasil["janggal"], "peringatan": hasil["peringatan"],
        }
        masalah.extend("{0}: {1}".format(k.component_name or kode, t) for t in hasil["janggal"])
        peringatan.extend("{0}: {1}".format(k.component_name or kode, t) for t in hasil["peringatan"])
        if k.component_type == "Potongan":
            tot_k += hasil["jumlah"]
        else:
            tot_p += hasil["jumlah"]

    return {
        "employee": he.name, "nama": he.employee_name, "department": he.department,
        "grup": he.employee_group, "pay_type": pay_type,
        "gaji_pokok": gaji_pokok, "per_hari": per_hari, "per_jam": per_jam,
        "kehadiran": kehadiran, "hari_hadir": hari_hadir,
        "sel": sel, "total_pendapatan": tot_p, "total_potongan": tot_k,
        "pajak": _("Ada") if he.get("pph21_enrolled") else _("Tidak"),
        "bpjs": _iuran_bpjs(he),
        "janggal": bool(masalah), "catatan": masalah + peringatan,
    }


@frappe.whitelist()
def ambil_data(mode="Per Tanggal", tanggal=None, periode=None, company=None, department=None,
               employee_group=None, employee=None, pay_type=None, tampilkan_nonaktif=0,
               termasuk_resign=0, halaman=1, ukuran=50, semua=0, tampilkan_tanpa_gaji=0):
    jenis_izin = _jenis_diizinkan()
    per_periode = mode == "Per Periode"
    info = []
    jadwal = None

    if per_periode:
        if not periode:
            frappe.throw(_("Pilih Periode Gaji."))
        p = frappe.db.get_value(
            PERIODE, periode, ["company", "payroll_schedule", "period_start", "period_end", "status"], as_dict=True)
        if not p:
            frappe.throw(_("Periode Gaji tidak ditemukan."))
        awal, akhir = getdate(p.period_start), getdate(p.period_end)
        jadwal = p.payroll_schedule
        company = company or p.company
        info.append(_("Periode {0}: {1} sampai {2}, status {3}.").format(periode, awal, akhir, p.status))
    else:
        if not tanggal:
            frappe.throw(_("Pilih Tanggal."))
        awal = akhir = getdate(tanggal)
        info.append(_("Tanggal {0}. Komponen Per Hari Hadir dihitung seolah karyawan hadir; "
                      "gaji per hari dan per jam karyawan Bulanan hanya tampil di tampilan Per Periode.").format(awal))
    if jenis_izin:
        info.append(_("Anda hanya melihat karyawan berjenis gaji {0}.").format(jenis_izin))

    komponen = _komponen(cint(tampilkan_nonaktif))
    karyawan = _karyawan(company, department, employee_group, employee, cint(termasuk_resign))
    kosong = {
        "mode": "Per Periode" if per_periode else "Per Tanggal", "awal": str(awal), "akhir": str(akhir),
        "komponen": [], "baris": [], "jumlah_baris": 0, "halaman": 1, "ukuran": cint(ukuran) or 50,
        "total": {"per_komponen": {}, "pendapatan": 0, "potongan": 0}, "jumlah_janggal": 0, "info": info,
    }
    kosong["komponen"] = [
        {"kode": k.name, "nama": k.component_name or k.name, "tipe": k.component_type,
         "basis": k.payment_basis, "aktif": bool(k.is_active)} for k in komponen
    ]
    if not karyawan:
        return kosong

    emps = [k.name for k in karyawan]
    gaji = _baris_gaji(emps, awal, akhir, jadwal)

    hec = {}
    kode_list = [k.name for k in komponen]
    if kode_list:
        for h in frappe.get_all(
            HEC,
            filters={"is_active": 1, "employee": ["in", emps], "component": ["in", kode_list],
                     "date_from": ["<=", akhir], "date_to": [">=", awal]},
            fields=["name", "employee", "component", "status", "amount", "date_from", "date_to"],
            order_by="date_from asc",
        ):
            hec.setdefault((h.employee, h.component), []).append(h)

    erp = [k.erpnext_employee for k in karyawan if k.erpnext_employee]
    wh = {}
    if erp:
        for r in frappe.get_all(
            WH,
            filters={"employee": ["in", erp], "work_date": ["between", [str(awal), str(akhir)]]},
            fields=["employee", "status", "scheduled_hours", "work_date"],
        ):
            wh.setdefault(r.employee, []).append(r)

    memo = {}

    def dasar_fn(he, kode):
        kunci = (he.department, he.employee_group, he.rule_follow, kode)
        if kunci not in memo:
            memo[kunci] = resolve_komponen_karyawan(he.department, he.employee_group, he.rule_follow, akhir, kode)
        return memo[kunci]

    semua_baris = []
    disembunyi = 0
    for he in karyawan:
        rows = gaji.get(he.name, [])
        jenis = rows[0].pay_type if rows else ""
        if jenis_izin and jenis != jenis_izin:
            continue
        if pay_type and jenis != pay_type:
            continue
        if per_periode and not jenis and not cint(tampilkan_tanpa_gaji):
            disembunyi += 1
            continue
        whr = wh.get(he.erpnext_employee, []) if he.erpnext_employee else []
        semua_baris.append(_satu_baris(he, rows, whr, komponen, hec, dasar_fn, per_periode, awal, akhir))

    if disembunyi:
        info.append(_("{0} karyawan tanpa baris gaji pada jadwal periode ini disembunyikan. Centang 'Tampilkan yang belum punya gaji' untuk melihatnya.").format(disembunyi))
    total = {"per_komponen": {k.name: 0 for k in komponen}, "pendapatan": 0, "potongan": 0}
    jumlah_janggal = 0
    for b in semua_baris:
        total["pendapatan"] += b["total_pendapatan"]
        total["potongan"] += b["total_potongan"]
        jumlah_janggal += 1 if b["janggal"] else 0
        for kode, c in b["sel"].items():
            if c.get("jumlah") is not None:
                total["per_komponen"][kode] += c["jumlah"]

    ukuran = max(cint(ukuran) or 50, 1)
    halaman = max(cint(halaman) or 1, 1)
    potong = semua_baris if cint(semua) else semua_baris[(halaman - 1) * ukuran: halaman * ukuran]
    if not komponen:
        info.append(_("Belum ada komponen aktif di katalog."))
    kosong.update({
        "baris": potong, "jumlah_baris": len(semua_baris), "halaman": halaman, "ukuran": ukuran,
        "total": total, "jumlah_janggal": jumlah_janggal,
    })
    return kosong
