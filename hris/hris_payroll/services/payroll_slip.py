"""Pembuatan dan perhitungan HRIS Payroll Slip (K-130); BPJS pada slip (K-133); PPh 21 TER (K-134)."""

import time
import uuid
from decimal import ROUND_HALF_UP, Decimal

import frappe
from frappe import _
from frappe.utils import cstr, flt, getdate, now_datetime

from hris.hris_payroll.doctype.hris_employee_pay.hris_employee_pay import boleh_baris
from hris.hris_payroll.services.payroll_bpjs import hitung_bpjs_slip
from hris.hris_payroll.services.payroll_pph21 import hitung_pph21_slip

SLIP = "HRIS Payroll Slip"
PERIOD = "HRIS Payroll Period"
WH = "HRIS Working Hour"
PERAN_PROSES = {"HRIS Payroll Manager", "HRIS Payroll Admin"}
CAKUPAN = ("Semua", "Karyawan", "Department", "Grup")
PENGALI_LEMBUR = 1.0  # K-98; DocType pengaturan menyusul
SYNC_LIMIT = 150
STATUS_TTL = 3600
QUEUE_STALE_AFTER = 60
RUN_STALE_AFTER = 120
ACTIVE_KEY = "hris_slip_run_active"
SAVEPOINT = "hris_slip_item"
CONTOH_MAKS = 5
ERROR_MAKS = 20


# ---------- angka ----------
def _d(nilai):
    return Decimal(str(flt(nilai)))


def _rupiah(nilai):
    return int(Decimal(nilai).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _rp(n):
    return "{0:,}".format(int(n)).replace(",", ".")


def _jam(x):
    return "{0:.2f}".format(float(x))


def hitung_komponen(pay_type, amount, baris, pengali=PENGALI_LEMBUR):
    """Fungsi murni. baris = daftar dict hari kerja (status, scheduled_hours, late_deduction_hours,
    early_leave_deduction_hours, overtime_minutes, absence_deducted, absence_class).

    Mengembalikan {"error": teks} atau {"komponen", "ringkasan", "catatan", "tarif_jam"}.
    """
    gaji = _d(amount)
    kali = _d(pengali)
    hadir = [b for b in baris if b.get("status") == "Hadir"]
    tidak_lengkap = [b for b in baris if b.get("status") == "Tidak Lengkap"]
    absen = [b for b in baris if b.get("status") == "Tidak Hadir"]
    hari_kerja = hadir + tidak_lengkap + absen
    if not hari_kerja:
        return {"error": _("Tidak ada hari kerja terjadwal (Hadir, Tidak Lengkap, atau Tidak Hadir) pada periode ini. Working Hour mungkin belum dihitung.")}

    jam_total = sum((_d(b.get("scheduled_hours")) for b in hari_kerja), Decimal(0))
    jam_telat = sum((_d(b.get("late_deduction_hours")) for b in hadir), Decimal(0))
    jam_cepat = sum((_d(b.get("early_leave_deduction_hours")) for b in hadir), Decimal(0))
    menit_lembur = sum(int(b.get("overtime_minutes") or 0) for b in hadir)
    menit_lain = sum(int(b.get("overtime_minutes") or 0) for b in baris if b.get("status") != "Hadir")
    dipotong = [b for b in absen if b.get("absence_deducted")]
    belum_klas = [b for b in absen if not cstr(b.get("absence_class"))]

    komponen = []
    catatan = []

    def tambah(nama, tipe, jumlah, dasar):
        komponen.append({"nama": nama, "tipe": tipe, "jumlah": _rupiah(jumlah), "dasar": dasar})

    tarif = Decimal(0)
    if pay_type == "Bulanan":
        if jam_total <= 0:
            return {"error": _("Jam terjadwal periode ini nol; tarif per jam tidak dapat dihitung.")}
        tarif = gaji / jam_total
        tarif_teks = _rp(_rupiah(tarif))
        tambah("Gaji Pokok", "Pendapatan", gaji, _("Gaji bulanan penuh"))
        if jam_telat > 0:
            tambah("Potongan Telat", "Potongan", jam_telat * tarif, "{0} jam x tarif {1}/jam".format(_jam(jam_telat), tarif_teks))
        if jam_cepat > 0:
            tambah("Potongan Pulang Cepat", "Potongan", jam_cepat * tarif, "{0} jam x tarif {1}/jam".format(_jam(jam_cepat), tarif_teks))
        if dipotong:
            tambah(
                "Potongan Absen", "Potongan",
                gaji / Decimal(len(hari_kerja)) * len(dipotong),
                "{0} hari x gaji / {1} hari kerja".format(len(dipotong), len(hari_kerja)),
            )
        if menit_lembur > 0:
            jam_lembur = Decimal(menit_lembur) / Decimal(60)
            tambah("Lembur", "Pendapatan", jam_lembur * tarif * kali, "{0} jam x tarif {1}/jam x {2}".format(_jam(jam_lembur), tarif_teks, kali))
        if tidak_lengkap:
            catatan.append(_("{0} hari Tidak Lengkap tidak dipotong (aturan gaji Bulanan untuk hari ini belum diputuskan).").format(len(tidak_lengkap)))
        if belum_klas:
            catatan.append(_("{0} hari Tidak Hadir belum diklasifikasi: tidak dipotong sampai HRD mengklasifikasi.").format(len(belum_klas)))
    elif pay_type == "Harian":
        tambah("Upah Harian", "Pendapatan", gaji * len(hadir), "{0} hari Hadir x {1}".format(len(hadir), _rp(_rupiah(gaji))))
        telat = cepat = lembur = Decimal(0)
        tanpa_jam = 0
        for b in hadir:
            jam = _d(b.get("scheduled_hours"))
            tl = _d(b.get("late_deduction_hours"))
            ce = _d(b.get("early_leave_deduction_hours"))
            lm = Decimal(int(b.get("overtime_minutes") or 0)) / Decimal(60)
            if jam <= 0:
                if tl > 0 or ce > 0 or lm > 0:
                    tanpa_jam += 1
                continue
            per_jam = gaji / jam
            telat += tl * per_jam
            cepat += ce * per_jam
            lembur += lm * per_jam * kali
        if jam_telat > 0 and telat > 0:
            tambah("Potongan Telat", "Potongan", telat, "{0} jam x upah / jam terjadwal hari itu".format(_jam(jam_telat)))
        if jam_cepat > 0 and cepat > 0:
            tambah("Potongan Pulang Cepat", "Potongan", cepat, "{0} jam x upah / jam terjadwal hari itu".format(_jam(jam_cepat)))
        if menit_lembur > 0 and lembur > 0:
            tambah("Lembur", "Pendapatan", lembur, "{0} jam x upah / jam terjadwal x {1}".format(_jam(Decimal(menit_lembur) / Decimal(60)), kali))
        if tidak_lengkap:
            catatan.append(_("{0} hari Tidak Lengkap tidak dibayar (aturan belum diputuskan).").format(len(tidak_lengkap)))
        if tanpa_jam:
            catatan.append(_("{0} hari Hadir tanpa jam terjadwal: potongan atau lembur hari itu tidak dihitung.").format(tanpa_jam))
    else:
        return {"error": _("Jenis gaji tidak dikenal: {0}.").format(pay_type)}

    if menit_lain > 0:
        catatan.append(_("{0} menit lembur pada hari bukan Hadir tidak dihitung (aturan belum diputuskan).").format(menit_lain))

    ringkasan = {
        "working_days": len(hari_kerja),
        "present_days": len(hadir),
        "absent_days": len(absen),
        "absent_deducted_days": len(dipotong) if pay_type == "Bulanan" else 0,
        "incomplete_days": len(tidak_lengkap),
        "unclassified_absent_days": len(belum_klas) if pay_type == "Bulanan" else 0,
        "scheduled_hours_total": float(jam_total),
        "late_deduction_hours": float(jam_telat),
        "early_deduction_hours": float(jam_cepat),
        "overtime_hours": float(Decimal(menit_lembur) / Decimal(60)),
    }
    return {
        "komponen": komponen,
        "ringkasan": ringkasan,
        "catatan": catatan,
        "tarif_jam": float(tarif.quantize(Decimal("0.01"))) if tarif else 0.0,
    }


# ---------- hak ----------
def _wajib_peran():
    user = frappe.session.user
    if user == "Administrator" or set(frappe.get_roles(user)) & PERAN_PROSES:
        return
    frappe.throw(_("Hanya HRIS Payroll Manager atau HRIS Payroll Admin yang boleh memproses slip gaji."), frappe.PermissionError)


# ---------- satu karyawan ----------
def proses_karyawan(period, he_name):
    """Membuat atau menghitung ulang satu slip. Mengembalikan ("dibuat"|"diperbarui", nama slip)
    atau ("dilewati", alasan)."""
    he = frappe.db.get_value(
        "HRIS Employee", he_name,
        ["name", "employee_name", "company", "department", "employee_group", "erpnext_employee",
         "date_of_joining", "resign_date", "status"],
        as_dict=True,
    )
    if not he:
        return "dilewati", _("Karyawan tidak ditemukan.")
    if not he.erpnext_employee:
        return "dilewati", _("Belum tersambung ke Employee ERPNext (sinkron belum berhasil).")
    if he.company != period.company:
        return "dilewati", _("Company karyawan berbeda dengan Company periode.")

    awal, akhir = getdate(period.period_start), getdate(period.period_end)
    baris_gaji = frappe.db.sql(
        """
        select name, pay_type, amount, effective_from, effective_to
        from `tabHRIS Employee Pay`
        where employee = %(e)s and payroll_schedule = %(j)s
          and effective_from <= %(akhir)s
          and (effective_to is null or effective_to >= %(awal)s)
        order by effective_from
        """,
        {"e": he.name, "j": period.payroll_schedule, "awal": awal, "akhir": akhir},
        as_dict=True,
    )
    if not baris_gaji:
        return "dilewati", _("Tidak punya baris gaji pada jadwal ini untuk periode ini.")
    if len(baris_gaji) > 1:
        return "dilewati", _("Baris gaji berubah di tengah periode ({0} baris); belum didukung, tangani manual.").format(len(baris_gaji))
    gaji = baris_gaji[0]
    if not boleh_baris(gaji.pay_type):
        return "dilewati", _("Tidak berhak memproses jenis gaji {0}.").format(gaji.pay_type)

    if gaji.pay_type == "Bulanan":
        masuk = getdate(he.date_of_joining) if he.date_of_joining else None
        keluar = getdate(he.resign_date) if (he.resign_date and he.status == "Resign") else None
        if (
            getdate(gaji.effective_from) > awal
            or (gaji.effective_to and getdate(gaji.effective_to) < akhir)
            or (masuk and masuk > awal)
            or (keluar and keluar < akhir)
        ):
            return "dilewati", _("Karyawan Bulanan masuk, keluar, atau berganti gaji di tengah periode; pro-rata belum dibuat, tangani manual.")

    rows = frappe.get_all(
        WH,
        filters={"employee": he.erpnext_employee, "work_date": ["between", [str(awal), str(akhir)]]},
        fields=["status", "scheduled_hours", "late_deduction_hours", "early_leave_deduction_hours",
                "overtime_minutes", "absence_deducted", "absence_class"],
    )
    if not rows:
        return "dilewati", _("Tidak ada data Working Hour pada periode ini (belum dihitung).")

    hasil = hitung_komponen(gaji.pay_type, gaji.amount, [dict(r) for r in rows])
    if hasil.get("error"):
        return "dilewati", hasil["error"]

    bpjs = hitung_bpjs_slip(he, period, gaji, hasil)
    if bpjs.get("dilewati"):
        return "dilewati", bpjs["dilewati"]
    hasil["komponen"].extend(bpjs["komponen"])
    hasil["catatan"].extend(bpjs["catatan"])
    pph21 = hitung_pph21_slip(he, period, gaji, hasil)
    if pph21.get("dilewati"):
        return "dilewati", pph21["dilewati"]
    hasil["komponen"].extend(pph21["komponen"])
    hasil["catatan"].extend(pph21["catatan"])

    kunci = "{0}|{1}".format(period.name, he.name)
    ada = frappe.db.get_value(SLIP, {"unique_key": kunci}, ["name", "status"], as_dict=True)
    if ada:
        if ada.status != "Draft":
            return "dilewati", _("Slip {0} berstatus {1} (terkunci).").format(ada.name, ada.status)
        doc = frappe.get_doc(SLIP, ada.name)
        doc.set("components", [r for r in doc.components if r.source == "Manual"])
        jenis = "diperbarui"
    else:
        doc = frappe.new_doc(SLIP)
        jenis = "dibuat"

    doc.payroll_period = period.name
    doc.employee = he.name
    doc.employee_name = he.employee_name
    doc.erpnext_employee = he.erpnext_employee
    doc.company = he.company
    doc.payroll_schedule = period.payroll_schedule
    doc.period_start = period.period_start
    doc.period_end = period.period_end
    doc.pay_date = period.pay_date
    doc.status = "Draft"
    doc.unique_key = kunci
    doc.pay_type = gaji.pay_type
    doc.base_amount = gaji.amount
    doc.hourly_rate = hasil["tarif_jam"]
    doc.overtime_multiplier = PENGALI_LEMBUR
    doc.employee_pay = gaji.name
    doc.employee_group = he.employee_group
    doc.department = he.department
    for fieldname, nilai in hasil["ringkasan"].items():
        doc.set(fieldname, nilai)
    doc.calc_notes = "\n".join(hasil["catatan"])
    doc.calculated_on = now_datetime()
    doc.calculated_by = frappe.session.user
    doc.set("bpjs_items", [])
    for baris_bpjs in bpjs["rincian"]:
        doc.append("bpjs_items", baris_bpjs)
    for k in hasil["komponen"]:
        doc.append("components", {
            "component": k["nama"], "component_type": k["tipe"], "amount": k["jumlah"],
            "basis": k["dasar"], "source": "Otomatis", "reason": "",
        })
    baris_urut = sorted(doc.components, key=lambda r: 0 if r.source == "Otomatis" else 1)
    for nomor, r in enumerate(baris_urut, 1):
        r.idx = nomor
    doc.components = baris_urut
    doc.flags.dari_layanan = True
    if jenis == "dibuat":
        doc.insert(ignore_permissions=True)
    else:
        doc.save(ignore_permissions=True)
    return jenis, doc.name


@frappe.whitelist()
def hitung_ulang_slip(name):
    _wajib_peran()
    slip = frappe.get_doc(SLIP, name)
    period = frappe.get_doc(PERIOD, slip.payroll_period)
    if period.status != "Draft" or slip.status != "Draft":
        frappe.throw(_("Slip hanya dihitung ulang saat Periode Gaji dan slip berstatus Draft."))
    if not boleh_baris(slip.pay_type):
        frappe.throw(_("Anda tidak berhak memproses jenis gaji {0}.").format(slip.pay_type), frappe.PermissionError)
    jenis, info = proses_karyawan(period, slip.employee)
    if jenis == "dilewati":
        frappe.throw(info)
    return info


# ---------- massal ----------
def _kandidat(period, cakupan, employee, department, employee_group):
    if cakupan not in CAKUPAN:
        frappe.throw(_("Cakupan tidak dikenal: {0}.").format(cakupan))
    butuh = {"Karyawan": employee, "Department": department, "Grup": employee_group}
    if cakupan in butuh and not butuh[cakupan]:
        frappe.throw(_("Pilih {0} untuk cakupan {0}.").format(cakupan))
    nama = frappe.db.sql_list(
        """
        select distinct ep.employee from `tabHRIS Employee Pay` ep
        where ep.payroll_schedule = %(j)s and ep.effective_from <= %(akhir)s
          and (ep.effective_to is null or ep.effective_to >= %(awal)s)
        """,
        {"j": period.payroll_schedule, "awal": period.period_start, "akhir": period.period_end},
    )
    if cakupan == "Karyawan":
        nama = [n for n in nama if n == employee]
        if not nama:
            frappe.throw(_("Karyawan ini tidak punya baris gaji pada jadwal dan periode ini."))
    elif cakupan in ("Department", "Grup") and nama:
        kolom = "department" if cakupan == "Department" else "employee_group"
        nilai = department if cakupan == "Department" else employee_group
        nama = frappe.get_all("HRIS Employee", filters={"name": ["in", nama], kolom: nilai}, pluck="name")
    return sorted(nama)


def _cache():
    c = frappe.cache
    if hasattr(c, "set_value"):
        return c
    return c()


def _key(run_id):
    return "hris_slip_run:" + str(run_id)


def _save(run_id, status):
    status["updated"] = time.time()
    _cache().set_value(_key(run_id), status, expires_in_sec=STATUS_TTL)


def _load(run_id):
    return _cache().get_value(_key(run_id))


def _proses(period, names, run_id=None, status=None, commit=False):
    hasil = {"total": len(names), "dibuat": 0, "diperbarui": 0, "dilewati": 0, "gagal": 0, "alasan": {}, "errors": []}
    for i, n in enumerate(names, 1):
        frappe.db.savepoint(SAVEPOINT)
        try:
            jenis, info = proses_karyawan(period, n)
            if jenis == "dilewati":
                hasil["dilewati"] += 1
                a = hasil["alasan"].setdefault(cstr(info), {"jumlah": 0, "contoh": []})
                a["jumlah"] += 1
                if len(a["contoh"]) < CONTOH_MAKS:
                    a["contoh"].append(n)
            else:
                hasil[jenis] += 1
        except Exception as exc:
            frappe.db.rollback(save_point=SAVEPOINT)
            hasil["gagal"] += 1
            if len(hasil["errors"]) < ERROR_MAKS:
                hasil["errors"].append("{0}: {1}".format(n, str(exc)[:150]))
            frappe.log_error(title="HRIS Payroll Slip: gagal {0}".format(n), message=frappe.get_traceback())
        if commit:
            frappe.db.commit()
        if status is not None and (i % 5 == 0 or i == len(names)):
            status.update(done=i, dibuat=hasil["dibuat"], diperbarui=hasil["diperbarui"], dilewati=hasil["dilewati"],
                          gagal=hasil["gagal"], alasan=hasil["alasan"], errors=list(hasil["errors"]))
            _save(run_id, status)
    return hasil


@frappe.whitelist()
def buat_slip(periode, cakupan="Semua", employee=None, department=None, employee_group=None):
    _wajib_peran()
    period = frappe.get_doc(PERIOD, periode)
    if period.status != "Draft":
        frappe.throw(_("Slip hanya dibuat atau dihitung ulang saat periode berstatus Draft (sekarang {0}). Untuk koreksi, kembalikan periode ke Draft.").format(period.status))
    names = _kandidat(period, cakupan or "Semua", employee, department, employee_group)
    if not names:
        return {"mode": "sync", "total": 0, "dibuat": 0, "diperbarui": 0, "dilewati": 0, "gagal": 0, "alasan": {}, "errors": [],
                "message": _("Tidak ada karyawan dengan baris gaji pada jadwal dan periode ini.")}
    if len(names) <= SYNC_LIMIT:
        hasil = _proses(period, names)
        hasil["mode"] = "sync"
        return hasil
    aktif = _cache().get_value(ACTIVE_KEY)
    if aktif:
        s = _load(aktif)
        if s and s.get("state") in ("Antre", "Berjalan") and time.time() - s.get("updated", 0) < 180:
            frappe.throw(_("Masih ada proses slip berjalan ({0} dari {1}). Tunggu sampai selesai.").format(s.get("done"), s.get("total")))
    run_id = uuid.uuid4().hex[:12]
    status = {"run_id": run_id, "state": "Antre", "user": frappe.session.user, "total": len(names), "done": 0,
              "dibuat": 0, "diperbarui": 0, "dilewati": 0, "gagal": 0, "alasan": {}, "errors": []}
    _save(run_id, status)
    _cache().set_value(ACTIVE_KEY, run_id, expires_in_sec=STATUS_TTL)
    frappe.enqueue("hris.hris_payroll.services.payroll_slip.run_batch", queue="long", timeout=3600,
                   run_id=run_id, periode=periode, names=names)
    return {"mode": "background", "run_id": run_id, "total": len(names)}


def run_batch(run_id, periode, names, commit=True):
    status = _load(run_id) or {"run_id": run_id}
    status["state"] = "Berjalan"
    _save(run_id, status)
    try:
        period = frappe.get_doc(PERIOD, periode)
        hasil = _proses(period, names, run_id=run_id, status=status, commit=commit)
        status.update(state="Selesai", done=hasil["total"], dibuat=hasil["dibuat"], diperbarui=hasil["diperbarui"],
                      dilewati=hasil["dilewati"], gagal=hasil["gagal"], alasan=hasil["alasan"], errors=list(hasil["errors"]))
        _save(run_id, status)
    except Exception:
        frappe.db.rollback()
        frappe.log_error(title="HRIS Payroll Slip: proses background gagal", message=frappe.get_traceback())
        frappe.db.commit()
        status.update(state="Gagal", message=_("Proses berhenti karena error. Lihat Error Log."))
        _save(run_id, status)
        raise
    finally:
        if _cache().get_value(ACTIVE_KEY) == run_id:
            _cache().delete_value(ACTIVE_KEY)


@frappe.whitelist()
def get_status(run_id):
    _wajib_peran()
    status = _load(run_id)
    if not status:
        return {"state": "Tidak Ada", "message": _("Status tidak ditemukan atau sudah kedaluwarsa (lebih dari 1 jam).")}
    umur = int(time.time() - status.get("updated", time.time()))
    status["warning"] = None
    if status.get("state") == "Antre" and umur > QUEUE_STALE_AFTER:
        status["warning"] = _("Belum diambil worker selama {0} detik. Worker background kemungkinan mati.").format(umur)
    elif status.get("state") == "Berjalan" and umur > RUN_STALE_AFTER:
        status["warning"] = _("Tidak ada kemajuan selama {0} detik. Periksa Error Log dan worker.").format(umur)
    return status
