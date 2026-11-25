"""Generator ID Finger untuk karyawan baru (rancangan U1-U7).

Hanya MEMBACA. Tidak menulis apa pun dan tidak memesan nomor. Perlindungan bentrok
ada di pengecekan unik saat simpan (HRISEmployee._cek_id_finger).
"""

import frappe

PERAN = ("HRIS Employee Admin", "HRIS HR Admin", "System Manager")

SUMBER = (
    ("employee", "Employee ERPNext", "tabEmployee", "attendance_device_id"),
    ("hris_employee", "HRIS Employee", "tabHRIS Employee", "attendance_device_id"),
    ("raw_log", "Raw Log mesin", "tabHRIS Raw Log", "device_user_id"),
)
ANGKA = "'^[0-9]+$'"


def _terbesar(tabel, kolom):
    nilai = frappe.db.sql(
        f"select max(cast(`{kolom}` as unsigned)) from `{tabel}` where `{kolom}` regexp {ANGKA}"
    )[0][0]
    return int(nilai or 0)


def _bukan_angka(tabel, kolom):
    nilai = frappe.db.sql(
        f"select count(distinct `{kolom}`) from `{tabel}` "
        f"where `{kolom}` is not null and `{kolom}` != '' and `{kolom}` not regexp {ANGKA}"
    )[0][0]
    return int(nilai or 0)


def _dipakai(nilai):
    for _kunci, _nama, tabel, kolom in SUMBER:
        if frappe.db.sql(f"select 1 from `{tabel}` where `{kolom}` = %s limit 1", (nilai,)):
            return True
    return False


@frappe.whitelist()
def ambil_id_berikutnya():
    """ID Finger berikutnya = angka terbesar di tiga sumber + 1. Tidak menyimpan apa pun."""
    frappe.only_for(PERAN)
    sumber, terbesar, bukan_angka = [], 0, 0
    for kunci, nama, tabel, kolom in SUMBER:
        t = _terbesar(tabel, kolom)
        b = _bukan_angka(tabel, kolom)
        sumber.append({"kunci": kunci, "nama": nama, "terbesar": t, "bukan_angka": b})
        terbesar = max(terbesar, t)
        bukan_angka += b
    kandidat = terbesar + 1
    for _ in range(50):
        if not _dipakai(str(kandidat)):
            break
        kandidat += 1
    return {
        "berikutnya": str(kandidat),
        "terbesar": terbesar,
        "sumber": sumber,
        "bukan_angka": bukan_angka,
    }
