"""Uji K-128: HRIS Payroll Period dan penguncian. Semua di-rollback.

Jalankan:
bench --site hris-uji.local execute hris.hris_payroll.tests.uji_payroll_period.periksa
"""

import frappe
from frappe.utils import strip_html

from hris.hris_payroll.doctype.hris_payroll_period import hris_payroll_period as P
from hris.hris_payroll.services import period_lock
from hris.hris_payroll.services.payroll_schedule import get_period_for_date

hasil = []
USERS = {
    "admin": ("uji.per.admin@uji.local", ["HRIS Payroll Admin"]),
    "manager": ("uji.per.manager@uji.local", ["HRIS Payroll Manager"]),
    "direksi": ("uji.per.direksi@uji.local", ["HRIS Direksi"]),
}


def _catat(nama, lulus, info=""):
    hasil.append(bool(lulus))
    print(("OK     " if lulus else "GAGAL  ") + nama + ((" | " + info) if info else ""))


def _ditolak(nama, fungsi, kata=None):
    try:
        fungsi()
    except (frappe.ValidationError, frappe.PermissionError) as e:
        pesan = strip_html(str(e))
        if kata:
            _catat(nama, all(k.lower() in pesan.lower() for k in ([kata] if isinstance(kata, str) else kata)), pesan[:160])
        else:
            _catat(nama, True, pesan[:160])
    except Exception as e:  # noqa: BLE001
        _catat(nama, False, "galat lain: " + repr(e)[:160])
    else:
        _catat(nama, False, "TIDAK ditolak")


def _lolos(nama, fungsi):
    try:
        fungsi()
    except Exception as e:  # noqa: BLE001
        _catat(nama, False, "ditolak: " + strip_html(str(e))[:160])
    else:
        _catat(nama, True)


def _sebagai(email, fungsi):
    frappe.set_user(email)
    try:
        return fungsi()
    finally:
        frappe.set_user("Administrator")


def _jadwal(perusahaan, nama, aktif):
    return frappe.get_doc(
        {"doctype": "HRIS Payroll Schedule", "schedule_name": nama, "company": perusahaan,
         "schedule_type": "Bulanan", "cut_off_day": 26, "is_active": aktif}
    ).insert(ignore_permissions=True)


def _periode(jadwal, ref):
    return frappe.get_doc(
        {"doctype": "HRIS Payroll Period", "payroll_schedule": jadwal, "reference_date": ref}
    ).insert(ignore_permissions=True)


def _pay(he, jadwal, dari, alasan=None):
    isi = {"doctype": "HRIS Employee Pay", "employee": he, "pay_type": "Harian", "amount": 100000,
           "payroll_schedule": jadwal, "effective_from": dari}
    if alasan:
        isi["change_reason"] = alasan
    return frappe.get_doc(isi).insert(ignore_permissions=True)


def _wh(erp, tanggal, status, review):
    doc = frappe.get_doc(
        {"doctype": "HRIS Working Hour", "employee": erp, "work_date": tanggal,
         "status": status, "review_status": review}
    )
    doc.flags.from_calculation = True
    doc.insert(ignore_permissions=True, ignore_mandatory=True)
    return doc


def _karyawan(perusahaan):
    return frappe.db.sql(
        """
        select he.name as he, he.erpnext_employee as erp
        from `tabHRIS Employee` he
        where he.erpnext_employee is not null and he.erpnext_employee != ''
          and he.status = 'Aktif' and he.company = %s
          and not exists (select 1 from `tabHRIS Employee Pay` ep where ep.employee = he.name)
        order by he.name limit 2
        """,
        perusahaan,
        as_dict=True,
    )


def _jalankan(perusahaan):
    from hris.hris_attendance.services import working_hour_batch as B
    from hris.hris_attendance.services.working_hour import calculate_working_hour

    kar = _karyawan(perusahaan)
    if len(kar) < 2:
        _catat("tersedia dua karyawan terhubung tanpa baris gaji", False, "ditemukan %d" % len(kar))
        return
    e1, e2 = kar
    j = _jadwal(perusahaan, "ZZ Uji Jadwal Period", 1).name
    j_mati = _jadwal(perusahaan, "ZZ Uji Jadwal Period Mati", 0).name
    for email, peran in USERS.values():
        frappe.get_doc(
            {"doctype": "User", "email": email, "first_name": "ZZ Uji", "enabled": 1,
             "send_welcome_email": 0, "user_type": "System User", "roles": [{"role": r} for r in peran]}
        ).insert(ignore_permissions=True)
    u_admin, u_manager, u_direksi = (USERS[k][0] for k in ("admin", "manager", "direksi"))

    # ---- pembuatan dan aturan dasar ----
    per = _periode(j, "2026-02-15")
    acuan = get_period_for_date(j, "2026-02-15")
    _catat(
        "P01 periode dibuat dari jadwal, tanggal diisi sistem, status Draft",
        per.name.startswith("HPP-") and per.status == "Draft"
        and str(per.period_start) == str(acuan["start"]) and str(per.period_end) == str(acuan["end"])
        and str(per.pay_date) == str(acuan["pay_date"]),
        "%s | %s s/d %s | bayar %s" % (per.name, per.period_start, per.period_end, per.pay_date),
    )
    _ditolak("P02 periode ganda untuk jadwal dan awal yang sama ditolak", lambda: _periode(j, "2026-02-20"), "sudah ada")
    per.reload()
    per.period_end = "2026-03-31"
    _ditolak("P03a ubah rentang manual ditolak", lambda: per.save(ignore_permissions=True), "tidak dapat diubah")
    per.reload()
    per.status = "Final"
    _ditolak("P03b ubah status manual ditolak", lambda: per.save(ignore_permissions=True), "Status hanya berubah")
    per.reload()
    _ditolak("P04 jadwal nonaktif ditolak", lambda: _periode(j_mati, "2026-02-15"), "aktif")

    # ---- peran dan alur ----
    _sebagai(u_admin, lambda: P.tinjau(per.name))
    per.reload()
    _catat("P05 Payroll Admin boleh meninjau (Draft ke Ditinjau)", per.status == "Ditinjau" and per.reviewed_by == u_admin)
    _ditolak("P06 Payroll Admin tidak boleh memfinalkan", lambda: _sebagai(u_admin, lambda: P.finalkan(per.name)), "tidak berhak")
    p15 = _periode(j, "2025-12-10")
    _ditolak("P15 Direksi tidak boleh meninjau", lambda: _sebagai(u_direksi, lambda: P.tinjau(p15.name)), "tidak berhak")
    _catat("P18 Direksi tidak punya hak buat", frappe.has_permission("HRIS Payroll Period", "create", user=u_direksi) is False)

    masa_depan = _periode(j, "2027-03-15")
    _sebagai(u_manager, lambda: P.tinjau(masa_depan.name))
    _ditolak("P07 periode yang belum berakhir tidak bisa Final", lambda: _sebagai(u_manager, lambda: P.finalkan(masa_depan.name)), "belum berakhir")

    # ---- syarat Final ----
    wh_a = _wh(e1["erp"], "2026-02-03", "Tidak Hadir", "Menunggu")
    _wh(e2["erp"], "2026-02-04", "Hadir", "Tidak Perlu")
    _pay(e1["he"], j, "2025-12-01")
    _ditolak(
        "P08 syarat Final: semua kekurangan ditampilkan sekaligus",
        lambda: _sebagai(u_manager, lambda: P.finalkan(per.name)),
        ["belum ditinjau", "tanpa baris gaji"],
    )
    wh_a.reload()
    wh_a.review_status = "Sudah Ditinjau"
    wh_a.save(ignore_permissions=True)
    _pay(e2["he"], j, "2025-12-01")
    _sebagai(u_manager, lambda: P.finalkan(per.name))
    per.reload()
    _catat("P09 Payroll Manager memfinalkan setelah syarat terpenuhi", per.status == "Final" and per.finalized_by == u_manager)

    # ---- penguncian ----
    wh_a.reload()
    wh_a.flags.from_calculation = False
    wh_a.review_status = "Menunggu"
    _ditolak("P10 edit manual Working Hour di periode Final ditolak", lambda: wh_a.save(ignore_permissions=True), "Final")
    _ditolak("P11 hitung ulang di periode Final ditolak", lambda: calculate_working_hour(e1["erp"], "2026-02-03"), "Final")
    pasang = B._protected([{"name": e1["erp"]}], "2026-02-01", "2026-02-28")
    _catat("P12 batch melewati hari terkunci", (e1["erp"], "2026-02-26") in pasang and (e1["erp"], "2026-02-27") not in pasang, "jumlah %d" % len(pasang))
    _catat("P13 hari di luar periode tidak terkunci", period_lock.is_locked(e1["erp"], "2026-02-27") is False)
    _ditolak(
        "P14a baris gaji berlaku mundur ke periode Final ditolak",
        lambda: _pay(e2["he"], j, "2026-02-10", "koreksi"),
        "Final",
    )
    _lolos("P14b baris gaji setelah periode Final diterima", lambda: _pay(e1["he"], j, "2026-03-01", "kenaikan"))

    # ---- buka kembali ----
    _ditolak("P16a buka kembali tanpa alasan ditolak", lambda: _sebagai(u_manager, lambda: P.buka_kembali(per.name, "")), "alasan")
    _ditolak("P16b Payroll Admin tidak boleh membuka kembali", lambda: _sebagai(u_admin, lambda: P.buka_kembali(per.name, "x")), "tidak berhak")
    _sebagai(u_manager, lambda: P.buka_kembali(per.name, "Koreksi uji"))
    per.reload()
    _catat("P16c buka kembali menjadi Draft dengan alasan tercatat", per.status == "Draft" and per.reopen_reason == "Koreksi uji" and not per.finalized_by)
    wh_a.reload()
    wh_a.flags.from_calculation = False
    wh_a.review_status = "Menunggu"
    _lolos("P16d edit Working Hour kembali lolos setelah dibuka", lambda: wh_a.save(ignore_permissions=True))
    _lolos("P16e baris gaji mundur kembali lolos setelah dibuka", lambda: _pay(e2["he"], j, "2026-02-10", "koreksi"))

    # ---- kembalikan dan hapus ----
    p2 = _periode(j, "2026-01-10")
    _sebagai(u_admin, lambda: P.tinjau(p2.name))
    _sebagai(u_admin, lambda: P.kembalikan(p2.name))
    p2.reload()
    _catat("P17a kembalikan Ditinjau ke Draft", p2.status == "Draft")
    frappe.delete_doc("HRIS Payroll Period", p2.name)
    _catat("P17b hapus periode Draft berhasil", not frappe.db.exists("HRIS Payroll Period", p2.name))
    _ditolak("P17c hapus periode Ditinjau ditolak", lambda: frappe.delete_doc("HRIS Payroll Period", masa_depan.name), "Draft")

    # ---- jalur tabel tidak ada (meniru produksi sebelum migrate) ----
    asli_ada = "table_exists" in frappe.db.__dict__
    frappe.db.table_exists = lambda *a, **k: False
    try:
        _catat("P19 tanpa tabel: is_locked False dan locked_pairs kosong",
               period_lock.is_locked(e1["erp"], "2026-02-03") is False
               and period_lock.locked_pairs([e1["erp"]], "2026-02-01", "2026-02-28") == set())
    finally:
        if not asli_ada:
            del frappe.db.table_exists
    _catat("P20 karyawan tidak dikenal tidak terkunci", period_lock.is_locked("TIDAK-ADA", "2026-02-03") is False)


def periksa():
    hasil.clear()
    perusahaan = frappe.get_all("Company", pluck="name", limit=1)[0]
    try:
        _jalankan(perusahaan)
    except Exception as ex:  # noqa: BLE001
        import traceback

        traceback.print_exc()
        _catat("uji berjalan tanpa galat tak terduga", False, repr(ex)[:200])
    finally:
        frappe.set_user("Administrator")
        frappe.db.rollback()
        for email, _peran in USERS.values():
            frappe.clear_cache(user=email)
    print("---")
    ringkas = "OK %d | GAGAL %d" % (hasil.count(True), hasil.count(False))
    print(ringkas)
    return ringkas
