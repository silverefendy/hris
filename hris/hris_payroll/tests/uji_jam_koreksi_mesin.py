"""Uji C4 tahap 5 (mesin hitung): jam koreksi dan tinjauan di calculate_working_hour. Semua perubahan di-rollback.
  bench --site hris-uji.local execute hris.hris_payroll.tests.uji_jam_koreksi_mesin.jalankan
"""
from datetime import datetime

import frappe
from frappe.utils import get_time, getdate

from hris.hris_attendance.services.working_hour import calculate_working_hour
from hris.hris_payroll.services.period_lock import is_locked

WH = "HRIS Working Hour"
SITE = "hris-uji.local"
KOLOM = ["status", "review_status", "check_in", "check_out", "manual_check_in", "manual_check_out",
         "review_reason", "needs_review"]


class _Cek:
    def __init__(self):
        self.ok = 0
        self.total = 0

    def __call__(self, nama, kondisi, detail=""):
        self.total += 1
        if kondisi:
            self.ok += 1
            print("OK    %s" % nama)
        else:
            print("GAGAL %s | %s" % (nama, detail))


def _mulai(doc):
    return datetime.combine(getdate(doc.work_date), get_time(doc.shift_start))


def _baca(n):
    return frappe.db.get_value(WH, n, KOLOM, as_dict=True)


def _bebas(emp, day):
    try:
        return not is_locked(emp, day)
    except Exception:
        return False


def _kandidat_pulang_saja():
    for r in frappe.get_all(
        WH,
        filters={"status": "Tidak Lengkap", "review_status": "Menunggu",
                 "check_in": ["is", "not set"], "check_out": ["is", "set"]},
        fields=["name", "employee", "work_date", "shift_start"], limit=40,
    ):
        if r.shift_start and _bebas(r.employee, r.work_date):
            return frappe.get_doc(WH, r.name)
    return None


def _kandidat_hadir():
    for r in frappe.get_all(
        WH,
        filters={"status": "Hadir", "check_in": ["is", "set"], "check_out": ["is", "set"]},
        fields=["name", "employee", "work_date", "shift_start"], limit=40,
    ):
        if r.shift_start and _bebas(r.employee, r.work_date):
            return frappe.get_doc(WH, r.name)
    return None


def jalankan():
    if frappe.local.site != SITE:
        print("Site bukan %s; berhenti." % SITE)
        return
    cek = _Cek()
    meta = frappe.get_meta(WH)
    ada = meta.has_field("manual_check_in") and meta.has_field("manual_check_out")
    cek("M0 field jam koreksi ada", ada, "jalankan migrate situs uji dulu")
    if ada:
        try:
            doc = _kandidat_pulang_saja()
            if not doc:
                print("Tidak ada dokumen Tidak Lengkap (hanya pulang, Menunggu) yang bisa dipakai.")
            else:
                n = doc.name
                mulai = _mulai(doc)
                doc.manual_check_in = mulai
                doc.review_note = "Lupa tap masuk (data uji)"
                doc.save()
                calculate_working_hour(doc.employee, getdate(doc.work_date))
                d = _baca(n)
                cek("M1 jam koreksi masuk: hari dihitung Hadir", d.status == "Hadir", str(d))
                cek("M2 check_in sama dengan jam koreksi", d.check_in == mulai, str(d))
                cek("M3 tinjauan dipertahankan (Sudah Ditinjau)", d.review_status == "Sudah Ditinjau", str(d))
                cek("M4 jam koreksi tersimpan dan alasan menyebut dikoreksi",
                    d.manual_check_in == mulai and "dikoreksi" in (d.review_reason or ""), str(d))
                teks = " ".join((v.data or "") for v in frappe.get_all(
                    "Version", filters={"ref_doctype": WH, "docname": n}, fields=["data"]))
                cek("M5 riwayat perubahan memuat jam koreksi dan status hasil hitung",
                    '"manual_check_in"' in teks and '"status"' in teks,
                    "Version tidak memuat keduanya; bila Audit Trail bukan berbasis Version, cek lewat browser (U7)")

                frappe.db.set_value(WH, n, {"manual_check_in": None, "manual_check_out": None}, update_modified=False)
                calculate_working_hour(doc.employee, getdate(doc.work_date))
                d = _baca(n)
                cek("M6 jam koreksi dikosongkan: kembali Tidak Lengkap dan Menunggu",
                    d.status == "Tidak Lengkap" and d.review_status == "Menunggu", str(d))

            h = _kandidat_hadir()
            if not h:
                print("Tidak ada dokumen Hadir yang bisa dipakai untuk uji opsi A.")
            else:
                n2 = h.name
                mulai2 = _mulai(h)
                # Opsi A: punch asli lengkap, jam koreksi tersimpan, data tersimpan usang (status beda)
                frappe.db.set_value(
                    WH, n2,
                    {"manual_check_in": mulai2, "review_status": "Sudah Ditinjau", "status": "Tidak Lengkap"},
                    update_modified=False,
                )
                calculate_working_hour(h.employee, getdate(h.work_date))
                d = _baca(n2)
                cek("M7 opsi A: punch asli lengkap, hari dihitung dari punch asli (Hadir)", d.status == "Hadir", str(d))
                cek("M8 opsi A: alasan 'diabaikan' tampil dan tinjauan tetap Sudah Ditinjau",
                    "diabaikan" in (d.review_reason or "") and d.review_status == "Sudah Ditinjau", str(d))
                cek("M9 opsi A: jam koreksi tetap tersimpan", d.manual_check_in == mulai2, str(d))
        finally:
            frappe.db.rollback()
    print("Lulus %d dari %d" % (cek.ok, cek.total))
