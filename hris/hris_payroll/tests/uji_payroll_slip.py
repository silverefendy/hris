import os

import frappe
from frappe.utils import flt

ok = 0
gagal = 0


def cek(nama, kondisi, info=""):
    global ok, gagal
    if kondisi:
        ok += 1
        print("OK     ", nama)
    else:
        gagal += 1
        print("GAGAL  ", nama, info)


def harus_gagal(nama, fn):
    try:
        fn()
    except frappe.ValidationError:
        cek(nama, True)
        return
    except Exception as exc:
        cek(nama, False, "galat lain: %r" % (exc,))
        return
    cek(nama, False, "tidak ditolak")


def baris(status="Hadir", jam=10, telat=0, cepat=0, lembur=0, potong=0, kelas=""):
    return {"status": status, "scheduled_hours": jam, "late_deduction_hours": telat,
            "early_leave_deduction_hours": cepat, "overtime_minutes": lembur,
            "absence_deducted": potong, "absence_class": kelas}


def jumlah(h, nama):
    for k in h["komponen"]:
        if k["nama"] == nama:
            return k["jumlah"]
    return None


def total(h, tipe):
    return sum(k["jumlah"] for k in h["komponen"] if k["tipe"] == tipe)


def uji_murni():
    from hris.hris_payroll.services.payroll_slip import hitung_komponen

    b = [baris() for _i in range(18)]
    b[0] = baris(telat=1.0, lembur=120)
    b[1] = baris(cepat=0.5)
    b += [baris("Tidak Lengkap"), baris("Tidak Hadir", potong=1, kelas="Mangkir")]
    h = hitung_komponen("Bulanan", 3000000, b)
    cek("M1 Bulanan: Gaji Pokok", jumlah(h, "Gaji Pokok") == 3000000, h)
    cek("M1 Bulanan: tarif per jam 15.000", h["tarif_jam"] == 15000.0, h["tarif_jam"])
    cek("M1 Bulanan: Potongan Telat 15.000", jumlah(h, "Potongan Telat") == 15000, h)
    cek("M1 Bulanan: Potongan Pulang Cepat 7.500", jumlah(h, "Potongan Pulang Cepat") == 7500, h)
    cek("M1 Bulanan: Potongan Absen 150.000 (3.000.000 / 20)", jumlah(h, "Potongan Absen") == 150000, h)
    cek("M1 Bulanan: Lembur 30.000", jumlah(h, "Lembur") == 30000, h)
    cek("M1 Bulanan: pendapatan 3.030.000 dan potongan 172.500", total(h, "Pendapatan") == 3030000 and total(h, "Potongan") == 172500, h)
    cek("M1 Bulanan: ringkasan hari", h["ringkasan"]["working_days"] == 20 and h["ringkasan"]["present_days"] == 18, h["ringkasan"])
    cek("M1 Bulanan: Tidak Lengkap tercatat di catatan", any("Tidak Lengkap" in c for c in h["catatan"]), h["catatan"])

    b = [baris(jam=8) for _i in range(5)]
    b[0] = baris(jam=8, telat=1.0)
    b[1] = baris(jam=8, lembur=60)
    b += [baris("Tidak Hadir", jam=8), baris("Tidak Lengkap", jam=8)]
    h = hitung_komponen("Harian", 100000, b)
    cek("M2 Harian: Upah Harian 500.000", jumlah(h, "Upah Harian") == 500000, h)
    cek("M2 Harian: Potongan Telat 12.500", jumlah(h, "Potongan Telat") == 12500, h)
    cek("M2 Harian: Lembur 12.500", jumlah(h, "Lembur") == 12500, h)
    cek("M2 Harian: bersih 500.000 (sama dengan contoh rancangan)", total(h, "Pendapatan") - total(h, "Potongan") == 500000, h)
    cek("M2 Harian: tanpa komponen absen", jumlah(h, "Potongan Absen") is None, h)

    h = hitung_komponen("Bulanan", 1000000, [baris(jam=173, telat=1.5)])
    cek("M3 pembulatan: 8.670,52 menjadi 8.671", jumlah(h, "Potongan Telat") == 8671, h)
    h = hitung_komponen("Harian", 1, [baris(jam=2, telat=1.0)])
    cek("M3 pembulatan setengah ke atas: 0,5 menjadi 1", jumlah(h, "Potongan Telat") == 1, h)

    cek("M4 tanpa hari kerja: galat", "error" in hitung_komponen("Bulanan", 1000000, []))
    cek("M4 jam terjadwal nol: galat", "error" in hitung_komponen("Bulanan", 1000000, [baris(jam=0)]))
    cek("M4 jenis tidak dikenal: galat", "error" in hitung_komponen("Mingguan", 1000000, [baris()]))


def uji_izin():
    from hris.hris_payroll.doctype.hris_employee_pay.hris_employee_pay import boleh_baris
    from hris.hris_payroll.doctype.hris_payroll_slip import hris_payroll_slip as ds

    asli = frappe.get_roles
    try:
        frappe.get_roles = lambda user=None: ["HRIS Payroll Admin"]
        c = ds.get_permission_query_conditions("a@uji.test")
        cek("I1 Payroll Admin: daftar slip hanya Harian", "Harian" in c and "Bulanan" not in c, c)
        cek("I1 Payroll Admin: slip Bulanan ditolak", ds.has_permission(frappe._dict(pay_type="Bulanan"), user="a@uji.test") is False)
        cek("I1 Payroll Admin: slip Harian boleh", ds.has_permission(frappe._dict(pay_type="Harian"), user="a@uji.test") is True)
        cek("I1 Payroll Admin: tidak berhak memproses Bulanan", boleh_baris("Bulanan", user="a@uji.test") is False)
        frappe.get_roles = lambda user=None: ["HRIS Payroll Manager"]
        cek("I2 Payroll Manager: semua slip", ds.get_permission_query_conditions("m@uji.test") == "")
        frappe.get_roles = lambda user=None: ["HRIS HR Admin"]
        cek("I3 peran lain: tidak melihat slip", ds.get_permission_query_conditions("h@uji.test") == "1=0")
    finally:
        frappe.get_roles = asli


def satu(tipe, nominal, company):
    from hris.hris_payroll.doctype.hris_payroll_period.hris_payroll_period import kembalikan, tinjau
    from hris.hris_payroll.services import payroll_slip as ps
    from hris.hris_payroll.services.payroll_schedule import get_period_for_date

    t = tipe[0] + " "
    sch = frappe.get_doc({
        "doctype": "HRIS Payroll Schedule", "schedule_name": "ZZ Uji Slip", "company": company,
        "schedule_type": "Bulanan", "is_active": 1, "pay_date_offset_days": 3,
        "sunday_rule": "Maju ke Senin", "cut_off_day": 26,
    }).insert(ignore_permissions=True)
    rentang = get_period_for_date(sch.name, "2026-10-17")
    awal, akhir = str(rentang["start"]), str(rentang["end"])
    kand = frappe.db.sql(
        """
        select he.name as he, he.erpnext_employee as emp, count(*) as n
        from `tabHRIS Employee` he
        inner join `tabHRIS Working Hour` wh on wh.employee = he.erpnext_employee
        where wh.work_date between %(a)s and %(b)s
          and he.company = %(co)s
          and he.date_of_joining <= %(a)s
          and (he.resign_date is null or he.resign_date > %(b)s)
          and wh.status in ('Hadir', 'Tidak Lengkap', 'Tidak Hadir')
          and ifnull(wh.scheduled_hours, 0) > 0
          and not exists (select 1 from `tabHRIS Employee Pay` ep where ep.employee = he.name)
        group by he.name, he.erpnext_employee
        order by n desc limit 1
        """,
        {"a": awal, "b": akhir, "co": company},
        as_dict=True,
    )
    cek(t + "D0 ada karyawan kandidat dengan Working Hour pada periode", bool(kand), "periode %s s/d %s" % (awal, akhir))
    if not kand:
        return
    he, emp = kand[0].he, kand[0].emp
    frappe.get_doc({
        "doctype": "HRIS Employee Pay", "employee": he, "pay_type": tipe, "amount": nominal,
        "payroll_schedule": sch.name, "effective_from": "2026-01-01",
    }).insert(ignore_permissions=True)
    period = frappe.get_doc({
        "doctype": "HRIS Payroll Period", "payroll_schedule": sch.name, "reference_date": "2026-10-17",
    }).insert(ignore_permissions=True)

    h = ps.buat_slip(period.name, "Karyawan", employee=he)
    cek(t + "D1 slip dibuat", h.get("dibuat") == 1, h)
    nama = frappe.db.get_value("HRIS Payroll Slip", {"unique_key": period.name + "|" + he}, "name")
    cek(t + "D1 slip ditemukan lewat kunci unik", bool(nama))
    if not nama:
        return
    cek(t + "D1 penomoran PSL-2610-", nama.startswith("PSL-2610-"), nama)

    rows = frappe.get_all("HRIS Working Hour", filters={"employee": emp, "work_date": ["between", [awal, akhir]]},
                          fields=["status", "scheduled_hours"])
    hadir = len([r for r in rows if r.status == "Hadir"])
    kerja = [r for r in rows if r.status in ("Hadir", "Tidak Lengkap", "Tidak Hadir")]
    jam = sum(flt(r.scheduled_hours) for r in kerja)

    doc = frappe.get_doc("HRIS Payroll Slip", nama)
    oto = {r.component: r.amount for r in doc.components if r.source == "Otomatis"}
    cek(t + "D2 status Draft, jenis gaji, dan tautan Employee ERPNext", doc.status == "Draft" and doc.pay_type == tipe and doc.erpnext_employee == emp,
        (doc.status, doc.pay_type, doc.erpnext_employee))
    cek(t + "D2 hari Hadir dan hari kerja sesuai hitungan SQL", doc.present_days == hadir and doc.working_days == len(kerja),
        (doc.present_days, hadir, doc.working_days, len(kerja)))
    if tipe == "Harian":
        cek(t + "D2 Upah Harian = hari Hadir x upah", oto.get("Upah Harian") == hadir * nominal, oto)
    else:
        cek(t + "D2 Gaji Pokok = gaji bulanan", oto.get("Gaji Pokok") == nominal, oto)
        cek(t + "D2 tarif per jam = gaji / jam terjadwal", abs(flt(doc.hourly_rate) - nominal / jam) < 0.01, (doc.hourly_rate, nominal / jam))
    cek(t + "D2 gaji bersih = pendapatan - potongan", abs(flt(doc.net_pay) - (flt(doc.total_earning) - flt(doc.total_deduction))) < 0.01)

    awal_net = flt(doc.net_pay)
    doc.append("components", {"component": "Tunjangan Uji", "component_type": "Pendapatan", "amount": 50000,
                              "source": "Manual", "reason": "uji"})
    doc.save()
    doc.reload()
    cek(t + "D3 komponen Manual menambah gaji bersih", abs(flt(doc.net_pay) - awal_net - 50000) < 0.01, (awal_net, doc.net_pay))
    net_manual = flt(doc.net_pay)

    d2 = frappe.get_doc("HRIS Payroll Slip", nama)
    d2.append("components", {"component": "Tanpa Alasan", "component_type": "Pendapatan", "amount": 1000, "source": "Manual", "reason": ""})
    harus_gagal(t + "D3 komponen Manual tanpa alasan ditolak", d2.save)
    d3 = frappe.get_doc("HRIS Payroll Slip", nama)
    for r in d3.components:
        if r.source == "Otomatis":
            r.amount = 1
            break
    harus_gagal(t + "D3 komponen Otomatis tidak bisa diubah tangan", d3.save)

    ps.hitung_ulang_slip(nama)
    doc.reload()
    nama_manual = [r.component for r in doc.components if r.source == "Manual"]
    cek(t + "D4 hitung ulang mempertahankan komponen Manual", nama_manual == ["Tunjangan Uji"], nama_manual)
    cek(t + "D4 hitung ulang menghasilkan gaji bersih yang sama", abs(flt(doc.net_pay) - net_manual) < 0.01, (doc.net_pay, net_manual))
    urut = [(r.idx, r.source) for r in doc.components]
    cek(t + "D4 nomor baris berurutan 1..n tanpa ganda", [i for i, _s in urut] == list(range(1, len(urut) + 1)), urut)
    cek(t + "D4 komponen Otomatis tampil sebelum Manual", [s for _i, s in urut] == sorted([s for _i, s in urut], key=lambda x: 0 if x == "Otomatis" else 1), urut)
    h2 = ps.buat_slip(period.name, "Karyawan", employee=he)
    cek(t + "D4 Buat Slip kedua kali memperbarui, bukan menggandakan", h2.get("diperbarui") == 1 and h2.get("dibuat") == 0, h2)
    cek(t + "D4 tetap satu slip untuk periode ini", frappe.db.count("HRIS Payroll Slip", {"payroll_period": period.name}) == 1)

    tinjau(period.name)
    cek(t + "D5 status slip mengikuti Periode (Ditinjau)", frappe.db.get_value("HRIS Payroll Slip", nama, "status") == "Ditinjau")
    d4 = frappe.get_doc("HRIS Payroll Slip", nama)
    d4.append("components", {"component": "Saat Terkunci", "component_type": "Pendapatan", "amount": 1000, "source": "Manual", "reason": "uji"})
    harus_gagal(t + "D5 slip Ditinjau tidak bisa diubah", d4.save)
    harus_gagal(t + "D5 hitung ulang ditolak saat Periode Ditinjau", lambda: ps.hitung_ulang_slip(nama))
    kembalikan(period.name)
    cek(t + "D5 status slip kembali Draft bersama Periode", frappe.db.get_value("HRIS Payroll Slip", nama, "status") == "Draft")
    try:
        ps.hitung_ulang_slip(nama)
        cek(t + "D5 hitung ulang boleh lagi setelah Draft", True)
    except Exception as exc:
        cek(t + "D5 hitung ulang boleh lagi setelah Draft", False, repr(exc))

    harus_gagal(t + "D6 Periode yang punya slip tidak bisa dihapus", lambda: frappe.delete_doc("HRIS Payroll Period", period.name))
    harus_gagal(t + "D6 slip tidak bisa dibuat dari form", lambda: frappe.get_doc(
        {"doctype": "HRIS Payroll Slip", "payroll_period": period.name, "employee": he}).insert())


def uji_db():
    company = frappe.db.get_value("Company", {}, "name")
    n_awal = frappe.db.count("HRIS Payroll Slip")
    for tipe, nominal in (("Harian", 100000), ("Bulanan", 3000000)):
        try:
            satu(tipe, nominal, company)
        finally:
            frappe.db.rollback()
    cek("A1 kolom Alasan tampil di tabel Komponen", bool(frappe.get_meta("HRIS Payroll Slip Item").get_field("reason").in_list_view))
    cek("Z1 tidak ada sisa slip uji", frappe.db.count("HRIS Payroll Slip") == n_awal)
    cek("Z1 tidak ada sisa jadwal uji", not frappe.db.exists("HRIS Payroll Schedule", "ZZ Uji Slip"))


def periksa():
    uji_murni()
    uji_izin()
    uji_db()
    print("HASIL: OK %d, GAGAL %d" % (ok, gagal))
    return gagal


if __name__ == "__main__":
    os.chdir("/home/it/erp/sites")
    frappe.init(site="hris-uji.local", sites_path=".")
    frappe.connect()
    frappe.set_user("Administrator")
    try:
        sisa = periksa()
    finally:
        frappe.db.rollback()
        frappe.destroy()
    raise SystemExit(1 if sisa else 0)
