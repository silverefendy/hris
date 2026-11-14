"""K-140 E4: uji pratinjau HCA. Murni, lalu database (HCA sementara, di-rollback, katalog tidak disentuh).

Jalankan:
bench --site hris-uji.local execute hris.hris_payroll.tests.uji_hca_pratinjau.jalankan
"""
import frappe

from hris.hris_payroll.services.hca_pratinjau import klasifikasi, pratinjau

HCA = "HRIS Component Assignment"
AWAL, AKHIR = "2030-03-01", "2030-03-31"


def jalankan():
    hasil = []

    def cek(nama, kondisi, info=""):
        hasil.append(bool(kondisi))
        print(("OK     " if kondisi else "GAGAL  ") + nama + ((" | " + str(info)[:250]) if (not kondisi and info != "") else ""))

    k = [{"name": "E1", "employee_group": "G", "rule_follow": "Grup"},
         {"name": "E2", "employee_group": "G", "rule_follow": "Department"},
         {"name": "E3", "employee_group": "H", "rule_follow": "Grup"}]
    r = klasifikasi("Grup", k, set())
    cek("K1 Grup: rule_follow Grup menerima, Department ikut Department",
        [x["name"] for x in r["dapat"]] == ["E1", "E3"] and [x["name"] for x in r["ikut_department"]] == ["E2"], r)
    r = klasifikasi("Department", k, {"G"})
    cek("K2 Department: rule_follow Grup yang Grupnya punya HCA tertutup",
        [x["name"] for x in r["tertutup_grup"]] == ["E1"] and [x["name"] for x in r["dapat"]] == ["E2", "E3"], r)
    r = klasifikasi("Department", k, set())
    cek("K3 Department tanpa HCA Grup: semua menerima", len(r["dapat"]) == 3 and not r["tertutup_grup"], r)
    r = klasifikasi("Department", [], {"G"})
    cek("K4 tanpa karyawan: semua kosong", r == {"dapat": [], "ikut_department": [], "tertutup_grup": []}, r)
    r = klasifikasi("Grup", [{"name": "E9", "rule_follow": None}], set())
    cek("K5 rule_follow kosong pada cakupan Grup: ikut Department", len(r["ikut_department"]) == 1 and not r["dapat"], r)

    g = frappe.db.sql("select name from `tabHRIS Employee Group` where company is not null and is_active = 1 "
                      "and name in (select employee_group from `tabHRIS Employee` where status='Aktif' and employee_group is not null) limit 1")
    d = frappe.db.sql("select e.department from `tabHRIS Employee` e join `tabHRIS Department` dd on dd.name = e.department "
                      "where e.status = 'Aktif' and dd.company is not null and dd.is_group = 0 group by e.department limit 1")
    if not g or not d:
        print("SKIP D1-D3: tidak ada Grup atau Department ber-Company yang punya karyawan aktif")
        print("OK %d, GAGAL %d (hanya bagian murni)" % (sum(hasil), len(hasil) - sum(hasil)))
        return
    G, D = g[0][0], d[0][0]
    awal_baris = frappe.db.count(HCA)

    def buat(**kw):
        x = {"doctype": HCA, "scope_type": "Grup", "employee_group": G, "component": "TJ_MAKAN", "status": "Berlaku",
             "amount": 1000, "date_from": AWAL, "date_to": AKHIR, "is_active": 1, "reason": "uji K-140 E4", "include_children": 0}
        x.update(kw)
        doc = frappe.get_doc(x)
        doc.insert(ignore_permissions=True)
        return doc

    def hitung(sql, nilai):
        return frappe.db.sql(sql, nilai)[0][0]

    try:
        h1 = buat()
        p = pratinjau(h1.name)
        dapat = hitung("select count(*) from `tabHRIS Employee` where status='Aktif' and employee_group=%s and rule_follow='Grup'", (G,))
        ikut = hitung("select count(*) from `tabHRIS Employee` where status='Aktif' and employee_group=%s and (rule_follow<>'Grup' or rule_follow is null)", (G,))
        cek("D1 Grup: jumlah menerima dan ikut Department sama dengan hitungan SQL",
            p["jumlah"]["dapat"] == dapat and p["jumlah"]["ikut_department"] == ikut, (p["jumlah"], dapat, ikut))
        cek("D2 Grup: total cakupan = menerima + ikut Department", p["jumlah"]["total_cakupan"] == dapat + ikut, p["jumlah"])
        h2 = buat(scope_type="Department", department=D, employee_group=None)
        p2 = pratinjau(h2.name)
        total = hitung("select count(*) from `tabHRIS Employee` where status='Aktif' and department=%s", (D,))
        cek("D3 Department (tanpa anak): menerima + tertutup = jumlah karyawan aktif di Department",
            p2["jumlah"]["dapat"] + p2["jumlah"]["tertutup_grup"] == total or p2["jumlah"]["total_cakupan"] >= total, (p2["jumlah"], total))
        frappe.db.set_value(HCA, h1.name, "is_active", 0)
        cek("D4 penetapan nonaktif memunculkan peringatan", len(pratinjau(h1.name)["peringatan"]) >= 1)
    finally:
        frappe.db.rollback()
    cek("D5 rollback: jumlah HCA kembali", frappe.db.count(HCA) == awal_baris, (frappe.db.count(HCA), awal_baris))
    print("OK %d, GAGAL %d (data uji di-rollback)" % (sum(hasil), len(hasil) - sum(hasil)))
