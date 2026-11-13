import frappe
from frappe.utils import flt

from hris.hris_payroll.doctype.hris_employee_component import hris_employee_component as mod
from hris.hris_payroll.doctype.hris_employee_pay.hris_employee_pay import boleh_baris

TABEL = "HRIS Employee Component"


def _buat(**k):
    d = {"doctype": TABEL, "status": "Tidak Berlaku", "is_active": 1, "reason": "uji"}
    d.update(k)
    doc = frappe.get_doc(d)
    doc.insert(ignore_permissions=True)
    return doc


def jalankan():
    hasil = []

    def cek(nama, kondisi, info=""):
        hasil.append(bool(kondisi))
        print(("OK     " if kondisi else "GAGAL  ") + nama + (" | " + str(info) if info else ""))

    def gagal(nama, fn, kata):
        try:
            fn()
            cek(nama, False, "tidak ditolak")
        except Exception as e:
            pesan = str(e)
            cek(nama, kata.lower() in pesan.lower(), pesan[:110])

    b = frappe.db.sql(
        "select employee, payroll_schedule from `tabHRIS Employee Pay` "
        "where pay_type='Bulanan' and effective_to is null limit 1"
    )
    n = frappe.db.sql(
        "select name from `tabHRIS Employee` he where not exists "
        "(select 1 from `tabHRIS Employee Pay` p where p.employee=he.name) limit 1"
    )
    B = b[0][0] if b else None
    JADWAL = b[0][1] if b else None
    N = n[0][0] if n else None
    N_company = frappe.db.get_value("HRIS Employee", N, "company") if N else None
    print("Bulanan=%s TanpaGaji=%s (company=%s)" % (B, N, N_company))
    if not B:
        print("SKIP: tidak ada karyawan Bulanan di site ini")
        return

    asli_roles = frappe.get_roles
    asli_final = mod.periode_final_sejak
    asli_user = frappe.session.user
    H = None
    try:
        # ---- aturan umum (karyawan Bulanan) ----
        d1 = _buat(employee=B, component="TJ_MAKAN", date_from="2030-03-15", date_to="2030-03-18")
        cek("T1 buat pengecualian", d1.name.startswith("HEC-"), d1.name)
        cek("T1b pay_type Bulanan, company terisi", d1.pay_type == "Bulanan" and bool(d1.company), "%s | %s" % (d1.pay_type, d1.company))

        gagal("T2 tumpang tindih ditolak", lambda: _buat(employee=B, component="TJ_MAKAN", date_from="2030-03-17", date_to="2030-03-20"), "tumpang tindih")
        d3 = _buat(employee=B, component="TJ_TRANSPORT", date_from="2030-03-15", date_to="2030-03-18")
        cek("T3 komponen lain di tanggal sama boleh", bool(d3.name))
        gagal("T4 Sampai sebelum Dari ditolak", lambda: _buat(employee=B, component="BONUS", date_from="2030-03-20", date_to="2030-03-19"), "sebelum")
        gagal("T5 alasan kosong ditolak", lambda: _buat(employee=B, component="BONUS", date_from="2030-03-20", date_to="2030-03-20", reason=" "), "alasan")

        d1.status = "Berlaku"
        d1.amount = 20000
        gagal("T6 ubah tanpa ganti alasan ditolak", d1.save, "alasan")
        d1 = frappe.get_doc(TABEL, d1.name)
        d1.status = "Berlaku"
        d1.amount = 20000
        d1.reason = "Bos minta dinaikkan"
        d1.save(ignore_permissions=True)
        cek("T6b ubah dengan alasan baru", flt(d1.amount) == 20000 and d1.status == "Berlaku")

        d7 = frappe.get_doc(TABEL, d1.name)
        d7.component = "BONUS"
        d7.reason = "coba ganti komponen"
        gagal("T7 ganti komponen ditolak", d7.save, "tidak dapat diubah")

        d8 = frappe.get_doc(TABEL, d1.name)
        d8.amount = -5
        d8.reason = "negatif"
        gagal("T8 nominal negatif ditolak", d8.save, "negatif")

        d9 = _buat(employee=B, component="INSENTIF", date_from="2030-04-01", date_to="2030-04-01", amount=5000)
        cek("T9 Tidak Berlaku mengosongkan nominal", flt(d9.amount) == 0)

        d10 = frappe.get_doc(TABEL, d3.name)
        d10.is_active = 0
        d10.reason = "dibatalkan"
        d10.save(ignore_permissions=True)
        d11 = _buat(employee=B, component="TJ_TRANSPORT", date_from="2030-03-16", date_to="2030-03-17")
        cek("T10 setelah dinonaktifkan, rentang sama boleh dibuat lagi", bool(d11.name))

        cek("T11 Version tercatat", frappe.db.count("Version", {"ref_doctype": TABEL, "docname": d1.name}) >= 1)
        cek("T14 hook izin terdaftar", TABEL in frappe.get_hooks("permission_query_conditions") and TABEL in frappe.get_hooks("has_permission"))

        # ---- karyawan tanpa baris gaji ----
        if N and N_company:
            e = _buat(employee=N, component="TJ_MAKAN", date_from="2030-06-01", date_to="2030-06-02")
            cek("T13 tanpa baris gaji: pay_type kosong", not e.pay_type, repr(e.pay_type))
        else:
            print("SKIP   T13: karyawan tanpa gaji tidak ada atau tidak punya Company")

        # ---- baris Harian sementara (di-rollback) ----
        if N and N_company:
            try:
                frappe.get_doc({
                    "doctype": "HRIS Employee Pay", "employee": N, "company": N_company,
                    "pay_type": "Harian", "amount": 100000, "payroll_schedule": JADWAL,
                    "effective_from": "2029-01-01",
                }).insert(ignore_permissions=True)
                H = N
                print("Baris Harian sementara dibuat untuk %s" % H)
            except Exception as ex:
                frappe.db.rollback()
                print("SKIP   uji Harian: baris sementara gagal dibuat | %s" % str(ex)[:200])
        if H:
            h1 = _buat(employee=H, component="BONUS", date_from="2030-09-01", date_to="2030-09-01")
            cek("H1 karyawan Harian: pay_type Harian", h1.pay_type == "Harian", h1.pay_type)

        # ---- peran ----
        frappe.get_roles = lambda user=None: ["HRIS Payroll Admin"]
        cek("P1 Admin: Harian boleh", boleh_baris("Harian", user="uji@uji.local") is True)
        cek("P2 Admin: Bulanan ditolak", boleh_baris("Bulanan", user="uji@uji.local") is False)
        cek("P3 Admin: tanpa gaji ditolak", boleh_baris("", user="uji@uji.local") is False)
        cek("P4 Admin: penyaring list Harian", "Harian" in mod.get_permission_query_conditions("uji@uji.local"))
        cek("P5 Admin: buka baris Bulanan ditolak", mod.has_permission(frappe._dict(name="HEC-00001", pay_type="Bulanan"), user="uji@uji.local") is False)
        cek("P6 Admin: buka baris Harian boleh", mod.has_permission(frappe._dict(name="HEC-00001", pay_type="Harian"), user="uji@uji.local") is True)
        frappe.session.user = "uji@uji.local"
        gagal("P7 Admin buat baris Bulanan ditolak", lambda: _buat(employee=B, component="BONUS", date_from="2030-07-01", date_to="2030-07-01"), "")
        if H:
            p8 = _buat(employee=H, component="INSENTIF", date_from="2030-07-01", date_to="2030-07-01")
            cek("P8 Admin buat baris Harian boleh", bool(p8.name))
        frappe.session.user = asli_user
        frappe.get_roles = lambda user=None: ["HRIS Payroll Manager"]
        cek("P9 Manager: tanpa penyaring", mod.get_permission_query_conditions("uji@uji.local") == "")
        frappe.get_roles = lambda user=None: ["HRIS Employee Admin"]
        cek("P10 Employee Admin: tidak melihat apa pun", mod.get_permission_query_conditions("uji@uji.local") == "1=0")
        frappe.get_roles = asli_roles

        # ---- periode Final (ditiru) ----
        mod.periode_final_sejak = lambda j, t: "HPP-UJI"
        gagal("F1 periode Final menolak", lambda: _buat(employee=B, component="BONUS", date_from="2030-08-01", date_to="2030-08-01"), "Final")
    finally:
        frappe.get_roles = asli_roles
        mod.periode_final_sejak = asli_final
        frappe.session.user = asli_user
        frappe.db.rollback()
    print("OK %d, GAGAL %d (semua data uji di-rollback)" % (sum(hasil), len(hasil) - sum(hasil)))
