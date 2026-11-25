"""Uji generator ID Finger. Hanya membaca.

Jalankan: bench --site <site> execute hris.hris_employee_data.uji_id_finger.periksa
"""

import frappe

from hris.hris_employee_data.services import id_finger


def periksa():
    hasil = {"ok": 0, "gagal": 0}

    def cek(nama, kondisi, info=""):
        if kondisi:
            hasil["ok"] += 1
            print("OK    ", nama)
        else:
            hasil["gagal"] += 1
            print("GAGAL ", nama, info)

    frappe.set_user("Administrator")
    h = id_finger.ambil_id_berikutnya()
    maks = max(id_finger._terbesar(t, k) for _a, _b, t, k in id_finger.SUMBER)
    pembanding = sum(id_finger._bukan_angka(t, k) for _a, _b, t, k in id_finger.SUMBER)

    cek("T1 nomor = terbesar + 1", int(h["berikutnya"]) == maks + 1, f"{h['berikutnya']} vs {maks + 1}")
    cek("T2 nomor belum dipakai di tiga sumber", not id_finger._dipakai(h["berikutnya"]))
    cek("T3 tiga sumber dilaporkan", len(h["sumber"]) == 3)
    cek("T4 jumlah ID bukan angka dilaporkan", h["bukan_angka"] == pembanding, f"{h['bukan_angka']} vs {pembanding}")
    cek("T5 angka terbesar dilaporkan benar", h["terbesar"] == maks, f"{h['terbesar']} vs {maks}")

    frappe.set_user("Guest")
    try:
        id_finger.ambil_id_berikutnya()
        ditolak = False
    except frappe.PermissionError:
        ditolak = True
    finally:
        frappe.set_user("Administrator")
    cek("T6 Guest ditolak", ditolak)

    print("periksa:", hasil["ok"], "OK,", hasil["gagal"], "GAGAL")
