import frappe

from hris.hris_payroll.services import payroll_summary as ps


def jalankan():
    hasil = []

    def cek(nama, kondisi, info=""):
        hasil.append(bool(kondisi))
        print(("OK     " if kondisi else "GAGAL  ") + nama + (" | " + str(info)[:150] if info else ""))

    aktif = frappe.db.count("HRIS Employee", {"status": "Aktif"})
    TGL = "2030-03-05"

    r0 = ps.ambil_data(mode="Per Tanggal", tanggal=TGL, semua=1)
    cek("X1 Per Tanggal: semua baris punya baris gaji", all(x["pay_type"] for x in r0["baris"]), r0["jumlah_baris"])
    cek("X2 sebagian karyawan disembunyikan", r0["jumlah_baris"] < aktif, (r0["jumlah_baris"], aktif))
    cek("X3 keterangan menyebut 'tanggal ini'", any("disembunyikan" in t and "tanggal ini" in t for t in r0["info"]), r0["info"])

    r1 = ps.ambil_data(mode="Per Tanggal", tanggal=TGL, semua=1, tampilkan_tanpa_gaji=1)
    cek("X4 opsi tampilkan tanpa gaji: semua karyawan aktif", r1["jumlah_baris"] == aktif, (r1["jumlah_baris"], aktif))
    cek("X5 selisih baris = jumlah disembunyikan", r1["jumlah_baris"] - r0["jumlah_baris"] == aktif - r0["jumlah_baris"])

    p = frappe.db.sql(
        "select p.name from `tabHRIS Payroll Period` p limit 1"
    )
    if p:
        rp = ps.ambil_data(mode="Per Periode", periode=p[0][0], semua=1)
        cek("X6 Per Periode tetap menyaring dan menyebut 'jadwal periode ini'",
            all(x["pay_type"] for x in rp["baris"]) and any("jadwal periode ini" in t for t in rp["info"]), rp["info"])
    else:
        print("SKIP   X6: tidak ada periode")
    print("OK %d, GAGAL %d (tidak ada data yang diubah)" % (sum(hasil), len(hasil) - sum(hasil)))
