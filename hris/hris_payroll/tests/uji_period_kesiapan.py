"""Uji K-128: aturan kesiapan campuran, daftar lengkap bertautan, notifikasi in-app. Di-rollback.

Jalankan:
bench --site hris-uji.local execute hris.hris_payroll.tests.uji_period_kesiapan.periksa
"""

import frappe
from frappe.utils import add_days

hasil = []


def _catat(nama, lulus, info=""):
    hasil.append(bool(lulus))
    print(("OK     " if lulus else "GAGAL  ") + nama + ((" | " + str(info)) if info else ""))


def _user(email, peran):
    u = frappe.get_doc(
        {"doctype": "User", "email": email, "first_name": "UjiK", "send_welcome_email": 0, "enabled": 1}
    )
    u.insert(ignore_permissions=True)
    u.add_roles(peran)
    return email


def _ada_log(user, nama):
    return bool(
        frappe.db.exists(
            "Notification Log", {"for_user": user, "document_type": "HRIS Payroll Period", "document_name": nama}
        )
    )


def _jalankan(perusahaan):
    from hris.hris_payroll.doctype.hris_payroll_period import hris_payroll_period as P
    from hris.hris_payroll.tests import uji_payroll_period as U

    for nama in ("_wh", "_pay", "_periode"):
        if not hasattr(U, nama):
            _catat("helper %s tersedia di uji_payroll_period" % nama, False)
            return

    baris = frappe.db.sql(
        """
        select he.name, he.erpnext_employee from `tabHRIS Employee` he
        where ifnull(he.erpnext_employee, '') != '' and he.status = 'Aktif' and he.company = %s
          and not exists (select 1 from `tabHRIS Employee Pay` ep where ep.employee = he.name)
        order by he.name limit 2
        """,
        perusahaan,
    )
    jadwal = frappe.get_all("HRIS Payroll Schedule", filters={"is_active": 1, "company": perusahaan}, pluck="name", limit=1)
    if len(baris) < 2 or not jadwal:
        _catat("tersedia dua karyawan tanpa baris gaji dan satu jadwal aktif", False, "%d karyawan, %d jadwal" % (len(baris), len(jadwal)))
        return
    (he1, erp1), (he2, erp2) = baris
    j = jadwal[0]
    antre_awal = frappe.db.count("Email Queue")

    per = U._periode(j, "2026-02-03")
    d = [add_days(per.period_start, n) for n in range(1, 6)]
    U._pay(he1, j, "2025-12-01")
    r1 = U._wh(erp1, d[0], "Tidak Hadir", "Tidak Perlu")
    r2 = U._wh(erp1, d[1], "Tidak Lengkap", "Tidak Perlu")
    r3 = U._wh(erp1, d[2], "Tidak Lengkap", "Sudah Ditinjau")
    r4 = U._wh(erp1, d[3], "Hadir", "Menunggu")
    r5 = U._wh(erp1, d[4], "Tidak Hadir", "Menunggu")
    U._wh(erp2, d[0], "Hadir", "Tidak Perlu")

    k = P.hitung_kesiapan(frappe.get_doc(P.TABEL, per.name))
    item = {i["kode"]: i for i in k["items"]}
    belum = item.get("belum_ditinjau") or {}
    nama = {x["name"] for x in belum.get("daftar", [])}

    _catat("K1 Tidak Hadir + Tidak Perlu tidak menghalangi", r1.name not in nama)
    _catat("K2 Tidak Lengkap + Tidak Perlu menghalangi", r2.name in nama)
    _catat("K3 Tidak Lengkap + Sudah Ditinjau tidak menghalangi", r3.name not in nama)
    _catat("K4 Hadir + Menunggu menghalangi", r4.name in nama)
    _catat("K5 Tidak Hadir + Menunggu menghalangi", r5.name in nama)
    _catat("K6 jumlah yang menghalangi tepat 3", belum.get("jumlah") == 3, belum.get("jumlah"))

    kunci = ("pesan", "penyebab", "tindakan", "berwenang", "daftar", "tautan", "terpotong")
    _catat(
        "K7 item memuat pesan, penyebab, tindakan, berwenang, daftar, tautan",
        all(x in belum for x in kunci) and all(e["doctype"] == "HRIS Working Hour" for e in belum.get("daftar", [])),
    )

    tanpa = item.get("tanpa_gaji") or {}
    _catat(
        "K8 karyawan Hadir tanpa gaji masuk daftar dengan tautan buat gaji",
        any(erp2 in (e.get("info") or "") and e.get("name") == he2 and e.get("aksi") == "buat_gaji" for e in tanpa.get("daftar", [])),
    )

    asli = P.MAKS_DAFTAR
    P.MAKS_DAFTAR = 2
    try:
        k2 = P.hitung_kesiapan(frappe.get_doc(P.TABEL, per.name))
    finally:
        P.MAKS_DAFTAR = asli
    b2 = {i["kode"]: i for i in k2["items"]}.get("belum_ditinjau") or {}
    _catat(
        "K9 daftar dipotong sesuai batas dan ditandai terpotong",
        len(b2.get("daftar", [])) == 2 and b2.get("terpotong") is True and b2.get("jumlah") == 3,
    )

    u_m = _user("uji.k.manager@uji.local", "HRIS Payroll Manager")
    u_a = _user("uji.k.admin@uji.local", "HRIS Payroll Admin")

    P.tinjau(per.name)
    _catat("K11a Tinjau memberi notifikasi ke Payroll Manager", _ada_log(u_m, per.name))
    _catat("K11b Tinjau tidak memberi notifikasi ke Payroll Admin", not _ada_log(u_a, per.name))

    try:
        P.finalkan(per.name)
        pesan = ""
    except Exception as ex:  # noqa: BLE001
        pesan = str(ex)
    _catat(
        "K10 pesan penolakan Final memuat Tindakan dan Berwenang",
        "belum ditinjau" in pesan and "Tindakan:" in pesan and "Berwenang:" in pesan,
        pesan[:120].replace("<br>", " "),
    )

    P.kembalikan(per.name)
    _catat("K11c Kembalikan memberi notifikasi ke Payroll Admin", _ada_log(u_a, per.name))

    asli_penerima = P._penerima

    def _rusak(*a, **kw):
        raise RuntimeError("uji kegagalan notifikasi")

    P._penerima = _rusak
    try:
        galat = None
        try:
            P.tinjau(per.name)
        except Exception as ex:  # noqa: BLE001
            galat = ex
    finally:
        P._penerima = asli_penerima
    _catat(
        "K12 notifikasi gagal tidak membatalkan perpindahan status",
        galat is None and frappe.db.get_value(P.TABEL, per.name, "status") == "Ditinjau",
        repr(galat) if galat else "",
    )
    def izin(dt, p, u):
        return bool(frappe.has_permission(dt, p, user=u))

    _catat(
        "K13 Payroll Manager dan Payroll Admin punya izin write Employee Pay (dari JSON)",
        izin("HRIS Employee Pay", "write", u_m) and izin("HRIS Employee Pay", "write", u_a),
    )
    _catat(
        "K14 Payroll Manager murni boleh membaca, menulis, dan membuat Payroll Schedule, tetapi tidak menghapus",
        izin("HRIS Payroll Schedule", "read", u_m)
        and izin("HRIS Payroll Schedule", "write", u_m)
        and izin("HRIS Payroll Schedule", "create", u_m)
        and not izin("HRIS Payroll Schedule", "delete", u_m),
    )
    _catat("K15 Payroll Admin tetap boleh menulis Payroll Schedule", izin("HRIS Payroll Schedule", "write", u_a))
    _catat("K16 Payroll Admin tidak boleh menghapus Payroll Schedule", not izin("HRIS Payroll Schedule", "delete", u_a))
    print("INFO   Email Queue: %d sebelum, %d sesudah (tidak dinilai)" % (antre_awal, frappe.db.count("Email Queue")))


def periksa():
    hasil.clear()
    perusahaan = frappe.get_all("Company", pluck="name", limit=1)[0]
    try:
        _jalankan(perusahaan)
    except Exception as ex:  # noqa: BLE001
        import traceback

        traceback.print_exc()
        _catat("uji berjalan tanpa galat tak terduga", False, repr(ex)[:200])
    finally:
        frappe.set_user("Administrator")
        frappe.db.rollback()
    print("---")
    ringkas = "OK %d | GAGAL %d" % (hasil.count(True), hasil.count(False))
    print(ringkas)
    return ringkas
