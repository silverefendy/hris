"""Uji BPJS pada slip (K-133, aturan angka tetap per karyawan). Semua perubahan di-rollback.
Jalankan dari folder sites: ../env/bin/python <path ini>."""

from datetime import date

import frappe
from frappe.utils import cstr, flt, getdate

SITE = "hris-uji.local"
SLIP = "HRIS Payroll Slip"
PERIOD = "HRIS Payroll Period"
SCHEDULE = "HRIS Payroll Schedule"
NAMA_BULANAN = "ZZ Uji BPJS Bulanan"
NAMA_MINGGUAN = "ZZ Uji BPJS Mingguan"
NAMA_TK = "ZZ Uji BPJS TK"
FLAG_RINCIAN = ["bpjs_jht_enrolled", "bpjs_jp_enrolled", "bpjs_jkk_enrolled", "bpjs_jkm_enrolled"]
FLAG = ["bpjs_kes_enrolled", "bpjs_jht_enrolled", "bpjs_jp_enrolled", "bpjs_jkk_enrolled", "bpjs_jkm_enrolled"]
JUMLAH = ["bpjs_kes_amount", "bpjs_jht_amount", "bpjs_jp_amount", "bpjs_jkk_amount", "bpjs_jkm_amount"]
ANGKA = {
    "bpjs_kes_amount": 30000, "bpjs_jht_amount": 60000, "bpjs_jp_amount": 30000,
    "bpjs_jkk_amount": 0, "bpjs_jkm_amount": 0,
}

frappe.init(site=SITE, sites_path=".")
frappe.connect()
frappe.set_user("Administrator")

hasil = []
skip = []
state = {"periods": []}


def cek(nama, kondisi, rinci=""):
    hasil.append(bool(kondisi))
    print(("OK      " if kondisi else "GAGAL   ") + nama + ("" if kondisi or not rinci else "  " + str(rinci)))


def lewati(nama, alasan):
    skip.append(nama)
    print("SKIP    " + nama + "  " + alasan)


def ditolak(fn):
    try:
        fn()
    except frappe.ValidationError as exc:
        return str(exc)
    return None


def komp(slip):
    return {r.component: flt(r.amount) for r in slip.components}


def uji_meta():
    meta = frappe.get_meta("HRIS Employee")
    for f in JUMLAH:
        df = meta.get_field(f)
        ok = df is not None and (df.permlevel or 0) == 1 and df.get("non_negative") in (1, True)
        cek("F1 %s: ada, permlevel 1, tidak boleh negatif" % f, ok, df.as_dict() if df else "field tidak ada")
    lama = [meta.get_field("bpjs_jkk_risk_class"), meta.get_field("bpjs_wage_basis")]
    cek("F2 Kelas Risiko JKK dan Dasar Upah BPJS disembunyikan", all(d is not None and d.hidden for d in lama))


def uji_murni():
    from hris.hris_payroll.services import payroll_bpjs as pb

    bulanan = {"schedule_type": "Bulanan", "cut_off_day": 26}
    cek(
        "M1 bulanan: slip bulan itu adalah yang pertama",
        pb.pertama_bulan_murni(bulanan, 3, "Maju ke Senin", date(2026, 9, 27), date(2026, 10, 29)) is True,
    )
    ming = {"schedule_type": "Mingguan", "week_start_day": "Kamis"}
    cek("W1 mingguan: bayar 1 Okt = pertama Oktober", pb.pertama_bulan_murni(ming, 1, "Maju ke Senin", date(2026, 9, 24), date(2026, 10, 1)) is True)
    cek("W2 mingguan: bayar 8 Okt bukan pertama", pb.pertama_bulan_murni(ming, 1, "Maju ke Senin", date(2026, 10, 1), date(2026, 10, 8)) is False)
    cek("W3 mingguan: bayar 29 Okt bukan pertama", pb.pertama_bulan_murni(ming, 1, "Maju ke Senin", date(2026, 10, 22), date(2026, 10, 29)) is False)
    cek("W4 mingguan: bayar 5 Nov = pertama November", pb.pertama_bulan_murni(ming, 1, "Maju ke Senin", date(2026, 10, 29), date(2026, 11, 5)) is True)
    tetap = {"schedule_type": "Tanggal Tetap", "cut_off_days": [14, 28]}
    cek("T1 tanggal tetap: bayar 15 Okt = pertama", pb.pertama_bulan_murni(tetap, 1, "Maju ke Senin", date(2026, 9, 29), date(2026, 10, 15)) is True)
    cek("T2 tanggal tetap: bayar 29 Okt bukan pertama", pb.pertama_bulan_murni(tetap, 1, "Maju ke Senin", date(2026, 10, 15), date(2026, 10, 29)) is False)
    dua = {"schedule_type": "Harian", "period_days": 14, "anchor_date": date(2026, 9, 24)}
    cek("D1 14 hari: bayar 8 Okt = pertama", pb.pertama_bulan_murni(dua, 1, "Maju ke Senin", date(2026, 9, 24), date(2026, 10, 8)) is True)
    cek("D2 14 hari: bayar 22 Okt bukan pertama", pb.pertama_bulan_murni(dua, 1, "Maju ke Senin", date(2026, 10, 8), date(2026, 10, 22)) is False)
    cek("D3 14 hari: bayar 5 Nov = pertama November", pb.pertama_bulan_murni(dua, 1, "Maju ke Senin", date(2026, 10, 22), date(2026, 11, 5)) is True)


def kandidat(awal, akhir):
    return frappe.db.sql(
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
        order by n desc limit 50
        """,
        {"a": str(awal), "b": str(akhir)},
        as_dict=True,
    )


def set_peserta(he, flags=(1, 1, 1, 1, 1), angka=None):
    nilai = dict(zip(FLAG, flags))
    nilai.update(ANGKA if angka is None else angka)
    frappe.db.set_value("HRIS Employee", he, nilai)


def uji_db():
    from hris.hris_payroll.services import payroll_bpjs as pb
    from hris.hris_payroll.services import payroll_slip as ps
    from hris.hris_payroll.services.payroll_schedule import compute_pay_date, compute_period

    awal, akhir = compute_period({"schedule_type": "Bulanan", "cut_off_day": 26}, date(2026, 10, 17))
    kand = kandidat(awal, akhir)
    cek("D0 ada karyawan kandidat dengan Working Hour pada periode", bool(kand), "periode %s s/d %s" % (awal, akhir))
    if not kand:
        return
    he, company = kand[0].he, kand[0].company

    # ---------- Bulanan ----------
    sch = frappe.get_doc(
        {
            "doctype": SCHEDULE, "schedule_name": NAMA_BULANAN, "company": company,
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
    period = frappe.get_doc({"doctype": PERIOD, "payroll_schedule": sch.name, "reference_date": "2026-10-17"}).insert(ignore_permissions=True)
    state["periods"].append(period.name)
    set_peserta(he)

    res = ps.buat_slip(period.name, "Karyawan", employee=he)
    cek("D1 slip Bulanan dibuat", res.get("dibuat") == 1, res)
    nama = frappe.db.get_value(SLIP, {"payroll_period": period.name, "employee": he}, "name")
    if not nama:
        return
    s = frappe.get_doc(SLIP, nama)
    k = komp(s)
    cek("B1 Iuran BPJS Kesehatan = 30.000 (angka tetap)", k.get("Iuran BPJS Kesehatan") == 30000, k)
    cek("B2 Iuran JHT = 60.000", k.get("Iuran JHT") == 60000, k)
    cek("B3 Iuran JP = 30.000", k.get("Iuran JP") == 30000, k)
    cek("B4 JKK dan JKM (angka 0) tidak menjadi potongan", "Iuran JKK" not in k and "Iuran JKM" not in k, k)
    nyata = {r.program: int(round(flt(r.employee_amount))) for r in s.bpjs_items}
    cek(
        "B5 rincian lima program sesuai angka",
        nyata == {"BPJS Kesehatan": 30000, "JHT": 60000, "JP": 30000, "JKK": 0, "JKM": 0},
        nyata,
    )
    potongan = sum(flt(r.amount) for r in s.components if r.component_type == "Potongan")
    pendapatan = sum(flt(r.amount) for r in s.components if r.component_type == "Pendapatan")
    cek(
        "B6 total potongan dan gaji bersih konsisten",
        abs(flt(s.total_deduction) - potongan) < 0.5 and abs(flt(s.net_pay) - (pendapatan - potongan)) < 0.5,
        (s.total_deduction, potongan, s.net_pay),
    )
    cek("B7 catatan hitung menyebut slip pertama", "slip pertama" in cstr(s.calc_notes), s.calc_notes)

    ps.hitung_ulang_slip(nama)
    s2 = frappe.get_doc(SLIP, nama)
    nama_komp = [r.component for r in s2.components]
    cek(
        "B8 hitung ulang tidak menggandakan iuran dan rincian",
        len(s2.bpjs_items) == 5 and nama_komp.count("Iuran JHT") == 1 and komp(s2).get("Iuran JHT") == 60000,
        (len(s2.bpjs_items), nama_komp),
    )

    doc = frappe.get_doc(SLIP, nama)
    doc.bpjs_items[0].employee_amount = flt(doc.bpjs_items[0].employee_amount) + 1000
    pesan = ditolak(lambda: doc.save(ignore_permissions=True))
    cek("B9 rincian BPJS tidak bisa diubah dengan tangan", pesan is not None and "BPJS" in pesan, pesan)

    frappe.db.set_value("HRIS Employee", he, "bpjs_jht_amount", 75000)
    ps.hitung_ulang_slip(nama)
    cek("B10 angka JHT diubah di data karyawan: hitung ulang memakai 75.000", komp(frappe.get_doc(SLIP, nama)).get("Iuran JHT") == 75000)

    frappe.db.set_value("HRIS Employee", he, "bpjs_jp_enrolled", 0)
    ps.hitung_ulang_slip(nama)
    s3 = frappe.get_doc(SLIP, nama)
    cek(
        "B11 JP dicabut: tanpa iuran JP dan rincian empat baris",
        "Iuran JP" not in komp(s3) and len(s3.bpjs_items) == 4 and all(r.program != "JP" for r in s3.bpjs_items),
        (komp(s3), len(s3.bpjs_items)),
    )

    frappe.db.set_value("HRIS Employee", he, "bpjs_kes_amount", 0)
    ps.hitung_ulang_slip(nama)
    s4 = frappe.get_doc(SLIP, nama)
    baris_kes = [r for r in s4.bpjs_items if r.program == "BPJS Kesehatan"]
    cek(
        "B12 peserta dengan angka 0: ada baris rincian, tanpa potongan",
        "Iuran BPJS Kesehatan" not in komp(s4) and len(baris_kes) == 1 and flt(baris_kes[0].employee_amount) == 0,
        komp(s4),
    )

    frappe.db.set_value("HRIS Employee", he, "bpjs_kes_amount", 5000000)
    ps.hitung_ulang_slip(nama)
    s5 = frappe.get_doc(SLIP, nama)
    cek(
        "B13 iuran lebih besar dari gaji: slip tetap tersimpan, ada peringatan negatif",
        flt(s5.net_pay) < 0 and "negatif" in cstr(s5.calc_notes).lower(),
        (s5.net_pay, s5.calc_notes),
    )

    frappe.db.set_value("HRIS Employee", he, {f: 0 for f in FLAG})
    ps.hitung_ulang_slip(nama)
    s6 = frappe.get_doc(SLIP, nama)
    cek(
        "B14 bukan peserta: tanpa iuran dan tanpa rincian",
        not any(r.component.startswith("Iuran ") for r in s6.components) and len(s6.bpjs_items) == 0,
        [r.component for r in s6.components],
    )

    # ---------- Harian, jadwal Mingguan ----------
    he2 = None
    for kk in kand:
        if kk.company == company and kk.he != he:
            he2 = kk
            break
    if not he2:
        lewati("H*", "tidak ada karyawan kandidat kedua di company yang sama")
        return
    params = {"schedule_type": "Mingguan", "week_start_day": "Kamis"}
    tanggal = frappe.db.sql_list(
        """
        select distinct wh.work_date from `tabHRIS Working Hour` wh
        where wh.employee = %(e)s and wh.work_date between %(a)s and %(b)s
          and wh.status in ('Hadir', 'Tidak Lengkap', 'Tidak Hadir') and ifnull(wh.scheduled_hours, 0) > 0
        order by wh.work_date
        """,
        {"e": he2.emp, "a": "2026-08-01", "b": "2026-11-09"},
    )
    info = []
    for d in tanggal:
        d = getdate(d)
        a, b = compute_period(params, d)
        bayar = compute_pay_date(b, 1, "Maju ke Senin")
        info.append((d, bayar, pb.pertama_bulan_murni(params, 1, "Maju ke Senin", a, bayar)))
    pasangan = None
    for d1, p1, f1 in info:
        if not f1:
            continue
        for d2, p2, f2 in info:
            if (not f2) and (p2.year, p2.month) == (p1.year, p1.month):
                pasangan = (d1, d2)
                break
        if pasangan:
            break
    if not pasangan:
        lewati("H*", "Working Hour karyawan kedua tidak punya pasangan minggu (pertama dan berikutnya di bulan bayar yang sama)")
        return
    cek("H0 pasangan minggu ditemukan (pertama dan berikutnya, bulan bayar sama)", True, pasangan)

    sch2 = frappe.get_doc(
        {
            "doctype": SCHEDULE, "schedule_name": NAMA_MINGGUAN, "company": company,
            "schedule_type": "Mingguan", "is_active": 1, "pay_date_offset_days": 1,
            "sunday_rule": "Maju ke Senin", "week_start_day": "Kamis",
        }
    ).insert(ignore_permissions=True)
    frappe.get_doc(
        {
            "doctype": "HRIS Employee Pay", "employee": he2.he, "pay_type": "Harian", "amount": 120000,
            "payroll_schedule": sch2.name, "effective_from": "2026-01-01",
        }
    ).insert(ignore_permissions=True)
    set_peserta(he2.he)

    slip_nama = {}
    for label, d in (("pertama", pasangan[0]), ("berikutnya", pasangan[1])):
        per = frappe.get_doc({"doctype": PERIOD, "payroll_schedule": sch2.name, "reference_date": str(d)}).insert(ignore_permissions=True)
        state["periods"].append(per.name)
        res = ps.buat_slip(per.name, "Karyawan", employee=he2.he)
        cek("H1 slip Harian %s dibuat" % label, res.get("dibuat") == 1, res)
        slip_nama[label] = frappe.db.get_value(SLIP, {"payroll_period": per.name, "employee": he2.he}, "name")
    if not all(slip_nama.values()):
        return
    sp = frappe.get_doc(SLIP, slip_nama["pertama"])
    sb = frappe.get_doc(SLIP, slip_nama["berikutnya"])
    kp = komp(sp)
    cek(
        "H2 slip pertama bulan itu: iuran penuh 30.000, 60.000, 30.000 (tidak bergantung upah)",
        kp.get("Iuran BPJS Kesehatan") == 30000 and kp.get("Iuran JHT") == 60000 and kp.get("Iuran JP") == 30000 and len(sp.bpjs_items) == 5,
        (kp, len(sp.bpjs_items)),
    )
    cek(
        "H3 slip berikutnya di bulan yang sama: tanpa iuran, tanpa rincian, catatan menjelaskan",
        not any(r.component.startswith("Iuran ") for r in sb.components) and len(sb.bpjs_items) == 0 and "tidak dipotong" in cstr(sb.calc_notes),
        (komp(sb), sb.calc_notes),
    )
    total = sum(flt(r.amount) for sl in (sp, sb) for r in sl.components if r.component.startswith("Iuran "))
    cek("H4 total iuran satu bulan = 120.000 (satu kali)", total == 120000, total)


def set_tk(he, tk=0, tk_angka=0, kes=0, kes_angka=0, rincian=(0, 0, 0, 0)):
    nilai = {
        "bpjs_tk_enrolled": tk, "bpjs_tk_amount": tk_angka,
        "bpjs_kes_enrolled": kes, "bpjs_kes_amount": kes_angka,
        "bpjs_jht_amount": 60000, "bpjs_jp_amount": 30000, "bpjs_jkk_amount": 0, "bpjs_jkm_amount": 0,
    }
    nilai.update(dict(zip(FLAG_RINCIAN, rincian)))
    frappe.db.set_value("HRIS Employee", he, nilai)


def uji_tk_meta():
    meta = frappe.get_meta("HRIS Employee")
    for f in ("bpjs_tk_enrolled", "bpjs_tk_amount"):
        df = meta.get_field(f)
        cek("K1 %s: ada dan permlevel 1" % f, df is not None and (df.permlevel or 0) == 1, "field tidak ada" if df is None else df.as_dict())
    df = meta.get_field("bpjs_tk_amount")
    cek("K2 angka Ketenagakerjaan tidak boleh negatif", df is not None and df.get("non_negative") in (1, True))
    for f in FLAG_RINCIAN:
        df = meta.get_field(f)
        cek("K3 %s: read-only bila centang total aktif" % f, df is not None and "bpjs_tk_enrolled" in cstr(df.get("read_only_depends_on")))
    df = meta.get_field("bpjs_tk_enrolled")
    cek("K4 centang total: read-only bila ada rincian aktif", df is not None and "bpjs_jht_enrolled" in cstr(df.get("read_only_depends_on")))
    urut = [d.fieldname for d in meta.fields]
    cek(
        "K5 Iuran Ketenagakerjaan tepat di bawah Iuran Kesehatan",
        "bpjs_tk_amount" in urut and urut.index("bpjs_tk_amount") == urut.index("bpjs_kes_amount") + 1,
    )
    cek(
        "K6 centang Ketenagakerjaan tepat di bawah centang Kesehatan",
        "bpjs_tk_enrolled" in urut and urut.index("bpjs_tk_enrolled") == urut.index("bpjs_kes_enrolled") + 1,
    )


def uji_tk_db():
    from hris.hris_payroll.services import payroll_slip as ps
    from hris.hris_payroll.services.payroll_schedule import compute_period

    awal, akhir = compute_period({"schedule_type": "Bulanan", "cut_off_day": 26}, date(2026, 10, 17))
    kand = kandidat(awal, akhir)
    cek("K0 ada karyawan kandidat dengan Working Hour pada periode", bool(kand), "periode %s s/d %s" % (awal, akhir))
    if not kand:
        return
    he, company = kand[0].he, kand[0].company
    sch = frappe.get_doc(
        {
            "doctype": SCHEDULE, "schedule_name": NAMA_TK, "company": company,
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
    period = frappe.get_doc({"doctype": PERIOD, "payroll_schedule": sch.name, "reference_date": "2026-10-17"}).insert(ignore_permissions=True)
    state["periods"].append(period.name)

    # --- bentrok sejak awal: total dan rincian sama-sama aktif ---
    set_tk(he, tk=1, tk_angka=150000, rincian=(1, 0, 0, 0))
    res = ps.buat_slip(period.name, "Karyawan", employee=he)
    cek("K10 bentrok total dan rincian: slip dilewati, tidak dibuat", res.get("dilewati") == 1 and res.get("dibuat") == 0, res)
    alasan = " ".join(res.get("alasan", {}).keys())
    cek("K11 pesan bentrok memuat Masalah, Penyebab, Tindakan", all(k in alasan for k in ("Masalah", "Penyebab", "Tindakan")), alasan)
    cek("K12 tidak ada slip tersimpan untuk karyawan bentrok", not frappe.db.exists(SLIP, {"payroll_period": period.name, "employee": he}))

    # --- jalur total (bersama Kesehatan) ---
    set_tk(he, tk=1, tk_angka=150000, kes=1, kes_angka=30000)
    res = ps.buat_slip(period.name, "Karyawan", employee=he)
    cek("K20 slip jalur total dibuat", res.get("dibuat") == 1, res)
    nama = frappe.db.get_value(SLIP, {"payroll_period": period.name, "employee": he}, "name")
    if not nama:
        return
    s = frappe.get_doc(SLIP, nama)
    k = komp(s)
    cek("K21 satu potongan Iuran BPJS Ketenagakerjaan = 150.000", k.get("Iuran BPJS Ketenagakerjaan") == 150000, k)
    cek("K22 tidak ada potongan JHT, JP, JKK, JKM", not any(n in k for n in ("Iuran JHT", "Iuran JP", "Iuran JKK", "Iuran JKM")), k)
    cek("K23 Iuran Kesehatan tetap 30.000", k.get("Iuran BPJS Kesehatan") == 30000, k)
    nyata = {r.program: int(round(flt(r.employee_amount))) for r in s.bpjs_items}
    cek("K24 rincian dua baris: Kesehatan dan Ketenagakerjaan", nyata == {"BPJS Kesehatan": 30000, "BPJS Ketenagakerjaan": 150000}, nyata)
    baris = [r for r in s.bpjs_items if r.program == "BPJS Ketenagakerjaan"]
    cek("K25 dasar rincian: Angka tetap dari data karyawan", len(baris) == 1 and "Angka tetap" in cstr(baris[0].basis), [cstr(r.basis) for r in baris])
    cek("K26 baris potongan Ketenagakerjaan hanya satu", [r.component for r in s.components].count("Iuran BPJS Ketenagakerjaan") == 1)

    # --- bentrok pada slip yang sudah ada: dilewati, slip lama utuh ---
    set_tk(he, tk=1, tk_angka=150000, rincian=(1, 0, 0, 0))
    jenis, info = ps.proses_karyawan(frappe.get_doc(PERIOD, period.name), he)
    cek("K30 bentrok pada slip yang ada: dilewati dengan pesan Masalah", jenis == "dilewati" and "Masalah" in cstr(info), (jenis, info))
    s2 = frappe.get_doc(SLIP, nama)
    cek("K31 slip lama tidak berubah saat dilewati", komp(s2).get("Iuran BPJS Ketenagakerjaan") == 150000 and len(s2.bpjs_items) == 2, komp(s2))

    # --- pindah total -> rincian -> total ---
    set_tk(he, tk=0, rincian=(1, 1, 0, 0))
    ps.hitung_ulang_slip(nama)
    s3 = frappe.get_doc(SLIP, nama)
    k3 = komp(s3)
    cek(
        "K40 pindah total ke rincian: Iuran JHT dan JP ada, baris Ketenagakerjaan hilang",
        k3.get("Iuran JHT") == 60000 and k3.get("Iuran JP") == 30000 and "Iuran BPJS Ketenagakerjaan" not in k3,
        k3,
    )
    cek("K41 rincian slip: hanya JHT dan JP", {r.program for r in s3.bpjs_items} == {"JHT", "JP"}, [r.program for r in s3.bpjs_items])
    set_tk(he, tk=1, tk_angka=150000)
    ps.hitung_ulang_slip(nama)
    s4 = frappe.get_doc(SLIP, nama)
    k4 = komp(s4)
    cek(
        "K42 pindah rincian ke total: hanya satu potongan Ketenagakerjaan dan satu baris rincian",
        k4.get("Iuran BPJS Ketenagakerjaan") == 150000 and "Iuran JHT" not in k4 and "Iuran JP" not in k4 and len(s4.bpjs_items) == 1,
        (k4, len(s4.bpjs_items)),
    )

    # --- total berangka 0 dan tidak ikut ---
    set_tk(he, tk=1, tk_angka=0)
    ps.hitung_ulang_slip(nama)
    s5 = frappe.get_doc(SLIP, nama)
    cek(
        "K50 total angka 0: tanpa potongan, satu baris rincian bernilai 0",
        "Iuran BPJS Ketenagakerjaan" not in komp(s5) and len(s5.bpjs_items) == 1 and flt(s5.bpjs_items[0].employee_amount) == 0,
        komp(s5),
    )
    set_tk(he)
    ps.hitung_ulang_slip(nama)
    s6 = frappe.get_doc(SLIP, nama)
    cek(
        "K60 tidak ikut apa pun: tanpa iuran dan tanpa rincian",
        not any(r.component.startswith("Iuran ") for r in s6.components) and len(s6.bpjs_items) == 0,
        [r.component for r in s6.components],
    )


try:
    if frappe.local.site != SITE:
        raise SystemExit("Site bukan %s; berhenti." % SITE)
    uji_meta()
    uji_murni()
    uji_db()
    frappe.db.rollback()
    uji_tk_meta()
    uji_tk_db()
finally:
    frappe.db.rollback()
    if hasil:
        sisa = [n for n in state["periods"] if frappe.db.exists(PERIOD, n)]
        cek("Z1 tidak ada sisa periode uji", not sisa, sisa)
        sisa2 = [n for n in (NAMA_BULANAN, NAMA_MINGGUAN, NAMA_TK) if frappe.db.exists(SCHEDULE, {"schedule_name": n})]
        cek("Z2 tidak ada sisa jadwal uji", not sisa2, sisa2)
        print("HASIL: OK %d, GAGAL %d, SKIP %d" % (hasil.count(True), hasil.count(False), len(skip)))
    frappe.destroy()
