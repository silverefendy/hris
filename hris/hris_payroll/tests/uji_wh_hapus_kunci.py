"""Uji 6b-1b: periode Final TANPA slip tetap memblokir hapus Working Hour.
  bench --site hris-uji.local execute hris.hris_payroll.tests.uji_wh_hapus_kunci.jalankan
Memakai data nyata. Tautan slip dilepas dan status periode diubah sementara, lalu di-rollback.
"""
import frappe

from hris.hris_attendance.services import working_hour_hapus as svc

JADWAL = "Uji Slip Browser 01"


def jalankan():
    ok = 0
    total = 0

    def cek(nama, kondisi):
        nonlocal ok, total
        total += 1
        if kondisi:
            ok += 1
            print("OK", nama)
        else:
            print("GAGAL", nama)

    def n_wh(nama_wh, klausa):
        return frappe.db.sql(
            "select count(*) from `tabHRIS Working Hour` wh where wh.name = %s and " + klausa, nama_wh
        )[0][0]

    k = frappe.db.sql(
        """
        select wh.name, wh.employee, wh.work_date, pp.name as periode, pp.status as status_periode
        from `tabHRIS Working Hour` wh
        inner join `tabHRIS Employee` he on he.erpnext_employee = wh.employee
        inner join `tabHRIS Employee Pay` ep on ep.employee = he.name
            and ep.effective_from <= wh.work_date
            and (ep.effective_to is null or ep.effective_to >= wh.work_date)
        inner join `tabHRIS Payroll Period` pp on pp.payroll_schedule = ep.payroll_schedule
            and wh.work_date between pp.period_start and pp.period_end
        where ep.payroll_schedule = %s and ifnull(pp.status, '') != 'Final'
        limit 1
        """,
        JADWAL,
        as_dict=True,
    )
    if not k:
        print("SKIP tidak ada WH ber-gaji pada periode jadwal", JADWAL)
        print("\nLulus 0 dari 0 (SKIP)")
        return
    k = k[0]
    tgl = str(k.work_date)

    slip_awal = frappe.db.sql(
        "select name, payroll_period, status from `tabHRIS Payroll Slip` where payroll_period = %s",
        k.periode,
        as_dict=True,
    )

    try:
        cek("sebelum Final: tidak terblokir", not svc.dokumen_terblokir(k.employee, k.work_date))
        r = svc.check_delete(tgl, tgl, [k.employee])
        cek("sebelum Final: check_delete blokir 0", r["blokir"]["jumlah"] == 0)

        # Lepas tautan slip ke periode: jalur slip tidak boleh aktif lagi.
        frappe.db.sql("update `tabHRIS Payroll Slip` set payroll_period = null where payroll_period = %s", k.periode)
        frappe.db.set_value("HRIS Payroll Period", k.periode, "status", "Final", update_modified=False)

        cek("jalur slip tidak aktif (slip Draft, tanpa periode)", n_wh(k.name, svc._SLIP_FINAL_ADA) == 0)
        cek("jalur kunci periode aktif", n_wh(k.name, svc._KUNCI_PERIODE) == 1)
        cek("dokumen_terblokir True", bool(svc.dokumen_terblokir(k.employee, k.work_date)))
        r = svc.check_delete(tgl, tgl, [k.employee])
        cek("check_delete blokir >= 1", r["blokir"]["jumlah"] >= 1)
        cek("check_delete boleh False", r["boleh"] is False)

        # Kontrol: WH tanpa baris gaji pada tanggalnya tidak boleh terblokir.
        pp = frappe.db.get_value("HRIS Payroll Period", k.periode, ["period_start", "period_end"], as_dict=True)
        kontrol = frappe.db.sql(
            "select wh.name, wh.employee, wh.work_date from `tabHRIS Working Hour` wh"
            " where wh.work_date between %s and %s and not exists (" + svc._ADA_GAJI + ") limit 1",
            (pp.period_start, pp.period_end),
            as_dict=True,
        )
        if kontrol:
            c = kontrol[0]
            cek("kontrol tanpa gaji: tidak terblokir", not svc.dokumen_terblokir(c.employee, c.work_date))
        else:
            print("SKIP kontrol tanpa gaji: tidak ada WH tanpa gaji di rentang periode itu")
    finally:
        frappe.db.rollback()

    status = frappe.db.get_value("HRIS Payroll Period", k.periode, "status")
    cek("status periode kembali semula", (status or "") == (k.status_periode or ""))
    slip_akhir = frappe.db.sql(
        "select name, payroll_period, status from `tabHRIS Payroll Slip` where payroll_period = %s",
        k.periode,
        as_dict=True,
    )
    cek("tautan slip kembali semula", len(slip_akhir) == len(slip_awal) and len(slip_awal) > 0)

    print("\nLulus %d dari %d" % (ok, total))
