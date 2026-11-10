"""Uji PPh 21 langkah 1 (tarif FIKTIF). Jalankan dari folder sites:
cd /home/it/erp/sites && ../env/bin/python ../apps/hris/hris/hris_payroll/tests/uji_pph21_rate.py
Semua data di-rollback."""
import frappe

frappe.init(site="hris-uji.local", sites_path=".")
frappe.connect()
frappe.set_user("Administrator")

from hris.hris_payroll.services.pph21_rate import find_rate

ok = gagal = 0


def cek(nama, kondisi, detail=""):
    global ok, gagal
    if kondisi:
        ok += 1
        print("OK    ", nama)
    else:
        gagal += 1
        print("GAGAL ", nama, detail)


def menolak(nama, fn):
    global ok, gagal
    try:
        fn()
    except Exception as e:
        ok += 1
        print("OK    ", nama, "->", str(e)[:70].replace("\n", " "))
    else:
        gagal += 1
        print("GAGAL ", nama, "(tidak ditolak)")


def baris(kat, dari, sampai, tarif, sejak="2026-01-01", terbuka=0, aktif=1):
    d = frappe.get_doc({"doctype": "HRIS PPh21 TER Rate", "ter_category": kat, "bruto_from": dari,
                        "bruto_to": sampai, "open_ended": terbuka, "rate_percent": tarif,
                        "effective_from": sejak, "enabled": aktif})
    d.insert()
    return d


try:
    a1 = baris("UJIA", 0, 5000000, 0)
    cek("T1 baris pertama diterima, kategori huruf besar", a1.ter_category == "UJIA")
    baris("UJIA", 5000001, 10000000, 2)
    cek("T2 baris kedua diterima", True)
    menolak("T3 rentang tumpang tindih ditolak", lambda: baris("UJIA", 9000000, 12000000, 3))
    baris("UJIA", 10000001, None, 5, terbuka=1)
    cek("T4 rentang terbuka diterima", True)
    menolak("T5 rentang terbuka kedua ditolak", lambda: baris("UJIA", 20000000, None, 6, terbuka=1))
    menolak("T6 dari > sampai ditolak", lambda: baris("UJIB", 100, 50, 1))
    menolak("T7a tarif 120 ditolak", lambda: baris("UJIB", 0, 100, 120))
    menolak("T7b tarif negatif ditolak", lambda: baris("UJIB", 0, 100, -1))
    baris("UJIB", 0, 5000000, 1)
    cek("T8 kategori lain boleh rentang sama", True)
    baris("UJIA", 0, 5000000, 3, sejak="2027-01-01")
    cek("T9 tanggal berlaku berbeda boleh rentang sama", True)

    r = find_rate("UJIA", 7500000, "2026-06-01")
    cek("T10a tarif 7,5 juta = 2", r and r.rate_percent == 2, r)
    r = find_rate("ujia", 15000000, "2026-06-01")
    cek("T10b rentang terbuka = 5, kategori tidak peka huruf", r and r.rate_percent == 5, r)
    r = find_rate("UJIA", 3000000, "2027-02-01")
    cek("T10c set 2027 berlaku = 3", r and r.rate_percent == 3, r)
    cek("T10d set 2027 menggantikan set lama (7,5 juta tanpa tarif)", find_rate("UJIA", 7500000, "2027-02-01") is None)
    cek("T11a sebelum tanggal berlaku paling awal = None", find_rate("UJIA", 1000, "2025-12-31") is None)
    cek("T11b kategori tidak ada = None", find_rate("ZZZ", 1000, "2026-06-01") is None)
    baris("UJIB", 5000001, 8000000, 9, aktif=0)
    cek("T12 baris nonaktif diabaikan", find_rate("UJIB", 6000000, "2026-06-01") is None)

    s = frappe.get_doc("HRIS PPh21 Settings")
    s.set("ptkp_map", [])
    s.append("ptkp_map", {"ptkp_status": "tk/0", "ter_category": "a"})
    s.append("ptkp_map", {"ptkp_status": "TK/0", "ter_category": "B"})
    menolak("T13a status PTKP ganda ditolak", s.save)
    s = frappe.get_doc("HRIS PPh21 Settings")
    s.set("ptkp_map", [])
    s.append("ptkp_map", {"ptkp_status": "tk/0", "ter_category": "a"})
    s.no_npwp_multiplier = 0
    menolak("T13b pengali 0 ditolak", s.save)
    s = frappe.get_doc("HRIS PPh21 Settings")
    s.set("ptkp_map", [])
    s.append("ptkp_map", {"ptkp_status": "tk/0", "ter_category": "a"})
    s.no_npwp_multiplier = 1.25
    s.save()
    s.reload()
    cek("T13c pemetaan disimpan dan dinormalkan huruf besar",
        s.ptkp_map[0].ptkp_status == "TK/0" and s.ptkp_map[0].ter_category == "A")

    def hak(dt, role, jenis):
        return any(p.role == role and p.permlevel == 0 and getattr(p, jenis, 0)
                   for p in frappe.get_meta(dt).permissions)

    for dt in ("HRIS PPh21 TER Rate", "HRIS PPh21 Settings"):
        cek(f"T14 HR Admin tulis ({dt})", hak(dt, "HRIS HR Admin", "write"))
        for role in ("HRIS Payroll Admin", "HRIS Payroll Manager", "HRIS Direksi"):
            cek(f"T14 {role} baca saja ({dt})", hak(dt, role, "read") and not hak(dt, role, "write"))
        cek(f"T14 HR Admin tanpa hapus ({dt})", not hak(dt, "HRIS HR Admin", "delete"))
        cek(f"T14 Employee Admin tanpa akses ({dt})", not hak(dt, "HRIS Employee Admin", "read"))
finally:
    frappe.db.rollback()
    print(f"\nHASIL: OK {ok}, GAGAL {gagal}")
    frappe.destroy()
