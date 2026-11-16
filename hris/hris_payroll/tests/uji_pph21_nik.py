"""Uji aturan KTP terisi dianggap punya NPWP pada PPh 21 TER (K-142 3a-1). Semua perubahan di-rollback.

bench --site hris-uji.local execute hris.hris_payroll.tests.uji_pph21_nik.jalankan
"""

from decimal import Decimal

import frappe

from hris.hris_payroll.services import payroll_pph21 as pph

SETTINGS = "HRIS PPh21 Settings"
RATE = "HRIS PPh21 TER Rate"
PERIODE = frappe._dict(name="SINT", pay_date="2030-03-31")
HE = frappe._dict(name="HRIS-EMP-SINT")
HASIL = {"komponen": [{"nama": "Gaji Pokok", "tipe": "Pendapatan", "jumlah": 10000000}]}
NPWP = "01.234.567.8-901.000"
KTP = "3275010101010001"


def cek(nama, kondisi, info=""):
    print(("OK     " if kondisi else "GAGAL  ") + nama + (" | " + str(info) if info else ""))


def pajak(npwp, ktp):
    pph._data_karyawan = lambda he: {"pph21_enrolled": 1, "ptkp_status": "ZZ/0", "npwp": npwp, "ktp_number": ktp}
    r = pph.hitung_pph21_slip(HE, PERIODE, None, HASIL)
    if r.get("dilewati"):
        return None, [r["dilewati"]]
    return sum(int(k["jumlah"]) for k in r["komponen"] if k["nama"] == "PPh 21"), r["catatan"]


def atur_nik(nilai):
    st = frappe.get_doc(SETTINGS)
    st.nik_as_npwp = nilai
    st.save(ignore_permissions=True)


def jalankan():
    asli = (pph._data_karyawan, pph._slip_saat_ini, pph._slip_lain, pph._slip_terakhir, pph._jumlah_slip_jadwal)
    aktif0 = frappe.db.get_single_value(SETTINGS, "enabled")
    n_rate0 = frappe.db.count(RATE)
    try:
        st = frappe.get_doc(SETTINGS)
        st.enabled = 1
        st.no_npwp_multiplier = 1.2
        st.nik_as_npwp = 1
        frappe.get_doc({"doctype": RATE, "ter_category": "UJINIK", "effective_from": "2030-03-01",
                        "enabled": 1, "bruto_from": 0, "open_ended": 1, "rate_percent": 5}).insert(ignore_permissions=True)
        st.append("ptkp_map", {"ptkp_status": "ZZ/0", "ter_category": "UJINIK"})
        st.save(ignore_permissions=True)
        pph._slip_saat_ini = lambda he, period: (None, Decimal(0))
        pph._slip_lain = lambda he, period, nama_ada, bebas: (0, Decimal(0), None)
        pph._slip_terakhir = lambda period: True
        pph._jumlah_slip_jadwal = lambda period: 1

        p, c = pajak(NPWP, "")
        cek("N1 NPWP terisi: tanpa pengali (500.000)", p == 500000, (p, c))
        p, c = pajak("", "")
        cek("N2 NPWP dan KTP kosong: pengali 1,2 berlaku (600.000)", p == 600000, (p, c))
        p, c = pajak("", KTP)
        cek("N3 NPWP kosong, KTP terisi, pilihan hidup: tanpa pengali (500.000)", p == 500000, (p, c))
        cek("N5 catatan menyebut NIK dipakai sebagai pengganti NPWP", any("NIK" in t for t in c), c)
        atur_nik(0)
        p, c = pajak("", KTP)
        cek("N4 NPWP kosong, KTP terisi, pilihan mati: pengali berlaku (600.000)", p == 600000, (p, c))
        cek("N6 pilihan belum disimpan dianggap hidup; 0 mati; 1 hidup",
            pph._nik_setara_npwp(frappe._dict()) is True
            and pph._nik_setara_npwp(frappe._dict(nik_as_npwp=None)) is True
            and pph._nik_setara_npwp(frappe._dict(nik_as_npwp=0)) is False
            and pph._nik_setara_npwp(frappe._dict(nik_as_npwp=1)) is True)
    except Exception as e:
        cek("N berhenti karena galat", False, repr(e)[:400])
    finally:
        pph._data_karyawan, pph._slip_saat_ini, pph._slip_lain, pph._slip_terakhir, pph._jumlah_slip_jadwal = asli
        frappe.db.rollback()
    cek("N7 rollback: pengaturan dan tarif kembali seperti semula",
        frappe.db.get_single_value(SETTINGS, "enabled") == aktif0 and frappe.db.count(RATE) == n_rate0)
