"""K-140 tahap E1: uji murni penggabungan HCA dengan HEC karyawan (tanpa database).

Jalankan:
bench --site hris-uji.local execute hris.hris_payroll.tests.uji_cakupan_komponen.jalankan
"""
from datetime import date

from frappe.utils import getdate

from hris.hris_payroll.services.cakupan_komponen import gabung_cakupan, pilih_cakupan
from hris.hris_payroll.services.komponen_slip import hitung_tunjangan

AWAL, AKHIR = "2030-03-01", "2030-03-31"
HADIR = [date(2030, 3, d) for d in range(1, 21)]
DASAR = {"nilai": 15000, "berlaku": True}


def baris(nama, status, dari, sampai, jumlah=0):
    return {"name": nama, "status": status, "amount": jumlah, "date_from": dari, "date_to": sampai}


def rentang(daftar):
    return [(x["name"], str(getdate(x["date_from"])), str(getdate(x["date_to"]))) for x in daftar]


def jalankan():
    hasil = []

    def cek(nama, kondisi, info=""):
        hasil.append(bool(kondisi))
        print(("OK     " if kondisi else "GAGAL  ") + nama + ((" | " + str(info)[:250]) if (not kondisi and info != "") else ""))

    g = baris("HCA-1", "Berlaku", AWAL, AKHIR)

    r = gabung_cakupan([], [g])
    cek("C1 tanpa HEC karyawan: HCA utuh", rentang(r) == [("HCA-1", AWAL, AKHIR)], rentang(r))
    r = gabung_cakupan([baris("HEC-1", "Tidak Berlaku", "2030-03-05", "2030-03-07")], [g])
    cek("C2 HEC di tengah: HCA terpotong dua, HEC tetap",
        rentang(r) == [("HCA-1", AWAL, "2030-03-04"), ("HEC-1", "2030-03-05", "2030-03-07"), ("HCA-1", "2030-03-08", AKHIR)]
        or rentang(r) == [("HCA-1", AWAL, "2030-03-04"), ("HEC-1", "2030-03-05", "2030-03-07"), ("HCA-1", "2030-03-08", AKHIR)], rentang(r))
    r = gabung_cakupan([baris("HEC-2", "Berlaku", AWAL, AKHIR)], [g])
    cek("C3 HEC menutup penuh: HCA hilang", rentang(r) == [("HEC-2", AWAL, AKHIR)], rentang(r))
    r = gabung_cakupan([baris("HEC-3", "Tidak Berlaku", AWAL, "2030-03-10")], [g])
    cek("C4 HEC di tepi awal: sisa HCA 11 sampai akhir", rentang(r) == [("HEC-3", AWAL, "2030-03-10"), ("HCA-1", "2030-03-11", AKHIR)], rentang(r))
    r = gabung_cakupan([baris("HEC-4", "Tidak Berlaku", "2030-04-01", "2030-04-05")], [g])
    cek("C5 HEC di luar rentang: HCA utuh", ("HCA-1", AWAL, AKHIR) in rentang(r) and len(r) == 2, rentang(r))
    r = gabung_cakupan([baris("HEC-5", "Berlaku", "2030-03-05", "2030-03-07"), baris("HEC-6", "Tidak Berlaku", "2030-03-20", "2030-03-22")], [g])
    cek("C6 dua HEC memotong: tiga sisa HCA",
        [x for x in rentang(r) if x[0] == "HCA-1"] == [("HCA-1", AWAL, "2030-03-04"), ("HCA-1", "2030-03-08", "2030-03-19"), ("HCA-1", "2030-03-23", AKHIR)], rentang(r))

    asal_hec, asal_hca = [baris("HEC-7", "Tidak Berlaku", "2030-03-05", "2030-03-07")], [dict(g)]
    gabung_cakupan(asal_hec, asal_hca)
    cek("C7 input tidak berubah", len(asal_hec) == 1 and asal_hca[0]["date_from"] == AWAL and asal_hca[0]["date_to"] == AKHIR, (asal_hec, asal_hca))
    r = gabung_cakupan([baris("HEC-8", "Berlaku", "2030-03-20", "2030-03-21")], [baris("HCA-2", "Berlaku", "2030-03-01", "2030-03-10")])
    cek("C8 hasil terurut menurut tanggal", [x[1] for x in rentang(r)] == sorted(x[1] for x in rentang(r)), rentang(r))

    bg, bd = [{"name": "G"}], [{"name": "D"}]
    cek("P1 Grup dengan baris Grup: pakai Grup", pilih_cakupan("Grup", "GRP", bg, bd) == bg)
    cek("P2 Grup tanpa baris Grup: pakai Department", pilih_cakupan("Grup", "GRP", [], bd) == bd)
    cek("P3 Department: pakai Department walau ada baris Grup", pilih_cakupan("Department", "GRP", bg, bd) == bd)
    cek("P4 Grup tanpa nama Grup: pakai Department", pilih_cakupan("Grup", None, bg, bd) == bd)

    def hit(basis, hec, hca, hadir=HADIR):
        return hitung_tunjangan("Bulanan", basis, DASAR if basis == "Per Hari Hadir" else {"nilai": 300000, "berlaku": True},
                                gabung_cakupan(hec, hca), AWAL, AKHIR, hadir)

    r = hit("Per Hari Hadir", [baris("HEC-9", "Tidak Berlaku", "2030-03-05", "2030-03-07")], [g])
    cek("H1 contoh: 20 hari hadir, 3 hari Tidak Berlaku karyawan: 17 x 15.000 = 255.000", r.get("jumlah") == 255000, r)
    r = hit("Per Hari Hadir", [], [g])
    cek("H2 HCA saja: 20 x 15.000 = 300.000", r.get("jumlah") == 300000, r)
    r = hit("Per Hari Hadir", [], [])
    cek("H3 tanpa HCA dan HEC: Rp0", r.get("jumlah") == 0, r)
    r = hit("Per Bulan", [baris("HEC-10", "Tidak Berlaku", AWAL, AKHIR)], [g])
    cek("H4 Per Bulan: HEC Tidak Berlaku penuh mengalahkan HCA Berlaku: Rp0", r.get("jumlah") == 0, r)
    r = hit("Per Bulan", [], [g])
    cek("H5 Per Bulan: HCA Berlaku penuh, tanpa HEC: 300.000", r.get("jumlah") == 300000, r)
    r = hit("Per Hari Hadir", [baris("HEC-11", "Berlaku", "2030-03-05", "2030-03-06", 20000)], [g])
    cek("H6 HEC nominal khusus 2 hari mengalahkan HCA: 18 x 15.000 + 2 x 20.000 = 310.000", r.get("jumlah") == 310000, r)

    print("OK %d, GAGAL %d (uji murni, tanpa database)" % (sum(hasil), len(hasil) - sum(hasil)))
