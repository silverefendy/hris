"""K-138 tahap 1: uji fungsi penentu Department, validasi Grup tanpa Department, jadwal, dan field baru.

Jalankan setelah migrate di hris-uji.local:
bench --site hris-uji.local execute hris.hris_payroll.tests.uji_p9_tahap1.jalankan
Data uji di-rollback.
"""
import frappe

from hris.hris_attendance.services.department_tujuan import tentukan_department as td
from hris.hris_attendance.services.shift_schedule import get_schedule_for_date


def _read_only(f):
    return int(f.read_only or 0) == 1


def jalankan():
    ok = []
    gagal = []

    def cek(nama, kondisi, ket=""):
        (ok if kondisi else gagal).append(nama)
        print("OK    " if kondisi else "GAGAL ", nama, ket)

    # --- fungsi murni ---
    cek("T1 tanpa peminjaman: Department karyawan", td("Produksi") == ("Produksi", "Department Karyawan"))
    cek("T2 pinjam Department saja", td("Produksi", "Finishing") == ("Finishing", "Peminjaman Department"))
    cek("T3 pinjam Grup saja", td("Produksi", None, "Gudang") == ("Gudang", "Peminjaman Grup"))
    cek("T4 keduanya sama: Department", td("Produksi", "Finishing", "Finishing") == ("Finishing", "Peminjaman Department"))
    cek("T5 beda, ikut Department", td("Produksi", "Finishing", "Gudang", "Department") == ("Finishing", "Peminjaman Department"))
    cek("T6 beda, ikut Grup", td("Produksi", "Finishing", "Gudang", "Grup") == ("Gudang", "Peminjaman Grup"))
    cek("T7 ikut kosong dianggap Department", td("Produksi", "Finishing", "Gudang", None) == ("Finishing", "Peminjaman Department"))
    cek("T8 tanpa Department sama sekali: None", td(None) == (None, "Department Karyawan"))

    # --- field baru ---
    f = frappe.get_meta("HRIS Employee").get_field("rule_follow")
    cek("M1 HRIS Employee.rule_follow ada, bawaan Department", bool(f) and f.default == "Department", str(f and f.default))
    f = frappe.get_meta("HRIS Working Hour").get_field("rule_department")
    cek("M2 HRIS Working Hour.rule_department ada dan hanya baca", bool(f) and _read_only(f), str(f and f.read_only))
    f = frappe.get_meta("HRIS Shift Assignment").get_field("borrowed_for_department")
    cek("M3 HRIS Shift Assignment.borrowed_for_department ada", bool(f) and f.options == "HRIS Department")

    # --- validasi Grup tanpa Department ---
    dept_uji = frappe.db.get_value("HRIS Department", {"is_group": 0}, "name") or frappe.db.get_value("HRIS Department", {}, "name")
    cek("D0 ada HRIS Department untuk uji", bool(dept_uji), str(dept_uji))

    # dokumen dibuat SEBELUM patch supaya pemuatan Meta memakai fungsi asli
    doc = frappe.new_doc("HRIS Shift Assignment")
    doc.borrowed_for_group = "GRUP-PALSU"
    asli = frappe.db.get_value

    def palsu(*a, **k):
        dt = a[0] if a else k.get("doctype")
        if dt == "HRIS Employee Group":
            return frappe._dict(is_active=1, department=None)
        return asli(*a, **k)

    frappe.db.get_value = palsu
    try:
        try:
            doc.validate_borrowed_group()
            cek("V1 Grup tanpa Department ditolak", False)
        except frappe.ValidationError as e:
            cek("V1 Grup tanpa Department ditolak", "belum punya Department" in str(e), str(e)[:80])
        doc.borrowed_for_department = dept_uji
        try:
            doc.validate_borrowed_group()
            cek("V2 lolos bila Department tujuan diisi", True)
        except frappe.ValidationError as e:
            cek("V2 lolos bila Department tujuan diisi", False, str(e)[:80])
    finally:
        frappe.db.get_value = asli

    # --- jadwal membawa Department tujuan ---
    emp = frappe.get_all("Employee", filters={"status": "Active"}, fields=["name", "company"], limit=1)
    shift = frappe.get_all("HRIS Shift", filters={"is_active": 1, "company": emp[0].company}, pluck="name", limit=1) if emp else []
    if not (emp and shift and dept_uji):
        print("INFO  tidak ada Employee aktif, Shift sepadan, atau Department; uji jadwal dilewati")
    else:
        frappe.db.savepoint("uji_p9")
        try:
            frappe.get_doc({
                "doctype": "HRIS Shift Assignment", "employee": emp[0].name, "from_date": "2099-01-05",
                "to_date": "2099-01-05", "shift": shift[0], "reason": "uji P9 tahap 1", "is_active": 1,
                "borrowed_for_department": dept_uji,
            }).insert(ignore_permissions=True)
            hasil = get_schedule_for_date(emp[0].name, "2099-01-05")
            cek("J1 jadwal membawa Department tujuan", hasil.get("borrowed_for_department") == dept_uji, str(hasil.get("borrowed_for_department")))
            cek("J2 sumber jadwal Shift Assignment", hasil.get("source") == "Shift Assignment", str(hasil.get("source")))
        except Exception as e:  # noqa: BLE001
            cek("J1 jadwal membawa Department tujuan", False, repr(e)[:200])
        finally:
            frappe.db.rollback(save_point="uji_p9")
        sisa = frappe.db.count("HRIS Shift Assignment", {"from_date": "2099-01-05"})
        cek("J3 uji bersih (rollback)", sisa == 0, str(sisa))

    print("HASIL: OK %d, GAGAL %d" % (len(ok), len(gagal)))
