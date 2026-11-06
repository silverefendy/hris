"""Uji K-102: logika pemetaan dan pembanding. Hanya baca, tidak menulis database.

bench --site hris-uji.local execute hris.hris_employee_data.uji_k102.periksa
"""

from datetime import date

import frappe

from hris.hris_employee_data.services import migrasi_employee as m

hasil = []


def _catat(nama, lulus, info=""):
    hasil.append(bool(lulus))
    print(("OK     " if lulus else "GAGAL  ") + nama + ((" | " + info) if info else ""))


def _emp(**kw):
    isi = {
        "name": "HR-EMP-ZZ1",
        "employee_name": "Uji Satu",
        "first_name": "Uji Satu",
        "last_name": None,
        "date_of_birth": date(1990, 5, 10),
        "gender": "Male",
        "company": "PT Uji",
        "branch": None,
        "department": None,
        "hris_employee_group": None,
        "hris_payroll_code": None,
        "attendance_device_id": "ZZ-K102-1",
        "date_of_joining": date(2020, 1, 1),
        "contract_end_date": None,
        "cell_number": None,
        "personal_email": None,
        "current_address": None,
        "status": "Active",
        "relieving_date": None,
        "marital_status": None,
        "hris_data_status": None,
        "hris_data_note": None,
        "reports_to": None,
    }
    isi.update(kw)
    return frappe._dict(isi)


def _ada(teks, daftar):
    return any(teks in x for x in daftar)


def periksa():
    hasil.clear()
    perusahaan = frappe.get_all("Company", pluck="name", limit=1)[0]

    nilai, p = m.petakan(_emp(company=perusahaan))
    _catat(
        "M1 Employee Active normal terpetakan tanpa masalah",
        not p
        and nilai["status"] == "Aktif"
        and nilai["gender"] == "Laki-laki"
        and nilai["sync_status"] == "Belum Disinkron"
        and nilai["erpnext_employee"] == "HR-EMP-ZZ1"
        and nilai["resign_date"] is None,
        repr(p),
    )

    nilai, p = m.petakan(_emp(status="Left", relieving_date=date(2026, 10, 31)))
    _catat(
        "M2 Left menjadi Resign dengan tanggal resign",
        not p and nilai["status"] == "Resign" and nilai["resign_date"] == date(2026, 10, 31),
        repr(p),
    )

    _, p = m.petakan(_emp(gender="Other"))
    _catat("M3 gender tak dikenal dilaporkan", _ada("gender", p), repr(p))

    _, p = m.petakan(_emp(status="Inactive"))
    _catat("M4 status Inactive dilaporkan", _ada("status tak dikenal", p), repr(p))

    n1, p1 = m.petakan(_emp(marital_status="Single"))
    n2, p2 = m.petakan(_emp(marital_status="Widowed"))
    n3, p3 = m.petakan(_emp(marital_status=None))
    _catat(
        "M5 status perkawinan: Single, Widowed, kosong",
        not (p1 or p2 or p3)
        and n1["marital_status"] == "Belum Menikah"
        and n2["marital_status"] == "Cerai Mati"
        and n3["marital_status"] is None,
    )

    _, p = m.petakan(_emp(marital_status="Aneh"))
    _catat("M6 status perkawinan tak dikenal dilaporkan", _ada("perkawinan", p), repr(p))

    n1, p1 = m.petakan(_emp(hris_data_status=None))
    n2, p2 = m.petakan(_emp(hris_data_status="Lengkap"))
    _catat(
        "M7 data_status kosong dan Lengkap diterima",
        not (p1 or p2) and n1["data_status"] is None and n2["data_status"] == "Lengkap",
    )

    _, p = m.petakan(_emp(hris_data_status="Aneh"))
    _catat("M8 data_status tak dikenal dilaporkan", _ada("hris_data_status", p), repr(p))

    nilai, _ = m.petakan(_emp(company=perusahaan, status="Left", relieving_date=None))
    galat = m.coba_validasi(nilai)
    _catat(
        "M9 Left tanpa tanggal ditolak validasi HRIS",
        bool(galat) and "Tanggal Resign" in galat,
        galat or "TIDAK ditolak",
    )

    pemegang = frappe.db.get_value(
        "Employee",
        {"attendance_device_id": ["!=", ""]},
        ["name", "attendance_device_id"],
        as_dict=True,
    )
    if pemegang:
        nilai, _ = m.petakan(
            _emp(
                company=perusahaan,
                name=pemegang.name,
                attendance_device_id=pemegang.attendance_device_id,
            )
        )
        galat = m.coba_validasi(nilai)
        _catat("M10 ID Finger milik Employee tertaut diterima", galat is None, galat or "")
        nilai["erpnext_employee"] = "HR-EMP-ZZ-LAIN"
        galat = m.coba_validasi(nilai)
        _catat(
            "M11 ID Finger milik Employee lain ditolak",
            bool(galat) and pemegang.name in galat,
            galat or "TIDAK ditolak",
        )
    else:
        _catat("M10/M11 butuh Employee ber-ID Finger", False, "tidak ada data")

    emp = _emp(company=perusahaan, first_name="Uji", last_name="Satu", employee_name="Uji Satu")
    nilai, _ = m.petakan(emp)
    beda = m.hitung_selisih(frappe._dict(nilai), emp)
    _catat("S1 nama terpisah first/last tidak dianggap selisih", beda == {}, repr(beda))

    emp2 = _emp(company=perusahaan, department="Dept-A")
    nilai, _ = m.petakan(emp2)
    nilai["department"] = "Dept-B"
    beda = m.hitung_selisih(frappe._dict(nilai), emp2)
    _catat("S2 selisih department terdeteksi", set(beda) == {"department"}, repr(beda))

    emp3 = _emp(company=perusahaan, hris_data_status="Perlu Dilengkapi")
    nilai, _ = m.petakan(emp3)
    nilai["data_status"] = "Lengkap"
    beda = m.hitung_selisih(frappe._dict(nilai), emp3)
    _catat("S3 selisih data_status terdeteksi", set(beda) == {"data_status"}, repr(beda))

    gagal = hasil.count(False)
    ringkas = "%d OK, %d GAGAL" % (len(hasil) - gagal, gagal)
    print("\n" + ringkas)
    return ringkas
