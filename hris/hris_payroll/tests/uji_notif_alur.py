"""K-137: uji alur penyimpanan HRIS Department Rule memicu pesan dan notifikasi (rollback penuh).

Hitungan slip dipalsukan menjadi 2; yang diuji: on_update terpanggil dari controller,
pesan oranye muncul hanya saat ada perubahan yang relevan, dan Notification Log dibuat.

Jalankan: bench --site hris-uji.local execute hris.hris_payroll.tests.uji_notif_alur.jalankan
"""
import frappe

from hris.hris_payroll.doctype.hris_payroll_period.hris_payroll_period import _penerima
from hris.hris_payroll.services import department_rule_notify as dn


def _pesan():
    return " ".join(str(m) for m in (frappe.local.message_log or []))


def jalankan():
    ok = []
    gagal = []

    def cek(nama, kondisi, ket=""):
        (ok if kondisi else gagal).append(nama)
        print("OK    " if kondisi else "GAGAL ", nama, ket)

    penerima = set()
    for peran in dn.PERAN_PENERIMA:
        if frappe.db.exists("Role", peran):
            penerima.update(_penerima(peran))

    asli = dn.hitung_slip_draft
    dn.hitung_slip_draft = lambda daftar, tanggal: 2
    frappe.db.savepoint("uji_alur")
    nama = None
    try:
        frappe.local.message_log = []
        doc = frappe.get_doc(
            {
                "doctype": "HRIS Department Rule",
                "department": "All Departments",
                "effective_from": "2099-01-01",
                "is_active": 1,
                "overtime_multiplier": 9.99,
            }
        ).insert(ignore_permissions=True)
        nama = doc.name
        cek("A1 Rule baru memunculkan pesan Slip Draft terpengaruh", "Slip Draft terpengaruh" in _pesan(), _pesan()[:90])
        dibuat = frappe.db.count("Notification Log", {"document_type": dn.RULE, "document_name": nama})
        cek("A2 Notification Log sama dengan jumlah penerima", dibuat == len(penerima), "(penerima %d, dibuat %d)" % (len(penerima), dibuat))

        frappe.local.message_log = []
        doc.overtime_multiplier = 9.5
        doc.save(ignore_permissions=True)
        cek("A3 ubah pengali memunculkan pesan lagi", "Slip Draft terpengaruh" in _pesan())

        frappe.local.message_log = []
        doc.reload()
        doc.save(ignore_permissions=True)
        cek("A4 simpan tanpa perubahan tidak memunculkan pesan", "Slip Draft terpengaruh" not in _pesan(), _pesan()[:90])
    finally:
        dn.hitung_slip_draft = asli
        frappe.db.rollback(save_point="uji_alur")
        frappe.local.message_log = []

    cek("A5 rollback bersih: Rule uji tidak tersisa", not (nama and frappe.db.exists("HRIS Department Rule", nama)))
    print("HASIL: OK %d, GAGAL %d" % (len(ok), len(gagal)))
