"""Laporan perbandingan user di mesin (HRIS Device User) dengan HRIS Employee.

Hanya membaca. Tidak mengubah data. Fungsi susun() murni (tanpa database)
agar mudah diuji.
"""
import re
from collections import OrderedDict, defaultdict

import frappe

KATEGORI = {
    "A": "A. Ada di mesin, tidak ada Employee",
    "B": "B. Nama beda (mesin vs Employee)",
    "C": "C. Employee Aktif tidak ada di mesin",
    "D": "D. Employee tidak Aktif masih di mesin",
    "E": "E. ID sama, nama beda antar mesin",
    "F": "F. Data Employee bermasalah",
}

TINDAKAN = {
    "A": "Tambah Employee dengan ID Finger ini, atau perbaiki ID Finger Employee yang sudah ada",
    "B": "Periksa, lalu perbaiki nama di HRIS atau di mesin",
    "C": "Daftarkan di mesin (sesuai aturan distribusi) atau periksa ID Finger",
    "D": "Hapus dari mesin secara manual (tidak otomatis)",
    "E": "Periksa: dua orang berbeda atau salah ketik",
    "F": "Lengkapi atau perbaiki data Employee",
}

KOLOM = [
    {"label": "Kategori", "fieldname": "kategori", "fieldtype": "Data", "width": 260},
    {"label": "ID Finger", "fieldname": "id_finger", "fieldtype": "Data", "width": 90},
    {"label": "Nama di Mesin", "fieldname": "nama_mesin", "fieldtype": "Data", "width": 200},
    {"label": "Mesin", "fieldname": "mesin", "fieldtype": "Data", "width": 200},
    {"label": "Employee", "fieldname": "employee", "fieldtype": "Link", "options": "HRIS Employee", "width": 110},
    {"label": "Nama Employee", "fieldname": "employee_name", "fieldtype": "Data", "width": 200},
    {"label": "Status", "fieldname": "status", "fieldtype": "Data", "width": 80},
    {"label": "Department", "fieldname": "department", "fieldtype": "Data", "width": 200},
    {"label": "Keterangan", "fieldname": "keterangan", "fieldtype": "Data", "width": 260},
    {"label": "Tindakan Disarankan", "fieldname": "tindakan", "fieldtype": "Data", "width": 320},
]


def _id(x):
    s = str(x or "").strip()
    if not s:
        return ""
    return s.lstrip("0") or "0"


def _norm(n):
    n = (n or "").lower()
    n = re.sub(r"\([^)]*\)", " ", n)
    n = re.sub(r"[^a-z0-9 ]", " ", n)
    return " ".join(n.split())


def bandingkan_nama(a, b):
    na, nb = _norm(a), _norm(b)
    if not na or not nb:
        return "tidak ada"
    if na == nb:
        return "sama"
    if na.startswith(nb) or nb.startswith(na):
        return "mirip"
    ta, tb = set(na.split()), set(nb.split())
    if ta <= tb or tb <= ta:
        return "mirip"
    if len(ta & tb) / float(len(ta | tb)) >= 0.5:
        return "mirip"
    return "beda"


def _baris(kat, id_finger, e=None, nama_mesin="", mesin="", ket=""):
    e = e or {}
    return {
        "kategori": KATEGORI[kat],
        "id_finger": id_finger,
        "nama_mesin": nama_mesin,
        "mesin": mesin,
        "employee": e.get("name") or "",
        "employee_name": e.get("employee_name") or "",
        "status": e.get("status") or "",
        "department": e.get("department") or "",
        "keterangan": ket,
        "tindakan": TINDAKAN[kat],
    }


def susun(users, employees, mesin_tanpa_snapshot=0):
    by_id = OrderedDict()
    for u in users:
        k = _id(u.get("device_user_id"))
        if not k:
            continue
        g = by_id.setdefault(k, {"mesin": [], "nama": OrderedDict()})
        g["mesin"].append(u.get("device") or "")
        n = (u.get("user_name_on_device") or "").strip()
        if n:
            g["nama"].setdefault(n, []).append(u.get("device") or "")

    emp_by_id = defaultdict(list)
    for e in employees:
        k = _id(e.get("attendance_device_id"))
        if k:
            emp_by_id[k].append(e)

    rows = []

    for k, g in by_id.items():
        mesin = ", ".join(sorted(set(g["mesin"])))
        namas = list(g["nama"].keys())
        gabung = " / ".join(namas)
        emps = emp_by_id.get(k, [])
        if not emps:
            rows.append(_baris("A", k, None, gabung, mesin))
            continue
        if len(emps) > 1:
            continue  # ambigu, ditangani kategori F
        e = emps[0]
        if e.get("status") != "Aktif":
            rows.append(_baris("D", k, e, gabung, mesin, "Status: {0}".format(e.get("status") or "-")))
        konflik = False
        for i in range(len(namas)):
            for j in range(i + 1, len(namas)):
                if bandingkan_nama(namas[i], namas[j]) == "beda":
                    konflik = True
        if konflik:
            ket = " | ".join("{0} ({1})".format(n, ", ".join(sorted(set(d)))) for n, d in g["nama"].items())
            rows.append(_baris("E", k, e, gabung, mesin, ket))
        else:
            beda = [n for n in namas if bandingkan_nama(n, e.get("employee_name")) == "beda"]
            if beda:
                rows.append(_baris("B", k, e, gabung, mesin, "Nama di mesin: " + ", ".join(beda)))

    for k, lst in emp_by_id.items():
        for e in lst:
            if e.get("status") == "Aktif" and k not in by_id:
                ket = "Ada {0} mesin belum punya snapshot".format(mesin_tanpa_snapshot) if mesin_tanpa_snapshot else ""
                rows.append(_baris("C", k, e, "", "", ket))
            if len(lst) > 1:
                lain = ", ".join(x.get("name") for x in lst if x is not e)
                rows.append(_baris("F", k, e, "", "", "ID Finger ganda dengan " + lain))

    for e in employees:
        aktif = e.get("status") == "Aktif"
        if aktif and not _id(e.get("attendance_device_id")):
            rows.append(_baris("F", "", e, "", "", "ID Finger kosong"))
        if re.fullmatch(r"\s*(id\s*)?\d+\s*", (e.get("employee_name") or "").lower()):
            rows.append(_baris("F", _id(e.get("attendance_device_id")), e, "", "", "Nama berisi angka atau ID"))
        if aktif and not e.get("department"):
            rows.append(_baris("F", _id(e.get("attendance_device_id")), e, "", "", "Department kosong"))

    def kunci(r):
        idf = r["id_finger"]
        return (r["kategori"][0], int(idf) if idf.isdigit() else 10 ** 12, idf)

    rows.sort(key=kunci)
    return rows


def execute(filters=None):
    filters = filters or {}
    users = frappe.get_all(
        "HRIS Device User", filters={"in_last_snapshot": 1},
        fields=["device", "device_user_id", "user_name_on_device"], limit_page_length=0)
    employees = frappe.get_all(
        "HRIS Employee",
        fields=["name", "attendance_device_id", "employee_name", "department", "status"],
        limit_page_length=0)
    aktif = frappe.get_all("HRIS Device", filters={"is_active": 1}, pluck="name")
    punya = set(frappe.db.sql_list("select distinct device from `tabHRIS Device User`"))
    tanpa = [d for d in aktif if d not in punya]

    data = susun(users, employees, len(tanpa))
    kat = (filters.get("kategori") or "").strip()
    if kat:
        data = [r for r in data if r["kategori"].startswith(kat + ".")]

    pesan = "<b>Hanya membaca.</b> Kategori: " + "; ".join(KATEGORI.values()) + "."
    if tanpa:
        pesan += "<br><b>Mesin belum punya snapshot:</b> {0}. Kategori C belum dapat dipercaya.".format(", ".join(tanpa))
    return KOLOM, data, pesan
