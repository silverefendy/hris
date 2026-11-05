import frappe


def _company():
    return frappe.db.get_value("Company", {}, "name")


def _buat(**kw):
    data = {
        "doctype": "HRIS Employee",
        "employee_name": "Uji Karyawan",
        "company": _company(),
        "date_of_joining": "2026-01-01",
        "gender": "Laki-laki",
        "birth_date": "1990-01-01",
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


def _ditolak_wajib(fn):
    try:
        fn()
    except frappe.MandatoryError:
        return True
    except Exception:
        return False
    return False


def _ditolak_pesan(fn, teks):
    try:
        fn()
    except Exception as e:
        return teks in str(e)
    return False


def jalankan():
    hasil = []

    def cek(nama, kondisi):
        hasil.append((nama, bool(kondisi)))

    try:
        d1 = _buat(employee_name="Uji A")
        cek("1. simpan dengan data wajib, nama HRE-", d1.name.startswith("HRE-"))

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
        cek(
            "14. gender kosong ditolak (wajib)",
            _ditolak_wajib(lambda: _buat(employee_name="Uji J", gender="")),
        )
        cek(
            "15. tanggal lahir kosong ditolak (wajib)",
            _ditolak_wajib(lambda: _buat(employee_name="Uji K", birth_date="")),
        )
        d16 = _buat(employee_name="Uji L", gender="Tidak Disebutkan")
        cek("16. gender Tidak Disebutkan diterima", d16.gender == "Tidak Disebutkan")

        a1 = _buat(employee_name="Uji M", attendance_device_id="ZZ-UJI-1")
        cek("17. ID finger tersimpan", a1.attendance_device_id == "ZZ-UJI-1")
        cek(
            "18. ID finger sama pada karyawan Aktif ditolak",
            _ditolak_pesan(
                lambda: _buat(employee_name="Uji N", attendance_device_id="ZZ-UJI-1"),
                "ID Finger",
            ),
        )
        cek(
            "19. ID finger sama dengan spasi tetap ditolak",
            _ditolak_pesan(
                lambda: _buat(employee_name="Uji O", attendance_device_id=" ZZ-UJI-1 "),
                "ID Finger",
            ),
        )
        r1 = _buat(
            employee_name="Uji P",
            attendance_device_id="ZZ-UJI-2",
            status="Resign",
            resign_date="2026-06-01",
        )
        r2 = _buat(employee_name="Uji Q", attendance_device_id="ZZ-UJI-2")
        cek(
            "20. ID finger sama dengan karyawan Resign diterima",
            r1.status == "Resign" and r2.attendance_device_id == "ZZ-UJI-2",
        )
        a1.save(ignore_permissions=True)
        cek(
            "21. simpan ulang dokumen sendiri tidak dianggap ganda",
            a1.attendance_device_id == "ZZ-UJI-1",
        )
        r1.status = "Aktif"
        cek(
            "22. mengaktifkan kembali dengan ID yang sudah dipakai ditolak",
            _ditolak_pesan(lambda: r1.save(ignore_permissions=True), "ID Finger"),
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
