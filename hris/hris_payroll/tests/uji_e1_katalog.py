import frappe
def jalankan():
    ok = g = 0
    def cek(n, k, ket=""):
        nonlocal ok, g
        if k: ok += 1
        else: g += 1
        print(("OK      " if k else "GAGAL   ") + n, ket)
    rows = frappe.get_all("HRIS Pay Component", fields=["name", "is_active", "component_type"])
    cek("K1 enam komponen awal ada", len(rows) >= 6, len(rows))
    cek("K2 semua awal nonaktif", all(r.is_active == 0 for r in rows), [r.name for r in rows if r.is_active])
    frappe.db.savepoint("e1")
    try:
        try:
            frappe.get_doc({"doctype": "HRIS Pay Component", "component_code": "salah kode", "component_name": "x", "component_type": "Pendapatan"}).insert()
            cek("K3 kode tidak valid ditolak", False)
        except frappe.ValidationError:
            cek("K3 kode tidak valid ditolak", True)
        d = frappe.get_doc({"doctype": "HRIS Pay Component", "component_code": "ZZ_UJI", "component_name": "Uji", "component_type": "Pendapatan"}).insert()
        d.component_code = "ZZ_UBAH"
        try:
            d.save()
            cek("K4 ubah kode ditolak", False)
        except Exception:
            cek("K4 ubah kode ditolak", True)
    finally:
        frappe.db.rollback(save_point="e1")
    cek("K5 rollback bersih", not frappe.db.exists("HRIS Pay Component", "ZZ_UJI"))
    print("HASIL: OK %d, GAGAL %d" % (ok, g))
