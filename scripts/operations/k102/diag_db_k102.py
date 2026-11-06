# Diagnosa BACA-SAJA database (tanpa commit, tanpa menulis)
import frappe


def p(k, v):
    print("DIAG|%s|%s" % (k, v))


def jalankan():
    c = frappe.conf
    p("developer_mode", c.get("developer_mode"))
    p("maintenance_mode", c.get("maintenance_mode"))
    p("pause_scheduler", c.get("pause_scheduler"))
    p("mute_emails", c.get("mute_emails"))
    r = frappe.db.sql("select count(*), max(modified) from `tabEmployee`")[0]
    p("employee", "jumlah=%s max_modified=%s" % r)
    p("employee_status", frappe.db.sql("select status, count(*) from `tabEmployee` group by status"))
    ada = frappe.db.sql("show tables like 'tabHRIS Employee'")
    p("tabel_HRIS_Employee", "ADA" if ada else "belum ada")
    if ada:
        p("HRIS_Employee_jumlah", frappe.db.sql("select count(*) from `tabHRIS Employee`")[0][0])
        kol = [x[0] for x in frappe.db.sql("show columns from `tabHRIS Employee`")]
        p("kolom_data_status_note", [k for k in kol if k in ("data_status", "data_note")])
    ada2 = frappe.db.sql("show tables like 'tabHRIS Payroll Schedule'")
    p("tabel_HRIS_Payroll_Schedule", "ADA" if ada2 else "belum ada")
    p("role_HRIS", [x[0] for x in frappe.db.sql("select name from tabRole where name like 'HRIS%' order by name")])
    p("module_HRIS", [x[0] for x in frappe.db.sql("select name from `tabModule Def` where app_name='hris' order by name")])
    p("sesi_aktif_24j", frappe.db.sql("select count(distinct user) from tabSessions where lastupdate > now() - interval 1 day")[0][0])
    p("user_aktif", frappe.db.sql("select count(*) from tabUser where enabled=1 and user_type='System User'")[0][0])
    p("scheduled_job_aktif", frappe.db.sql("select count(*) from `tabScheduled Job Type` where stopped=0")[0][0])
    print("DIAG-DB-SELESAI")
