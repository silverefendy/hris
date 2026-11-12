import frappe

from hris.hris_attendance.services import department_aturan as da

HASIL = {"ok": 0, "gagal": 0}


def cek(nama, kondisi, info=""):
    HASIL["ok" if kondisi else "gagal"] += 1
    print(("OK    " if kondisi else "GAGAL ") + nama + ("" if kondisi else "  -> " + str(info)))


def jalankan():
    HASIL["ok"] = HASIL["gagal"] = 0
    g = da._gabung
    cek("L1 tanpa HRIS Employee: Department ERPNext", g("Produksi", None, None, None) == "Produksi")
    cek("L2 HRIS Employee menang atas ERPNext", g("X", ("Finishing", "Department"), None, None) == "Finishing")
    cek("L3 pinjam Department", g("X", ("Produksi", "Department"), "Finishing", None) == "Finishing")
    cek("L4 pinjam Grup", g("X", ("Produksi", "Department"), None, "Packing") == "Packing")
    cek("L5 beda, ikut Grup", g("X", ("Produksi", "Grup"), "Finishing", "Packing") == "Packing")
    cek("L6 beda, ikut Department", g("X", ("Produksi", "Department"), "Finishing", "Packing") == "Finishing")
    cek("L7 HRIS Department kosong tidak jatuh ke ERPNext", g("X", (None, "Department"), None, None) is None)
    cek("L8 rule_follow kosong dianggap Department", g("X", ("P", None), "F", "K") == "F")

    baris = frappe.get_all("HRIS Working Hour", fields=["name", "employee", "work_date", "rule_department"], limit=5)
    if baris:
        b = baris[0]
        sebelum = frappe.db.get_value("HRIS Working Hour", b.name, ["needs_review", "review_reason", "review_status"], as_dict=True)
        da._tandai(b.name, "Dept Uji", b.rule_department, "uji")
        sesudah = frappe.db.get_value("HRIS Working Hour", b.name, ["needs_review", "review_reason", "review_status"], as_dict=True)
        cek("T1 penanda terisi", sesudah.needs_review == 1 and sesudah.review_status == "Menunggu"
            and "Dept Uji" in (sesudah.review_reason or ""), sesudah)
        frappe.db.rollback()
        pulih = frappe.db.get_value("HRIS Working Hour", b.name, ["needs_review", "review_reason", "review_status"], as_dict=True)
        cek("T2 rollback memulihkan baris", pulih == sebelum, "%s vs %s" % (pulih, sebelum))
        galat = []
        for r in baris:
            try:
                sched = __import__("hris.hris_attendance.services.shift_schedule", fromlist=["x"]).get_schedule_for_date(r.employee, r.work_date)
                da.tentukan_rule_department(r.employee, None, sched)
            except Exception as e:
                galat.append("%s: %s" % (r.name, e))
        cek("S1 asap: penentu jalan pada %d baris nyata" % len(baris), not galat, galat)
    else:
        print("LEWAT T1, T2, S1: tidak ada baris Working Hour di site ini")
    print("HASIL: OK %d GAGAL %d" % (HASIL["ok"], HASIL["gagal"]))
