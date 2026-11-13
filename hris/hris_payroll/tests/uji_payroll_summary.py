import frappe

from hris.hris_payroll.services import payroll_summary as ps

HEC = "HRIS Employee Component"
KATALOG = "HRIS Pay Component"
TGL_A = "2030-03-05"
TGL_B = "2030-03-15"


def _buat(**k):
    d = {"doctype": HEC, "status": "Tidak Berlaku", "is_active": 1, "reason": "uji"}
    d.update(k)
    doc = frappe.get_doc(d)
    doc.insert(ignore_permissions=True)
    return doc


def jalankan():
    hasil = []

    def cek(nama, kondisi, info=""):
        hasil.append(bool(kondisi))
        print(("OK     " if kondisi else "GAGAL  ") + nama + (" | " + str(info)[:140] if info else ""))

    def gagal(nama, fn, kata):
        try:
            fn()
            cek(nama, False, "tidak ditolak")
        except Exception as e:
            cek(nama, kata.lower() in str(e).lower(), str(e)[:100])

    b = frappe.db.sql(
        "select employee, payroll_schedule from `tabHRIS Employee Pay` "
        "where pay_type='Bulanan' and effective_to is null limit 1"
    )
    if not b:
        print("SKIP: tidak ada karyawan Bulanan")
        return
    B, JADWAL = b[0]
    periode = frappe.db.get_value("HRIS Payroll Period", {"payroll_schedule": JADWAL}, ["name", "period_start"], as_dict=True)
    print("Karyawan=%s Jadwal=%s Periode=%s" % (B, JADWAL, periode.name if periode else None))

    asli_roles = frappe.get_roles
    try:
        frappe.db.set_value(KATALOG, "TJ_MAKAN", "is_active", 1)
        frappe.db.set_value(KATALOG, "INSENTIF", "is_active", 1)
        frappe.db.set_value(KATALOG, "TJ_JABATAN", "is_active", 0)
        _buat(employee=B, component="TJ_MAKAN", status="Berlaku", amount=15000, date_from="2030-03-01", date_to="2030-03-10")
        _buat(employee=B, component="TJ_MAKAN", status="Berlaku", amount=0, date_from="2030-03-11", date_to="2030-03-20")

        r = ps.ambil_data(mode="Per Tanggal", tanggal=TGL_A, employee=B)
        kodes = [k["kode"] for k in r["komponen"]]
        cek("T1 satu baris untuk karyawan terpilih", r["jumlah_baris"] == 1, r["jumlah_baris"])
        cek("T2 komponen aktif tampil, nonaktif tersembunyi", "TJ_MAKAN" in kodes and "INSENTIF" in kodes and "TJ_JABATAN" not in kodes, kodes)
        sel = r["baris"][0]["sel"]["TJ_MAKAN"]
        cek("T3 nominal khusus 15.000", sel.get("jumlah") == 15000, sel)
        cek("T3b sumber menyebut pengecualian HEC", str(sel.get("sumber")).startswith("Pengecualian HEC-"), sel.get("sumber"))
        cek("T3c Bulanan: per hari dan per jam '-' di Per Tanggal", r["baris"][0]["per_hari"] is None and r["baris"][0]["per_jam"] is None)

        r2 = ps.ambil_data(mode="Per Tanggal", tanggal=TGL_B, employee=B)
        b2 = r2["baris"][0]
        cek("T4 Berlaku tanpa nominal, dasar nol: janggal", b2["janggal"] and r2["jumlah_janggal"] == 1, b2["catatan"])
        cek("T4b jumlah 0", b2["sel"]["TJ_MAKAN"]["jumlah"] == 0, b2["sel"]["TJ_MAKAN"])

        r3 = ps.ambil_data(mode="Per Tanggal", tanggal="2030-04-05", employee=B)
        c3 = r3["baris"][0]["sel"]["TJ_MAKAN"]
        cek("T5 tanpa pengecualian: tidak ada nilai", c3["jumlah"] == 0 and c3["sumber"] == "Tidak ada nilai", c3)

        r4 = ps.ambil_data(mode="Per Tanggal", tanggal=TGL_A, employee=B, tampilkan_nonaktif=1)
        cek("T6 opsi tampilkan nonaktif", "TJ_JABATAN" in [k["kode"] for k in r4["komponen"]])

        r5 = ps.ambil_data(mode="Per Tanggal", tanggal=TGL_A, ukuran=1, halaman=1)
        cek("T7 halaman: satu baris, total seluruh hasil", len(r5["baris"]) <= 1 and r5["jumlah_baris"] >= 1, r5["jumlah_baris"])
        r6 = ps.ambil_data(mode="Per Tanggal", tanggal=TGL_A, ukuran=1, semua=1)
        cek("T7b semua=1 mengembalikan seluruh baris", len(r6["baris"]) == r6["jumlah_baris"], len(r6["baris"]))

        if periode:
            rp = ps.ambil_data(mode="Per Periode", periode=periode.name, employee=B)
            cek("T8 Per Periode: rentang sama dengan periode", rp["awal"] == str(periode.period_start), rp["awal"])
            cek("T8b Per Periode: karyawan muncul", rp["jumlah_baris"] == 1, rp["jumlah_baris"])
        else:
            print("SKIP   T8: tidak ada periode untuk jadwal ini")

        gagal("T9 Per Periode tanpa periode ditolak", lambda: ps.ambil_data(mode="Per Periode"), "periode")

        frappe.db.set_value(KATALOG, "TJ_MAKAN", "payment_basis", "Per Hari Hadir")
        r7 = ps.ambil_data(mode="Per Tanggal", tanggal=TGL_A, employee=B)
        cek("T10 Bulanan + Per Hari Hadir: galat di sel, tidak mogok", "error" in r7["baris"][0]["sel"]["TJ_MAKAN"] and r7["baris"][0]["janggal"])
        frappe.db.set_value(KATALOG, "TJ_MAKAN", "payment_basis", "Per Bulan")

        frappe.get_roles = lambda user=None: ["HRIS Payroll Admin"]
        ra = ps.ambil_data(mode="Per Tanggal", tanggal=TGL_A, employee=B)
        cek("R1 Payroll Admin tidak melihat karyawan Bulanan", ra["jumlah_baris"] == 0, ra["jumlah_baris"])
        rb = ps.ambil_data(mode="Per Tanggal", tanggal=TGL_A)
        cek("R2 Payroll Admin: semua baris Harian", all(x["pay_type"] == "Harian" for x in rb["baris"]), rb["jumlah_baris"])
        frappe.get_roles = lambda user=None: ["HRIS Payroll Manager"]
        rm = ps.ambil_data(mode="Per Tanggal", tanggal=TGL_A, employee=B)
        cek("R3 Payroll Manager melihat semua", rm["jumlah_baris"] == 1)
        frappe.get_roles = lambda user=None: ["HRIS Payroll User"]
        gagal("R4 peran lain ditolak", lambda: ps.ambil_data(mode="Per Tanggal", tanggal=TGL_A), "berhak")
    finally:
        frappe.get_roles = asli_roles
        frappe.db.rollback()
    print("OK %d, GAGAL %d (semua data uji di-rollback)" % (sum(hasil), len(hasil) - sum(hasil)))
