"""Uji K-127: HRIS Employee Pay. Semua di-rollback.

Jalankan:
bench --site hris-uji.local execute hris.hris_payroll.tests.uji_employee_pay.periksa
"""

import frappe
from frappe.utils import strip_html

hasil = []
S = {}

USERS = {
    "admin": ("uji.pay.admin@uji.local", ["HRIS Payroll Admin"]),
    "manager": ("uji.pay.manager@uji.local", ["HRIS Payroll Manager"]),
    "direksi": ("uji.pay.direksi@uji.local", ["HRIS Direksi"]),
    "biasa": ("uji.pay.biasa@uji.local", ["HR User"]),
}


def _catat(nama, lulus, info=""):
    hasil.append(bool(lulus))
    print(("OK     " if lulus else "GAGAL  ") + nama + ((" | " + info) if info else ""))


def _info(nama, info=""):
    print("INFO   " + nama + ((" | " + info) if info else ""))


def _harus_ditolak(nama, fungsi, kata_kunci=None):
    try:
        fungsi()
    except (frappe.ValidationError, frappe.PermissionError) as e:
        pesan = strip_html(str(e))
        if kata_kunci:
            _catat(nama, kata_kunci.lower() in pesan.lower(), pesan[:120])
        else:
            _catat(nama, True, pesan[:120])
    except Exception as e:  # noqa: BLE001
        _catat(nama, False, "galat lain: " + repr(e)[:120])
    else:
        _catat(nama, False, "TIDAK ditolak")


def _harus_lolos(nama, fungsi):
    try:
        fungsi()
    except Exception as e:  # noqa: BLE001
        _catat(nama, False, "ditolak: " + strip_html(str(e))[:120])
    else:
        _catat(nama, True)


def _buat_jadwal(perusahaan, nama, aktif):
    doc = frappe.get_doc(
        {
            "doctype": "HRIS Payroll Schedule",
            "schedule_name": nama,
            "company": perusahaan,
            "schedule_type": "Bulanan",
            "cut_off_day": 26,
            "is_active": aktif,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc


def _buat_karyawan(perusahaan, nama):
    doc = frappe.get_doc(
        {
            "doctype": "HRIS Employee",
            "employee_name": nama,
            "birth_date": "1990-05-10",
            "gender": "Laki-laki",
            "company": perusahaan,
            "date_of_joining": "2020-01-01",
            "status": "Aktif",
        }
    )
    doc.flags.skip_sync = True
    doc.insert(ignore_permissions=True)
    return doc


def _buat_user(email, peran):
    frappe.get_doc(
        {
            "doctype": "User",
            "email": email,
            "first_name": "ZZ Uji",
            "enabled": 1,
            "send_welcome_email": 0,
            "user_type": "System User",
            "roles": [{"role": r} for r in peran],
        }
    ).insert(ignore_permissions=True)


def _pay(emp, **kw):
    isi = {
        "doctype": "HRIS Employee Pay",
        "employee": emp.name,
        "pay_type": "Harian",
        "amount": 100000,
        "payroll_schedule": S["jadwal"],
        "effective_from": "2026-01-01",
    }
    isi.update(kw)
    return frappe.get_doc(isi)


def _sebagai(email, fungsi):
    frappe.set_user(email)
    try:
        return fungsi()
    finally:
        frappe.set_user("Administrator")


def _boleh(jenis, nama_doc, email):
    return frappe.has_permission("HRIS Employee Pay", jenis, doc=nama_doc, user=email)


def _terbuka(emp):
    return frappe.db.count(
        "HRIS Employee Pay", {"employee": emp.name, "effective_to": ["is", "not set"]}
    )


def _jalankan(perusahaan):
    for _email, peran in USERS.values():
        for r in peran:
            if not frappe.db.exists("Role", r):
                _catat("role ada: " + r, False, "belum ada di site ini, uji dihentikan")
                return

    S["jadwal"] = _buat_jadwal(perusahaan, "ZZ Uji Jadwal 127", 1).name
    S["jadwal_mati"] = _buat_jadwal(perusahaan, "ZZ Uji Jadwal Mati 127", 0).name
    a = _buat_karyawan(perusahaan, "ZZ Uji K127 A")
    b = _buat_karyawan(perusahaan, "ZZ Uji K127 B")
    c = _buat_karyawan(perusahaan, "ZZ Uji K127 C")
    d = _buat_karyawan(perusahaan, "ZZ Uji K127 D")
    e = _buat_karyawan(perusahaan, "ZZ Uji K127 E")
    for email, peran in USERS.values():
        _buat_user(email, peran)
    u_admin, u_manager = USERS["admin"][0], USERS["manager"][0]
    u_direksi, u_biasa = USERS["direksi"][0], USERS["biasa"][0]

    # ---- aturan baris (sebagai Administrator) ----
    p1 = _pay(a).insert(ignore_permissions=True)
    _catat(
        "T01 baris pertama dibuat, terbuka, nomor HEP-",
        p1.name.startswith("HEP-")
        and not p1.effective_to
        and p1.company == perusahaan
        and p1.employee_name == "ZZ Uji K127 A",
        "%s | %s" % (p1.name, p1.effective_to),
    )

    _harus_ditolak("T02a nominal 0 ditolak", lambda: _pay(b, amount=0).insert(ignore_permissions=True), "nominal")
    _harus_ditolak("T02b nominal negatif ditolak", lambda: _pay(b, amount=-5).insert(ignore_permissions=True), "nominal")
    _harus_ditolak(
        "T03 baris kedua tanpa alasan ditolak",
        lambda: _pay(a, effective_from="2026-07-01").insert(ignore_permissions=True),
        "alasan",
    )
    _harus_ditolak(
        "T04a tanggal sama dengan baris terbuka ditolak",
        lambda: _pay(a, effective_from="2026-01-01", change_reason="x").insert(ignore_permissions=True),
        "setelah",
    )
    _harus_ditolak(
        "T04b tanggal sebelum baris terbuka ditolak",
        lambda: _pay(a, effective_from="2025-12-01", change_reason="x").insert(ignore_permissions=True),
        "setelah",
    )

    p2 = _pay(a, amount=110000, effective_from="2026-07-01", change_reason="Kenaikan").insert(
        ignore_permissions=True
    )
    p1.reload()
    _catat(
        "T05 baris lama ditutup otomatis, hanya satu baris terbuka",
        str(p1.effective_to) == "2026-06-30" and not p2.effective_to and _terbuka(a) == 1,
        "p1.effective_to=%s | terbuka=%s" % (p1.effective_to, _terbuka(a)),
    )

    p1.amount = 1
    _harus_ditolak("T06a ubah nominal baris tertutup ditolak", lambda: p1.save(ignore_permissions=True), "tidak dapat diubah")
    p1.reload()
    p2.amount = 5
    _harus_ditolak("T06b ubah nominal baris terbuka ditolak", lambda: p2.save(ignore_permissions=True), "tidak dapat diubah")
    p2.reload()
    p2.effective_to = "2026-12-31"
    _harus_ditolak("T06c isi manual Berlaku Sampai ditolak", lambda: p2.save(ignore_permissions=True), "tidak dapat diubah")
    p2.reload()

    _harus_ditolak(
        "T07 jadwal nonaktif ditolak",
        lambda: _pay(b, payroll_schedule=S["jadwal_mati"]).insert(ignore_permissions=True),
        "aktif",
    )
    _harus_ditolak(
        "T08 jenis gaji di luar pilihan ditolak",
        lambda: _pay(b, pay_type="Mingguan").insert(ignore_permissions=True),
    )
    _harus_lolos(
        "T09 tanggal berlaku mundur (2020) diterima",
        lambda: _pay(c, effective_from="2020-01-01").insert(ignore_permissions=True),
    )
    pb = _pay(b, pay_type="Bulanan", amount=3000000).insert(ignore_permissions=True)
    _catat("T10 baris Bulanan dibuat", bool(pb.name), pb.name)

    # ---- Payroll Admin ----
    _catat("T11a Payroll Admin boleh baca baris Harian", _boleh("read", p2.name, u_admin) is True)
    _catat("T11b Payroll Admin TIDAK boleh baca baris Bulanan", _boleh("read", pb.name, u_admin) is False)
    nama_list = frappe.get_list(
        "HRIS Employee Pay",
        filters={"employee": ["in", [a.name, b.name]]},
        pluck="name",
        user=u_admin,
    )
    _catat(
        "T11c daftar Payroll Admin berisi Harian, tanpa Bulanan",
        p1.name in nama_list and p2.name in nama_list and pb.name not in nama_list,
        str(nama_list),
    )
    _harus_ditolak(
        "T11d Payroll Admin tidak boleh membuat baris Bulanan",
        lambda: _sebagai(u_admin, lambda: _pay(d, pay_type="Bulanan", amount=4000000).insert()),
    )
    _harus_ditolak(
        "T11e Payroll Admin tidak boleh menimpa karyawan yang gajinya Bulanan",
        lambda: _sebagai(
            u_admin,
            lambda: _pay(b, effective_from="2026-09-01", change_reason="coba").insert(),
        ),
    )
    p3 = _sebagai(
        u_admin,
        lambda: _pay(a, amount=120000, effective_from="2026-09-01", change_reason="Kenaikan 2").insert(),
    )
    p2.reload()
    _catat(
        "T11f Payroll Admin boleh membuat baris Harian, baris lama ditutup",
        bool(p3.name) and str(p2.effective_to) == "2026-08-31",
        "p2.effective_to=%s" % p2.effective_to,
    )

    # ---- Payroll Manager ----
    _catat(
        "T12a Payroll Manager baca Harian dan Bulanan",
        _boleh("read", p2.name, u_manager) is True and _boleh("read", pb.name, u_manager) is True,
    )
    _harus_lolos(
        "T12b Payroll Manager boleh membuat baris Bulanan",
        lambda: _sebagai(u_manager, lambda: _pay(d, pay_type="Bulanan", amount=4000000).insert()),
    )

    # ---- Direksi ----
    _catat("T13a Direksi baca baris Bulanan", _boleh("read", pb.name, u_direksi) is True)
    _harus_ditolak(
        "T13b Direksi tidak boleh membuat baris",
        lambda: _sebagai(u_direksi, lambda: _pay(e).insert()),
    )

    # ---- HR User (tanpa hak gaji) ----
    _catat("T14a HR User tidak boleh baca baris gaji", _boleh("read", p2.name, u_biasa) is False)
    try:
        ada = frappe.get_list(
            "HRIS Employee Pay",
            filters={"employee": ["in", [a.name, b.name]]},
            pluck="name",
            user=u_biasa,
        )
        _catat("T14b daftar HR User kosong", not ada, str(ada))
    except frappe.PermissionError:
        _catat("T14b daftar HR User ditolak", True, "PermissionError")

    # ---- hak hapus ----
    _catat("T15a Payroll Admin tanpa hak hapus", _boleh("delete", p2.name, u_admin) is False)
    _catat("T15b Payroll Manager tanpa hak hapus", _boleh("delete", p2.name, u_manager) is False)
    _harus_ditolak(
        "T16 hapus baris yang sudah ditutup ditolak",
        lambda: frappe.delete_doc("HRIS Employee Pay", p1.name),
        "ditutup",
    )
    frappe.delete_doc("HRIS Employee Pay", p3.name)
    p2.reload()
    _catat(
        "T17 hapus baris terbaru membuka kembali baris sebelumnya",
        not p2.effective_to and _terbuka(a) == 1,
        "p2.effective_to=%s | terbuka=%s" % (p2.effective_to, _terbuka(a)),
    )

    # ---- informasi: penjaga jadwal (K-105), tidak dihitung lulus/gagal ----
    jd = frappe.get_doc("HRIS Payroll Schedule", S["jadwal"])
    jd.is_active = 0
    try:
        jd.save(ignore_permissions=True)
        _info("T18 jadwal yang sudah dipakai lalu dinonaktifkan: TIDAK ditolak", "periksa validate_deactivation")
    except frappe.ValidationError as ex:
        _info("T18 jadwal yang sudah dipakai tidak bisa dinonaktifkan (penjaga aktif)", strip_html(str(ex))[:120])


def periksa():
    hasil.clear()
    S.clear()
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
        for email, _peran in USERS.values():
            frappe.clear_cache(user=email)
    print("---")
    ringkas = "OK %d | GAGAL %d" % (hasil.count(True), hasil.count(False))
    print(ringkas)
    return ringkas
