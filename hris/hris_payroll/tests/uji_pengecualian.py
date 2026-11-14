import frappe
from datetime import date
from frappe.utils import flt, getdate

from hris.hris_payroll.doctype.hris_employee_component import hris_employee_component as hec_mod
from hris.hris_payroll.services import payroll_summary as ps
from hris.hris_payroll.services import pengecualian as pe

HEC = "HRIS Employee Component"
KOMP = "TJ_TRANSPORT"


def E(nama, status, amount, dari, sampai):
    return {"name": nama, "status": status, "amount": amount, "date_from": dari, "date_to": sampai}


def jalankan():
    hasil = []

    def cek(nama, kondisi, info=""):
        hasil.append(bool(kondisi))
        print(("OK     " if kondisi else "GAGAL  ") + nama + (" | " + str(info)[:150] if info else ""))

    def gagal(nama, fn, kata):
        try:
            fn()
            cek(nama, False, "tidak ditolak")
        except Exception as e:
            cek(nama, kata.lower() in str(e).lower(), str(e)[:110])

    def ringkas(r):
        return (len(r["nonaktif"]), len(r["ubah"]), len(r["buat"]))

    # ---------- rencana murni ----------
    r = pe.rencanakan([], "Tidak Berlaku", "2031-03-15", "2031-03-17")
    cek("S1 kosong lalu Tidak Berlaku: 1 baris baru", ringkas(r) == (0, 0, 1) and r["buat"][0]["amount"] == 0, r)

    r = pe.rencanakan([E("A", "Tidak Berlaku", 0, "2031-03-15", "2031-03-17")], "Tidak Berlaku", "2031-03-18", "2031-03-19")
    cek("S2 bersambung bernilai sama: digabung (A diperluas)", ringkas(r) == (0, 1, 0) and str(r["ubah"][0]["date_to"]) == "2031-03-19", r)

    r = pe.rencanakan([E("A", "Tidak Berlaku", 0, "2031-03-15", "2031-03-17")], "Tidak Berlaku", "2031-03-18", "2031-03-19", gabung_tetangga=False)
    cek("S2b tanpa gabung tetangga: baris baru terpisah", ringkas(r) == (0, 0, 1), r)

    r = pe.rencanakan([E("A", "Tidak Berlaku", 0, "2031-03-15", "2031-03-19")], "Berlaku", "2031-03-16", "2031-03-17", 20000)
    status = sorted(b["status"] for b in r["buat"])
    cek("S3 membelah: A dipersempit, dua baris baru", ringkas(r) == (0, 1, 2) and r["ubah"][0]["menyusut"] and status == ["Berlaku", "Tidak Berlaku"], r)

    r = pe.rencanakan([E("A", "Tidak Berlaku", 0, "2031-03-16", "2031-03-17")], "Berlaku", "2031-03-15", "2031-03-19", 10000)
    cek("S4 tertutup penuh: A dinonaktifkan, satu baris baru", ringkas(r) == (1, 0, 1) and r["nonaktif"] == ["A"], r)

    r = pe.rencanakan([E("A", "Tidak Berlaku", 0, "2031-03-15", "2031-03-19")], "Hapus", "2031-03-16", "2031-03-17")
    cek("S5 Hapus di tengah: A dipersempit, sisa kanan jadi baris baru", ringkas(r) == (0, 1, 1), r)

    r = pe.rencanakan([E("A", "Tidak Berlaku", 0, "2031-03-16", "2031-03-17")], "Hapus", "2031-03-15", "2031-03-19")
    cek("S6 Hapus menutup penuh: hanya dinonaktifkan", ringkas(r) == (1, 0, 0), r)

    r = pe.rencanakan([E("A", "Berlaku", 10000, "2031-03-15", "2031-03-17")], "Berlaku", "2031-03-16", "2031-03-16", 10000)
    cek("S7 nilai sama di dalam baris yang ada: tidak ada perubahan", ringkas(r) == (0, 0, 0), r)

    r = pe.rencanakan(
        [E("A", "Tidak Berlaku", 0, "2031-03-15", "2031-03-17"), E("B", "Berlaku", 5000, "2031-03-18", "2031-03-20")],
        "Tidak Berlaku", "2031-03-18", "2031-03-18",
    )
    cek("S8 menimpa awal B dan menyambung A: dua ubah, B (menyusut) dulu",
        ringkas(r) == (0, 2, 0) and r["ubah"][0]["name"] == "B" and str(r["ubah"][1]["date_to"]) == "2031-03-18", r)

    r = pe.rencanakan([], "Hapus", "2031-03-15", "2031-03-17")
    cek("S9 Hapus tanpa baris: tidak ada perubahan", ringkas(r) == (0, 0, 0), r)

    r = pe.rencanakan([E("A", "Tidak Berlaku", 0, "2031-03-15", "2031-03-16"), E("B", "Tidak Berlaku", 0, "2031-03-18", "2031-03-19")],
                      "Tidak Berlaku", "2031-03-16", "2031-03-18")
    cek("S10 menjembatani dua baris bernilai sama: A diperluas, B dinonaktifkan", ringkas(r) == (1, 1, 0) and r["nonaktif"] == ["B"], r)

    try:
        pe.rencanakan([], "Hapus", "2031-03-17", "2031-03-15")
        cek("S11 Sampai sebelum Dari ditolak", False)
    except ValueError:
        cek("S11 Sampai sebelum Dari ditolak", True)

    # ---------- penyimpanan nyata (di-rollback) ----------
    b = frappe.db.sql(
        "select employee, payroll_schedule from `tabHRIS Employee Pay` where pay_type='Bulanan' and effective_to is null limit 1"
    )
    if not b:
        print("SKIP: tidak ada karyawan Bulanan untuk uji database")
    else:
        B = b[0][0]

        def aktif():
            return frappe.get_all(HEC, filters={"employee": B, "component": KOMP, "is_active": 1},
                                  fields=["name", "status", "amount", "date_from", "date_to"], order_by="date_from asc")

        asli_final = hec_mod.periode_final_sejak
        try:
            r = pe.simpan_pengecualian(B, KOMP, "Tidak Berlaku", "2031-03-15", "2031-03-17", "uji 1")
            cek("D1 simpan baru", r["dibuat"] == 1 and len(aktif()) == 1, r)

            r = pe.simpan_pengecualian(B, KOMP, "Tidak Berlaku", "2031-03-18", "2031-03-19", "uji 2")
            a = aktif()
            cek("D2 digabung menjadi satu baris 15 sampai 19", r["diubah"] == 1 and len(a) == 1 and str(a[0].date_to) == "2031-03-19", r)

            r = pe.simpan_pengecualian(B, KOMP, "Berlaku", "2031-03-16", "2031-03-17", "uji 3", 20000)
            a = aktif()
            cek("D3 menimpa tengah: tiga baris", len(a) == 3, [(x.status, str(x.date_from), str(x.date_to)) for x in a])
            cek("D3b urutan Tidak Berlaku, Berlaku 20.000, Tidak Berlaku",
                [x.status for x in a] == ["Tidak Berlaku", "Berlaku", "Tidak Berlaku"] and flt(a[1].amount) == 20000)

            r = pe.simpan_pengecualian(B, KOMP, "Hapus", "2031-03-15", "2031-03-19", "uji 4")
            cek("D4 Hapus seluruh rentang: tidak ada baris aktif", len(aktif()) == 0, r)

            r = pe.simpan_pengecualian(B, KOMP, "Tidak Berlaku", "2031-04-01", "2031-04-03", "uji 5")
            r2 = pe.simpan_pengecualian(B, KOMP, "Tidak Berlaku", "2031-04-01", "2031-04-03", "uji 5b")
            cek("D5 ulang identik: tidak ada perubahan", r2["dibuat"] == 0 and r2["diubah"] == 0 and r2["dinonaktifkan"] == 0, r2)

            gagal("D6 alasan kosong ditolak", lambda: pe.simpan_pengecualian(B, KOMP, "Tidak Berlaku", "2031-05-01", "2031-05-02", " "), "alasan")
            gagal("D7 aksi tidak dikenal ditolak", lambda: pe.simpan_pengecualian(B, KOMP, "Lain", "2031-05-01", "2031-05-02", "x"), "aksi")

            # periode Final menolak
            hec_mod.periode_final_sejak = lambda j, t: "HPP-UJI"
            gagal("F1 periode Final menolak", lambda: pe.simpan_pengecualian(B, KOMP, "Tidak Berlaku", "2031-06-01", "2031-06-01", "uji final"), "Final")
            hec_mod.periode_final_sejak = asli_final

            # gabung ke baris terkunci: kembali ke baris terpisah
            pe.simpan_pengecualian(B, KOMP, "Tidak Berlaku", "2031-07-01", "2031-07-05", "uji terkunci A")
            hec_mod.periode_final_sejak = lambda j, t: "HPP-UJI" if getdate(t) <= date(2031, 7, 5) else None
            r = pe.simpan_pengecualian(B, KOMP, "Tidak Berlaku", "2031-07-06", "2031-07-07", "uji terkunci B")
            tgl = [(str(x.date_from), str(x.date_to)) for x in aktif() if str(x.date_from) >= "2031-07-01"]
            cek("F2 gabung mengenai baris terkunci: baris baru dibuat terpisah", r["dibuat"] == 1 and len(tgl) == 2 and "catatan" in r, tgl)
            hec_mod.periode_final_sejak = asli_final

            # penyaringan Per Periode
            periode = frappe.db.get_value("HRIS Payroll Period", {"payroll_schedule": b[0][1]}, "name")
            if periode:
                r0 = ps.ambil_data(mode="Per Periode", periode=periode, semua=1)
                r1 = ps.ambil_data(mode="Per Periode", periode=periode, semua=1, tampilkan_tanpa_gaji=1)
                cek("P1 Per Periode: semua baris punya baris gaji", all(x["pay_type"] for x in r0["baris"]), r0["jumlah_baris"])
                cek("P2 Per Periode: opsi tampilkan tanpa gaji menambah baris", r1["jumlah_baris"] >= r0["jumlah_baris"], (r0["jumlah_baris"], r1["jumlah_baris"]))
                cek("P3 catatan jumlah yang disembunyikan", (r1["jumlah_baris"] == r0["jumlah_baris"]) or any("disembunyikan" in t for t in r0["info"]), r0["info"])
            else:
                print("SKIP   P1-P3: tidak ada periode untuk jadwal ini")
        finally:
            hec_mod.periode_final_sejak = asli_final
            frappe.db.rollback()
    print("OK %d, GAGAL %d (semua data uji di-rollback)" % (sum(hasil), len(hasil) - sum(hasil)))
