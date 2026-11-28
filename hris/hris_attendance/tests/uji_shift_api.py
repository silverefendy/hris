"""Uji endpoint jadwal shift: hasil massal harus sama dengan shift_schedule.get_schedule_for_date.

Menjalankan (hanya membaca):
    bench --site <site> execute hris.hris_attendance.tests.uji_shift_api.run
"""
import time

import frappe
from frappe.utils import add_days, getdate, nowdate

from hris.hris_attendance.integrations import shift_api
from hris.hris_attendance.services import shift_schedule as ss

gagal = 0


def cek(kode, uraian, ok, info=""):
    global gagal
    if not ok:
        gagal += 1
    print(("OK     " if ok else "GAGAL  ") + kode + " " + uraian + (("  |  " + info) if info else ""))


def run():
    global gagal
    gagal = 0
    sampai = getdate(nowdate())
    dari = add_days(sampai, -27)

    t0 = time.time()
    hasil = shift_api.bangun_jadwal(dari, sampai)
    detik = time.time() - t0
    cek("E1", "endpoint menghitung 28 hari", len(hasil["baris"]) > 0, "%d baris, %d karyawan, %.1f dtk" % (len(hasil["baris"]), hasil["diproses"], detik))
    for p in hasil["peringatan"]:
        print("INFO   peringatan: " + p)

    kol = {n: i for i, n in enumerate(hasil["kolom"])}
    idx = {}
    for b in hasil["baris"]:
        idx[(b[kol["id"]], b[kol["tanggal"]])] = b

    group_field = ss._group_fieldname()
    hris = frappe.get_all(
        "HRIS Employee",
        filters={"status": "Aktif", "attendance_device_id": ["is", "set"]},
        fields=["name", "attendance_device_id", "erpnext_employee"],
        order_by="name asc",
    )
    hitung_id = {}
    for r in hris:
        k = (r.attendance_device_id or "").strip()
        hitung_id[k] = hitung_id.get(k, 0) + 1
    kandidat = [r for r in hris if r.erpnext_employee and hitung_id.get((r.attendance_device_id or "").strip()) == 1]

    pemegang = set(
        a.employee
        for a in frappe.get_all(
            "HRIS Shift Assignment",
            filters={"is_active": 1, "from_date": ["<=", sampai], "to_date": [">=", dari]},
            fields=["employee"],
        )
    )
    per_grup = {}
    sampel = []
    for r in kandidat:
        g = frappe.db.get_value("Employee", r.erpnext_employee, group_field)
        if r.erpnext_employee in pemegang or per_grup.get(g, 0) < 3:
            per_grup[g] = per_grup.get(g, 0) + 1
            sampel.append(r)
        if len(sampel) >= 80:
            break

    dibanding = 0
    galat = 0
    beda = []
    for r in sampel:
        kode = (r.attendance_device_id or "").strip()
        for i in range(28):
            day = add_days(dari, i)
            try:
                res = ss.get_schedule_for_date(r.erpnext_employee, day)
            except Exception:
                galat += 1
                continue
            dibanding += 1
            row = idx.get((kode, str(day)))
            b_shift = (row[kol["shift"]] or None) if row else None
            b_off = row[kol["off"]] if row else 0
            b_works = row[kol["works"]] if row else 0
            b_libur = row[kol["libur"]] if row else 0
            r_shift = res["shift"] or None
            salah = b_shift != r_shift or b_off != res["is_off"] or b_works != res["works"]
            if b_libur != res["is_holiday"] or (row and row[kol["wajib"]] != res["is_required"]):
                salah = True
            if salah:
                beda.append("%s %s: massal=%s/%s/%s resmi=%s/%s/%s" % (kode, day, b_shift, b_off, b_works, res["shift"], res["is_off"], res["works"]))

    cek("E2", "ada sampel yang dibandingkan", dibanding > 0, "%d karyawan, %d hari-karyawan, grup: %d" % (len(sampel), dibanding, len(per_grup)))
    cek("E3", "tidak ada galat pada fungsi resmi", galat == 0, "galat %d" % galat)
    cek("E4", "hasil massal sama dengan fungsi resmi", len(beda) == 0, "%d beda" % len(beda))
    for s in beda[:10]:
        print("       " + s)

    try:
        shift_api.bangun_jadwal(dari, add_days(dari, 63))
        ok = False
    except Exception:
        ok = True
    cek("E5", "rentang 64 hari ditolak", ok)

    try:
        shift_api.bangun_jadwal(sampai, add_days(sampai, -1))
        ok = False
    except Exception:
        ok = True
    cek("E6", "tanggal terbalik ditolak", ok)

    kunci = set(hasil.keys())
    cek("E7", "respons tanpa kunci nama/karyawan", kunci == {"dari", "sampai", "kolom", "baris", "shift", "diproses", "peringatan"}, ",".join(sorted(kunci)))

    print()
    print("SEMUA LULUS" if gagal == 0 else "ADA YANG GAGAL: %d" % gagal)
