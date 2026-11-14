"""K-140 tahap B: uji tombol massal. Bagian murni, lalu bagian database (di-rollback).

Jalankan:
bench --site hris-uji.local execute hris.hris_payroll.tests.uji_hec_massal.jalankan
"""
import frappe

from hris.hris_payroll.services import hec_massal as hm

HEC = "HRIS Employee Component"
KATALOG = "HRIS Pay Component"
AWAL, AKHIR = "2030-03-01", "2030-03-31"
ALASAN = "uji K-140 massal"


def _h(nama, status, dari, sampai):
    return {"name": nama, "status": status, "date_from": dari, "date_to": sampai}


def jalankan():
    hasil = []

    def cek(nama, kondisi, info=""):
        hasil.append(bool(kondisi))
        print(("OK     " if kondisi else "GAGAL  ") + nama + ((" | " + str(info)[:250]) if (not kondisi and info != "") else ""))

    def gagal_dengan(nama, fn):
        try:
            fn()
            cek(nama, False, "tidak ditolak")
        except (frappe.ValidationError, frappe.PermissionError):
            cek(nama, True)
            frappe.clear_messages()

    k = [{"name": "E1", "employee_name": "A"}, {"name": "E2", "employee_name": "B"}, {"name": "E3", "employee_name": "C"}]

    r = hm.rencanakan_massal(k, {}, {}, AWAL, AKHIR)
    cek("M1 tanpa HEC: semua dibuat, urutan terjaga", r["buat"] == ["E1", "E2", "E3"] and r["lewati"] == [], r)
    r = hm.rencanakan_massal(k, {"E2": [_h("HEC-X", "Berlaku", "2030-03-10", "2030-03-12")]}, {}, AWAL, AKHIR)
    cek("M2 HEC Berlaku bertumpuk: dilewati, alasan menyebut HEC", r["buat"] == ["E1", "E3"] and "HEC-X" in r["lewati"][0]["alasan"], r)
    r = hm.rencanakan_massal(k, {"E1": [_h("HEC-Y", "Tidak Berlaku", AWAL, AKHIR)]}, {}, AWAL, AKHIR)
    cek("M3 HEC Tidak Berlaku bertumpuk: tetap dilewati (tidak ditimpa)", r["buat"] == ["E2", "E3"] and r["lewati"][0]["employee"] == "E1", r)
    r = hm.rencanakan_massal(k, {"E3": [_h("HEC-Z", "Berlaku", "2030-04-01", "2030-04-30")]}, {}, AWAL, AKHIR)
    cek("M4 HEC di luar rentang: dibuat", r["buat"] == ["E1", "E2", "E3"], r)
    r = hm.rencanakan_massal(k, {"E1": [_h("HEC-T", "Berlaku", "2030-02-20", AWAL)]}, {}, AWAL, AKHIR)
    cek("M5 HEC menyentuh tepi (satu hari sama): dilewati", r["buat"] == ["E2", "E3"], r)
    r = hm.rencanakan_massal(k, {}, {"E2": False}, AWAL, AKHIR)
    cek("M6 tidak berhak: dilewati dengan alasan hak", r["buat"] == ["E1", "E3"] and "berhak" in r["lewati"][0]["alasan"].lower(), r)
    r = hm.rencanakan_massal(k, {"E1": [_h("HEC-A", "Berlaku", AWAL, AKHIR)]}, {"E2": False}, AWAL, AKHIR)
    cek("M7 campuran: 1 dibuat, 2 dilewati", r["buat"] == ["E3"] and len(r["lewati"]) == 2, r)

    g = frappe.db.sql(
        "select employee_group from `tabHRIS Employee` where status='Aktif' and employee_group is not null "
        "and company is not null group by employee_group having count(*) between 2 and 40 order by count(*) desc limit 1"
    )
    anak = frappe.db.sql("select parent_department from `tabHRIS Department` where parent_department is not null limit 1")
    awal_hec = frappe.db.count(HEC)
    try:
        frappe.db.set_value(KATALOG, "TJ_MAKAN", "is_active", 1)
        if anak:
            sendiri = len(hm._pilih(anak[0][0], 0, None))
            semua = len(hm._pilih(anak[0][0], 1, None))
            cek("D0 termasuk anak: jumlah tidak lebih sedikit", semua >= sendiri and sendiri >= 0, (sendiri, semua))
        else:
            print("SKIP   D0: tidak ada Department bertingkat")
        gagal_dengan("D1 Department dan Grup bersamaan ditolak", lambda: hm.pratinjau("TJ_MAKAN", AWAL, AKHIR, department="X", employee_group="Y"))
        gagal_dengan("D2 amount negatif ditolak", lambda: hm.terapkan("TJ_MAKAN", AWAL, AKHIR, ALASAN, amount=-1, employee_group="Y"))
        gagal_dengan("D3 alasan kosong ditolak", lambda: hm.terapkan("TJ_MAKAN", AWAL, AKHIR, " ", employee_group="Y"))
        if not g:
            print("SKIP   D4-D8: tidak ada Grup dengan 2 sampai 40 karyawan aktif ber-Company")
        else:
            G = g[0][0]
            n = len(hm._pilih(None, 0, G))
            print("INFO   uji database memakai Grup %s (%d karyawan aktif)" % (G, n))
            p1 = hm.pratinjau("TJ_MAKAN", AWAL, AKHIR, employee_group=G)
            cek("D4 pratinjau: dibuat + dilewati = jumlah karyawan", p1["akan_dibuat"] + p1["dilewati"] == n and p1["dipilih"] == n, p1)
            t1 = hm.terapkan("TJ_MAKAN", AWAL, AKHIR, ALASAN, amount=0, employee_group=G)
            cek("D5 terapkan: dibuat + gagal = rencana pratinjau, minimal 1 dibuat",
                t1["dibuat"] + t1["gagal"] == p1["akan_dibuat"] and t1["dibuat"] >= 1, t1)
            ada = frappe.db.count(HEC, {"component": "TJ_MAKAN", "date_from": AWAL, "reason": "Massal: " + ALASAN})
            cek("D6 jumlah HEC di database sama dengan dibuat", ada == t1["dibuat"], (ada, t1["dibuat"]))
            t2 = hm.terapkan("TJ_MAKAN", AWAL, AKHIR, ALASAN, amount=0, employee_group=G)
            cek("D7 diulang: tidak ada yang dibuat, semua dilewati", t2["dibuat"] == 0 and t2["dilewati"] >= t1["dibuat"], t2)
            p3 = hm.pratinjau("TJ_MAKAN", "2030-03-15", "2030-04-15", employee_group=G)
            cek("D8 rentang tumpang tindih sebagian: yang sudah punya dilewati", p3["dilewati"] >= t1["dibuat"], p3)
        frappe.db.set_value(KATALOG, "TJ_MAKAN", "is_active", 0)
        gagal_dengan("D9 komponen nonaktif ditolak", lambda: hm.pratinjau("TJ_MAKAN", AWAL, AKHIR, employee_group="Y"))
    finally:
        frappe.db.rollback()
    cek("D10 rollback: jumlah HEC kembali seperti awal", frappe.db.count(HEC) == awal_hec, (frappe.db.count(HEC), awal_hec))
    print("OK %d, GAGAL %d (data uji di-rollback)" % (sum(hasil), len(hasil) - sum(hasil)))
