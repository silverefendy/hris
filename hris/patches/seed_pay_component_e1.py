import frappe

AWAL = [
    ("TJ_JABATAN", "Tunjangan Jabatan", "Pendapatan", 1, 1),
    ("TJ_TRANSPORT", "Tunjangan Transport", "Pendapatan", 1, 0),
    ("TJ_MAKAN", "Tunjangan Makan", "Pendapatan", 1, 0),
    ("INSENTIF", "Insentif", "Pendapatan", 1, 0),
    ("BONUS", "Bonus", "Pendapatan", 1, 0),
    ("POT_LAIN", "Potongan Lain", "Potongan", 0, 0),
]


def execute():
    """E1 tahap 1: isi katalog awal, semua nonaktif. Idempoten."""
    if not frappe.db.table_exists("HRIS Pay Component"):
        return
    for kode, nama, jenis, pajak, bpjs in AWAL:
        if frappe.db.exists("HRIS Pay Component", kode):
            continue
        frappe.get_doc({
            "doctype": "HRIS Pay Component", "component_code": kode, "component_name": nama,
            "component_type": jenis, "is_taxable": pajak, "in_bpjs_base": bpjs, "is_active": 0,
            "notes": "Nilai kena pajak dan dasar BPJS adalah tebakan awal; verifikasi HRD atau pajak.",
        }).insert(ignore_permissions=True)
    frappe.db.commit()
