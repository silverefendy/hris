"""K-140 tahap A: uji murni aturan default tidak dapat dan Bulanan + Per Hari Hadir (tanpa database).

Jalankan:
bench --site hris-uji.local execute hris.hris_payroll.tests.uji_default_tidak_dapat.jalankan
"""

from hris.hris_payroll.services.komponen_slip import hitung_tunjangan

AWAL = "2026-10-01"
AKHIR = "2026-10-31"
HADIR = ["2026-10-%02d" % d for d in range(1, 23)]


def hec(status, dari=AWAL, sampai=AKHIR, jumlah=0, nama="H1"):
    return {"name": nama, "status": status, "amount": jumlah, "date_from": dari, "date_to": sampai}


def hit(pay_type, basis, dasar, daftar, hadir=HADIR):
    return hitung_tunjangan(pay_type, basis, {"nilai": dasar, "berlaku": dasar > 0}, daftar, AWAL, AKHIR, hadir)


def jalankan():
    hasil = []

    def cek(nama, kondisi, info=""):
        hasil.append(bool(kondisi))
        tambahan = (" | " + str(info)[:250]) if (not kondisi and info != "") else ""
        print(("OK     " if kondisi else "GAGAL  ") + nama + tambahan)

    r = hit("Harian", "Per Hari Hadir", 20000, [])
    cek("P1 Harian Per Hari Hadir tanpa penetapan: Rp0", r.get("jumlah") == 0 and not r.get("error"), r)
    r = hit("Bulanan", "Per Hari Hadir", 20000, [hec("Berlaku")])
    cek("P2 Bulanan Per Hari Hadir, penetapan Berlaku: 22 hari x 20.000", r.get("jumlah") == 440000 and not r.get("error"), r)
    r = hit("Bulanan", "Per Hari Hadir", 20000, [])
    cek("P3 Bulanan Per Hari Hadir tanpa penetapan: Rp0 dan tanpa galat", r.get("jumlah") == 0 and not r.get("error"), r)
    r = hit("Bulanan", "Per Hari Hadir", 20000, [hec("Berlaku", sampai="2026-10-10")])
    cek("P4 penetapan hanya 10 hari pertama: 10 hari x 20.000", r.get("jumlah") == 200000, r)
    r = hit("Harian", "Per Hari Hadir", 20000, [hec("Tidak Berlaku")])
    cek("P5 Tidak Berlaku seluruh periode: Rp0", r.get("jumlah") == 0, r)
    r = hit("Bulanan", "Per Hari Hadir", 20000, [hec("Berlaku", jumlah=25000)])
    cek("P6 nominal khusus 25.000: 22 hari x 25.000", r.get("jumlah") == 550000, r)
    r = hit("Bulanan", "Per Hari Hadir", 0, [hec("Berlaku")])
    cek("P7 Berlaku tanpa nominal dan nilai dasar nol: Rp0 dan janggal", r.get("jumlah") == 0 and bool(r.get("janggal")), r)
    r = hit("Bulanan", "Per Hari Hadir", 20000, [hec("Berlaku")], hadir=[])
    cek("P8 tidak ada hari Hadir: Rp0", r.get("jumlah") == 0, r)
    r = hit("Bulanan", "Per Bulan", 500000, [])
    cek("P9 Per Bulan tanpa penetapan: Rp0", r.get("jumlah") == 0 and not r.get("error"), r)
    r = hit("Bulanan", "Per Bulan", 500000, [hec("Berlaku")])
    cek("P10 Per Bulan penetapan Berlaku penuh: 500.000", r.get("jumlah") == 500000, r)
    r = hit("Bulanan", "Per Bulan", 500000, [hec("Berlaku")], hadir=[])
    cek("P10b Per Bulan tetap penuh walau tidak ada hari Hadir (tunjangan jabatan)", r.get("jumlah") == 500000, r)
    r = hit("Bulanan", "Per Bulan", 500000, [hec("Berlaku", sampai="2026-10-15")])
    cek("P11 Per Bulan penetapan sebagian periode: dibayar penuh dan ada peringatan",
        r.get("jumlah") == 500000 and bool(r.get("peringatan")), r)
    r = hit("Bulanan", "Per Bulan", 500000, [hec("Tidak Berlaku")])
    cek("P12 Per Bulan Tidak Berlaku seluruh periode: Rp0", r.get("jumlah") == 0, r)
    r = hit("Bulanan", "Per Bulan", 500000, [hec("Berlaku", jumlah=750000)])
    cek("P13 Per Bulan nominal khusus 750.000", r.get("jumlah") == 750000, r)
    r = hit("Harian", "Per Slip", 100000, [hec("Berlaku")])
    cek("P14 Per Slip penetapan Berlaku: 100.000", r.get("jumlah") == 100000, r)
    r = hit("Harian", "Per Slip", 100000, [])
    cek("P14b Per Slip tanpa penetapan: Rp0", r.get("jumlah") == 0, r)
    r = hit("Bulanan", "Per Bulan", 0, [hec("Berlaku")])
    cek("P15 Per Bulan Berlaku tanpa nominal dan nilai dasar nol: Rp0 dan janggal",
        r.get("jumlah") == 0 and bool(r.get("janggal")), r)
    r = hit("Mingguan", "Per Bulan", 500000, [])
    cek("P16 jenis gaji tidak dikenal tetap galat", bool(r.get("error")), r)
    print("OK %d, GAGAL %d (uji murni, tanpa database)" % (sum(hasil), len(hasil) - sum(hasil)))
