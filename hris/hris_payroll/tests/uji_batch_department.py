"""K-138: scope Department hitung ulang massal memakai HRIS Employee. Hanya baca. hris-uji.local."""
import os

import frappe

os.chdir("/home/it/erp/sites")
frappe.init(site="hris-uji.local", sites_path=".")
frappe.connect()
frappe.set_user("Administrator")

ok = 0
gagal = 0


def cek(kode, kondisi, ket=""):
    global ok, gagal
    if kondisi:
        ok += 1
    else:
        gagal += 1
    print(("OK      " if kondisi else "GAGAL   ") + kode + " " + str(ket))


from hris.hris_attendance.services import working_hour_batch as B

dept = frappe.db.sql(
    """select he.department from `tabHRIS Employee` he
       inner join `tabEmployee` e on e.name = he.erpnext_employee
       where he.erpnext_employee is not null and he.erpnext_employee != ''
         and he.department is not null and he.department != '' and e.status = 'Active'
       group by he.department order by count(*) desc limit 1""")
dept = dept[0][0] if dept else None
cek("D0 ada Department dengan karyawan terhubung", bool(dept), dept)
if dept:
    harap = set(frappe.get_all("HRIS Employee", filters={"department": dept, "erpnext_employee": ["is", "set"]}, pluck="erpnext_employee"))
    harap = {n for n in harap if frappe.db.get_value("Employee", n, "status") == "Active"}
    hasil = {r["name"] for r in B._employees({"scope": "Department", "department": dept})}
    cek("F1 hasil = karyawan HRIS Employee aktif di Department itu", hasil == harap, "hasil=%d harapan=%d" % (len(hasil), len(harap)))
    kosong = B._employees({"scope": "Department", "department": "ZZ-TIDAK-ADA"})
    cek("F2 Department tidak ada: hasil kosong", len(kosong) == 0, len(kosong))
    semua = B._employees({"scope": "Semua"})
    cek("F3 scope Semua tidak berubah (ada isi)", len(semua) > 0, len(semua))

print("HASIL: OK %d, GAGAL %d" % (ok, gagal))
frappe.destroy()
raise SystemExit(1 if gagal else 0)
