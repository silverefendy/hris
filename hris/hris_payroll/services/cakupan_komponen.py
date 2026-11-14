"""K-140 tahap E1: penetapan komponen per Grup atau Department (HCA) digabung dengan HEC karyawan.

Fungsi murni (tanpa database). Prioritas: HEC karyawan menang atas HCA pada tanggal yang sama. HCA hanya
berlaku pada tanggal yang tidak tertutup HEC karyawan (Berlaku maupun Tidak Berlaku). Tanpa keduanya = tidak dapat.

Baris berbentuk {name, status, amount, date_from, date_to}, sama dengan HEC, sehingga hasilnya bisa langsung
diberikan ke hitung_tunjangan() di komponen_slip.py.
"""
import frappe
from frappe.utils import add_days, getdate
from frappe.utils.nestedset import get_ancestors_of


def _kurangi(dari, sampai, potong):
    """Sisa rentang [dari, sampai] setelah dikurangi daftar rentang (a, b). Mengembalikan daftar (awal, akhir)."""
    segmen = [(dari, sampai)]
    for a, b in potong:
        baru = []
        for s, e in segmen:
            if b < s or a > e:
                baru.append((s, e))
                continue
            if s < a:
                baru.append((s, getdate(add_days(a, -1))))
            if e > b:
                baru.append((getdate(add_days(b, 1)), e))
        segmen = baru
    return segmen


def gabung_cakupan(hec_karyawan, hca):
    """hec_karyawan dan hca = daftar baris (dict). Mengembalikan daftar baru terurut; input tidak diubah.
    Baris HCA yang tidak tersentuh tetap utuh; yang tertutup sebagian dipotong; yang tertutup penuh hilang."""
    potong = [(getdate(h["date_from"]), getdate(h["date_to"])) for h in hec_karyawan]
    hasil = [dict(h) for h in hec_karyawan]
    for g in hca:
        dari, sampai = getdate(g["date_from"]), getdate(g["date_to"])
        sisa = _kurangi(dari, sampai, potong)
        if sisa == [(dari, sampai)]:
            hasil.append(dict(g))
            continue
        for s, e in sisa:
            baris = dict(g)
            baris["date_from"], baris["date_to"] = s, e
            hasil.append(baris)
    hasil.sort(key=lambda x: (getdate(x["date_from"]), str(x.get("name") or "")))
    return hasil


def pilih_cakupan(rule_follow, group, baris_grup, baris_department):
    """Memilih HCA yang berlaku untuk satu karyawan dan komponen. Meniru nilai dasar (department_komponen.py):
    rule_follow = Grup dan Grup punya baris untuk komponen itu -> baris Grup; selain itu -> baris Department."""
    if rule_follow == "Grup" and group and baris_grup:
        return list(baris_grup)
    return list(baris_department)


# ---------- E3: penyusunan tingkat HCA dan pemuatan dari database ----------
HCA = "HRIS Component Assignment"
DEPT = "HRIS Department"
GRUP = "HRIS Employee Group"
KOLOM = ["name", "scope_type", "department", "employee_group", "include_children", "component",
         "status", "amount", "date_from", "date_to"]


def susun_tingkat(department, rantai_atas, group, rule_follow, baris_grup, baris_dept, grup_aktif):
    """Fungsi murni. Mengembalikan daftar tingkat (terdekat dulu), tiap tingkat = daftar baris HCA.
    rule_follow = Grup dan Grup aktif dan punya baris -> hanya tingkat Grup. Selain itu: Department karyawan,
    lalu Department induk hanya untuk baris dengan include_children. baris_dept = {department: [baris]}."""
    if rule_follow == "Grup" and group and grup_aktif and baris_grup:
        return [list(baris_grup)]
    tingkat = []
    for i, dep in enumerate([department] + list(rantai_atas)):
        if not dep:
            continue
        baris = [r for r in baris_dept.get(dep, []) if i == 0 or r.get("include_children")]
        if baris:
            tingkat.append(baris)
    return tingkat


def gabung_semua(hec_karyawan, tingkat):
    """HEC karyawan menang, lalu tiap tingkat HCA (terdekat dulu) hanya mengisi tanggal yang belum tertutup."""
    hasil = [dict(h) for h in hec_karyawan]
    for baris in tingkat:
        hasil = gabung_cakupan(hasil, baris)
    return hasil


def _filter_dasar(kode, awal, akhir):
    return {"component": kode, "is_active": 1, "date_from": ["<=", getdate(akhir)], "date_to": [">=", getdate(awal)]}


def ambil_tingkat(department, group, rule_follow, kode, awal, akhir):
    """Satu karyawan dan satu komponen. Tabel HCA belum ada (site belum dimigrasi) = tidak ada tingkat."""
    if not frappe.db.table_exists(HCA):
        return []
    baris_grup, grup_aktif = [], False
    if rule_follow == "Grup" and group:
        grup_aktif = bool(frappe.db.get_value(GRUP, group, "is_active"))
        if grup_aktif:
            baris_grup = frappe.get_all(
                HCA, filters=dict(_filter_dasar(kode, awal, akhir), scope_type="Grup", employee_group=group),
                fields=KOLOM, order_by="date_from asc")
    rantai = list(get_ancestors_of(DEPT, department)) if department else []
    nama = [d for d in [department] + rantai if d]
    baris_dept = {}
    if nama and not baris_grup:
        for r in frappe.get_all(
            HCA, filters=dict(_filter_dasar(kode, awal, akhir), scope_type="Department", department=["in", nama]),
            fields=KOLOM, order_by="date_from asc",
        ):
            baris_dept.setdefault(r["department"], []).append(r)
    return susun_tingkat(department, rantai, group, rule_follow, baris_grup, baris_dept, grup_aktif)


class GabungHec:
    """Pembungkus kamus HEC {(employee, kode): [baris]} untuk Payroll Summary: .get() mengembalikan HEC karyawan
    yang sudah digabung dengan HCA. HCA dimuat sekali untuk seluruh karyawan."""

    def __init__(self, hec, info, by_grup, by_dept, aktif):
        self.hec, self.info, self.by_grup, self.by_dept, self.aktif = hec, info, by_grup, by_dept, aktif
        self.rantai = {}

    def _rantai(self, dep):
        if dep not in self.rantai:
            self.rantai[dep] = list(get_ancestors_of(DEPT, dep)) if dep else []
        return self.rantai[dep]

    def get(self, kunci, default=None):
        emp, kode = kunci
        hec_k = list(self.hec.get(kunci, []))
        dep, grp, rf = self.info.get(emp, (None, None, None))
        baris_grup = self.by_grup.get((grp, kode), []) if (rf == "Grup" and grp) else []
        rantai = self._rantai(dep)
        baris_dept = {d: self.by_dept.get((d, kode), []) for d in [dep] + rantai if d}
        tingkat = susun_tingkat(dep, rantai, grp, rf, baris_grup, baris_dept, grp in self.aktif)
        hasil = gabung_semua(hec_k, tingkat)
        if hasil:
            return hasil
        return default if default is not None else []


def muat_hca(hec, karyawan, kode_list, awal, akhir):
    """Memuat HCA aktif yang menyentuh rentang untuk semua komponen, lalu membungkus kamus HEC.
    Tanpa tabel HCA atau tanpa baris HCA: mengembalikan kamus HEC apa adanya."""
    if not kode_list or not frappe.db.table_exists(HCA):
        return hec
    baris = frappe.get_all(
        HCA,
        filters={"component": ["in", list(kode_list)], "is_active": 1,
                 "date_from": ["<=", getdate(akhir)], "date_to": [">=", getdate(awal)]},
        fields=KOLOM, order_by="date_from asc",
    )
    if not baris:
        return hec
    by_grup, by_dept, nama_grup = {}, {}, set()
    for r in baris:
        if r["scope_type"] == "Grup":
            by_grup.setdefault((r["employee_group"], r["component"]), []).append(r)
            nama_grup.add(r["employee_group"])
        else:
            by_dept.setdefault((r["department"], r["component"]), []).append(r)
    aktif = set(frappe.get_all(GRUP, filters={"name": ["in", list(nama_grup)], "is_active": 1}, pluck="name")) if nama_grup else set()
    info = {k.get("name"): (k.get("department"), k.get("employee_group"), k.get("rule_follow")) for k in karyawan}
    return GabungHec(hec, info, by_grup, by_dept, aktif)
