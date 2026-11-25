"""Uji pencatatan Pull Run kiriman agen. HANYA untuk site uji.
bench --site hris-uji.local execute hris.hris_attendance.uji_kirim_agen.jalankan
Catatan uji dihapus sendiri di akhir."""
import frappe
from frappe.utils import add_to_date, now_datetime

from hris.hris_attendance.services.pull_run_log import catat_kirim_agen

DOCTYPE = "HRIS Pull Run"


def _cek(nama, kondisi, hasil=""):
    print(("OK     " if kondisi else "GAGAL  ") + nama + ("" if kondisi else " -> " + str(hasil)))
    return 1 if kondisi else 0


def _ring(diterima, baru, dup, err, pesan=""):
    hasil = [{"index": 0, "status": "error", "message": pesan}] if err else []
    return {"received": diterima, "created": baru, "duplicate": dup, "error": err, "results": hasil}


def _nilai(nama):
    return frappe.db.get_value(
        DOCTYPE, nama,
        ["jenis", "status", "punch_dalam_rentang", "baru", "sudah_ada", "gagal", "pesan_error", "device"],
        as_dict=True)


def jalankan():
    if "uji" not in frappe.local.site:
        print("BERHENTI: skrip ini hanya untuk site uji. Site sekarang:", frappe.local.site)
        return
    devs = frappe.get_all("HRIS Device", filters={"is_active": 1}, pluck="name",
                          order_by="name", limit_page_length=2)
    if len(devs) < 2:
        print("GAGAL: butuh minimal 2 HRIS Device aktif")
        return
    d1, d2 = devs
    dibuat = set()
    ok = total = 0
    try:
        total += 1
        ok += _cek("detak (0 baris) tidak dicatat", catat_kirim_agen(d1, _ring(0, 0, 0, 0)) is None)

        n1 = catat_kirim_agen(d1, _ring(500, 500, 0, 0))
        if n1:
            dibuat.add(n1)
        v = _nilai(n1) if n1 else {}
        total += 1
        ok += _cek("batch 1: record dibuat, jenis Kirim Agen, status Selesai",
                   bool(n1) and v.get("jenis") == "Kirim Agen" and v.get("status") == "Selesai", v)
        total += 1
        ok += _cek("batch 1: angka 500/500", v.get("punch_dalam_rentang") == 500 and v.get("baru") == 500, v)

        n2 = catat_kirim_agen(d1, _ring(226, 200, 26, 0))
        v = _nilai(n1)
        total += 1
        ok += _cek("batch 2: masuk record yang sama", n2 == n1, (n1, n2))
        total += 1
        ok += _cek("batch 2: angka dijumlahkan 726/700/26",
                   v.get("punch_dalam_rentang") == 726 and v.get("baru") == 700 and v.get("sudah_ada") == 26, v)

        n3 = catat_kirim_agen(d2, _ring(10, 10, 0, 0))
        if n3:
            dibuat.add(n3)
        total += 1
        ok += _cek("mesin lain: record terpisah", bool(n3) and n3 != n1, (n1, n3))

        frappe.db.set_value(DOCTYPE, n1, "finished_at", add_to_date(now_datetime(), minutes=-30))
        frappe.db.commit()
        n4 = catat_kirim_agen(d1, _ring(5, 5, 0, 0))
        if n4:
            dibuat.add(n4)
        total += 1
        ok += _cek("lewat 5 menit: sesi baru", bool(n4) and n4 != n1, (n1, n4))

        n5 = catat_kirim_agen(d1, _ring(3, 0, 0, 3, "Pesan uji"))
        v = _nilai(n4) if n4 else {}
        total += 1
        ok += _cek("baris error: masuk sesi berjalan, gagal=3, pesan tersimpan",
                   n5 == n4 and v.get("gagal") == 3 and "Pesan uji" in (v.get("pesan_error") or ""), v)
    finally:
        for n in dibuat:
            frappe.db.delete(DOCTYPE, {"name": n})
        frappe.db.commit()
        print("Catatan uji dibersihkan:", len(dibuat))
    print("== {0} OK dari {1} ==".format(ok, total))
