import frappe

USER_HR = "uji.hr@uji.local"
USER_PAY = "uji.payroll@uji.local"
DOC_NAMA = "Uji Tampilan Permlevel"


def _buat_user(email, nama, role, password):
    if frappe.db.exists("User", email):
        frappe.delete_doc("User", email, force=True, ignore_permissions=True)
    u = frappe.get_doc({
        "doctype": "User", "email": email, "first_name": nama,
        "send_welcome_email": 0, "user_type": "System User",
    })
    u.append("roles", {"role": role})
    u.insert(ignore_permissions=True)
    u.new_password = password
    u.save(ignore_permissions=True)


def siapkan(password):
    """Buat 2 user uji dan 1 dokumen uji (KTP palsu). Hanya untuk site uji."""
    if "uji" not in frappe.local.site:
        print("BERHENTI: bukan site uji"); return "berhenti"
    _buat_user(USER_HR, "Uji HR", "HR User", password)
    _buat_user(USER_PAY, "Uji Payroll", "HRIS Payroll Admin", password)
    if not frappe.db.exists("HRIS Employee", {"employee_name": DOC_NAMA}):
        frappe.get_doc({
            "doctype": "HRIS Employee", "employee_name": DOC_NAMA,
            "company": frappe.db.get_value("Company", {}, "name"),
            "date_of_joining": "2026-01-01",
            "ktp_number": "9999999999999999", "bank_account_number": "000111222",
        }).insert(ignore_permissions=True)
    frappe.db.commit()
    print("user dan dokumen uji siap")
    return "siap"


def periksa():
    nama = frappe.db.get_value("HRIS Employee", {"employee_name": DOC_NAMA}, "name")
    hasil = []
    for user, boleh_lihat in ((USER_HR, False), (USER_PAY, True)):
        frappe.set_user(user)
        try:
            baca = frappe.has_permission("HRIS Employee", "read", user=user)
            doc = frappe.get_doc("HRIS Employee", nama)
            doc.apply_fieldlevel_read_permissions()
            tampil = bool(doc.get("ktp_number")) and bool(doc.get("bank_account_number"))
            nama_tampil = bool(doc.get("employee_name"))
        finally:
            frappe.set_user("Administrator")
        hasil.append(("%s bisa baca dokumen" % user, baca))
        hasil.append(("%s melihat nama" % user, nama_tampil))
        hasil.append(("%s %s KTP dan rekening" % (user, "melihat" if boleh_lihat else "TIDAK melihat"), tampil == boleh_lihat))
    gagal = 0
    for n, ok in hasil:
        print(("OK     " if ok else "GAGAL  ") + n)
        gagal += 0 if ok else 1
    ringkas = "TOTAL: %d OK, GAGAL %d" % (len(hasil) - gagal, gagal)
    print(ringkas)
    return ringkas


def bersihkan():
    for e in (USER_HR, USER_PAY):
        if frappe.db.exists("User", e):
            frappe.delete_doc("User", e, force=True, ignore_permissions=True)
    for n in frappe.get_all("HRIS Employee", filters={"employee_name": DOC_NAMA}, pluck="name"):
        frappe.delete_doc("HRIS Employee", n, force=True, ignore_permissions=True)
    frappe.db.commit()
    print("dibersihkan")
    return "dibersihkan"


def periksa_audit():
    """Uji: audit trail tidak membocorkan nilai field permlevel 1."""
    from hris.hris_attendance.services.audit_trail import get_audit_trail

    nama = frappe.db.get_value("HRIS Employee", {"employee_name": DOC_NAMA}, "name")
    if not nama:
        print("BERHENTI: jalankan siapkan dulu")
        return "berhenti"
    d = frappe.get_doc("HRIS Employee", nama)
    d.bank_account_number = "999888777" if d.bank_account_number != "999888777" else "000111222"
    d.save(ignore_permissions=True)
    frappe.db.commit()

    hasil = []
    for user, boleh_lihat in ((USER_HR, False), (USER_PAY, True)):
        frappe.set_user(user)
        try:
            baris = get_audit_trail("HRIS Employee", nama)
        finally:
            frappe.set_user("Administrator")
        teks = " ".join("%s %s" % (r["old"], r["new"]) for r in baris)
        ada_angka = "999888777" in teks or "000111222" in teks
        hasil.append(("%s audit trail tidak kosong" % user, len(baris) > 1))
        hasil.append(
            ("%s %s nilai rekening di audit trail" % (user, "melihat" if boleh_lihat else "TIDAK melihat"), ada_angka == boleh_lihat)
        )
    gagal = 0
    for n, ok in hasil:
        print(("OK     " if ok else "GAGAL  ") + n)
        gagal += 0 if ok else 1
    ringkas = "TOTAL: %d OK, GAGAL %d" % (len(hasil) - gagal, gagal)
    print(ringkas)
    return ringkas
