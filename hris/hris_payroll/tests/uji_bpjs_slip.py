"""Uji BPJS pada slip (K-133 langkah 3). Semua tarif hanya CONTOH FIKTIF. Semua perubahan di-rollback.
Jalankan dari folder sites: ../env/bin/python <path ini>."""

from datetime import date

import frappe
from frappe.utils import cstr, flt

SITE = "hris-uji.local"
SLIP = "HRIS Payroll Slip"
RATE = "HRIS BPJS Rate"
SCHEDULE = "HRIS Payroll Schedule"
CATATAN = "TARIF CONTOH UJI, BUKAN TARIF RESMI"
NAMA_JADWAL = "ZZ Uji BPJS Slip"
FLAG = ["bpjs_kes_enrolled", "bpjs_jht_enrolled", "bpjs_jp_enrolled", "bpjs_jkk_enrolled", "bpjs_jkm_enrolled"]

frappe.init(site=SITE, sites_path=".")
frappe.connect()
frappe.set_user("Administrator")

hasil = []
state = {"period": None}


def cek(nama, kondisi, rinci=""):
    hasil.append(bool(kondisi))
    print(("OK      " if kondisi else "GAGAL   ") + nama + ("" if kondisi or not rinci else "  " + str(rinci)))


def ditolak(fn):
    try:
        fn()
    except frappe.ValidationError as exc:
        return str(exc)
    return None


def komp(slip):
    return {r.component: flt(r.amount) for r in slip.components}


def uji_murni():
    from hris.hris_payroll.services import payroll_bpjs as pb

    h = pb.hitung_iuran(3000000, 0, 2, 3.7)
    cek("P1 iuran biasa (60.000 dan 111.000)", h == {"dasar_iuran": 3000000, "iuran_karyawan": 60000, "bagian_perusahaan": 111000}, h)
    h = pb.hitung_iuran(15000000, 10000000, 1, 2)
    cek("P2 batas upah (dasar 10.000.000)", h == {"dasar_iuran": 10000000, "iuran_karyawan": 100000, "bagian_perusahaan": 200000}, h)
    h = pb.hitung_iuran(100, 0, 0.5, 0.5)
    cek("P3 pembulatan setengah ke atas (0,5 menjadi 1)", h["iuran_karyawan"] == 1 and h["bagian_perusahaan"] == 1, h)
    h = pb.hitung_iuran(3000000, 0, 0, 0)
    cek("P4 tarif nol: iuran nol", h["iuran_karyawan"] == 0 and h["bagian_perusahaan"] == 0, h)
    h = pb.hitung_iuran(5000000, None, 1, 1)
    cek("P5 batas kosong = tanpa batas", h["dasar_iuran"] == 5000000 and h["iuran_karyawan"] == 50000, h)

    mingguan = {"schedule_type": "Mingguan", "week_start_day": "Kamis"}
    cek(
        "T1 mingguan: periode berakhir 28 Okt = slip terakhir Oktober",
        pb.terakhir_bulan_murni(mingguan, 1, "Tetap", date(2026, 10, 28), date(2026, 10, 29)) is True,
    )
    cek(
        "T2 mingguan: periode berakhir 21 Okt bukan slip terakhir",
        pb.terakhir_bulan_murni(mingguan, 1, "Tetap", date(2026, 10, 21), date(2026, 10, 22)) is False,
    )
    bulanan = {"schedule_type": "Bulanan", "cut_off_day": 26}
    cek(
        "T3 bulanan: selalu slip terakhir bulan itu",
        pb.terakhir_bulan_murni(bulanan, 3, "Maju ke Senin", date(2026, 10, 26), date(2026, 10, 29)) is True,
    )
    tetap = {"schedule_type": "Tanggal Tetap", "cut_off_days": [14, 28]}
    cek(
        "T4a tanggal tetap: periode berakhir 14 Okt bukan slip terakhir",
        pb.terakhir_bulan_murni(tetap, 1, "Tetap", date(2026, 10, 14), date(2026, 10, 15)) is False,
    )
    cek(
        "T4b tanggal tetap: periode berakhir 28 Okt slip terakhir",
        pb.terakhir_bulan_murni(tetap, 1, "Tetap", date(2026, 10, 28), date(2026, 10, 29)) is True,
    )
    sebelum = pb.sebelumnya_murni(mingguan, 1, "Tetap", date(2026, 10, 22), date(2026, 10, 29))
    cek("T5 mingguan: 4 periode sebelumnya dibayar di Oktober", len(sebelum) == 4, sebelum)


def uji_db():
    from hris.hris_payroll.services import payroll_slip as ps
    from hris.hris_payroll.services.payroll_schedule import compute_period

    awal, akhir = compute_period({"schedule_type": "Bulanan", "cut_off_day": 26}, date(2026, 10, 17))
    kand = frappe.db.sql(
        """
        select he.name as he, he.company as company, he.erpnext_employee as emp, count(*) as n
        from `tabHRIS Employee` he
        inner join `tabHRIS Working Hour` wh on wh.employee = he.erpnext_employee
        where wh.work_date between %(a)s and %(b)s
          and he.date_of_joining <= %(a)s
          and (he.resign_date is null or he.resign_date > %(b)s)
          and wh.status in ('Hadir', 'Tidak Lengkap', 'Tidak Hadir')
          and ifnull(wh.scheduled_hours, 0) > 0
          and not exists (select 1 from `tabHRIS Employee Pay` ep where ep.employee = he.name)
        group by he.name, he.company, he.erpnext_employee
        order by n desc limit 1
        """,
        {"a": str(awal), "b": str(akhir)},
        as_dict=True,
    )
    cek("D0 ada karyawan kandidat dengan Working Hour pada periode", bool(kand), "periode %s s/d %s" % (awal, akhir))
    if not kand:
        return
    he, company = kand[0].he, kand[0].company
    n_rate = frappe.db.count(RATE)
    cek("D0b tabel HRIS BPJS Rate kosong (uji tidak bercampur data nyata)", n_rate == 0, n_rate)
    if n_rate:
        return

    def tarif(program, kar, per, cap=0, kelas=""):
        d = frappe.get_doc(
            {
                "doctype": RATE, "company": company, "program": program, "risk_class": kelas,
                "employee_rate": kar, "company_rate": per, "wage_cap": cap,
                "effective_from": "2026-01-01", "notes": CATATAN,
            }
        )
        d.insert(ignore_permissions=True)
        return d

    kes = tarif("BPJS Kesehatan", 1, 4, 12000000)
    jht = tarif("JHT", 2, 3.7)
    tarif("JP", 1, 2, 10000000)
    tarif("JKK", 0, 0.24, 0, "I")
    tarif("JKM", 0, 0.3)

    sch = frappe.get_doc(
        {
            "doctype": SCHEDULE, "schedule_name": NAMA_JADWAL, "company": company,
            "schedule_type": "Bulanan", "is_active": 1, "pay_date_offset_days": 3,
            "sunday_rule": "Maju ke Senin", "cut_off_day": 26,
        }
    ).insert(ignore_permissions=True)
    frappe.get_doc(
        {
            "doctype": "HRIS Employee Pay", "employee": he, "pay_type": "Bulanan", "amount": 3000000,
            "payroll_schedule": sch.name, "effective_from": "2026-01-01",
        }
    ).insert(ignore_permissions=True)
    period = frappe.get_doc(
        {"doctype": "HRIS Payroll Period", "payroll_schedule": sch.name, "reference_date": "2026-10-17"}
    ).insert(ignore_permissions=True)
    state["period"] = period.name

    semua = {k: 1 for k in FLAG}
    semua["bpjs_jkk_risk_class"] = "I"
    frappe.db.set_value("HRIS Employee", he, semua)

    res = ps.buat_slip(period.name, "Karyawan", employee=he)
    cek("D1 slip dibuat", res.get("dibuat") == 1, res)
    nama = frappe.db.get_value(SLIP, {"payroll_period": period.name, "employee": he}, "name")
    if not nama:
        return
    s = frappe.get_doc(SLIP, nama)
    k = komp(s)
    cek("B1 Iuran BPJS Kesehatan 1% x 3.000.000 = 30.000", k.get("Iuran BPJS Kesehatan") == 30000, k)
    cek("B2 Iuran JHT 2% = 60.000", k.get("Iuran JHT") == 60000, k)
    cek("B3 Iuran JP 1% = 30.000", k.get("Iuran JP") == 30000, k)
    cek("B4 JKK dan JKM (tarif karyawan 0) tidak menjadi potongan", "Iuran JKK" not in k and "Iuran JKM" not in k, k)
    cek("B5 rincian BPJS lima baris", len(s.bpjs_items) == 5, len(s.bpjs_items))
    harapan = {
        "BPJS Kesehatan": (30000, 120000), "JHT": (60000, 111000), "JP": (30000, 60000),
        "JKK": (0, 7200), "JKM": (0, 9000),
    }
    nyata = {r.program: (int(round(flt(r.employee_amount))), int(round(flt(r.company_amount)))) for r in s.bpjs_items}
    cek("B6 iuran karyawan dan bagian perusahaan per program sesuai hitungan tangan", nyata == harapan, nyata)
    potongan = sum(flt(r.amount) for r in s.components if r.component_type == "Potongan")
    pendapatan = sum(flt(r.amount) for r in s.components if r.component_type == "Pendapatan")
    cek(
        "B7 total potongan dan gaji bersih konsisten",
        abs(flt(s.total_deduction) - potongan) < 0.5 and abs(flt(s.net_pay) - (pendapatan - potongan)) < 0.5,
        (s.total_deduction, potongan, s.net_pay),
    )
    cek("B8 catatan hitung menyebut BPJS", "BPJS" in cstr(s.calc_notes), s.calc_notes)

    ps.hitung_ulang_slip(nama)
    s2 = frappe.get_doc(SLIP, nama)
    nama_komp = [r.component for r in s2.components]
    cek(
        "B9 hitung ulang tidak menggandakan iuran dan rincian",
        len(s2.bpjs_items) == 5 and nama_komp.count("Iuran JHT") == 1 and komp(s2).get("Iuran JHT") == 60000,
        (len(s2.bpjs_items), nama_komp),
    )

    doc = frappe.get_doc(SLIP, nama)
    doc.bpjs_items[0].employee_amount = flt(doc.bpjs_items[0].employee_amount) + 1000
    pesan = ditolak(lambda: doc.save(ignore_permissions=True))
    cek("B10 rincian BPJS tidak bisa diubah dengan tangan", pesan is not None and "BPJS" in pesan, pesan)

    frappe.db.set_value(RATE, jht.name, "is_active", 0)
    pesan = ditolak(lambda: ps.hitung_ulang_slip(nama))
    cek("B11 tarif JHT hilang: slip dilewati dengan pesan menyebut JHT", pesan is not None and "JHT" in pesan, pesan)
    frappe.db.set_value(RATE, jht.name, "is_active", 1)

    frappe.db.set_value("HRIS Employee", he, "bpjs_jkk_risk_class", "")
    pesan = ditolak(lambda: ps.hitung_ulang_slip(nama))
    cek("B12 JKK tanpa kelas risiko: slip dilewati dengan pesan", pesan is not None and "Kelas Risiko" in pesan, pesan)
    frappe.db.set_value("HRIS Employee", he, "bpjs_jkk_risk_class", "I")

    frappe.db.set_value(RATE, kes.name, "wage_cap", 2000000)
    ps.hitung_ulang_slip(nama)
    s3 = frappe.get_doc(SLIP, nama)
    item = [r for r in s3.bpjs_items if r.program == "BPJS Kesehatan"]
    cek(
        "B13 batas upah 2.000.000: iuran Kesehatan 20.000 dan dasar iuran dibatasi",
        komp(s3).get("Iuran BPJS Kesehatan") == 20000 and item and int(flt(item[0].capped_base)) == 2000000,
        komp(s3),
    )

    frappe.db.set_value("HRIS Employee", he, {k2: 0 for k2 in FLAG})
    ps.hitung_ulang_slip(nama)
    s4 = frappe.get_doc(SLIP, nama)
    cek(
        "B14 bukan peserta: tanpa iuran dan tanpa rincian",
        not any(r.component.startswith("Iuran ") for r in s4.components) and len(s4.bpjs_items) == 0,
        [r.component for r in s4.components],
    )


try:
    if frappe.local.site != SITE:
        raise SystemExit("Site bukan %s; berhenti." % SITE)
    uji_murni()
    uji_db()
finally:
    frappe.db.rollback()
    if hasil:
        cek("Z1 tidak ada sisa tarif uji", frappe.db.count(RATE) == 0)
        sisa = frappe.db.exists(SLIP, {"payroll_period": state["period"]}) if state["period"] else None
        cek("Z2 tidak ada sisa slip uji", not sisa)
        print("HASIL: OK %d, GAGAL %d" % (hasil.count(True), hasil.count(False)))
    frappe.destroy()
