import frappe
from frappe import _
from frappe.utils import flt

ROLES = {"HRIS Payroll Manager", "HRIS Direksi", "System Manager"}
SLIP = "HRIS Payroll Slip"
WH = "HRIS Working Hour"
PERIOD = "HRIS Payroll Period"
DEPT = "HRIS Department"
HARI_KERJA = ("Hadir", "Tidak Lengkap", "Tidak Hadir")


def execute(filters=None):
    filters = frappe._dict(filters or {})
    _cek(filters)
    data, pesan = hitung(filters)
    return get_columns(filters), data, pesan


def _cek(f):
    if not (ROLES & set(frappe.get_roles())):
        frappe.throw(_("Anda tidak punya izin untuk membuka laporan ini."), frappe.PermissionError)
    if not f.get("payroll_period"):
        frappe.throw(_("Payroll Period wajib diisi."))
    if (f.get("group_by") or "Department") not in ("Department", "Employee Group"):
        frappe.throw(_("Pengelompokan tidak dikenal."))


def get_columns(f):
    judul = _("Employee Group") if f.get("group_by") == "Employee Group" else _("Department")
    return [
        {"fieldname": "kelompok", "label": judul, "fieldtype": "Data", "width": 240},
        {"fieldname": "jumlah_slip", "label": _("Slip (asal)"), "fieldtype": "Int", "width": 90},
        {"fieldname": "bruto_asal", "label": _("Bruto Asal"), "fieldtype": "Currency", "width": 140},
        {"fieldname": "pinjaman_keluar", "label": _("Pinjaman Keluar"), "fieldtype": "Currency", "width": 140},
        {"fieldname": "pinjaman_masuk", "label": _("Pinjaman Masuk"), "fieldtype": "Currency", "width": 140},
        {"fieldname": "total_biaya", "label": _("Total Biaya"), "fieldtype": "Currency", "width": 150},
        {"fieldname": "perkiraan_draft", "label": _("Perkiraan (Draft)"), "fieldtype": "Currency", "width": 150},
    ]


def _rp(n):
    return int(round(flt(n)))


def _tujuan(r, dimensi):
    if dimensi == "Department":
        t, asal = r.get("rule_department"), r.get("department")
    else:
        t, asal = r.get("borrowed_for_group"), r.get("employee_group")
    return t if (t and t != asal) else None


def _nilai_hari(s, r, tarif, pengali):
    """Porsi bruto (Pendapatan) satu hari; rumus sama dengan hitung_komponen di payroll_slip.py."""
    jumlah = 0.0
    lembur_jam = flt(r.get("overtime_minutes")) / 60.0
    if s.pay_type == "Bulanan":
        if r.status in HARI_KERJA and flt(s.working_days) > 0:
            jumlah += flt(s.base_amount) / flt(s.working_days)
        if r.status == "Hadir" and lembur_jam > 0:
            jumlah += lembur_jam * tarif * pengali
    elif s.pay_type == "Harian" and r.status == "Hadir":
        jumlah += flt(s.base_amount)
        if lembur_jam > 0 and flt(r.get("scheduled_hours")) > 0:
            jumlah += lembur_jam * (flt(s.base_amount) / flt(r.scheduled_hours)) * pengali
    return jumlah
# AKHIR_A


def hitung(f):
    dimensi = f.get("group_by") or "Department"
    kosong = "(Tanpa Department)" if dimensi == "Department" else "(Tanpa Grup)"
    per = frappe.db.get_value(PERIOD, f.payroll_period, ["period_start", "period_end"], as_dict=True)
    if not per:
        frappe.throw(_("Payroll Period tidak ditemukan."))
    kond = ["payroll_period = %(p)s"]
    nilai = {"p": f.payroll_period}
    if f.get("status") and f.status != "Semua":
        kond.append("status = %(s)s")
        nilai["s"] = f.status
    slips = frappe.db.sql(
        """
        select name, status, erpnext_employee, department, employee_group, pay_type, base_amount,
               overtime_multiplier, working_days, scheduled_hours_total, total_earning
        from `tabHRIS Payroll Slip`
        where {0}
        """.format(" and ".join(kond)),
        nilai,
        as_dict=True,
    )
    if not slips:
        return [], _("Tidak ada slip pada periode dan status ini.")

    kolom = ["employee", "work_date", "status", "scheduled_hours", "overtime_minutes", "department", "employee_group"]
    for k in ("rule_department", "borrowed_for_group"):
        if frappe.db.has_column(WH, k):
            kolom.append(k)
    emps = list({s.erpnext_employee for s in slips if s.erpnext_employee})
    rows = []
    if emps:
        rows = frappe.get_all(
            WH,
            filters={"employee": ["in", emps], "work_date": ["between", [str(per.period_start), str(per.period_end)]]},
            fields=kolom,
            limit_page_length=0,
        )
    per_emp = {}
    for r in rows:
        per_emp.setdefault(r.employee, []).append(r)

    try:
        from hris.hris_payroll.services.payroll_slip import _pasang_pengali_harian
    except Exception:  # noqa: BLE001
        _pasang_pengali_harian = None

    agg = {}

    def akun(k):
        return agg.setdefault(k, {"jumlah_slip": 0, "bruto_asal": 0, "pinjaman_keluar": 0,
                                  "pinjaman_masuk": 0, "perkiraan_draft": 0})

    peringatan = []
    total_slip = 0
    for s in slips:
        draft = s.status == "Draft"
        bruto = _rp(s.total_earning)
        total_slip += bruto
        asal = (s.department if dimensi == "Department" else s.employee_group) or kosong
        a = akun(asal)
        a["jumlah_slip"] += 1
        a["bruto_asal"] += bruto
        if draft:
            a["perkiraan_draft"] += bruto
        pindah = {}
        for r in per_emp.get(s.erpnext_employee, []):
            t = _tujuan(r, dimensi)
            if t:
                pindah.setdefault(t, []).append(r)
        if not pindah:
            continue
        semua = [r for lst in pindah.values() for r in lst]
        default_kali = flt(s.overtime_multiplier) or 1.0
        if _pasang_pengali_harian:
            try:
                galat = _pasang_pengali_harian(s.department, semua)
            except Exception as e:  # noqa: BLE001
                galat = str(e)
            if galat:
                peringatan.append(_("Slip {0}: pengali per hari gagal ({1}); memakai pengali slip.").format(s.name, galat))
        tarif = flt(s.base_amount) / flt(s.scheduled_hours_total) if flt(s.scheduled_hours_total) > 0 else 0.0
        porsi = {}
        for t, lst in pindah.items():
            jml = sum(_nilai_hari(s, r, tarif, flt(r.get("pengali")) or default_kali) for r in lst)
            if jml > 0:
                porsi[t] = _rp(jml)
        total_porsi = sum(porsi.values())
        if total_porsi > bruto and total_porsi > 0:
            peringatan.append(_("Slip {0}: porsi pinjam {1} melebihi bruto {2}; diskalakan turun.").format(s.name, total_porsi, bruto))
            faktor = bruto / float(total_porsi)
            porsi = {k: _rp(v * faktor) for k, v in porsi.items()}
        for t, v in porsi.items():
            a["pinjaman_keluar"] += v
            akun(t)["pinjaman_masuk"] += v
            if draft:
                a["perkiraan_draft"] -= v
                akun(t)["perkiraan_draft"] += v

    selisih = sum(v["pinjaman_masuk"] for v in agg.values()) - sum(v["pinjaman_keluar"] for v in agg.values())
    total_lap = sum(v["bruto_asal"] + v["pinjaman_masuk"] - v["pinjaman_keluar"] for v in agg.values())
    pesan = [_("Rekonsiliasi: total laporan {0} vs total_earning slip {1}; selisih masuk-keluar {2}.").format(total_lap, total_slip, selisih)]
    if abs(total_lap - total_slip) > 1 or abs(selisih) > 1:
        pesan.insert(0, _("PERINGATAN: total laporan tidak sama dengan total slip."))
    pesan.extend(peringatan[:10])
    pesan.append(_("Bruto = Pendapatan slip (tanpa potongan dan tanpa BPJS). Draft adalah perkiraan."))

    if dimensi == "Department" and f.get("parent_department"):
        lr = frappe.db.get_value(DEPT, f.parent_department, ["lft", "rgt"], as_dict=True)
        if not lr:
            frappe.throw(_("Department induk tidak ditemukan."))
        boleh = set(frappe.get_all(DEPT, filters={"lft": [">=", lr.lft], "rgt": ["<=", lr.rgt]}, pluck="name"))
        agg = {k: v for k, v in agg.items() if k in boleh}

    data = []
    for k in sorted(agg):
        v = agg[k]
        data.append({
            "kelompok": k,
            "jumlah_slip": v["jumlah_slip"],
            "bruto_asal": v["bruto_asal"],
            "pinjaman_keluar": v["pinjaman_keluar"],
            "pinjaman_masuk": v["pinjaman_masuk"],
            "total_biaya": v["bruto_asal"] + v["pinjaman_masuk"] - v["pinjaman_keluar"],
            "perkiraan_draft": v["perkiraan_draft"],
        })
    return data, "<br>".join(pesan)


def periksa(periode):
    """Uji cepat: bench --site hris-uji.local execute <path>.periksa --kwargs '{"periode": "..."}'"""
    total_slip = frappe.db.sql("select sum(total_earning) from `tabHRIS Payroll Slip` where payroll_period=%s", periode)[0][0]
    print("sum total_earning slip:", total_slip)
    for dim in ("Department", "Employee Group"):
        _k, data, pesan = execute({"payroll_period": periode, "group_by": dim})
        print(dim, "| baris:", len(data), "| total biaya:", sum(d["total_biaya"] for d in data),
              "| keluar:", sum(d["pinjaman_keluar"] for d in data), "| masuk:", sum(d["pinjaman_masuk"] for d in data))
        print(pesan.replace("<br>", "\n"))
# AKHIR
