#!/bin/bash
# Cek pasca-migrasi K-102. HANYA MEMBACA. Pemakaian: bash cek_pasca.sh <site>
set -uo pipefail
BENCH=/home/it/erp
SITE="${1:-}"
[ -n "$SITE" ] && [ -d "$BENCH/sites/$SITE" ] || { echo "Pemakaian: bash $0 <site>"; exit 1; }
MASALAH=0
sql() { (cd "$BENCH" && bench --site "$SITE" mariadb -N -e "$1" 2>/dev/null | tail -n 1); }
baris() { printf '%-55s %s\n' "$1" "$2"; }
periksa() {
  if [ "$2" = "$3" ]; then baris "$1" "OK ($2)"; else baris "$1" "PERLU DICEK (dapat: ${2:-kosong}, harap: $3)"; MASALAH=1; fi
}
echo "== Cek pasca: $SITE =="
for dt in "HRIS Employee" "HRIS Employee Pay" "HRIS Employee Component" "HRIS Component Assignment" \
          "HRIS Pay Component" "HRIS Payroll Slip BPJS" "HRIS BPJS Rate" "HRIS PPh21 Settings" "HRIS PPh21 TER Rate"; do
  periksa "DocType ada: $dt" "$(sql "SELECT COUNT(*) FROM tabDocType WHERE name='$dt';")" "1"
done
for r in "HRIS HR Admin" "HRIS Employee Admin" "HRIS Payroll Admin" "HRIS Payroll Manager" "HRIS Direksi"; do
  periksa "Role ada: $r" "$(sql "SELECT COUNT(*) FROM tabRole WHERE name='$r';")" "1"
done
for dt in "HRIS PPh21 Pasal17 Rate" "HRIS Payroll Period" "HRIS Payroll Slip" "HRIS Department" "HRIS Department Rule"; do
  periksa "DocType ada: $dt" "$(sql "SELECT COUNT(*) FROM tabDocType WHERE name='$dt';")" "1"
done
for dt in "HRIS PPh21 TER Rate" "HRIS PPh21 Pasal17 Rate"; do
  periksa "allow_import menyala: $dt" "$(sql "SELECT allow_import FROM tabDocType WHERE name='$dt';")" "1"
  periksa "Izin Import System Manager ada: $dt" "$(sql "SELECT IF(COUNT(*)>=1,1,0) FROM tabDocPerm WHERE parent='$dt' AND role='System Manager' AND \`import\`=1 AND permlevel=0;")" "1"
  periksa "Izin Import peran lain (harus 0): $dt" "$(sql "SELECT COUNT(*) FROM tabDocPerm WHERE parent='$dt' AND role<>'System Manager' AND \`import\`=1;")" "0"
done
periksa "Komponen katalog aktif (harus 0)" "$(sql "SELECT COUNT(*) FROM \`tabHRIS Pay Component\` WHERE is_active=1;")" "0"
periksa "PPh21 Settings Aktif (harus 0)" "$(sql "SELECT IFNULL(MAX(value),'0') FROM tabSingles WHERE doctype='HRIS PPh21 Settings' AND field='enabled';")" "0"
baris "INFO tabEmployee" "$(sql "SELECT COUNT(*) FROM tabEmployee;")"
baris "INFO HRIS Employee" "$(sql "SELECT COUNT(*) FROM \`tabHRIS Employee\`;")"
baris "INFO HRIS PPh21 TER Rate" "$(sql "SELECT COUNT(*) FROM \`tabHRIS PPh21 TER Rate\`;")"
for app in hris wms; do
  d="$BENCH/apps/$app"
  baris "INFO app $app" "$(cd "$d" && git rev-parse --abbrev-ref HEAD) $(cd "$d" && git rev-parse --short HEAD)"
  periksa "app $app: pohon kerja bersih" "$(cd "$d" && git status --porcelain | wc -l)" "0"
done
echo
if [ "$MASALAH" = "0" ]; then echo "SEMUA OK."; else echo "ADA YANG PERLU DICEK."; fi
exit "$MASALAH"
