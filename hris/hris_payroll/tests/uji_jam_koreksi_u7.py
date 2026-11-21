"""U7 versi 2: alur jam koreksi dan jejak perubahan. Semua perubahan di-rollback.
  bench --site hris-uji.local execute hris.hris_payroll.tests.uji_jam_koreksi_u7.jalankan
"""
import json
from datetime import datetime, timedelta

import frappe
from frappe.utils import get_time, getdate

from hris.hris_attendance.services.working_hour import calculate_working_hour
from hris.hris_payroll.services.period_lock import is_locked

WH = "HRIS Working Hour"
SITE = "hris-uji.local"
KOLOM = ["status", "review_status", "check_in", "check_out", "manual_check_in", "manual_check_out"]


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


def _jam(dt):
    return dt.strftime("%H:%M")


def _baca(n):
    return frappe.db.get_value(WH, n, KOLOM, as_dict=True)


def _bebas(emp, day):
    try:
        return not is_locked(emp, day)
    except Exception:
        return False


def _kandidat():
    for r in frappe.get_all(
        WH,
        filters={"status": "Tidak Lengkap", "review_status": "Menunggu",
                 "check_in": ["is", "not set"], "check_out": ["is", "set"]},
        fields=["name", "employee", "work_date", "shift_start"], limit=40,
    ):
        if r.shift_start and _bebas(r.employee, r.work_date):
            return frappe.get_doc(WH, r.name)
    return None


def _jejak(n):
    baris = []
    for v in frappe.get_all("Version", filters={"ref_doctype": WH, "docname": n},
                            fields=["creation", "owner", "data"], order_by="creation asc"):
        try:
            d = json.loads(v.data or "{}")
        except ValueError:
            continue
        for item in d.get("changed", []):
            baris.append((str(v.creation)[:19], v.owner, item[0], item[1], item[2]))
    return baris


def _ada(baris, field, lama_jam=None, lama_kosong=False, baru_jam=None, baru_kosong=False, baru_teks=None):
    for _w, _u, f, lama, baru in baris:
        if f != field:
            continue
        if lama_kosong and lama:
            continue
        if lama_jam is not None and lama_jam not in str(lama or ""):
            continue
        if baru_kosong and baru:
            continue
        if baru_jam is not None and baru_jam not in str(baru or ""):
            continue
        if baru_teks is not None and baru_teks != str(baru or ""):
            continue
        return True
    return False


def _langkah(cek, nama, fn):
    """Jalankan satu langkah; galat dicatat sebagai GAGAL dan tidak menghentikan skrip."""
    try:
        fn()
        return True
    except Exception as e:
        cek("%s (galat saat dijalankan)" % nama, False, "%s: %s" % (type(e).__name__, e))
        return False


def jalankan():
    if frappe.local.site != SITE:
        print("Site bukan %s; berhenti." % SITE)
        return
    cek = _Cek()
    meta = frappe.get_meta(WH)
    ada = meta.has_field("manual_check_in") and meta.has_field("manual_check_out")
    cek("U0a field jam koreksi ada", ada, "jalankan migrate situs uji dulu")
    cek("U0b track_changes aktif", bool(meta.track_changes))
    if ada:
        try:
            doc = _kandidat()
            if not doc:
                print("Tidak ada dokumen kandidat.")
            else:
                n, emp, hari = doc.name, doc.employee, getdate(doc.work_date)
                mulai = datetime.combine(hari, get_time(doc.shift_start))
                baru_masuk = mulai + timedelta(minutes=10)
                awal = len(_jejak(n))
                print("Dokumen uji: %s" % n)

                # 1. isi jam koreksi + Simpan
                def l1():
                    d = frappe.get_doc(WH, n)
                    d.manual_check_in = mulai
                    d.review_note = "Lupa tap masuk (data uji U7)"
                    d.save()
                    r = _jejak(n)[awal:]
                    cek("U1 simpan jam koreksi tercatat (lama kosong, baru %s)" % _jam(mulai),
                        _ada(r, "manual_check_in", lama_kosong=True, baru_jam=_jam(mulai)), str(r))
                _langkah(cek, "U1", l1)

                # 2. hitung ulang
                def l2():
                    a = len(_jejak(n))
                    calculate_working_hour(emp, hari)
                    r = _jejak(n)[a:]
                    d = _baca(n)
                    cek("U2 hari Hadir dan Sudah Ditinjau",
                        d.status == "Hadir" and d.review_status == "Sudah Ditinjau", str(d))
                    cek("U3 perubahan status ke Hadir tercatat", _ada(r, "status", baru_teks="Hadir"), str(r))
                _langkah(cek, "U2", l2)

                # 3. ubah jam koreksi
                def l3():
                    d = frappe.get_doc(WH, n)
                    d.manual_check_in = baru_masuk
                    d.review_note = "Jam koreksi diubah (data uji U7)"
                    a = len(_jejak(n))
                    d.save()
                    calculate_working_hour(emp, hari)
                    r = _jejak(n)[a:]
                    cek("U4 ubah jam koreksi tercatat (%s -> %s)" % (_jam(mulai), _jam(baru_masuk)),
                        _ada(r, "manual_check_in", lama_jam=_jam(mulai), baru_jam=_jam(baru_masuk)), str(r))
                _langkah(cek, "U4", l3)

                # 4. kosongkan jam koreksi (alur HRD: Simpan lalu Hitung Ulang)
                def l4():
                    d = frappe.get_doc(WH, n)
                    d.manual_check_in = None
                    d.review_note = "Jam koreksi dihapus (data uji U7)"
                    a = len(_jejak(n))
                    d.save()
                    calculate_working_hour(emp, hari)
                    r = _jejak(n)[a:]
                    s = _baca(n)
                    cek("U5 pengosongan tercatat (lama %s, baru kosong)" % _jam(baru_masuk),
                        _ada(r, "manual_check_in", lama_jam=_jam(baru_masuk), baru_kosong=True), str(r))
                    cek("U6 hari kembali Tidak Lengkap dan Menunggu",
                        s.status == "Tidak Lengkap" and s.review_status == "Menunggu", str(s))
                _langkah(cek, "U5/U6", l4)

                print("-- Jejak perubahan dokumen uji --")
                for w, u, f, lama, baru in _jejak(n)[awal:]:
                    print("%s | %s | %s | %s -> %s" % (w, u, f, lama, baru))
        finally:
            frappe.db.rollback()
    print("Lulus %d dari %d" % (cek.ok, cek.total))
