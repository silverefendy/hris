"""Uji 3b: tunjangan dan potongan komponen masuk HRIS Payroll Slip (K1-K6, D1-D3).

Semua perubahan data di-rollback. Jalankan:
bench --site hris-uji.local execute hris.hris_payroll.tests.uji_tunjangan_slip_integrasi.jalankan
"""

from decimal import Decimal

import frappe
from frappe.utils import flt

from hris.hris_payroll.services import payroll_pph21 as pph
from hris.hris_payroll.services import tunjangan_slip as ts
from hris.hris_payroll.services.payroll_slip import PERIOD, SLIP, proses_karyawan

TABEL = "HRIS Employee Component"
KATALOG = "HRIS Pay Component"
ITEM = "HRIS Payroll Slip Item"
PAY = "HRIS Employee Pay"
EMP = "HRIS Employee"
SAKLAR = ts.SAKLAR


def baca(nama):
    return frappe.db.sql(
        "select component, component_type, amount, taxable, source from `tab{0}` "
        "where parent=%s and parenttype=%s and parentfield='components' order by idx".format(ITEM),
        (nama, SLIP), as_dict=True)


def total(nama):
    return frappe.db.get_value(SLIP, nama, ["total_earning", "total_deduction", "net_pay", "calc_notes"], as_dict=True)


def ringkas(nama):
    return [(r.component, flt(r.amount), r.taxable) for r in baca(nama)]


def bruto_kena_pajak(baris):
    return sum((Decimal(str(r.amount)) for r in baris if r.component_type == "Pendapatan" and r.taxable), Decimal(0))


def foto():
    """Keadaan data gaji dan tanggal masuk, untuk membuktikan rollback (Z4)."""
    return (
        frappe.db.sql("select name, effective_from, effective_to from `tab{0}` order by name".format(PAY)),
        frappe.db.sql(
            "select name, date_of_joining from `tab{0}` where name in (select employee from `tab{1}`) order by name".format(EMP, PAY)),
    )


def pilih_pasangan():
    """Mencari (periode Draft, karyawan) yang bisa diproses.

    Untuk karyawan Bulanan dengan satu baris gaji, tanggal masuk dan masa berlaku gaji dinormalkan di dalam
    transaksi uji (di-rollback). Mengembalikan (period, karyawan, nama_slip, pay_type, {}) atau
    (None, None, None, None, {alasan: [periode/karyawan]})."""
    alasan = {}
    for p in frappe.get_all(PERIOD, filters={"status": "Draft"}, fields=["name", "payroll_schedule"], order_by="name"):
        period = frappe.get_doc(PERIOD, p.name)
        daftar = frappe.db.sql_list(
            "select distinct employee from `tab{0}` where payroll_schedule=%s order by employee".format(PAY), p.payroll_schedule)
        for e in daftar:
            baris = frappe.get_all(PAY, filters={"employee": e, "payroll_schedule": p.payroll_schedule}, fields=["name", "pay_type"])
            if len(baris) == 1 and baris[0].pay_type == "Bulanan":
                frappe.db.set_value(PAY, baris[0].name, {"effective_from": "2000-01-01", "effective_to": None})
                frappe.db.set_value(EMP, e, "date_of_joining", "2000-01-01")
            jenis, info = proses_karyawan(period, e)
            if jenis != "dilewati":
                return period, e, info, frappe.db.get_value(SLIP, info, "pay_type"), {}
            alasan.setdefault(str(info)[:170], []).append("%s/%s" % (p.name, e))
    return None, None, None, None, alasan


def uji_database(cek, lewati):
    period, karyawan, nama, tipe, alasan = pilih_pasangan()
    if period is None:
        lewati("uji database", "tidak ada pasangan periode Draft dan karyawan yang bisa diproses. Alasan per kandidat:")
        for a, daftar in list(alasan.items())[:6]:
            print("         - %s [%s]" % (a, ", ".join(daftar[:3])))
        return
    print("INFO   uji database memakai %s / %s (%s)" % (period.name, karyawan, tipe))
    nama_bonus = frappe.db.get_value(KATALOG, "BONUS", "component_name") or "BONUS"
    nama_pot = frappe.db.get_value(KATALOG, "POT_LAIN", "component_name") or "POT_LAIN"
    baris0, total0 = baca(nama), total(nama)
    he = frappe._dict(name=karyawan)

    def hitung_ulang():
        return proses_karyawan(period, karyawan)

    def aktif(kode, nilai=1):
        frappe.db.set_value(KATALOG, kode, "is_active", nilai)

    def buat(kode, status, jumlah):
        d = frappe.get_doc({
            "doctype": TABEL, "employee": karyawan, "component": kode, "status": status, "amount": jumlah,
            "date_from": str(period.period_start), "date_to": str(period.period_end),
            "is_active": 1, "reason": "uji 3b",
        })
        d.insert(ignore_permissions=True)
        return d

    def hitung_notif():
        return frappe.db.count("Notification Log", {"document_type": PERIOD, "document_name": period.name})

    cek("U1 semua komponen nonaktif: tidak ada baris tunjangan Otomatis",
        all(r.component not in (nama_bonus, nama_pot) for r in baris0 if r.source == "Otomatis"),
        [(r.component, r.source) for r in baris0])

    cek("U1b tanpa komponen otomatis: tidak ada peringatan nama ganda", "ada baris Manual" not in (total0.calc_notes or ""))

    # ---- U2 tunjangan masuk, saklar mati ----
    buat("BONUS", "Berlaku", 12345)
    aktif("BONUS")
    jenis, nama = hitung_ulang()
    baris = baca(nama)
    b = [r for r in baris if r.component == nama_bonus and r.source == "Otomatis"]
    cek("U2 tunjangan masuk: baris Otomatis, Pendapatan, 12.345",
        len(b) == 1 and b[0].source == "Otomatis" and b[0].component_type == "Pendapatan" and flt(b[0].amount) == 12345, b)
    cek("U2b saklar mati: taxable 0", bool(b) and b[0].taxable == 0, b)
    t = total(nama)
    cek("U2c total_earning naik 12.345", flt(t.total_earning) - flt(total0.total_earning) == 12345, (t.total_earning, total0.total_earning))
    lain_mati = pph._slip_lain(he, period, None, set())[1]
    cek("U2d PPh 21 slip lain: tunjangan taxable 0 tidak dihitung", lain_mati == bruto_kena_pajak(baris), (lain_mati, bruto_kena_pajak(baris)))

    manual0 = [(r.component, flt(r.amount)) for r in baris0 if r.source == "Manual"]
    cek("U2e baris Manual tidak tersentuh (nama boleh sama dengan komponen otomatis)",
        [(r.component, flt(r.amount)) for r in baris if r.source == "Manual"] == manual0, manual0)

    cek("U2f peringatan nama ganda (K7): Manual Bonus dan Bonus otomatis",
        "ada baris Manual" in (t.calc_notes or ""), (t.calc_notes or "")[:200])

    # ---- U3 saklar hidup ----
    frappe.conf[SAKLAR] = 1
    hitung_ulang()
    baris = baca(nama)
    b = [r for r in baris if r.component == nama_bonus and r.source == "Otomatis"]
    cek("U3 saklar hidup: taxable mengikut is_taxable (1)", bool(b) and b[0].taxable == 1, b)
    lain_hidup = pph._slip_lain(he, period, None, set())[1]
    cek("U3b PPh 21 slip lain: tunjangan ikut bruto, selisih 12.345",
        lain_hidup - lain_mati == 12345 and lain_hidup == bruto_kena_pajak(baris), (lain_hidup, lain_mati))
    frappe.conf.pop(SAKLAR, None)

    # ---- U4 Potongan (K3) ----
    sebelum_pot = total(nama)
    buat("POT_LAIN", "Berlaku", 5000)
    aktif("POT_LAIN")
    hitung_ulang()
    baris = baca(nama)
    p = [r for r in baris if r.component == nama_pot and r.source == "Otomatis"]
    cek("U4 Potongan: baris Otomatis, Potongan, 5.000, taxable 0",
        len(p) == 1 and p[0].component_type == "Potongan" and flt(p[0].amount) == 5000 and p[0].taxable == 0, p)
    t = total(nama)
    cek("U4b total_deduction naik 5.000", flt(t.total_deduction) - flt(sebelum_pot.total_deduction) == 5000, (t.total_deduction, sebelum_pot.total_deduction))

    # ---- U5 nonaktif lagi (K4) ----
    aktif("BONUS", 0)
    aktif("POT_LAIN", 0)
    hitung_ulang()
    t = total(nama)
    cek("U5 komponen nonaktif: baris hilang dan total kembali ke dasar",
        all(r.component not in (nama_bonus, nama_pot) for r in baca(nama) if r.source == "Otomatis")
        and flt(t.total_earning) == flt(total0.total_earning) and flt(t.total_deduction) == flt(total0.total_deduction),
        (t.total_earning, total0.total_earning))

    cek("U5b tanpa komponen otomatis: tidak ada peringatan nama ganda",
        "ada baris Manual" not in (total(nama).calc_notes or ""))

    # ---- U6 janggal (K5) + notifikasi ringkasan (D2) ----
    janggal_ok = True
    try:
        buat("TJ_MAKAN", "Berlaku", 0)
    except frappe.ValidationError as e:
        janggal_ok = False
        lewati("U6 janggal", "HEC Berlaku tanpa nominal ditolak sistem: %s" % str(e)[:100])
    if janggal_ok:
        aktif("TJ_MAKAN")
        ts.mulai_ringkasan()
        jenis, info = hitung_ulang()
        s = frappe.flags.get(ts.KUNCI)
        t = total(nama)
        cek("U6 janggal: slip tetap diperbarui", jenis == "diperbarui", (jenis, info))
        cek("U6b peringatan masuk calc_notes", "TJ_MAKAN" in (t.calc_notes or ""), (t.calc_notes or "")[:200])
        cek("U6c slip tercatat untuk ringkasan", s is not None and len(s["periksa"]) == 1, s)
        n0 = hitung_notif()
        ts.kirim_ringkasan(period)
        n1 = hitung_notif()
        cek("U6d notifikasi ringkasan dibuat", n1 > n0, (n0, n1))
        cek("U6e ringkasan direset setelah dikirim", frappe.flags.get(ts.KUNCI) is None)
        aktif("TJ_MAKAN", 0)

    # ---- U7 galat: karyawan dilewati dengan pesan jelas (D1), hanya Bulanan ----
    if tipe == "Bulanan":
        sebelum = ringkas(nama)
        frappe.db.set_value(KATALOG, "BONUS", "payment_basis", "Per Hari Hadir")
        aktif("BONUS")
        ts.mulai_ringkasan()
        jenis, info = hitung_ulang()
        s = frappe.flags.get(ts.KUNCI)
        cek("U7 komponen galat: dilewati dengan pesan Masalah yang menyebut komponen",
            jenis == "dilewati" and info.startswith("Masalah") and "BONUS" in info, (jenis, str(info)[:200]))
        cek("U7b slip lama tidak berubah", ringkas(nama) == sebelum)
        cek("U7c galat tercatat untuk ringkasan", s is not None and len(s["galat"]) == 1, s)
        frappe.flags[ts.KUNCI] = None
        frappe.db.set_value(KATALOG, "BONUS", "payment_basis", "Per Bulan")
        aktif("BONUS", 0)
    else:
        lewati("U7 galat", "karyawan terpilih %s; galat Per Hari Hadir hanya berlaku untuk Bulanan" % tipe)

    # ---- U8 slip Final tidak disentuh (K2) ----
    aktif("BONUS")
    sebelum = ringkas(nama)
    frappe.db.set_value(SLIP, nama, "status", "Final")
    jenis, info = hitung_ulang()
    cek("U8 slip Final: dilewati (terkunci) dan isi tidak berubah",
        jenis == "dilewati" and "terkunci" in str(info) and ringkas(nama) == sebelum, (jenis, str(info)[:120]))
    frappe.db.set_value(SLIP, nama, "status", "Draft")
    aktif("BONUS", 0)


def jalankan():
    hasil = []

    def cek(nama, kondisi, info=""):
        hasil.append(bool(kondisi))
        print(("OK     " if kondisi else "GAGAL  ") + nama + (" | " + str(info)[:220] if info != "" else ""))

    def lewati(nama, alasan):
        print("SKIP   %s | %s" % (nama, alasan))

    awal_hec = frappe.db.count(TABEL)
    awal_item = frappe.db.count(ITEM)
    awal_slip = frappe.db.count(SLIP)
    foto0 = foto()
    saklar_asli = frappe.conf.get(SAKLAR)
    try:
        # ---- murni ----
        frappe.conf.pop(SAKLAR, None)
        cek("M1 tanpa kunci: saklar mati", ts.saklar_pajak_hidup() is False)
        for nilai, harap in ((1, True), ("1", True), (0, False), ("0", False)):
            frappe.conf[SAKLAR] = nilai
            cek("M2 nilai %r -> %s" % (nilai, harap), ts.saklar_pajak_hidup() is harap)
        frappe.conf.pop(SAKLAR, None)
        komp = [
            {"nama": "Gaji Pokok", "tipe": "Pendapatan", "jumlah": 3000000},
            {"nama": "Bonus", "tipe": "Pendapatan", "jumlah": 12345, "taxable": 0},
            {"nama": "Tunjangan Makan", "tipe": "Pendapatan", "jumlah": 300000, "taxable": 1},
            {"nama": "Potongan Telat", "tipe": "Potongan", "jumlah": 50000},
            {"nama": "Lembur", "tipe": "Pendapatan", "jumlah": 100000},
        ]
        cek("M3 bruto: taxable 0 tidak dihitung; tanpa kunci taxable tetap dihitung",
            pph._bruto_sendiri(komp, set()) == Decimal(3400000), pph._bruto_sendiri(komp, set()))
        cek("M4 daftar pengecualian PPh 21 tetap berlaku",
            pph._bruto_sendiri(komp, {"lembur"}) == Decimal(3300000), pph._bruto_sendiri(komp, {"lembur"}))

        # ---- database ----
        if frappe.db.count(KATALOG, {"is_active": 1}):
            lewati("uji database", "ada komponen aktif di katalog; nonaktifkan semuanya dulu")
        elif not all(frappe.db.exists(KATALOG, k) for k in ("BONUS", "POT_LAIN", "TJ_MAKAN")):
            lewati("uji database", "komponen BONUS, POT_LAIN, atau TJ_MAKAN tidak ada di katalog")
        else:
            uji_database(cek, lewati)
    finally:
        frappe.db.rollback()
        frappe.flags[ts.KUNCI] = None
        if saklar_asli is None:
            frappe.conf.pop(SAKLAR, None)
        else:
            frappe.conf[SAKLAR] = saklar_asli

    cek("Z1 tidak ada sisa HEC uji", frappe.db.count(TABEL) == awal_hec, (frappe.db.count(TABEL), awal_hec))
    cek("Z2 slip dan baris slip kembali seperti semula",
        frappe.db.count(SLIP) == awal_slip and frappe.db.count(ITEM) == awal_item)
    cek("Z3 katalog kembali: tidak ada komponen aktif, basis BONUS Per Bulan",
        frappe.db.count(KATALOG, {"is_active": 1}) == 0
        and (frappe.db.get_value(KATALOG, "BONUS", "payment_basis") or "Per Bulan") == "Per Bulan")
    cek("Z4 tanggal berlaku gaji dan tanggal masuk kembali seperti semula", foto() == foto0)
    print("OK %d, GAGAL %d (data uji di-rollback)" % (sum(hasil), len(hasil) - sum(hasil)))
