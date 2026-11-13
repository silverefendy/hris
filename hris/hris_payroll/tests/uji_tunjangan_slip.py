import frappe
from datetime import date

from hris.hris_payroll.services.komponen_slip import (
    ambil_pengecualian, hitung_tunjangan, hitung_tunjangan_karyawan,
)

TABEL = "HRIS Employee Component"
AWAL, AKHIR = "2030-03-01", "2030-03-31"
HADIR = [date(2030, 3, d) for d in range(1, 21)]
DASAR = {"nilai": 15000, "berlaku": True}
BULANAN = {"nilai": 300000, "berlaku": True}
NOL = {"nilai": 0, "berlaku": False}


def hec(nama, status, amount, dari, sampai):
    return {"name": nama, "status": status, "amount": amount, "date_from": dari, "date_to": sampai}


def jalankan():
    hasil = []

    def cek(nama, kondisi, info=""):
        hasil.append(bool(kondisi))
        print(("OK     " if kondisi else "GAGAL  ") + nama + (" | " + str(info) if info else ""))

    def harian(dasar, daftar):
        return hitung_tunjangan("Harian", "Per Hari Hadir", dasar, daftar, AWAL, AKHIR, HADIR)

    def periode(pay_type, basis, dasar, daftar):
        return hitung_tunjangan(pay_type, basis, dasar, daftar, AWAL, AKHIR, [])

    # ---- Per Hari Hadir ----
    r = harian(DASAR, [])
    cek("P1 tanpa pengecualian: 20 x 15.000", r["jumlah"] == 300000, r["jumlah"])
    r = harian(DASAR, [hec("HEC-T1", "Tidak Berlaku", 0, "2030-03-05", "2030-03-07")])
    cek("P2 Tidak Berlaku 3 hari: 255.000", r["jumlah"] == 255000, r["jumlah"])
    cek("P2b dasar menyebut 3 hari", "3 hari" in r["dasar"], r["dasar"])
    r = harian(DASAR, [hec("HEC-T2", "Berlaku", 20000, "2030-03-05", "2030-03-06")])
    cek("P3 nominal khusus 2 hari: 310.000", r["jumlah"] == 310000, r["jumlah"])
    r = harian(NOL, [hec("HEC-T3", "Berlaku", 0, "2030-03-05", "2030-03-06")])
    cek("P4 Berlaku tanpa nominal, dasar nol: 0", r["jumlah"] == 0, r["jumlah"])
    cek("P4b ditandai janggal", len(r["janggal"]) == 1, r["janggal"])
    r = harian(DASAR, [hec("HEC-T4", "Tidak Berlaku", 0, "2030-03-25", "2030-03-26")])
    cek("P5 pengecualian di hari tidak hadir tidak berpengaruh", r["jumlah"] == 300000, r["jumlah"])
    r = harian(NOL, [])
    cek("P6 dasar tidak berlaku, tanpa pengecualian: 0", r["jumlah"] == 0, r["jumlah"])
    cek("P6b tidak janggal", r["janggal"] == [], r["janggal"])
    r = harian(DASAR, [hec("HEC-T5", "Berlaku", 0, "2030-03-05", "2030-03-06")])
    cek("P7 Berlaku tanpa nominal, dasar 15.000: 300.000", r["jumlah"] == 300000, r["jumlah"])
    cek("P7b tidak janggal", r["janggal"] == [], r["janggal"])

    # ---- Per Bulan / Per Slip ----
    r = periode("Bulanan", "Per Bulan", BULANAN, [])
    cek("B1 tanpa pengecualian: 300.000", r["jumlah"] == 300000, r["jumlah"])
    r = periode("Bulanan", "Per Bulan", BULANAN, [hec("HEC-B1", "Tidak Berlaku", 0, "2030-03-10", "2030-03-12")])
    cek("B2 Tidak Berlaku sebagian: tetap 300.000", r["jumlah"] == 300000, r["jumlah"])
    cek("B2b ada 1 peringatan", len(r["peringatan"]) == 1, r["peringatan"])
    r = periode("Bulanan", "Per Bulan", BULANAN, [hec("HEC-B2", "Tidak Berlaku", 0, "2030-03-01", "2030-03-31")])
    cek("B3 Tidak Berlaku seluruh periode: 0", r["jumlah"] == 0, r["jumlah"])
    cek("B3b tanpa peringatan", r["peringatan"] == [], r["peringatan"])
    r = periode("Bulanan", "Per Bulan", BULANAN, [hec("HEC-B3", "Berlaku", 500000, "2030-03-01", "2030-03-31")])
    cek("B4 nominal khusus seluruh periode menggantikan: 500.000", r["jumlah"] == 500000, r["jumlah"])
    r = periode("Bulanan", "Per Bulan", BULANAN, [hec("HEC-B4", "Berlaku", 500000, "2030-03-10", "2030-03-12")])
    cek("B5 nominal khusus sebagian tidak menggantikan: 300.000", r["jumlah"] == 300000, r["jumlah"])
    cek("B5b ada 1 peringatan", len(r["peringatan"]) == 1, r["peringatan"])
    r = periode("Bulanan", "Per Bulan", NOL, [hec("HEC-B5", "Berlaku", 0, "2030-03-01", "2030-03-31")])
    cek("B6 Berlaku tanpa nominal seluruh periode, dasar nol: 0", r["jumlah"] == 0, r["jumlah"])
    cek("B6b ditandai janggal", len(r["janggal"]) == 1, r["janggal"])
    r = periode("Bulanan", "Per Hari Hadir", BULANAN, [])
    cek("B7 Bulanan + Per Hari Hadir: error", "error" in r, r.get("error"))
    r = periode("Harian", "Per Bulan", BULANAN, [])
    cek("B8 Harian + Per Bulan: satu nilai per periode", r["jumlah"] == 300000, r.get("jumlah"))
    r = periode("Lain", "Per Bulan", BULANAN, [])
    cek("B9 jenis gaji tidak dikenal: error", "error" in r, r.get("error"))
    r = periode("Bulanan", "Per Slip", BULANAN, [])
    cek("B10 Per Slip sama dengan Per Bulan", r["jumlah"] == 300000, r.get("jumlah"))
    r = periode("Bulanan", "Per Bulan", NOL, [hec("HEC-B6", "Tidak Berlaku", 0, "2030-03-10", "2030-03-12")])
    cek("B11 dasar nol: tidak ada peringatan menyesatkan", r["peringatan"] == [], r["peringatan"])
    r = periode("Bulanan", "Per Bulan", BULANAN, [hec("HEC-B7", "Tidak Berlaku", 0, "2030-02-25", "2030-03-02")])
    cek("B12 pengecualian melewati batas periode dihitung sebagai sebagian", len(r["peringatan"]) == 1 and r["jumlah"] == 300000, r)

    # ---- akses database (di-rollback) ----
    b = frappe.db.sql(
        "select employee from `tabHRIS Employee Pay` where pay_type='Bulanan' and effective_to is null limit 1"
    )
    k = frappe.db.sql(
        "select component_code from `tabHRIS Pay Component` "
        "where payment_basis in ('Per Bulan','Per Slip') and component_code != 'TJ_MAKAN' limit 1"
    )
    B = b[0][0] if b else None
    KODE_BULAN = k[0][0] if k else None
    print("Karyawan=%s KomponenPerBulan=%s" % (B, KODE_BULAN))
    if not B:
        print("SKIP: tidak ada karyawan Bulanan untuk uji database")
    else:
        try:
            def buat(**kw):
                d = {"doctype": TABEL, "status": "Tidak Berlaku", "is_active": 1, "reason": "uji"}
                d.update(kw)
                doc = frappe.get_doc(d)
                doc.insert(ignore_permissions=True)
                return doc

            h1 = buat(employee=B, component="TJ_MAKAN", date_from="2030-03-05", date_to="2030-03-07")
            buat(employee=B, component="TJ_MAKAN", date_from="2030-03-10", date_to="2030-03-10", is_active=0)
            buat(employee=B, component="TJ_MAKAN", date_from="2030-05-01", date_to="2030-05-02")
            baris = ambil_pengecualian(B, "TJ_MAKAN", AWAL, AKHIR)
            cek("D1 hanya HEC aktif yang menyentuh periode", len(baris) == 1 and baris[0].name == h1.name, [x.name for x in baris])
            r = hitung_tunjangan_karyawan(B, "TJ_MAKAN", "Harian", AWAL, AKHIR, HADIR)
            cek("D2 pembungkus: tanpa galat, kunci terisi", "error" not in r and r.get("kode") == "TJ_MAKAN" and "janggal" in r, r)
            if KODE_BULAN:
                buat(employee=B, component=KODE_BULAN, status="Berlaku", amount=12345,
                     date_from="2030-03-01", date_to="2030-03-31")
                r = hitung_tunjangan_karyawan(B, KODE_BULAN, "Bulanan", AWAL, AKHIR, [])
                cek("D3 pembungkus: nominal khusus seluruh periode", r.get("jumlah") == 12345, r)
            else:
                print("SKIP   D3: tidak ada komponen Per Bulan/Per Slip selain TJ_MAKAN di katalog")
        finally:
            frappe.db.rollback()
    print("OK %d, GAGAL %d (data uji di-rollback)" % (sum(hasil), len(hasil) - sum(hasil)))
