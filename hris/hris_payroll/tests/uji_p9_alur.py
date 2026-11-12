"""K-138 tahap 2: uji alur penuh hook Shift Assignment. Semua di-rollback.

Jalankan:
bench --site hris-uji.local execute hris.hris_payroll.tests.uji_p9_alur.jalankan
"""
import frappe
from frappe.utils import add_days, getdate, now_datetime

ALASAN = "uji P9 tahap 2 alur"
hasil = []


def cek(nama, kondisi, ket=""):
    hasil.append(bool(kondisi))
    print(("OK     " if kondisi else "GAGAL  ") + nama + ((" | " + str(ket)) if ket != "" else ""))


def _blok_bebas(erp, mulai, panjang, batas=90):
    """Cari `panjang` hari berurutan tanpa Working Hour dan tanpa penugasan untuk karyawan."""
    d = getdate(mulai)
    for i in range(batas):
        hari = [str(add_days(d, i + k)) for k in range(panjang)]
        bentrok = False
        for s in hari:
            if frappe.db.exists("HRIS Working Hour", {"employee": erp, "work_date": s}) or frappe.db.exists(
                "HRIS Shift Assignment", {"employee": erp, "from_date": ["<=", s], "to_date": [">=", s]}
            ):
                bentrok = True
                break
        if not bentrok:
            return hari
    return None


def _wh(erp, tanggal, rule, review="Tidak Perlu", status="Hadir"):
    doc = frappe.get_doc(
        {"doctype": "HRIS Working Hour", "employee": erp, "work_date": tanggal,
         "status": status, "review_status": review}
    )
    doc.flags.from_calculation = True
    doc.insert(ignore_permissions=True, ignore_mandatory=True)
    frappe.db.set_value("HRIS Working Hour", doc.name, "rule_department", rule, update_modified=False)
    return doc.name


def _baris(erp, tanggal):
    return frappe.db.get_value(
        "HRIS Working Hour", {"employee": erp, "work_date": tanggal},
        ["name", "rule_department", "needs_review", "review_status", "review_reason", "adjustment_hours", "modified"],
        as_dict=True,
    )


def _penugasan(erp, dari, sampai, shift, dept=None):
    isi = {"doctype": "HRIS Shift Assignment", "employee": erp, "from_date": dari, "to_date": sampai,
           "shift": shift, "reason": ALASAN, "is_active": 1}
    if dept:
        isi["borrowed_for_department"] = dept
    return frappe.get_doc(isi).insert(ignore_permissions=True)


def _jalankan(perusahaan, mulai_log):
    kar = frappe.db.sql(
        """
        select he.name as he, he.erpnext_employee as erp, he.department as dept
        from `tabHRIS Employee` he
        where he.erpnext_employee is not null and he.erpnext_employee != ''
          and he.status = 'Aktif' and he.company = %s
          and he.department is not null and he.department != ''
          and not exists (select 1 from `tabHRIS Employee Pay` ep where ep.employee = he.name)
        order by he.name limit 1
        """,
        perusahaan, as_dict=True,
    )
    if not kar:
        cek("D0 ada karyawan uji (terhubung, punya Department, tanpa baris gaji)", False)
        return
    k = kar[0]
    erp, he, own = k["erp"], k["he"], k["dept"]
    dept_uji = frappe.db.get_value("HRIS Department", {"name": ["!=", own]}, "name")
    shift = frappe.get_all("HRIS Shift", filters={"is_active": 1, "company": perusahaan}, pluck="name", limit=1)
    blok = _blok_bebas(erp, "2026-03-02", 5)
    feb = _blok_bebas(erp, "2026-02-02", 1, batas=24)
    cek("D0 data uji lengkap", bool(dept_uji and shift and blok and feb),
        "karyawan=%s dept=%s tujuan=%s shift=%s blok=%s feb=%s" % (erp, own, dept_uji, shift[:1], blok and blok[0], feb))
    if not (dept_uji and shift and blok and feb):
        return
    shift = shift[0]
    d1, d2, d3, d4, d5 = blok

    # ---------------- A ----------------
    for d in (d1, d2, d3):
        _wh(erp, d, own)
    pen = _penugasan(erp, d1, d2, shift, dept_uji)
    cek("A1 pinjam: D1 dan D2 pindah ke Department tujuan",
        _baris(erp, d1).rule_department == dept_uji and _baris(erp, d2).rule_department == dept_uji,
        "%s | %s" % (_baris(erp, d1).rule_department, _baris(erp, d2).rule_department))

    pen.reload()
    pen.to_date = d1
    pen.save(ignore_permissions=True)
    cek("A2 persempit rentang: D1 tetap tujuan, D2 kembali ke karyawan",
        _baris(erp, d1).rule_department == dept_uji and _baris(erp, d2).rule_department == own,
        "%s | %s" % (_baris(erp, d1).rule_department, _baris(erp, d2).rule_department))

    frappe.delete_doc("HRIS Shift Assignment", pen.name, ignore_permissions=True, force=True)
    cek("A3 hapus penugasan: D1 kembali ke karyawan", _baris(erp, d1).rule_department == own,
        _baris(erp, d1).rule_department)

    sebelum = _baris(erp, d3)
    _penugasan(erp, d3, d3, shift)
    sesudah = _baris(erp, d3)
    cek("A4 penugasan biasa tidak menyentuh baris",
        sebelum.modified == sesudah.modified and sesudah.rule_department == own,
        "%s -> %s" % (sebelum.modified, sesudah.modified))

    # ---------------- B ----------------
    _wh(erp, d4, own, review="Sudah Ditinjau")
    _wh(erp, d5, own)
    frappe.db.set_value("HRIS Working Hour", {"employee": erp, "work_date": d5}, "adjustment_hours", 1.5, update_modified=False)
    _penugasan(erp, d4, d5, shift, dept_uji)
    b1, b2 = _baris(erp, d4), _baris(erp, d5)
    cek("B1 Sudah Ditinjau: tidak dihitung ulang, ditandai Menunggu",
        b1.rule_department == own and b1.needs_review == 1 and b1.review_status == "Menunggu"
        and dept_uji in (b1.review_reason or ""),
        "rule=%s needs=%s status=%s" % (b1.rule_department, b1.needs_review, b1.review_status))
    cek("B2 adjustment_hours: tidak dihitung ulang, ditandai",
        b2.rule_department == own and b2.needs_review == 1 and dept_uji in (b2.review_reason or ""),
        "rule=%s needs=%s" % (b2.rule_department, b2.needs_review))

    # ---------------- C ----------------
    jadwal = frappe.get_doc(
        {"doctype": "HRIS Payroll Schedule", "schedule_name": "ZZ Uji Alur P9", "company": perusahaan,
         "schedule_type": "Bulanan", "cut_off_day": 26, "is_active": 1}
    ).insert(ignore_permissions=True)
    per = frappe.get_doc(
        {"doctype": "HRIS Payroll Period", "payroll_schedule": jadwal.name, "reference_date": "2026-02-15"}
    ).insert(ignore_permissions=True)
    frappe.get_doc(
        {"doctype": "HRIS Employee Pay", "employee": he, "pay_type": "Harian", "amount": 100000,
         "payroll_schedule": jadwal.name, "effective_from": "2025-12-01"}
    ).insert(ignore_permissions=True)
    frappe.db.set_value("HRIS Payroll Period", per.name, "status", "Final", update_modified=False)
    _wh(erp, feb[0], own)
    sebelum = frappe.db.get_value("HRIS Working Hour", {"employee": erp, "work_date": feb[0]}, "*", as_dict=True)
    _penugasan(erp, feb[0], feb[0], shift, dept_uji)
    sesudah = frappe.db.get_value("HRIS Working Hour", {"employee": erp, "work_date": feb[0]}, "*", as_dict=True)
    beda = {f for f in sebelum if sebelum[f] != sesudah.get(f)}
    boleh = {"needs_review", "review_reason", "review_status"}
    cek("C1 periode Final: hanya tiga kolom penanda yang berubah",
        sesudah.needs_review == 1 and beda <= boleh and sesudah.rule_department == own,
        "kolom berubah: %s" % sorted(beda))


def jalankan():
    hasil.clear()
    mulai_log = now_datetime()
    perusahaan = frappe.get_all("Company", pluck="name", limit=1)[0]
    frappe.db.savepoint("uji_alur")
    try:
        _jalankan(perusahaan, mulai_log)
    except Exception as ex:  # noqa: BLE001
        import traceback
        traceback.print_exc()
        cek("uji berjalan tanpa galat tak terduga", False, repr(ex)[:200])
    finally:
        galat = frappe.get_all("Error Log", filters={"creation": [">=", mulai_log], "method": ["like", "K-138%"]},
                               fields=["method"], limit=10)
        galat += frappe.get_all("Error Log", filters={"creation": [">=", mulai_log]}, fields=["method"], limit=10)
        for g in galat:
            print("INFO  Error Log tercatat:", g.method)
        frappe.db.rollback(save_point="uji_alur")
        sisa = frappe.db.count("HRIS Shift Assignment", {"reason": ALASAN})
        cek("Z1 uji bersih (rollback)", sisa == 0, str(sisa))
    ringkas = "HASIL: OK %d, GAGAL %d" % (hasil.count(True), hasil.count(False))
    print(ringkas)
    return ringkas
