"""Uji logika laporan perbandingan. Jalankan:
bench --site hris-uji.local execute hris.hris_attendance.uji_perbandingan.jalankan"""
from collections import Counter

from hris.hris_attendance.report.perbandingan_user_mesin_dan_employee.perbandingan_user_mesin_dan_employee import (
    bandingkan_nama, susun)


def _cek(nama, kondisi, hasil=""):
    print(("OK     " if kondisi else "GAGAL  ") + nama + ("" if kondisi else " -> " + str(hasil)))
    return 1 if kondisi else 0


def jalankan():
    def u(d, i, n):
        return {"device": d, "device_user_id": i, "user_name_on_device": n}

    def e(nm, i, n, dep="D", st="Aktif"):
        return {"name": nm, "attendance_device_id": i, "employee_name": n, "department": dep, "status": st}

    users = [u("M1", "1", "BUDI SANTOSO"), u("M2", "1", "Budi Santoso (Gudang)"),
             u("M1", "2", "SITI"), u("M1", "3", "ANDI"), u("M1", "4", "TONO"),
             u("M1", "5", "DEWI"), u("M1", "6", "Eko"), u("M2", "6", "Fajar")]
    emps = [e("E1", "1", "Budi Santoso"), e("E2", "2", "Siti Aminah"), e("E3", "3", "Rudi Hartono"),
            e("E5", "5", "Dewi Lestari", st="Resign"), e("E6", "6", "Eko"), e("E7", "7", "Yanti"),
            e("E8", "", "Tanpa ID"), e("E9", "9", "ID 9", dep=""),
            e("E10", "10", "Ganda 1"), e("E11", "10", "Ganda 2")]

    rows = susun(users, emps, 0)
    hitung = Counter(r["kategori"][0] for r in rows)
    harapan = {"A": 1, "B": 1, "C": 4, "D": 1, "E": 1, "F": 5}
    ok = total = 0
    for k, n in sorted(harapan.items()):
        total += 1
        ok += _cek("kategori {0} = {1}".format(k, n), hitung.get(k, 0) == n, dict(hitung))
    total += 1
    ok += _cek("nama mirip: SITI vs Siti Aminah", bandingkan_nama("SITI", "Siti Aminah") == "mirip")
    total += 1
    ok += _cek("nama sama: buang teks dalam kurung", bandingkan_nama("Budi (X)", "budi") == "sama")
    total += 1
    ok += _cek("nama beda: ANDI vs Rudi Hartono", bandingkan_nama("ANDI", "Rudi Hartono") == "beda")
    print("== {0} OK dari {1} ==".format(ok, total))
