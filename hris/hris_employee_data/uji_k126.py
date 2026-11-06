"""Uji K-126: validasi tanggal dan ID Finger HRIS Employee. Semua di-rollback.

Jalankan:
bench --site hris-uji.local execute hris.hris_employee_data.uji_k126.periksa
"""

import frappe
from frappe.utils import strip_html

hasil = []


def _catat(nama, lulus, info=""):
    hasil.append(bool(lulus))
    print(("OK     " if lulus else "GAGAL  ") + nama + ((" | " + info) if info else ""))


def _buat(perusahaan, **kw):
    isi = {
        "doctype": "HRIS Employee",
        "employee_name": "ZZ Uji K126",
        "birth_date": "1990-05-10",
        "gender": "Laki-laki",
        "company": perusahaan,
        "date_of_joining": "2020-01-01",
        "status": "Aktif",
    }
    isi.update(kw)
    doc = frappe.get_doc(isi)
    doc.flags.skip_sync = True  # hanya uji validasi, jangan buat Employee ERPNext
    doc.insert(ignore_permissions=True)
    return doc


def _harus_ditolak(nama, fungsi, kata_kunci):
    try:
        fungsi()
    except frappe.ValidationError as e:
        pesan = strip_html(str(e))
        _catat(nama, kata_kunci.lower() in pesan.lower(), pesan[:120])
    except Exception as e:  # noqa: BLE001
        _catat(nama, False, "galat lain: " + repr(e)[:120])
    else:
        _catat(nama, False, "TIDAK ditolak")


def _harus_lolos(nama, fungsi):
    try:
        fungsi()
    except Exception as e:  # noqa: BLE001
        _catat(nama, False, "ditolak: " + strip_html(str(e))[:120])
    else:
        _catat(nama, True)


def periksa():
    hasil.clear()
    perusahaan = frappe.get_all("Company", pluck="name", limit=1)[0]
    pemegang = frappe.db.get_value(
        "Employee",
        {"attendance_device_id": ["!=", ""]},
        ["name", "attendance_device_id"],
        as_dict=True,
    )
    if not pemegang:
        print("GAGAL  tidak ada Employee ber-ID Finger di site ini, uji V2 tidak bisa jalan")
        return "batal"

    try:
        # V1: tanggal
        _harus_ditolak(
            "V1-1 gabung sebelum lahir ditolak",
            lambda: _buat(perusahaan, birth_date="1990-05-10", date_of_joining="1989-01-01"),
            "Tanggal Bergabung",
        )
        _harus_ditolak(
            "V1-2 gabung sama dengan lahir ditolak",
            lambda: _buat(perusahaan, birth_date="1990-05-10", date_of_joining="1990-05-10"),
            "Tanggal Bergabung",
        )
        _harus_lolos(
            "V1-3 gabung setelah lahir diterima",
            lambda: _buat(perusahaan, birth_date="1990-05-10", date_of_joining="2020-01-01"),
        )

        # V2: ID Finger terhadap Employee ERPNext
        _harus_ditolak(
            "V2-1 ID milik Employee lain (tak tertaut) ditolak",
            lambda: _buat(perusahaan, attendance_device_id=pemegang.attendance_device_id),
            pemegang.name,
        )
        _harus_lolos(
            "V2-2 ID milik Employee yang tertaut diterima (jalur migrasi)",
            lambda: _buat(
                perusahaan,
                attendance_device_id=pemegang.attendance_device_id,
                erpnext_employee=pemegang.name,
            ),
        )
        _harus_lolos(
            "V2-3 ID baru yang unik diterima",
            lambda: _buat(perusahaan, attendance_device_id="ZZ-K126-UNIK"),
        )
        _harus_ditolak(
            "V2-4 status Resign tetap diperiksa ke Employee ERPNext",
            lambda: _buat(
                perusahaan,
                status="Resign",
                resign_date="2026-10-31",
                attendance_device_id=pemegang.attendance_device_id,
            ),
            pemegang.name,
        )

        # Aturan lama tetap jalan
        _buat(perusahaan, attendance_device_id="ZZ-K126-DUA")
        _harus_ditolak(
            "Lama-1 ID sama antar HRIS Aktif tetap ditolak",
            lambda: _buat(perusahaan, attendance_device_id="ZZ-K126-DUA"),
            "yang masih Aktif",
        )
    finally:
        frappe.db.rollback()
        frappe.local.message_log = []

    gagal = hasil.count(False)
    ringkas = "%d OK, %d GAGAL" % (len(hasil) - gagal, gagal)
    print("\n" + ringkas)
    return ringkas


def periksa_resign():
    """Uji V1b. Jalankan:
    bench --site hris-uji.local execute hris.hris_employee_data.uji_k126.periksa_resign
    """
    hasil.clear()
    perusahaan = frappe.get_all("Company", pluck="name", limit=1)[0]
    try:
        _harus_ditolak(
            "V1b-1 resign sebelum gabung ditolak",
            lambda: _buat(
                perusahaan,
                status="Resign",
                date_of_joining="2020-01-01",
                resign_date="2019-12-31",
            ),
            "Tanggal Resign",
        )
        _harus_lolos(
            "V1b-2 resign setelah gabung diterima",
            lambda: _buat(
                perusahaan,
                status="Resign",
                date_of_joining="2020-01-01",
                resign_date="2020-06-01",
            ),
        )
        _harus_lolos(
            "V1b-3 Aktif dengan sisa resign_date lama tidak ditolak (dikosongkan)",
            lambda: _buat(
                perusahaan,
                status="Aktif",
                date_of_joining="2020-01-01",
                resign_date="2019-12-31",
            ),
        )
        doc = _buat(perusahaan, status="Aktif", date_of_joining="2020-01-01")
        _catat("V1b-4 Aktif tanpa resign tetap diterima", bool(doc.name))
    finally:
        frappe.db.rollback()
        frappe.local.message_log = []

    gagal = hasil.count(False)
    ringkas = "%d OK, %d GAGAL" % (len(hasil) - gagal, gagal)
    print("\n" + ringkas)
    return ringkas
