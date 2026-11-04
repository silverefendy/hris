import frappe


def _company():
    return frappe.db.get_value("Company", {}, "name")


def _buat(**kw):
    data = {
        "doctype": "HRIS Employee",
        "employee_name": "Uji Karyawan",
        "company": _company(),
        "date_of_joining": "2026-01-01",
    }
    data.update(kw)
    doc = frappe.get_doc(data)
    doc.insert(ignore_permissions=True)
    return doc


def _ditolak(fn):
    try:
        fn()
    except Exception:
        return True
    return False


def jalankan():
    hasil = []

    def cek(nama, kondisi):
        hasil.append((nama, bool(kondisi)))

    try:
        d1 = _buat(employee_name="Uji A")
        cek("1. simpan minimal, nama HRE-", d1.name.startswith("HRE-"))

        d2 = _buat(employee_name="Uji B")
        d3 = _buat(employee_name="Uji C")
        cek("2. dua KTP kosong sama-sama diterima", d2.name != d3.name)

        d4 = _buat(employee_name="Uji D", ktp_number="1111111111111111")
        cek("3. KTP 16 digit diterima", d4.ktp_number == "1111111111111111")

        cek(
            "4. KTP ganda ditolak",
            _ditolak(lambda: _buat(employee_name="Uji E", ktp_number="1111111111111111")),
        )
        cek("5. KTP 15 digit ditolak", _ditolak(lambda: _buat(employee_name="Uji F", ktp_number="111111111111111")))
        cek("6. KTP berisi huruf ditolak", _ditolak(lambda: _buat(employee_name="Uji G", ktp_number="11111111111111ab")))
        cek("7. Resign tanpa tanggal ditolak", _ditolak(lambda: _buat(employee_name="Uji H", status="Resign")))
        cek(
            "8. akhir kontrak sebelum gabung ditolak",
            _ditolak(lambda: _buat(employee_name="Uji I", contract_end_date="2025-01-01")),
        )

        meta = frappe.get_meta("HRIS Employee")
        sensitif = ["ktp_number", "npwp", "bpjs_tk_no", "bpjs_kes_no", "bank_name", "bank_account_holder", "bank_account_number"]
        cek("9. 7 field sensitif ada di permlevel 1", all(meta.get_field(f).permlevel == 1 for f in sensitif))
        cek("10. nama dan foto di permlevel 0", meta.get_field("employee_name").permlevel == 0 and meta.get_field("image").permlevel == 0)

        role_level1 = {p.role for p in meta.permissions if p.permlevel == 1}
        cek("11. HR User tidak punya izin level 1", "HR User" not in role_level1)
        cek("12. Payroll Admin dan Manager punya level 1", {"HRIS Payroll Admin", "HRIS Payroll Manager"} <= role_level1)
        cek("13. role Payroll Manager ada", frappe.db.exists("Role", "HRIS Payroll Manager"))
    finally:
        frappe.db.rollback()

    gagal = 0
    for nama, ok in hasil:
        print(("OK     " if ok else "GAGAL  ") + nama)
        if not ok:
            gagal += 1
    ringkas = "TOTAL: %d OK, GAGAL %d" % (len(hasil) - gagal, gagal)
    print(ringkas)
    return ringkas
