from datetime import date

from hris.hris_payroll.services.komponen_slip import hitung_tunjangan

AWAL, AKHIR = "2030-03-01", "2030-03-07"
HADIR = [date(2030, 3, d) for d in range(1, 6)]
BULANAN = {"nilai": 300000, "berlaku": True}
HARIAN = {"nilai": 15000, "berlaku": True}


def hec(nama, status, amount, dari, sampai):
    return {"name": nama, "status": status, "amount": amount, "date_from": dari, "date_to": sampai}


PENUH = hec("HEC-PENUH", "Berlaku", 0, AWAL, AKHIR)


def per_bulan(waktu, giliran, daftar=None, basis="Per Bulan"):
    return hitung_tunjangan("Bulanan", basis, BULANAN, [PENUH] if daftar is None else daftar,
                            AWAL, AKHIR, [], giliran, waktu)


def jalankan():
    def cek(nama, kondisi, info=""):
        print(("OK     " if kondisi else "GAGAL  ") + nama + (" | " + str(info) if info else ""))

    r = per_bulan("Slip Pertama", None)
    cek("G1 tanpa giliran: perilaku lama 300.000", r["jumlah"] == 300000, r["jumlah"])
    r = per_bulan("Slip Pertama", {"pertama": True, "terakhir": False})
    cek("G2 Slip Pertama dan slip pertama: 300.000", r["jumlah"] == 300000, r["jumlah"])
    r = per_bulan("Slip Pertama", {"pertama": False, "terakhir": True})
    cek("G3 Slip Pertama tetapi bukan slip pertama: 0", r["jumlah"] == 0, r["jumlah"])
    cek("G3b keterangan menyebut slip pertama", "slip pertama" in r["dasar"], r["dasar"])
    r = per_bulan("Slip Terakhir", {"pertama": False, "terakhir": True})
    cek("G4 Slip Terakhir dan slip terakhir: 300.000", r["jumlah"] == 300000, r["jumlah"])
    r = per_bulan("Slip Terakhir", {"pertama": True, "terakhir": False})
    cek("G5 Slip Terakhir tetapi bukan slip terakhir: 0", r["jumlah"] == 0, r["jumlah"])
    cek("G5b keterangan menyebut slip terakhir", "slip terakhir" in r["dasar"], r["dasar"])
    r = per_bulan("Slip Terakhir", {"pertama": False, "terakhir": False}, basis="Per Slip")
    cek("G6 Per Slip tidak terpengaruh giliran: 300.000", r["jumlah"] == 300000, r["jumlah"])
    r = hitung_tunjangan("Harian", "Per Hari Hadir", HARIAN, [PENUH], AWAL, AKHIR, HADIR,
                         {"pertama": False, "terakhir": False}, "Slip Terakhir")
    cek("G7 Per Hari Hadir tidak terpengaruh giliran: 5 x 15.000", r["jumlah"] == 75000, r["jumlah"])
    a = per_bulan("Slip Pertama", {"pertama": True, "terakhir": True})["jumlah"]
    b = per_bulan("Slip Terakhir", {"pertama": True, "terakhir": True})["jumlah"]
    cek("G8 slip tunggal sebulan dibayar pada kedua waktu bayar", a == 300000 and b == 300000, (a, b))
    r = per_bulan("Slip Pertama", {"pertama": True, "terakhir": True}, [hec("HEC-X", "Tidak Berlaku", 0, AWAL, AKHIR)])
    cek("G9 pengecualian penuh pada slip gilirannya: 0", r["jumlah"] == 0, r["jumlah"])
    sebagian = [PENUH, hec("HEC-S", "Tidak Berlaku", 0, "2030-03-03", "2030-03-04")]
    r = per_bulan("Slip Pertama", {"pertama": False, "terakhir": False}, sebagian)
    cek("G10 bukan giliran dengan pengecualian sebagian: 0", r["jumlah"] == 0, r["jumlah"])
    cek("G10b tanpa peringatan", r["peringatan"] == [], r["peringatan"])
    cek("G10c tanpa janggal", r["janggal"] == [], r["janggal"])
    r = per_bulan("Slip Pertama", {"pertama": True, "terakhir": False}, sebagian)
    cek("G11 giliran dengan pengecualian sebagian: tetap 300.000", r["jumlah"] == 300000, r["jumlah"])
    cek("G11b tepat satu peringatan", len(r["peringatan"]) == 1, r["peringatan"])


def lihat():
    """Hanya membaca: giliran dari 8 periode terbaru."""
    import frappe
    from hris.hris_payroll.services.giliran_bulan import giliran_bulan
    for nama in frappe.get_all("HRIS Payroll Period", pluck="name", order_by="creation desc", limit=8):
        d = frappe.get_doc("HRIS Payroll Period", nama)
        print(nama, d.payroll_schedule, d.period_start, d.period_end, d.pay_date, giliran_bulan(d))
