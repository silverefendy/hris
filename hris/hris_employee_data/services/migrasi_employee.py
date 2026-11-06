"""Migrasi sekali jalan K-102: Employee ERPNext -> HRIS Employee.

Semua perintah dijalankan dengan bench --site <nama> execute ...
  dry_run     baca saja, tidak menulis apa pun
  migrasi     menulis semua atau tidak sama sekali; wajib konfirmasi nama site
  verifikasi  membandingkan HRIS Employee dengan Employee ERPNext

Sinkron otomatis dimatikan selama migrasi (flags.skip_sync), sehingga Employee
ERPNext tidak disentuh sama sekali.
"""

import time
from collections import Counter

import frappe
from frappe.utils import cstr, now_datetime, strip_html

from hris.hris_employee_data.services.employee_sync import (
    GENDER,
    PERKAWINAN,
    STATUS,
    bangun_nilai,
)

GENDER_BALIK = {v: k for k, v in GENDER.items()}
STATUS_BALIK = {v: k for k, v in STATUS.items()}
PERKAWINAN_BALIK = {v: k for k, v in PERKAWINAN.items()}
DATA_STATUS_SAH = ("", "Lengkap", "Perlu Dilengkapi")
TAMPIL_MAKS = 30

FIELD_EMPLOYEE = [
    "name", "employee_name", "date_of_birth", "gender", "company", "branch",
    "department", "hris_employee_group", "hris_payroll_code", "attendance_device_id",
    "date_of_joining", "contract_end_date", "cell_number", "personal_email",
    "current_address", "status", "relieving_date", "marital_status",
    "hris_data_status", "hris_data_note", "reports_to",
]


def petakan(e):
    """Satu baris Employee -> (nilai HRIS Employee, daftar masalah). Fungsi murni."""
    masalah = []

    gender = GENDER_BALIK.get(e.get("gender"))
    if not gender:
        masalah.append("gender tak dikenal: %r" % (e.get("gender"),))

    status = STATUS_BALIK.get(e.get("status"))
    if not status:
        masalah.append("status tak dikenal: %r" % (e.get("status"),))

    kawin = None
    if e.get("marital_status"):
        kawin = PERKAWINAN_BALIK.get(e.get("marital_status"))
        if not kawin:
            masalah.append("status perkawinan tak dikenal: %r" % (e.get("marital_status"),))

    data_status = e.get("hris_data_status") or ""
    if data_status not in DATA_STATUS_SAH:
        masalah.append("hris_data_status tak dikenal: %r" % (data_status,))

    nilai = {
        "doctype": "HRIS Employee",
        "employee_name": e.get("employee_name"),
        "birth_date": e.get("date_of_birth"),
        "gender": gender,
        "company": e.get("company"),
        "branch": e.get("branch"),
        "department": e.get("department"),
        "employee_group": e.get("hris_employee_group"),
        "legacy_payroll_code": e.get("hris_payroll_code"),
        "attendance_device_id": e.get("attendance_device_id"),
        "date_of_joining": e.get("date_of_joining"),
        "contract_end_date": e.get("contract_end_date"),
        "phone": e.get("cell_number"),
        "email": e.get("personal_email"),
        "address": e.get("current_address"),
        "status": status,
        "resign_date": e.get("relieving_date") if status == "Resign" else None,
        "marital_status": kawin,
        "data_status": data_status or None,
        "data_note": e.get("hris_data_note"),
        "erpnext_employee": e.get("name"),
        "sync_status": "Belum Disinkron",
    }
    return nilai, masalah


def coba_validasi(nilai):
    """Jalankan validate controller HRIS Employee tanpa menyimpan. Galat atau None."""
    jumlah = len(frappe.local.message_log)
    try:
        doc = frappe.get_doc(nilai)
        doc.flags.skip_sync = True
        doc.run_method("validate")
    except Exception as e:  # noqa: BLE001
        return strip_html(cstr(e))[:200]
    finally:
        frappe.local.message_log = frappe.local.message_log[:jumlah]
    return None


def hitung_selisih(doc, emp):
    """Selisih HRIS Employee (doc) terhadap Employee ERPNext (emp). Kosong = sama.

    Nama dibandingkan lewat employee_name (bukan first/middle/last), sebab sinkron
    menaruh nama lengkap di first_name.
    """
    nilai = bangun_nilai(doc)
    for k in ("first_name", "middle_name", "last_name"):
        nilai.pop(k, None)
    nilai["employee_name"] = doc.get("employee_name")
    hasil = {}
    for k, v in nilai.items():
        if cstr(emp.get(k)) != cstr(v):
            hasil[k] = (cstr(emp.get(k)), cstr(v))
    for hris, erp in (("data_status", "hris_data_status"), ("data_note", "hris_data_note")):
        if cstr(doc.get(hris)) != cstr(emp.get(erp)):
            hasil[hris] = (cstr(emp.get(erp)), cstr(doc.get(hris)))
    return hasil


def _field_siap():
    meta = frappe.get_meta("HRIS Employee")
    hilang = [f for f in ("data_status", "data_note") if not meta.has_field(f)]
    if hilang:
        print("BERHENTI: field %s belum ada. Jalankan skrip F lalu migrate." % ", ".join(hilang))
        return False
    return True


def siapkan():
    tertaut = set(
        frappe.get_all(
            "HRIS Employee",
            filters={"erpnext_employee": ["is", "set"]},
            pluck="erpnext_employee",
            limit_page_length=0,
        )
    )
    semua = frappe.get_all(
        "Employee", fields=FIELD_EMPLOYEE, order_by="name asc", limit_page_length=0
    )
    rencana, masalah, dilewati = [], [], 0
    for e in semua:
        if e["name"] in tertaut:
            dilewati += 1
            continue
        nilai, p = petakan(e)
        if not p:
            galat = coba_validasi(nilai)
            if galat:
                p.append("validasi: " + galat)
        if p:
            masalah.append((e["name"], "; ".join(p)))
        else:
            rencana.append((e["name"], nilai))
    return semua, rencana, masalah, dilewati


def _cetak_masalah(masalah):
    for nama, alasan in masalah[:TAMPIL_MAKS]:
        print("  MASALAH", nama, "|", alasan)
    if len(masalah) > TAMPIL_MAKS:
        print("  ... dan %d lainnya" % (len(masalah) - TAMPIL_MAKS))


def dry_run():
    if not _field_siap():
        return "berhenti"
    semua, rencana, masalah, dilewati = siapkan()
    print("Site                               :", frappe.local.site)
    print("Employee ERPNext                   :", len(semua))
    print("Sudah punya HRIS Employee (lewati) :", dilewati)
    print("Akan dibuat                        :", len(rencana))
    print("Bermasalah                         :", len(masalah))
    _cetak_masalah(masalah)
    for judul, kunci in (("Status", "status"), ("Gender", "gender"), ("data_status", "data_status")):
        print(judul, dict(Counter((n.get(kunci) or "(kosong)") for _, n in rencana)))
    atasan = {e.get("reports_to") for e in semua if e.get("reports_to")}
    punya = sum(1 for e in semua if e.get("reports_to"))
    print("Info: punya atasan (reports_to):", punya, "| menjadi atasan:", len(atasan))
    hasil = "SIAP" if not masalah else "TIDAK SIAP (%d masalah)" % len(masalah)
    print("\nHasil:", hasil)
    return hasil


def migrasi(konfirmasi=""):
    if konfirmasi != frappe.local.site:
        print("DITOLAK. Untuk menjalankan, tambahkan:")
        print("  --kwargs \"{'konfirmasi': '%s'}\"" % frappe.local.site)
        return "ditolak"
    if not _field_siap():
        return "berhenti"
    _, rencana, masalah, dilewati = siapkan()
    if masalah:
        print("BERHENTI: %d karyawan bermasalah, tidak ada yang ditulis." % len(masalah))
        _cetak_masalah(masalah)
        return "berhenti"
    dibuat = 0
    try:
        for nama, nilai in rencana:
            doc = frappe.get_doc(nilai)
            doc.flags.skip_sync = True
            doc.insert(ignore_permissions=True)
            dibuat += 1
    except Exception as e:  # noqa: BLE001
        frappe.db.rollback()
        frappe.local.message_log = []
        print("GAGAL pada %s: %s" % (nama, strip_html(cstr(e))[:200]))
        print("Semua dibatalkan (rollback). Dibuat sebelum gagal: %d, tersimpan: 0" % dibuat)
        return "gagal"
    frappe.db.commit()
    print("Dibuat: %d | dilewati (sudah tertaut): %d" % (dibuat, dilewati))
    print("Langkah berikut: verifikasi, lalu verifikasi dengan terapkan=1")
    return "selesai"


def verifikasi(terapkan=0, rinci=0):
    terapkan, rinci = int(terapkan), int(rinci)
    if not _field_siap():
        return "berhenti"
    tertaut = frappe.get_all(
        "HRIS Employee",
        filters={"erpnext_employee": ["is", "set"]},
        fields=["name", "erpnext_employee", "sync_status"],
        limit_page_length=0,
    )
    nama_tertaut = [t.erpnext_employee for t in tertaut]
    himpunan = set(nama_tertaut)
    ganda = [n for n, c in Counter(nama_tertaut).items() if c > 1]
    semua_emp = frappe.get_all("Employee", pluck="name", limit_page_length=0)
    belum = [n for n in semua_emp if n not in himpunan]

    selisih, galat, diubah = [], [], 0
    for t in tertaut:
        try:
            doc = frappe.get_doc("HRIS Employee", t.name)
            emp = frappe.get_doc("Employee", t.erpnext_employee)
            beda = hitung_selisih(doc, emp)
        except Exception as e:  # noqa: BLE001
            galat.append((t.name, strip_html(cstr(e))[:120]))
            frappe.local.message_log = []
            continue
        if beda:
            selisih.append((t.name, beda))
        elif terapkan and t.sync_status == "Belum Disinkron":
            frappe.db.set_value(
                "HRIS Employee",
                t.name,
                {"sync_status": "Berhasil", "last_sync": now_datetime(), "sync_error": None},
                update_modified=False,
            )
            diubah += 1
    if terapkan and not frappe.flags.get("hris_latih"):
        frappe.db.commit()

    print("Employee ERPNext                 :", len(semua_emp))
    print("HRIS Employee tertaut            :", len(tertaut))
    print("Employee tanpa HRIS Employee     :", len(belum), belum[:TAMPIL_MAKS])
    print("Tautan ganda ke satu Employee    :", len(ganda), ganda[:TAMPIL_MAKS])
    print("Isi berbeda                      :", len(selisih))
    for nama, beda in selisih[:TAMPIL_MAKS]:
        print("  SELISIH", nama, "|", beda if rinci else ", ".join(sorted(beda)))
    print("Galat baca                       :", len(galat))
    for nama, alasan in galat[:TAMPIL_MAKS]:
        print("  GALAT", nama, "|", alasan)
    if terapkan:
        print("Diubah ke Berhasil               :", diubah)
    sama = not (belum or ganda or selisih or galat)
    hasil = "SAMA" if sama else "ADA SELISIH"
    print("\nHasil:", hasil)
    return hasil


def latih(konfirmasi=""):
    """Latihan penuh: tulis semua, verifikasi (terapkan=1), lalu BATALKAN (rollback).

    Tidak meninggalkan data. Mengukur lama tulis untuk perkiraan di produksi.
    """
    if konfirmasi != frappe.local.site:
        print("DITOLAK. Untuk menjalankan, tambahkan:")
        print("  --kwargs \"{'konfirmasi': '%s'}\"" % frappe.local.site)
        return "ditolak"
    if not _field_siap():
        return "berhenti"
    _, rencana, masalah, dilewati = siapkan()
    if masalah:
        print("BERHENTI: %d karyawan bermasalah, tidak ada yang ditulis." % len(masalah))
        _cetak_masalah(masalah)
        return "berhenti"

    sebelum = frappe.db.count("HRIS Employee")
    frappe.flags.hris_latih = True
    hasil = "gagal"
    nama = "-"
    try:
        mulai = time.time()
        for nama, nilai in rencana:
            doc = frappe.get_doc(nilai)
            doc.flags.skip_sync = True
            doc.insert(ignore_permissions=True)
        print("Ditulis sementara: %d dokumen dalam %.1f detik" % (len(rencana), time.time() - mulai))
        mulai = time.time()
        hasil = verifikasi(terapkan=1)
        print("Verifikasi: %.1f detik" % (time.time() - mulai))
        berhasil = frappe.db.count("HRIS Employee", {"sync_status": "Berhasil"})
        belum = frappe.db.count("HRIS Employee", {"sync_status": "Belum Disinkron"})
        print("Dalam latihan: Berhasil=%d, Belum Disinkron=%d" % (berhasil, belum))
    except Exception as e:  # noqa: BLE001
        print("GAGAL pada %s: %s" % (nama, strip_html(cstr(e))[:200]))
    finally:
        frappe.db.rollback()
        frappe.flags.hris_latih = False
        frappe.local.message_log = []

    sesudah = frappe.db.count("HRIS Employee")
    print("HRIS Employee sebelum latihan: %d, sesudah rollback: %d" % (sebelum, sesudah))
    print("DIBATALKAN (rollback). Hasil latihan:", hasil)
    return hasil if sesudah == sebelum else "PERINGATAN: jumlah berubah setelah rollback"
