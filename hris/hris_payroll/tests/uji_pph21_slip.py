"""Uji PPh 21 pada slip (K-134 langkah 4), tarif FIKTIF. Fungsi data dan jadwal diganti agar logika diuji terpisah;
deteksi slip terakhir diuji terhadap Periode yang ada (hanya baca). Semua data di-rollback.
Jalankan dari folder sites: ../env/bin/python <path ini>."""

from decimal import Decimal

import frappe

SITE = "hris-uji.local"
frappe.init(site=SITE, sites_path=".")
frappe.connect()
frappe.set_user("Administrator")

from hris.hris_payroll.services import payroll_bpjs as bp
from hris.hris_payroll.services import payroll_pph21 as pp

hasil_uji = []


def cek(nama, kondisi, rinci=""):
    hasil_uji.append(bool(kondisi))
    print(("OK      " if kondisi else "GAGAL   ") + nama + ("" if kondisi or not rinci else "  " + str(rinci)))


S = {}
pp._data_karyawan = lambda he: S["data"]
pp._slip_saat_ini = lambda he, period: (None, Decimal(S["manual"]))
pp._slip_lain = lambda he, period, nama_ada, bebas: (S["lain"][0], Decimal(S["lain"][1]), S["lain"][2])
pp._slip_terakhir = lambda period: S["terakhir"]
pp._jumlah_slip_jadwal = lambda period: S["jadwal"]

HE = frappe._dict(name="UJI-PPH-HE")
PERIODE = frappe._dict(name="UJI-PERIODE", pay_date="2026-10-29", period_start="2026-10-27", period_end="2026-11-26")


def baru(data=None, manual=0, lain=(0, 0, None), terakhir=True, jadwal=1):
    S.update({"data": data if data is not None else {"pph21_enrolled": 1, "ptkp_status": "TK/0", "npwp": "123"},
              "manual": manual, "lain": lain, "terakhir": terakhir, "jadwal": jadwal})


def komp(*baris):
    return {"komponen": [{"nama": n, "tipe": t, "jumlah": Decimal(j), "dasar": ""} for n, t, j in baris], "catatan": []}


H4 = komp(("Upah Harian", "Pendapatan", 2500000), ("Uang Makan", "Pendapatan", 100000), ("Potongan Telat", "Potongan", 12500))


def jml(h):
    return h["komponen"][0]["jumlah"] if h["komponen"] else None


def atur(enabled=1, peta=None, bebas=(), pengali=1, pembulatan="Ke Bawah"):
    s = frappe.get_doc("HRIS PPh21 Settings")
    s.enabled = enabled
    s.set("ptkp_map", [])
    for a, b in (peta or {"TK/0": "UJIA"}).items():
        s.append("ptkp_map", {"ptkp_status": a, "ter_category": b})
    s.set("exempt_components", [])
    for n in bebas:
        s.append("exempt_components", {"component_name": n})
    s.no_npwp_multiplier = pengali
    s.rounding = pembulatan
    s.save()


def tarif(kat, dari, sampai, persen, terbuka=0):
    frappe.get_doc({"doctype": "HRIS PPh21 TER Rate", "ter_category": kat, "bruto_from": dari, "bruto_to": sampai,
                    "open_ended": terbuka, "rate_percent": persen, "effective_from": "2026-01-01", "enabled": 1}).insert()


try:
    if frappe.local.site != SITE:
        raise SystemExit("Site bukan %s; berhenti." % SITE)
    if frappe.db.count("HRIS PPh21 TER Rate", {"ter_category": ["in", ["UJIA", "UJIB"]]}):
        raise SystemExit("Ada sisa tarif UJIA/UJIB di site uji; hapus dulu, lalu ulangi.")
    tarif("UJIA", 0, 5000000, 0)
    tarif("UJIA", 5000001, 10000000, 2)
    tarif("UJIA", 10000001, None, 5, terbuka=1)
    tarif("UJIB", 0, None, 1.5, terbuka=1)

    baru(data={"pph21_enrolled": 0, "ptkp_status": "", "npwp": ""})
    atur()
    h = pp.hitung_pph21_slip(HE, PERIODE, None, H4)
    cek("U1 bukan peserta: tanpa komponen dan tanpa catatan", not h["komponen"] and not h["catatan"] and "dilewati" not in h)

    baru()
    atur(enabled=0)
    h = pp.hitung_pph21_slip(HE, PERIODE, None, H4)
    cek("U2 Settings mati: tanpa potongan, catatan menyebut belum diaktifkan",
        not h["komponen"] and "belum diaktifkan" in " ".join(h["catatan"]))

    atur()
    baru(data={"pph21_enrolled": 1, "ptkp_status": "", "npwp": "1"})
    h = pp.hitung_pph21_slip(HE, PERIODE, None, H4)
    cek("U3 PTKP kosong: dilewati dengan pesan", "Status PTKP kosong" in h.get("dilewati", ""), h)

    baru(data={"pph21_enrolled": 1, "ptkp_status": "K/3", "npwp": "1"})
    h = pp.hitung_pph21_slip(HE, PERIODE, None, H4)
    cek("U4 PTKP belum dipetakan: dilewati", "belum dipetakan" in h.get("dilewati", ""), h)

    baru(terakhir=False, lain=(3, 7500000, None), jadwal=4)
    h = pp.hitung_pph21_slip(HE, PERIODE, None, H4)
    cek("U5a bukan slip terakhir: tanpa potongan dan satu catatan",
        not h["komponen"] and len(h["catatan"]) == 1 and "slip terakhir" in h["catatan"][0], h)
    baru(terakhir=False, lain=(3, 7500000, "PSL-X"), jadwal=4)
    h = pp.hitung_pph21_slip(HE, PERIODE, None, H4)
    cek("U5b slip terakhir sudah memuat PPh 21: ada peringatan menyebut slipnya",
        len(h["catatan"]) == 2 and "PSL-X" in h["catatan"][1], h)

    baru(lain=(3, 7500000, None), jadwal=4)
    h = pp.hitung_pph21_slip(HE, PERIODE, None, H4)
    cek("U6 bruto 10,1 juta tarif 5% = 505.000", jml(h) == 505000 and h["komponen"][0]["nama"] == "PPh 21"
        and h["komponen"][0]["tipe"] == "Potongan", h)
    cek("U6b catatan memuat PPh 21 dan tidak ada peringatan (4 dari 4 slip)",
        "dipotong pada slip ini" in h["catatan"][0] and len(h["catatan"]) == 1, h["catatan"])

    atur(bebas=("uang makan",))
    h = pp.hitung_pph21_slip(HE, PERIODE, None, H4)
    cek("U7 komponen bebas pajak (tidak peka huruf): bruto 10,0 juta tarif 2% = 200.000", jml(h) == 200000, h)

    atur()
    baru(manual=500000, lain=(3, 7500000, None), jadwal=4)
    h = pp.hitung_pph21_slip(HE, PERIODE, None, H4)
    cek("U8 Manual kena pajak ikut: bruto 10,6 juta = 530.000", jml(h) == 530000, h)

    baru(lain=(1, 1400000, None), jadwal=2)
    h = pp.hitung_pph21_slip(HE, PERIODE, None, H4)
    cek("U9 tarif 0%: tanpa potongan, catatan menyebut tidak ada potongan",
        not h["komponen"] and "tidak ada potongan" in h["catatan"][0], h)

    atur(peta={"TK/0": "UJIZ"})
    baru(lain=(3, 7500000, None), jadwal=4)
    h = pp.hitung_pph21_slip(HE, PERIODE, None, H4)
    cek("U10 tarif tidak ketemu: dilewati dengan pesan", "Tarif TER tidak ditemukan" in h.get("dilewati", ""), h)

    atur(pengali=1.2)
    baru(data={"pph21_enrolled": 1, "ptkp_status": "TK/0", "npwp": ""}, lain=(3, 7500000, None), jadwal=4)
    h = pp.hitung_pph21_slip(HE, PERIODE, None, H4)
    cek("U11a tanpa NPWP: 505.000 x 1,2 = 606.000", jml(h) == 606000, h)
    baru(lain=(3, 7500000, None), jadwal=4)
    h = pp.hitung_pph21_slip(HE, PERIODE, None, H4)
    cek("U11b dengan NPWP: pengali tidak dipakai", jml(h) == 505000, h)

    satu = komp(("Upah Harian", "Pendapatan", 1000333))
    atur(peta={"TK/0": "UJIB"}, pembulatan="Ke Bawah")
    baru()
    h = pp.hitung_pph21_slip(HE, PERIODE, None, satu)
    cek("U12a pembulatan ke bawah: 15.004,995 menjadi 15.004", jml(h) == 15004, h)
    atur(peta={"TK/0": "UJIB"}, pembulatan="Terdekat")
    h = pp.hitung_pph21_slip(HE, PERIODE, None, satu)
    cek("U12b pembulatan terdekat: 15.004,995 menjadi 15.005", jml(h) == 15005, h)

    atur()
    baru(lain=(1, 7500000, None), jadwal=4)
    h = pp.hitung_pph21_slip(HE, PERIODE, None, H4)
    cek("U13 slip kurang dari jadwal: peringatan 2 dari 4",
        any("2 slip" in c and "4 slip" in c for c in h["catatan"]), h["catatan"])

    baru(lain=(3, 10000000, None), jadwal=4)
    h = pp.hitung_pph21_slip(HE, PERIODE, None, komp(("Upah Harian", "Pendapatan", 100000)))
    cek("U14 gaji bersih negatif: ada peringatan", any("negatif" in c for c in h["catatan"]), h["catatan"])

    # R: deteksi slip terakhir terhadap Periode nyata (hanya baca)
    nama_periode = frappe.get_all("HRIS Payroll Period", pluck="name", limit=30)
    if not nama_periode:
        print("INFO    tidak ada HRIS Payroll Period di site uji; R1-R3 dilewati")
    # kembalikan fungsi asli untuk pemeriksaan ini
    import importlib
    importlib.reload(pp)
    for nama in nama_periode:
        try:
            p = frappe.get_doc("HRIS Payroll Period", nama)
            params, offset, aturan = bp._jadwal(p)
            pertama = bp.pertama_bulan_murni(params, offset, aturan, p.period_start, p.pay_date)
            terakhir = pp._slip_terakhir(p)
            m = pp._jumlah_slip_jadwal(p)
            ok1 = m is not None and m >= 1
            ok2 = (m != 1) or (pertama and terakhir)
            ok3 = not (pertama and terakhir) or m == 1
            cek("R %s: M=%s pertama=%s terakhir=%s konsisten" % (nama, m, pertama, terakhir), ok1 and ok2 and ok3)
        except Exception as e:
            cek("R %s: tanpa galat" % nama, False, repr(e)[:120])

    # Employee: validasi server
    emp = frappe.db.get_value("HRIS Employee", {}, "name")
    if not emp:
        print("LEWATI  E1-E3: tidak ada HRIS Employee")
    else:
        d = frappe.get_doc("HRIS Employee", emp)
        d.pph21_enrolled = 1
        d.ptkp_status = ""
        try:
            d._cek_pph21()
            cek("E1 server menolak PPh 21 dicentang tanpa PTKP", False)
        except frappe.ValidationError:
            cek("E1 server menolak PPh 21 dicentang tanpa PTKP", True)
        d.ptkp_status = "TK/0"
        try:
            d._cek_pph21()
            cek("E2 dengan PTKP diterima", True)
        except Exception as e:
            cek("E2 dengan PTKP diterima", False, repr(e)[:100])
        d.pph21_enrolled = 0
        d.ptkp_status = ""
        try:
            d._cek_pph21()
            cek("E3 bukan peserta: PTKP boleh kosong", True)
        except Exception as e:
            cek("E3 bukan peserta: PTKP boleh kosong", False, repr(e)[:100])
finally:
    frappe.db.rollback()
    frappe.destroy()
    print("\nHASIL: OK %d, GAGAL %d" % (sum(hasil_uji), len(hasil_uji) - sum(hasil_uji)))
