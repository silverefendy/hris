import frappe

from hris.hris_employee_data.services import employee_sync


def _company():
    return frappe.db.get_value("Company", {}, "name")


def _buat(**kw):
    skip = kw.pop("skip_sync", False)
    data = {
        "doctype": "HRIS Employee",
        "employee_name": "Uji Sinkron",
        "company": _company(),
        "date_of_joining": "2024-01-01",
        "gender": "Laki-laki",
        "birth_date": "1990-01-01",
    }
    data.update(kw)
    doc = frappe.get_doc(data)
    if skip:
        doc.flags.skip_sync = True
    doc.insert(ignore_permissions=True)
    return doc


def _hris(nama, field):
    return frappe.db.get_value("HRIS Employee", nama, field)


def _emp(nama, field):
    if not nama:
        return None
    return frappe.db.get_value("Employee", nama, field)


def _simpan(doc, **kw):
    doc.reload()
    doc.update(kw)
    doc.save(ignore_permissions=True)


def jalankan():
    if not frappe.local.site.endswith(".local"):
        raise SystemExit("GAGAL: uji ini hanya untuk site uji (*.local).")
    hasil = []

    def cek(nama, kondisi):
        hasil.append((nama, bool(kondisi)))

    try:
        cek(
            "1. pemetaan cocok dengan Employee ERPNext",
            employee_sync.periksa_pemetaan() == [],
        )

        a = _buat(employee_name="Uji Sinkron A", attendance_device_id="ZZ-SYNC-1")
        emp_a = _hris(a.name, "erpnext_employee")
        cek(
            "2. simpan baru: status Berhasil dan Employee dibuat",
            _hris(a.name, "sync_status") == "Berhasil"
            and emp_a
            and frappe.db.exists("Employee", emp_a),
        )
        cek(
            "3. field terpetakan benar",
            _emp(emp_a, "first_name") == "Uji Sinkron A"
            and _emp(emp_a, "gender") == "Male"
            and str(_emp(emp_a, "date_of_birth")) == "1990-01-01"
            and _emp(emp_a, "status") == "Active"
            and _emp(emp_a, "attendance_device_id") == "ZZ-SYNC-1",
        )

        b = _buat(employee_name="Uji Sinkron B", gender="Perempuan")
        c = _buat(employee_name="Uji Sinkron C", gender="Tidak Disebutkan")
        cek(
            "4. gender Perempuan dan Tidak Disebutkan terpetakan",
            _emp(_hris(b.name, "erpnext_employee"), "gender") == "Female"
            and _emp(_hris(c.name, "erpnext_employee"), "gender") == "Prefer not to say",
        )

        _simpan(a, phone="081234567890")
        cek("5. perubahan HRIS ikut ke Employee", _emp(emp_a, "cell_number") == "081234567890")

        cek(
            "6. sinkron tanpa perubahan melapor Tidak ada perubahan",
            employee_sync.sinkron_employee(a.name) == "Tidak ada perubahan",
        )

        frappe.db.set_value("Employee", emp_a, "personal_email", "uji@example.com")
        employee_sync.sinkron_employee(a.name)
        cek(
            "7. nilai kosong di HRIS tidak menimpa Employee",
            _emp(emp_a, "personal_email") == "uji@example.com",
        )

        _simpan(a, status="Resign", resign_date="2026-06-01")
        cek(
            "8. Resign menjadi Left dengan tanggal keluar",
            _emp(emp_a, "status") == "Left"
            and str(_emp(emp_a, "relieving_date")) == "2026-06-01",
        )

        _simpan(a, status="Aktif")
        cek(
            "9. kembali Aktif: Active dan tanggal keluar kosong",
            _emp(emp_a, "status") == "Active" and not _emp(emp_a, "relieving_date"),
        )

        d = _buat(
            employee_name="Uji Sinkron D",
            bank_account_number="123456789",
            ktp_number="2222222222222222",
        )
        emp_d = _hris(d.name, "erpnext_employee")
        cek(
            "10. Data Sensitif tidak ikut ke Employee",
            emp_d and not _emp(emp_d, "bank_ac_no"),
        )

        frappe.db.set_value("Employee", emp_a, "last_name", "Tambahan")
        employee_sync.sinkron_employee(a.name)
        cek(
            "11. last_name dikosongkan agar nama tidak ganda",
            not _emp(emp_a, "last_name") and _emp(emp_a, "employee_name") == "Uji Sinkron A",
        )

        awal = len(frappe.local.message_log)
        e = _buat(
            employee_name="Uji Sinkron E",
            birth_date="2000-01-01",
            date_of_joining="1999-01-01",
        )
        cek(
            "12. galat sinkron: HRIS tersimpan, status Gagal, ada pesan",
            frappe.db.exists("HRIS Employee", e.name)
            and _hris(e.name, "sync_status") == "Gagal"
            and _hris(e.name, "sync_error")
            and not _hris(e.name, "erpnext_employee"),
        )
        cek("13. galat sinkron tidak memunculkan popup", len(frappe.local.message_log) == awal)

        frappe.db.set_value("HRIS Employee", e.name, "date_of_joining", "2024-01-01")
        employee_sync.sinkron_employee(e.name)
        cek(
            "14. setelah data diperbaiki, Sinkron Ulang berhasil",
            _hris(e.name, "sync_status") == "Berhasil" and _hris(e.name, "erpnext_employee"),
        )

        frappe.db.delete("Employee", {"name": emp_d})
        hasil_hapus = employee_sync.sinkron_employee(d.name)
        cek(
            "15. Employee tertaut hilang: Gagal dan tidak dibuat ulang",
            hasil_hapus.startswith("Gagal")
            and _hris(d.name, "erpnext_employee") == emp_d
            and _hris(d.name, "sync_status") == "Gagal",
        )

        versi = frappe.get_all(
            "Version",
            filters={"ref_doctype": "HRIS Employee", "docname": a.name},
            pluck="data",
        )
        medan = ("sync_status", "last_sync", "sync_error", "erpnext_employee")
        bocor = [v for v in versi if any(f in v for f in medan)]
        cek("16. Audit Trail tidak memuat perubahan field sinkron", versi and not bocor)

        f = _buat(employee_name="Uji Sinkron F", skip_sync=True)
        cek(
            "17. bendera skip_sync melewati sinkron",
            not _hris(f.name, "erpnext_employee") and not _hris(f.name, "sync_status"),
        )
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
