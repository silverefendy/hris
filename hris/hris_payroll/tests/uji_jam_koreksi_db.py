"""Uji C4 tahap 1 (controller): jam koreksi di HRIS Working Hour. Semua perubahan di-rollback.
  bench --site hris-uji.local execute hris.hris_payroll.tests.uji_jam_koreksi_db.jalankan
"""
from datetime import datetime, timedelta

import frappe
from frappe.utils import get_time, getdate

WH = "HRIS Working Hour"
SITE = "hris-uji.local"


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


def _tolak(fn, kata):
    try:
        fn()
    except frappe.ValidationError as e:
        return kata in str(e)
    return False


def _waktu(doc):
    mulai = datetime.combine(getdate(doc.work_date), get_time(doc.shift_start))
    selesai = mulai + timedelta(minutes=int(doc.scheduled_minutes or 0) + int(doc.break_minutes or 0))
    return mulai, selesai


def _baca(n):
    return frappe.db.get_value(
        WH, n, ["status", "review_status", "reviewed_by", "manual_check_in", "manual_check_out", "incomplete_outcome"], as_dict=True)


def jalankan():
    if frappe.local.site != SITE:
        print("Site bukan %s; berhenti." % SITE)
        return
    cek = _Cek()
    meta = frappe.get_meta(WH)
    ada = meta.has_field("manual_check_in") and meta.has_field("manual_check_out")
    cek("J0 field manual_check_in dan manual_check_out ada", ada, "jalankan migrate situs uji dulu")
    if not ada:
        print("Lulus %d dari %d" % (cek.ok, cek.total))
        return
    try:
        nama = None
        kandidat = [r.name for r in frappe.get_all(
            WH, filters={"status": "Tidak Lengkap", "review_status": "Menunggu", "check_in": ["is", "not set"], "check_out": ["is", "set"]},
            fields=["name"], limit=30)]
        for n in kandidat:
            doc = frappe.get_doc(WH, n)
            if not doc.shift_start:
                continue
            mulai, selesai = _waktu(doc)
            doc.manual_check_in = mulai
            doc.review_note = ""
            try:
                doc.save()
            except frappe.ValidationError as e:
                if "Catatan Tinjauan" in str(e):
                    nama = n
                    cek("J1 jam koreksi tanpa catatan ditolak", True)
                    break
                continue
            nama = n
            cek("J1 jam koreksi tanpa catatan ditolak", False, "tersimpan tanpa catatan")
            break
        if not nama:
            print("Tidak ada dokumen Tidak Lengkap (hanya pulang, Menunggu) yang bisa dipakai.")
            print("Lulus %d dari %d" % (cek.ok, cek.total))
            return

        doc = frappe.get_doc(WH, nama)
        mulai, selesai = _waktu(doc)
        doc.manual_check_in = mulai
        doc.review_note = "Lupa tap masuk (data uji)"
        doc.save()
        d = _baca(nama)
        cek("J2 jam koreksi dan catatan tersimpan, otomatis Sudah Ditinjau", d.review_status == "Sudah Ditinjau" and d.manual_check_in is not None, str(d))
        cek("J3 Ditinjau Oleh terisi", bool(d.reviewed_by), str(d))

        doc = frappe.get_doc(WH, nama)
        doc.manual_check_in = mulai - timedelta(hours=12)
        cek("J4 jam masuk di luar jendela ditolak", _tolak(doc.save, "Jam Masuk Koreksi"))

        doc = frappe.get_doc(WH, nama)
        doc.incomplete_outcome = "Dihitung Hadir"
        cek("J5 jam koreksi bersama hasil tinjauan ditolak", _tolak(doc.save, "salah satu"))

        doc = frappe.get_doc(WH, nama)
        doc.adjustment_hours = 1
        doc.adjustment_reason = "uji"
        cek("J6 Penyesuaian bersama jam koreksi ditolak", _tolak(doc.save, "Penyesuaian"))

        doc = frappe.get_doc(WH, nama)
        doc.manual_check_out = selesai + timedelta(hours=1)
        cek("J7 jam pulang melewati akhir shift ditolak (lembur)", _tolak(doc.save, "lembur"))

        hasil8 = None
        for r in frappe.get_all(WH, filters={"status": "Hadir"}, fields=["name"], limit=20):
            d8 = frappe.get_doc(WH, r.name)
            if not d8.shift_start:
                continue
            m8, _s8 = _waktu(d8)
            d8.manual_check_in = m8
            d8.review_note = "uji"
            try:
                d8.save()
                hasil8 = False
                break
            except frappe.ValidationError as e:
                if "hanya untuk hari berstatus" in str(e):
                    hasil8 = True
                    break
        cek("J8 hari Hadir: jam koreksi ditolak", hasil8 is True, str(hasil8))

        doc = frappe.get_doc(WH, nama)
        doc.manual_check_in = None
        doc.manual_check_out = None
        doc.review_status = "Menunggu"
        doc.save()
        d = _baca(nama)
        cek("J9 jam koreksi dikosongkan dan kembali Menunggu", d.manual_check_in is None and d.review_status == "Menunggu", str(d))
    finally:
        frappe.db.rollback()
    print("Lulus %d dari %d" % (cek.ok, cek.total))
