"""Uji HRIS Device User. Jalankan: bench --site <site uji> execute hris.hris_attendance.uji_device_user.jalankan"""
import frappe

from hris.hris_attendance.services.device_user_ingest import save_device_users

MESIN = "CML Cemara"
ID_UJI = ["99991", "99992", "99993"]


def _cek(nama, kondisi, hasil):
    print(("OK     " if kondisi else "GAGAL  ") + nama + ("" if kondisi else " -> " + str(hasil)))
    return 1 if kondisi else 0


def _bersihkan():
    for i in ID_UJI:
        key = "{0}|{1}".format(MESIN, i)
        if frappe.db.exists("HRIS Device User", key):
            frappe.delete_doc("HRIS Device User", key, force=True, ignore_permissions=True)
    frappe.db.commit()


def jalankan():
    nyata = frappe.db.count("HRIS Device User", {"device": MESIN, "device_user_id": ["not in", ID_UJI]})
    if nyata:
        print("BERHENTI: sudah ada {0} data nyata untuk {1}. Uji dibatalkan.".format(nyata, MESIN))
        return
    _bersihkan()
    ok = 0
    total = 0

    def user(i, nama):
        return {"device_user_id": i, "name": nama, "privilege": 0, "enabled": 1, "finger_count": 2}

    h1 = save_device_users(MESIN, [user("99991", "UJI A"), user("99992", "UJI B"), user("99993", "UJI C")],
                           "2026-11-25 14:00:00", 1)
    total += 1; ok += _cek("snapshot 1: 3 dibuat", h1["created"] == 3 and h1["error"] == 0, h1)

    h2 = save_device_users(MESIN, [user("99991", "UJI A"), user("99992", "UJI B"), user("99993", "UJI C")],
                           "2026-11-25 14:05:00", 1)
    total += 1; ok += _cek("snapshot 2 (sama): 3 tidak berubah", h2["unchanged"] == 3 and h2["created"] == 0, h2)

    h3 = save_device_users(MESIN, [user("99991", "UJI A2"), user("99992", "UJI B")],
                           "2026-11-25 14:10:00", 1)
    total += 1; ok += _cek("snapshot 3: 1 diperbarui, 1 sama, 1 ditandai hilang",
                           h3["updated"] == 1 and h3["unchanged"] == 1 and h3["marked_absent"] == 1, h3)

    hilang = frappe.db.get_value("HRIS Device User", "{0}|99993".format(MESIN), "in_last_snapshot")
    total += 1; ok += _cek("99993 in_last_snapshot = 0", hilang == 0, hilang)

    nama = frappe.db.get_value("HRIS Device User", "{0}|99991".format(MESIN), "user_name_on_device")
    total += 1; ok += _cek("nama 99991 jadi UJI A2", nama == "UJI A2", nama)

    h4 = save_device_users(MESIN, [{"device_user_id": "", "name": "kosong"}], "2026-11-25 14:15:00", 0)
    total += 1; ok += _cek("ID kosong -> error 1", h4["error"] == 1, h4)

    try:
        save_device_users("MESIN-TIDAK-ADA", [], None, 0)
        total += 1; ok += _cek("mesin tidak ada ditolak", False, "tidak ada galat")
    except Exception:
        total += 1; ok += _cek("mesin tidak ada ditolak", True, "")

    _bersihkan()
    print("== {0} OK dari {1} ==".format(ok, total))
