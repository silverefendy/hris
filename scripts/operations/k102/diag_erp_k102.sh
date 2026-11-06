#!/usr/bin/env bash
# Diagnosa BACA-SAJA kondisi produksi sebelum migrasi K-102
SITE="${SITE_TARGET:-erp.ciptamebel.co.id}"
BENCH=/home/it/erp
cd "$BENCH" || exit 1

echo "DIAG|waktu_utc|$(date -u '+%F %T')  (WIB = UTC+7)"
echo "DIAG|site|$SITE"
echo "DIAG|hris_commit|$(git -C $BENCH/apps/hris log -1 --format='%h %s' 2>&1)"
echo "DIAG|hris_cabang|$(git -C $BENCH/apps/hris rev-parse --abbrev-ref HEAD 2>&1)"
echo "DIAG|hris_belum_push|$(git -C $BENCH/apps/hris rev-list --count origin/main..HEAD 2>&1)"
echo "DIAG|hris_perubahan_lokal|$(git -C $BENCH/apps/hris status --porcelain 2>&1 | wc -l)"
echo "DIAG|versi|$(bench version 2>&1 | tr '\n' ' ')"
echo "DIAG|disk|$(df -h / | awk 'NR==2{print "pakai "$3" sisa "$4" ("$5")"}')"
echo "DIAG|proses_bench|$(pgrep -fc 'bench start|honcho|frappe serve|frappe worker|frappe schedule' 2>/dev/null)"
echo "DIAG|cadangan_di_lan|$(ls /home/it/cadangan_k102 2>/dev/null | wc -l) berkas"

cat > /tmp/diag_k102_$$.py <<'PY'
import frappe
def p(k, v): print("DIAG|%s|%s" % (k, v))
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
p("tabel_HRIS_Payroll_Schedule", "ADA" if frappe.db.sql("show tables like 'tabHRIS Payroll Schedule'") else "belum ada")
p("role_HRIS", [x[0] for x in frappe.db.sql("select name from tabRole where name like 'HRIS%' order by name")])
p("module_HRIS", [x[0] for x in frappe.db.sql("select name from `tabModule Def` where app_name='hris' order by name")])
p("sesi_aktif_24j", frappe.db.sql("select count(distinct user) from tabSessions where lastupdate > now() - interval 1 day")[0][0])
p("user_enabled", frappe.db.sql("select count(*) from tabUser where enabled=1 and user_type='System User'")[0][0])
p("scheduled_job_aktif", frappe.db.sql("select count(*) from `tabScheduled Job Type` where stopped=0")[0][0])
PY
bench --site "$SITE" console < /tmp/diag_k102_$$.py 2>&1 | grep '^DIAG|'
rm -f /tmp/diag_k102_$$.py
echo "DIAG-SELESAI"
