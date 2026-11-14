"""K-140 tahap E1: penetapan komponen per Grup atau Department (HCA) digabung dengan HEC karyawan.

Fungsi murni (tanpa database). Prioritas: HEC karyawan menang atas HCA pada tanggal yang sama. HCA hanya
berlaku pada tanggal yang tidak tertutup HEC karyawan (Berlaku maupun Tidak Berlaku). Tanpa keduanya = tidak dapat.

Baris berbentuk {name, status, amount, date_from, date_to}, sama dengan HEC, sehingga hasilnya bisa langsung
diberikan ke hitung_tunjangan() di komponen_slip.py.
"""
from frappe.utils import add_days, getdate


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
