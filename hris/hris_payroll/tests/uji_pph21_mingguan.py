"""Uji PPh 21 multi-slip Mingguan (K-134), tarif FIKTIF 2%.
Jadwal Mingguan Senin offset 10: slip terakhir bayar Oktober = minggu 12-18 Okt.
Slip dibuat urutan terbalik. Hasil diperiksa terhadap slip yang benar-benar terbentuk.
Semua data di-rollback. Jalankan: cd /home/it/erp/sites && ../env/bin/python <path ini>."""

import os

import frappe
from frappe.utils import getdate

SITE = "hris-uji.local"
ok = 0
gagal = 0

MINGGU = (
    ("2026-09-21", "2026-09-27", "2026-09-24"),
    ("2026-09-28", "2026-10-04", "2026-10-01"),
    ("2026-10-05", "2026-10-11", "2026-10-08"),
    ("2026-10-12", "2026-10-18", "2026-10-15"),
)


def cek(nama, kondisi, info=""):
    global ok, gagal
    if kondisi:
        ok += 1
        print("OK     ", nama)
    else:
        gagal += 1
        print("GAGAL  ", nama, info)


def uji():
    from hris.hris_payroll.services import payroll_pph21 as pp
    from hris.hris_payroll.services import payroll_slip as ps

    company = frappe.db.get_value("Company", {}, "name")
    kandidat = frappe.db.sql_list(
        """
        select he.name from `tabHRIS Employee` he
        inner join `tabHRIS Working Hour` wh on wh.employee = he.erpnext_employee
        where he.company = %(co)s and he.date_of_joining <= %(a)s
          and (he.resign_date is null or he.resign_date > %(b)s)
          and not exists (select 1 from `tabHRIS Employee Pay` ep where ep.employee = he.name)
        group by he.name
        having sum(wh.status = 'Hadir' and wh.work_date between %(w2a)s and %(w2b)s) > 0
           and sum(wh.status = 'Hadir' and wh.work_date between %(w4a)s and %(w4b)s) > 0
        order by he.name limit 1
        """,
        {"co": company, "a": MINGGU[0][0], "b": MINGGU[3][1],
         "w2a": MINGGU[1][0], "w2b": MINGGU[1][1], "w4a": MINGGU[3][0], "w4b": MINGGU[3][1]},
    )
    cek("D0 ada karyawan Hadir di minggu 28 Sep dan 12 Okt", bool(kandidat))
    if not kandidat:
        return
    he = kandidat[0]
    if frappe.db.count("HRIS PPh21 TER Rate", {"ter_category": "UJIM"}):
        raise SystemExit("Ada sisa tarif UJIM di site uji; hapus dulu, lalu ulangi.")

    try:
        sch = frappe.get_doc({
            "doctype": "HRIS Payroll Schedule", "schedule_name": "ZZ Uji Multislip", "company": company,
            "is_active": 1, "schedule_type": "Mingguan", "week_start_day": "Senin",
            "pay_date_offset_days": 10, "sunday_rule": "Maju ke Senin",
        }).insert(ignore_permissions=True)
    except Exception as exc:
        cek("D1 jadwal uji (offset 10) dibuat", False, repr(exc)[:300])
        return
    frappe.get_doc({"doctype": "HRIS Employee Pay", "employee": he, "pay_type": "Harian", "amount": 100000,
                    "payroll_schedule": sch.name, "effective_from": "2026-01-01"}).insert(ignore_permissions=True)
    frappe.get_doc({"doctype": "HRIS PPh21 TER Rate", "ter_category": "UJIM", "bruto_from": 0, "bruto_to": None,
                    "open_ended": 1, "rate_percent": 2, "effective_from": "2026-01-01", "enabled": 1}).insert()
    st = frappe.get_doc("HRIS PPh21 Settings")
    st.enabled = 1
    st.set("ptkp_map", [])
    st.append("ptkp_map", {"ptkp_status": "TK/0", "ter_category": "UJIM"})
    st.set("exempt_components", [])
    st.no_npwp_multiplier = 1
    st.rounding = "Ke Bawah"
    st.save()
    frappe.db.set_value("HRIS Employee", he, {"pph21_enrolled": 1, "ptkp_status": "TK/0"})

    P = [frappe.get_doc({"doctype": "HRIS Payroll Period", "payroll_schedule": sch.name, "reference_date": m[2]})
         .insert(ignore_permissions=True) for m in MINGGU]
    cek("P0 awal periode sesuai dan bayar 7, 14, 21, 28 Okt",
        [str(getdate(p.period_start)) for p in P] == [m[0] for m in MINGGU]
        and [str(getdate(p.pay_date)) for p in P] == ["2026-10-07", "2026-10-14", "2026-10-21", "2026-10-28"],
        [(str(p.period_start), str(p.pay_date)) for p in P])
    cek("P0 minggu 12-18 Okt = slip terakhir bulan bayar Oktober, yang lain bukan",
        pp._slip_terakhir(P[3]) and not any(pp._slip_terakhir(p) for p in P[:3]))
    cek("P0 jumlah slip jadwal (M) = 4", pp._jumlah_slip_jadwal(P[3]) == 4, pp._jumlah_slip_jadwal(P[3]))

    def slip_dari(p):
        nama = frappe.db.get_value("HRIS Payroll Slip", {"unique_key": "%s|%s" % (p.name, he)}, "name")
        return frappe.get_doc("HRIS Payroll Slip", nama) if nama else None

    def pph(s):
        return [r for r in s.components if r.component == "PPh 21" and r.component_type == "Potongan"]

    def pendapatan(s):
        return sum(int(r.amount or 0) for r in s.components if r.component_type == "Pendapatan")

    # 1. slip terakhir dibuat lebih dulu
    r4 = ps.buat_slip(P[3].name, "Karyawan", employee=he)
    s4 = slip_dari(P[3])
    cek("P1 slip terakhir terbentuk tanpa gagal", r4["gagal"] == 0 and s4 is not None, r4)
    if s4 is None:
        return
    own = pendapatan(s4)
    cek("P1 PPh 21 = 2%% bruto slip ini (%d)" % own, len(pph(s4)) == 1 and int(pph(s4)[0].amount) == own * 2 // 100,
        [(r.component, r.amount) for r in s4.components])
    cek("P1 peringatan jumlah slip: 1 dari 4", "dihitung dari 1 slip" in (s4.calc_notes or "") and "4 slip" in (s4.calc_notes or ""), s4.calc_notes)

    # 2. slip lain; minggu tanpa Hadir boleh terbentuk atau dilewati
    ada = []
    for p in P[:3]:
        r = ps.buat_slip(p.name, "Karyawan", employee=he)
        s = slip_dari(p)
        if s is None:
            print("INFO    minggu %s: slip tidak terbentuk (dilewati=%s) alasan=%s" % (p.period_start, r.get("dilewati"), r.get("alasan")))
        else:
            print("INFO    minggu %s: slip terbentuk, bruto %d" % (p.period_start, pendapatan(s)))
            ada.append(s)
    cek("P2 minimal satu slip lain terbentuk (agar agregasi antar-slip terbukti)", bool(ada),
        "Hanya 1 slip; agregasi belum terbukti")
    cek("P2 slip bukan terakhir: tanpa baris PPh 21 dan catatan 'tidak dipotong pada slip ini'",
        all(not pph(s) and "tidak dipotong pada slip ini" in (s.calc_notes or "") for s in ada), [s.calc_notes for s in ada])
    cek("P2 slip bukan terakhir memuat peringatan yang menyebut slip terakhir",
        all(("Peringatan: slip %s" % s4.name) in (s.calc_notes or "") for s in ada), [s.calc_notes for s in ada])

    # 3. hitung ulang slip terakhir
    n = 1 + len(ada)
    total = sum(pendapatan(s) for s in ada) + own
    ps.buat_slip(P[3].name, "Karyawan", employee=he)
    s4 = slip_dari(P[3])
    cek("P3 PPh 21 = 2%% x bruto %d slip (%d)" % (n, total), len(pph(s4)) == 1 and int(pph(s4)[0].amount) == total * 2 // 100,
        [(r.component, r.amount) for r in s4.components])
    catatan = s4.calc_notes or ""
    if n == 4:
        cek("P3 catatan tanpa peringatan jumlah (4 dari 4)", "dihitung dari" not in catatan, catatan)
    else:
        cek("P3 catatan menyebut %d dari 4 slip" % n, ("dihitung dari %d slip" % n) in catatan and "4 slip" in catatan, catatan)

    # 4. idempotensi
    awal = int(pph(s4)[0].amount)
    ps.buat_slip(P[3].name, "Karyawan", employee=he)
    s4 = slip_dari(P[3])
    cek("P4 hitung ulang lagi: satu baris PPh 21, angka sama", len(pph(s4)) == 1 and int(pph(s4)[0].amount) == awal)
    cek("P5 slip bukan terakhir tetap tanpa PPh 21", all(not pph(slip_dari(p)) for p in P[:3] if slip_dari(p)))


def periksa():
    awal_enabled = frappe.db.get_single_value("HRIS PPh21 Settings", "enabled")
    n_slip = frappe.db.count("HRIS Payroll Slip")
    try:
        uji()
    finally:
        frappe.db.rollback()
    cek("Z1 tidak ada sisa jadwal, tarif UJIM, dan slip uji",
        not frappe.db.exists("HRIS Payroll Schedule", "ZZ Uji Multislip")
        and not frappe.db.count("HRIS PPh21 TER Rate", {"ter_category": "UJIM"})
        and frappe.db.count("HRIS Payroll Slip") == n_slip)
    cek("Z1 pengaturan PPh 21 kembali seperti semula", frappe.db.get_single_value("HRIS PPh21 Settings", "enabled") == awal_enabled)
    print("HASIL: OK %d, GAGAL %d" % (ok, gagal))
    return gagal


if __name__ == "__main__":
    os.chdir("/home/it/erp/sites")
    frappe.init(site=SITE, sites_path=".")
    frappe.connect()
    frappe.set_user("Administrator")
    try:
        sisa = periksa()
    finally:
        frappe.db.rollback()
        frappe.destroy()
    raise SystemExit(1 if sisa else 0)
