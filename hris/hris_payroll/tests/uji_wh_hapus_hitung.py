"""Uji 6b-1: hitung dulu hapus Working Hour (baca saja). Tidak meninggalkan data (rollback).
  bench --site hris-uji.local execute hris.hris_payroll.tests.uji_wh_hapus_hitung.jalankan
"""
import frappe

from hris.hris_attendance.services import working_hour_hapus as svc

DT = "HRIS Working Hour"


def _lempar(fn, jenis):
    try:
        fn()
    except jenis:
        return True
    except Exception:
        return False
    return False


def jalankan():
    hasil = []

    def cek(nama, kondisi):
        hasil.append(bool(kondisi))
        print(("OK " if kondisi else "GAGAL ") + nama)

    r = frappe.db.sql("select min(work_date), max(work_date) from `tabHRIS Working Hour`")[0]
    if not r[0]:
        print("SKIP tidak ada data Working Hour")
        return
    dari, sampai = str(r[0]), str(r[1])
    wh_sebelum = frappe.db.count(DT)
    dd_sebelum = frappe.db.count("Deleted Document")

    try:
        # --- penghitungan dasar ---
        a = svc.check_delete(dari, sampai)
        cek("total = jumlah dokumen pada rentang",
            a["total"] == frappe.db.count(DT, {"work_date": ["between", [dari, sampai]]}))
        cek("per_status berjumlah sama dengan total", sum(a["per_status"].values()) == a["total"])

        st = next(iter(a["per_status"]))
        b = svc.check_delete(dari, sampai, status=[st])
        cek("filter status %s = jumlah per_status" % st, b["total"] == a["per_status"][st])
        c = svc.check_delete(dari, sampai, status='["%s"]' % st)
        cek("status boleh berupa JSON string", c["total"] == b["total"])
        d = svc.check_delete(dari, sampai, tanpa_gaji=1)
        cek("tanpa_gaji tidak melebihi total", d["total"] <= a["total"])

        # --- validasi masukan ---
        cek("tanggal terbalik ditolak",
            _lempar(lambda: svc.check_delete("2099-01-02", "2099-01-01"), frappe.ValidationError))
        cek("tanggal kosong ditolak",
            _lempar(lambda: svc.check_delete(None, sampai), frappe.ValidationError))
        cek("status tidak dikenal ditolak",
            _lempar(lambda: svc.check_delete(dari, sampai, status=["Bukan Status"]), frappe.ValidationError))
        e = svc.check_delete("2000-01-01", "2000-01-02")
        cek("rentang kosong: total 0 dan boleh False", e["total"] == 0 and e["boleh"] is False)

        # --- slip: Draft memperingatkan, Final memblokir ---
        slip = frappe.db.sql(
            """select s.name, s.erpnext_employee, s.period_start, s.period_end, s.payroll_period
               from `tabHRIS Payroll Slip` s
               left join `tabHRIS Payroll Period` pp on pp.name = s.payroll_period
               where ifnull(s.erpnext_employee, '') != '' and s.status != 'Final'
                 and ifnull(pp.status, '') != 'Final'
               limit 1""",
            as_dict=True,
        )
        if not slip:
            print("SKIP tidak ada slip belum Final untuk menguji blokir")
        else:
            s = slip[0]
            args = dict(date_from=str(s.period_start), date_to=str(s.period_end), karyawan=[s.erpnext_employee])
            f = svc.check_delete(**args)
            cek("slip belum Final: tidak diblokir dan boleh", f["blokir"]["jumlah"] == 0 and f["boleh"])
            cek("slip belum Final: ada peringatan slip_belum_final",
                any(p["kode"] == "slip_belum_final" for p in f["peringatan"]))

            frappe.db.set_value("HRIS Payroll Slip", s.name, "status", "Final", update_modified=False)
            g = svc.check_delete(**args)
            cek("slip Final: blokir > 0 dan boleh False", g["blokir"]["jumlah"] > 0 and not g["boleh"])
            cek("daftar blokir memuat slip itu", any(x["name"] == s.name for x in g["blokir"]["slip"]))
            frappe.db.rollback()

            if s.payroll_period:
                frappe.db.set_value("HRIS Payroll Period", s.payroll_period, "status", "Final", update_modified=False)
                h = svc.check_delete(**args)
                cek("Period Final (slip Draft): blokir > 0", h["blokir"]["jumlah"] > 0 and not h["boleh"])
                frappe.db.rollback()

            i = svc.check_delete(**args)
            cek("setelah rollback: blokir kembali 0", i["blokir"]["jumlah"] == 0 and i["boleh"])

        # --- input manual ---
        wh = frappe.db.sql(
            "select name, employee, work_date from `tabHRIS Working Hour` order by work_date limit 1",
            as_dict=True,
        )[0]
        args2 = dict(date_from=str(wh.work_date), date_to=str(wh.work_date), karyawan=[wh.employee])
        j = svc.check_delete(**args2)
        cek("tanpa input manual: tidak ada peringatan input_manual",
            not any(p["kode"] == "input_manual" for p in j["peringatan"]))
        frappe.db.set_value(DT, wh.name, "classified_by", "Administrator", update_modified=False)
        k = svc.check_delete(**args2)
        cek("input manual terdeteksi",
            any(p["kode"] == "input_manual" and p["jumlah"] >= 1 for p in k["peringatan"]))
        frappe.db.rollback()

        # --- izin ---
        frappe.set_user("Guest")
        try:
            cek("tanpa role: PermissionError",
                _lempar(lambda: svc.check_delete(dari, sampai), frappe.PermissionError))
        finally:
            frappe.set_user("Administrator")
    except Exception as exc:
        cek("tidak ada error tak terduga: %s" % str(exc)[:150], False)
    finally:
        frappe.set_user("Administrator")
        frappe.db.rollback()

    cek("jumlah Working Hour tidak berubah", frappe.db.count(DT) == wh_sebelum)
    cek("Deleted Document tidak bertambah", frappe.db.count("Deleted Document") == dd_sebelum)
    print("\nLulus %d dari %d" % (sum(hasil), len(hasil)))
