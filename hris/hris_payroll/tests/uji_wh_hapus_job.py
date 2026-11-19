"""Uji 6b-2: job hapus Working Hour per batch. Memakai data sintetis (awalan UJIWHD-) yang selalu dibersihkan.
  bench --site hris-uji.local execute hris.hris_payroll.tests.uji_wh_hapus_job.jalankan
"""
import frappe
from frappe.utils import add_days, now_datetime

from hris.hris_attendance.services import working_hour_hapus as svc
from hris.hris_attendance.services import working_hour_hapus_job as job

DT = svc.WH
SAKLAR = job.SAKLAR
KOLOM = [
    "name", "creation", "modified", "modified_by", "owner", "docstatus", "idx",
    "employee", "employee_name", "work_date", "unique_key", "status",
]


def _lempar(fn, jenis):
    try:
        fn()
    except jenis:
        return True
    except Exception:
        return False
    return False


def _bersih():
    frappe.db.delete(DT, {"name": ["like", "UJIWHD-%"]})
    frappe.db.delete("Comment", {"reference_doctype": DT, "reference_name": ["like", "UJIWHD-%"]})
    frappe.db.commit()


def _isi(awalan, n, karyawan, tanggal):
    now = now_datetime()
    nilai = []
    for i in range(n):
        nm = "%s%05d" % (awalan, i + 1)
        nilai.append((nm, now, now, "Administrator", "Administrator", 0, 0,
                      karyawan(i), "Uji WHD", str(tanggal(i)), nm, "Tidak Hadir"))
    frappe.db.bulk_insert(DT, KOLOM, nilai)


def jalankan():
    hasil = []

    def cek(nama, kondisi):
        hasil.append(bool(kondisi))
        print(("OK " if kondisi else "GAGAL ") + nama)

    asli_saklar = frappe.conf.get(SAKLAR)
    sebelum = None
    log = None
    s = None
    status_asli = None
    try:
        _bersih()
        sebelum = frappe.db.count(DT)

        # --- saklar ---
        frappe.conf[SAKLAR] = 0
        cek("saklar mati: hapus ditolak",
            _lempar(lambda: job.enqueue_delete("2099-03-01", "2099-03-31", confirm_total=1), frappe.ValidationError))
        frappe.conf[SAKLAR] = 1

        # --- validasi server pada data sintetis ---
        _isi("UJIWHD-A", 2500, lambda i: "UJIWHD-EMP", lambda i: add_days("2099-03-01", i % 28))
        frappe.db.commit()
        a = svc.check_delete("2099-03-01", "2099-03-31")
        cek("hitung dulu: 2500 dokumen sintetis", a["total"] == 2500)
        cek("jumlah konfirmasi salah ditolak",
            _lempar(lambda: job.enqueue_delete("2099-03-01", "2099-03-31", confirm_total=1), frappe.ValidationError))
        frappe.db.set_value(DT, "UJIWHD-A00001", "classified_by", "Administrator", update_modified=False)
        frappe.db.commit()
        cek("peringatan input_manual belum dikonfirmasi ditolak",
            _lempar(lambda: job.enqueue_delete("2099-03-01", "2099-03-31", confirm_total=2500, konfirmasi=[]),
                    frappe.ValidationError))

        frappe.get_doc({"doctype": "Comment", "comment_type": "Info", "reference_doctype": DT,
                        "reference_name": "UJIWHD-A00002", "content": "uji"}).insert(ignore_permissions=True)
        frappe.db.commit()
        cek("Comment uji ada sebelum hapus",
            frappe.db.count("Comment", {"reference_doctype": DT, "reference_name": "UJIWHD-A00002"}) == 1)

        # --- job hapus per batch (3 batch: 1000 + 1000 + 500) ---
        _, _, flt = svc._siapkan("2099-03-01", "2099-03-31")
        log = job._log_buat(flt, 2500, ["input_manual"], "Administrator")
        n = job.run_delete_job("2099-03-01", "2099-03-31", notify_user="Administrator", log_name=log)
        cek("job menghapus 2500 dokumen", n == 2500)
        cek("tidak ada sisa dokumen sintetis A", frappe.db.count(DT, {"name": ["like", "UJIWHD-A%"]}) == 0)
        cek("Comment dokumen ikut terhapus",
            frappe.db.count("Comment", {"reference_doctype": DT, "reference_name": ["like", "UJIWHD-A%"]}) == 0)
        lg = frappe.db.get_value(job.LOG, log, ["status", "jumlah_dihapus", "total_cocok"], as_dict=True) if log else None
        cek("catatan audit Selesai dengan jumlah benar",
            bool(lg) and lg.status == "Selesai" and lg.jumlah_dihapus == 2500 and lg.total_cocok == 2500)
        st = job.delete_status()
        cek("status cache Selesai", st.get("status") == "Selesai" and st.get("terhapus") == 2500)

        # --- blokir slip Final ---
        slip = frappe.db.sql(
            """select s.name, s.erpnext_employee, s.period_start, s.period_end
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
            status_asli = frappe.db.get_value("HRIS Payroll Slip", s.name, "status")
            _isi("UJIWHD-B", 600, lambda i: s.erpnext_employee, lambda i: add_days(s.period_start, i % 20))
            frappe.db.commit()
            args = dict(date_from=str(s.period_start), date_to=str(s.period_end), karyawan=[s.erpnext_employee])

            frappe.db.set_value("HRIS Payroll Slip", s.name, "status", "Final", update_modified=False)
            r = job.enqueue_delete(confirm_total=1, **args)
            cek("slip Final: hapus ditolak (queued False)", r.get("queued") is False)

            # Commit dimatikan: bila logika blokir rusak, penghapusan data nyata ikut di-rollback.
            commit_asli = frappe.db.commit
            frappe.db.commit = lambda *a, **k: None
            try:
                berhenti = _lempar(
                    lambda: job.run_delete_job(args["date_from"], args["date_to"], karyawan=args["karyawan"]),
                    frappe.ValidationError,
                )
            finally:
                frappe.db.commit = commit_asli
            frappe.db.rollback()
            cek("job berhenti saat dokumen di bawah slip Final", berhenti)
            cek("dokumen sintetis B tidak terhapus", frappe.db.count(DT, {"name": ["like", "UJIWHD-B%"]}) == 600)
            cek("status slip kembali ke semula",
                frappe.db.get_value("HRIS Payroll Slip", s.name, "status") == status_asli)
    except Exception as exc:
        cek("tidak ada error tak terduga: %s" % str(exc)[:150], False)
    finally:
        frappe.db.rollback()
        if s is not None and frappe.db.get_value("HRIS Payroll Slip", s.name, "status") != status_asli:
            frappe.db.set_value("HRIS Payroll Slip", s.name, "status", status_asli, update_modified=False)
            frappe.db.commit()
        if asli_saklar is None:
            frappe.conf.pop(SAKLAR, None)
        else:
            frappe.conf[SAKLAR] = asli_saklar
        _bersih()
        if log:
            frappe.db.delete(job.LOG, {"name": log})
            frappe.db.commit()

    if sebelum is not None:
        cek("jumlah Working Hour nyata tidak berubah", frappe.db.count(DT) == sebelum)
    cek("tidak ada sisa data uji", frappe.db.count(DT, {"name": ["like", "UJIWHD-%"]}) == 0)
    print("\nLulus %d dari %d" % (sum(hasil), len(hasil)))
