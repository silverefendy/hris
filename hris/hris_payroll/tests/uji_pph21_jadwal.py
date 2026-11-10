"""Uji jadwal dan PPh 21 multi-slip (K-134), tarif FIKTIF.
Bagian J: sifat 'slip terakhir' dan 'slip pertama' pada beberapa jenis jadwal sepanjang 2026.
Bagian P: PPh 21 pada 4 slip Mingguan yang dibayar di Oktober 2026, dibuat dengan urutan terbalik.
Semua data di-rollback. Jalankan: cd /home/it/erp/sites && ../env/bin/python <path ini>."""

import os
from collections import defaultdict
from datetime import timedelta

import frappe
from frappe.utils import getdate

SITE = "hris-uji.local"
ok = 0
gagal = 0
COMPANY = None


def cek(nama, kondisi, info=""):
    global ok, gagal
    if kondisi:
        ok += 1
        print("OK     ", nama)
    else:
        gagal += 1
        print("GAGAL  ", nama, info)


def buat_jadwal(nama, hari=None, **kw):
    isi = {"doctype": "HRIS Payroll Schedule", "schedule_name": nama, "company": COMPANY, "is_active": 1}
    isi.update(kw)
    doc = frappe.get_doc(isi)
    for h in hari or []:
        doc.append("cut_off_dates", {"day_of_month": h})
    return doc.insert(ignore_permissions=True)


# ---------- bagian J ----------
def uji_jadwal(nama, label, kw, hari=None):
    from hris.hris_payroll.services import payroll_bpjs as bp
    from hris.hris_payroll.services import payroll_pph21 as pp
    from hris.hris_payroll.services.payroll_schedule import compute_pay_date, compute_period

    try:
        doc = buat_jadwal(nama, hari=hari, **kw)
    except Exception as exc:
        cek("J %s: jadwal uji dibuat" % label, False, repr(exc)[:200])
        return
    params, offset, aturan = bp._jadwal(frappe._dict(payroll_schedule=doc.name))
    periode = []
    awal, akhir = compute_period(params, getdate("2025-10-01"))
    while awal <= getdate("2027-02-28"):
        bayar = compute_pay_date(akhir, offset, aturan)
        periode.append(frappe._dict(payroll_schedule=doc.name, period_start=awal, period_end=akhir, pay_date=bayar))
        awal, akhir = compute_period(params, akhir + timedelta(days=1))
    grup = defaultdict(list)
    for p in periode:
        grup[(p.pay_date.year, p.pay_date.month)].append(p)
    salah = []
    banyak = 0
    for (tahun, bulan), daftar in sorted(grup.items()):
        if tahun != 2026:
            continue
        daftar.sort(key=lambda p: p.period_start)
        banyak += 1 if len(daftar) > 1 else 0
        terakhir = [p for p in daftar if pp._slip_terakhir(p)]
        pertama = [p for p in daftar if bp.pertama_bulan_murni(params, offset, aturan, p.period_start, p.pay_date)]
        jumlah = [pp._jumlah_slip_jadwal(p) for p in daftar]
        benar = (
            len(terakhir) == 1 and terakhir[0] is daftar[-1]
            and len(pertama) == 1 and pertama[0] is daftar[0]
            and all(j == len(daftar) for j in jumlah)
        )
        if not benar:
            salah.append("%d-%02d: n=%d terakhir=%d pertama=%d M=%s" % (tahun, bulan, len(daftar), len(terakhir), len(pertama), jumlah))
    cek("J %s: 12 bulan konsisten (bulan dengan >1 slip: %d)" % (label, banyak), not salah, salah[:3])


JADWAL = (
    ("ZZ Uji Jadwal 1", "Bulanan potong 26, offset 3",
     dict(schedule_type="Bulanan", cut_off_day=26, pay_date_offset_days=3, sunday_rule="Maju ke Senin"), None),
    ("ZZ Uji Jadwal 2", "Mingguan Senin, offset 3",
     dict(schedule_type="Mingguan", week_start_day="Senin", pay_date_offset_days=3, sunday_rule="Maju ke Senin"), None),
    ("ZZ Uji Jadwal 3", "Mingguan Senin, offset 0 (Minggu digeser ke Senin)",
     dict(schedule_type="Mingguan", week_start_day="Senin", pay_date_offset_days=0, sunday_rule="Maju ke Senin"), None),
    ("ZZ Uji Jadwal 4", "Mingguan Sabtu, offset 2",
     dict(schedule_type="Mingguan", week_start_day="Sabtu", pay_date_offset_days=2, sunday_rule="Maju ke Senin"), None),
    ("ZZ Uji Jadwal 5", "Harian 10 hari, offset 2",
     dict(schedule_type="Harian", period_days=10, anchor_date="2026-01-01", pay_date_offset_days=2, sunday_rule="Maju ke Senin"), None),
    ("ZZ Uji Jadwal 6", "Tanggal Tetap 10 dan 25, offset 3",
     dict(schedule_type="Tanggal Tetap", pay_date_offset_days=3, sunday_rule="Maju ke Senin"), [10, 25]),
)


# ---------- bagian P ----------
def uji_pph21_mingguan():
    from hris.hris_payroll.services import payroll_slip as ps

    minggu = (("2026-09-28", "2026-10-04"), ("2026-10-05", "2026-10-11"), ("2026-10-12", "2026-10-18"), ("2026-10-19", "2026-10-25"))
    kandidat = frappe.db.sql_list(
        """
        select he.name from `tabHRIS Employee` he
        inner join `tabHRIS Working Hour` wh on wh.employee = he.erpnext_employee
        where wh.work_date between %(a)s and %(b)s and he.company = %(co)s
          and he.date_of_joining <= %(a)s and (he.resign_date is null or he.resign_date > %(b)s)
          and not exists (select 1 from `tabHRIS Employee Pay` ep where ep.employee = he.name)
        group by he.name
        having sum(wh.status = 'Hadir' and wh.work_date between %(w1a)s and %(w1b)s) > 0
           and sum(wh.status = 'Hadir' and wh.work_date between %(w2a)s and %(w2b)s) > 0
           and sum(wh.status = 'Hadir' and wh.work_date between %(w3a)s and %(w3b)s) > 0
           and sum(wh.status = 'Hadir' and wh.work_date between %(w4a)s and %(w4b)s) > 0
        order by he.name limit 1
        """,
        {"a": minggu[0][0], "b": minggu[3][1], "co": COMPANY,
         "w1a": minggu[0][0], "w1b": minggu[0][1], "w2a": minggu[1][0], "w2b": minggu[1][1],
         "w3a": minggu[2][0], "w3b": minggu[2][1], "w4a": minggu[3][0], "w4b": minggu[3][1]},
    )
    if not kandidat:
        print("INFO    tidak ada karyawan dengan hari Hadir di 4 minggu itu; bagian P dilewati")
        return
    he = kandidat[0]
    if frappe.db.count("HRIS PPh21 TER Rate", {"ter_category": "UJIM"}):
        raise SystemExit("Ada sisa tarif UJIM di site uji; hapus dulu, lalu ulangi.")

    sch = buat_jadwal("ZZ Uji Jadwal Minggu", schedule_type="Mingguan", week_start_day="Senin",
                      pay_date_offset_days=3, sunday_rule="Maju ke Senin")
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

    periode = []
    for acuan, awal_harap in (("2026-10-01", "2026-09-28"), ("2026-10-08", "2026-10-05"),
                              ("2026-10-15", "2026-10-12"), ("2026-10-22", "2026-10-19")):
        p = frappe.get_doc({"doctype": "HRIS Payroll Period", "payroll_schedule": sch.name, "reference_date": acuan}).insert(ignore_permissions=True)
        periode.append(p)
    cek("P0 4 periode mingguan: awal sesuai dan semua dibayar di Oktober",
        all(str(getdate(p.period_start)) == a for p, a in zip(periode, [m[0] for m in minggu]))
        and all(getdate(p.pay_date).month == 10 for p in periode),
        [(str(p.period_start), str(p.pay_date)) for p in periode])

    def slip_dari(p):
        nama = frappe.db.get_value("HRIS Payroll Slip", {"unique_key": "%s|%s" % (p.name, he)}, "name")
        return frappe.get_doc("HRIS Payroll Slip", nama) if nama else None

    def buat(p):
        r = ps.buat_slip(p.name, "Karyawan", employee=he)
        cek("P  slip periode %s dibuat tanpa gagal" % p.period_start, r["gagal"] == 0 and r["dibuat"] + r["diperbarui"] == 1, r)
        return slip_dari(p)

    def pph(slip):
        return [r for r in slip.components if r.component == "PPh 21" and r.component_type == "Potongan"]

    def pendapatan(slip):
        return sum(int(r.amount or 0) for r in slip.components if r.component_type == "Pendapatan")

    # Urutan terbalik: slip terakhir (minggu ke-4) dulu
    s4 = buat(periode[3])
    own = pendapatan(s4)
    cek("P1 slip terakhir dibuat lebih dulu: PPh 21 dari bruto 1 slip (2%%)", len(pph(s4)) == 1 and int(pph(s4)[0].amount) == own * 2 // 100,
        (own, [(r.component, r.amount) for r in s4.components]))
    cek("P1 peringatan 1 dari 4 slip ada", "dihitung dari 1 slip" in (s4.calc_notes or "") and "4 slip" in (s4.calc_notes or ""), s4.calc_notes)

    s_lain = [buat(p) for p in periode[:3]]
    cek("P2 slip bukan terakhir: tanpa baris PPh 21 dan catatan menyebut dipotong di slip terakhir",
        all(not pph(s) and "tidak dipotong pada slip ini" in (s.calc_notes or "") for s in s_lain), [s.calc_notes for s in s_lain])
    cek("P2 slip bukan terakhir yang dibuat setelah slip terakhir memuat PPh: ada peringatan menyebut slipnya",
        all(("Peringatan: slip %s" % s4.name) in (s.calc_notes or "") for s in s_lain), [s.calc_notes for s in s_lain])

    total = sum(pendapatan(s) for s in s_lain) + own
    s4 = buat(periode[3])
    cek("P3 hitung ulang slip terakhir: PPh 21 = 2%% x bruto 4 slip (%d)" % total,
        len(pph(s4)) == 1 and int(pph(s4)[0].amount) == total * 2 // 100, [(r.component, r.amount) for r in s4.components])
    cek("P3 catatan menyebut 4 slip dan tanpa peringatan jumlah", "dari 4 slip" in (s4.calc_notes or "") and "dihitung dari" not in (s4.calc_notes or ""), s4.calc_notes)
    jumlah_awal = int(pph(s4)[0].amount) if pph(s4) else None
    s4 = buat(periode[3])
    cek("P4 hitung ulang lagi: satu baris PPh 21 dan angka sama (idempoten)", len(pph(s4)) == 1 and int(pph(s4)[0].amount) == jumlah_awal)
    s1 = slip_dari(periode[0])
    cek("P5 hanya slip terakhir yang memuat PPh 21", not pph(s1) and len(pph(s4)) == 1)


def periksa():
    global COMPANY
    COMPANY = frappe.db.get_value("Company", {}, "name")
    awal_settings = frappe.db.get_single_value("HRIS PPh21 Settings", "enabled")
    n_slip = frappe.db.count("HRIS Payroll Slip")
    try:
        for nama, label, kw, hari in JADWAL:
            uji_jadwal(nama, label, kw, hari)
        uji_pph21_mingguan()
    finally:
        frappe.db.rollback()
    cek("Z1 tidak ada sisa jadwal uji", not frappe.db.count("HRIS Payroll Schedule", {"schedule_name": ["like", "ZZ Uji Jadwal%"]}))
    cek("Z1 tidak ada sisa tarif UJIM dan slip uji", not frappe.db.count("HRIS PPh21 TER Rate", {"ter_category": "UJIM"})
        and frappe.db.count("HRIS Payroll Slip") == n_slip)
    cek("Z1 pengaturan PPh 21 kembali seperti semula", frappe.db.get_single_value("HRIS PPh21 Settings", "enabled") == awal_settings)
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
