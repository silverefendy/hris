"""Salin Department ERPNext ke HRIS Department (K-136 tahap 2).

Pemakaian (dari folder sites):
  ../env/bin/python ../apps/hris/hris/hris_employee_data/services/migrasi_department.py coba
  ../env/bin/python ../apps/hris/hris/hris_employee_data/services/migrasi_department.py salin
Setelah salinan, aturan akar HRIS Department Rule dibuat (patch idempoten) dalam transaksi yang sama.
Variabel SITE menentukan site (bawaan hris-uji.local). Site lain ditolak
kecuali IZINKAN_SITE_LAIN=ya.
"""

import os
import sys

import frappe

DT = "HRIS Department"
ROOT = "All Departments"
BAWAAN = [
    "Accounts", "Customer Service", "Dispatch", "Human Resources", "Legal",
    "Management", "Marketing", "Operations", "Production", "Purchase",
    "Quality Management", "Research & Development", "Sales",
]


def _salin():
    laporan = {"salin": 0, "dilewati": [], "nama_beda": [], "galat": []}

    if frappe.db.count(DT):
        raise SystemExit("BERHENTI: tabel HRIS Department sudah berisi data")

    baris = frappe.get_all(
        "Department",
        fields=["name", "department_name", "company", "parent_department", "is_group", "disabled", "lft"],
        order_by="lft asc",
    )
    akar = [b for b in baris if not b.parent_department]
    if len(akar) != 1:
        raise SystemExit("BERHENTI: akar ERPNext ditemukan %d (harus 1)" % len(akar))
    nama_akar = akar[0].name

    pegawai = dict(
        frappe.db.sql("select department, count(*) from `tabEmployee` where department is not null group by department")
    )

    # company="" mencegah Frappe mengisi default Company user pada akar
    root = frappe.get_doc({"doctype": DT, "department_name": ROOT, "company": "", "is_group": 1, "is_active": 1})
    root.flags.skip_sync = True
    root.insert(ignore_permissions=True)
    if root.name == ROOT:
        frappe.db.set_value(DT, ROOT, "company", None, update_modified=False)
    laporan["nama_akar_hris"] = root.name
    if root.name != ROOT:
        raise SystemExit("BERHENTI: nama akar HRIS = %r, bukan %r (company terisi otomatis?)" % (root.name, ROOT))

    for b in baris:
        if b.name == nama_akar:
            continue
        if b.department_name in BAWAAN and not b.is_group and not pegawai.get(b.name):
            laporan["dilewati"].append(b.name)
            continue
        induk = ROOT if b.parent_department == nama_akar else b.parent_department
        d = frappe.get_doc(
            {
                "doctype": DT,
                "department_name": b.department_name,
                "company": b.company,
                "parent_department": induk,
                "is_group": b.is_group,
                "is_active": 0 if b.disabled else 1,
            }
        )
        d.flags.skip_sync = True
        d.insert(ignore_permissions=True)
        laporan["salin"] += 1
        if d.name != b.name:
            laporan["nama_beda"].append((b.name, d.name))

    laporan["total_erpnext"] = len(baris)
    return laporan


def jalankan(mode):
    site = os.environ.get("SITE", "hris-uji.local")
    if site != "hris-uji.local" and os.environ.get("IZINKAN_SITE_LAIN") != "ya":
        raise SystemExit("BERHENTI: site %s ditolak (set IZINKAN_SITE_LAIN=ya bila sengaja)" % site)
    frappe.init(site=site, sites_path=".")
    frappe.connect()
    frappe.set_user("Administrator")
    ok = False
    try:
        lap = _salin()
        harapan = lap["total_erpnext"] - 1 - len(lap["dilewati"])
        print("Site                : %s (mode %s)" % (site, mode))
        print("Department ERPNext  : %d" % lap["total_erpnext"])
        print("Dilewati (bawaan)   : %d" % len(lap["dilewati"]))
        print("Disalin             : %d (harapan %d)" % (lap["salin"], harapan))
        print("Nama akar HRIS      : %s" % lap["nama_akar_hris"])
        print("Nama berbeda        : %d %s" % (len(lap["nama_beda"]), lap["nama_beda"][:5]))
        hitung = frappe.db.count(DT)
        print("Baris HRIS Department: %d (harapan %d termasuk akar)" % (hitung, harapan + 1))
        ok = lap["salin"] == harapan and not lap["nama_beda"] and hitung == harapan + 1
        if ok:
            # K-136: aturan akar dibuat dalam transaksi yang sama dengan salinan.
            # Patch idempoten; hasil harus tepat 1 aturan akar aktif.
            try:
                from hris.patches.v1_0.buat_aturan_akar_department import execute as buat_aturan_akar

                buat_aturan_akar()
                n_akar = frappe.db.sql(
                    "select count(*) from `tabHRIS Department Rule` "
                    "where department=%s and is_active=1 and overtime_multiplier>0",
                    (ROOT,),
                )[0][0]
            except Exception as e:
                n_akar = -1
                print("Galat membuat aturan akar: %s" % e)
            print("Aturan akar aktif   : %d (harapan 1)" % n_akar)
            ok = n_akar == 1
        print("HASIL: " + ("OK" if ok else "GAGAL"))
        if mode == "salin" and ok:
            frappe.db.commit()
            print("DISIMPAN (commit)")
        else:
            frappe.db.rollback()
            print("DI-ROLLBACK (tidak ada yang tersimpan)")
    finally:
        frappe.destroy()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("coba", "salin"):
        raise SystemExit("Pemakaian: migrasi_department.py coba|salin")
    jalankan(sys.argv[1])
