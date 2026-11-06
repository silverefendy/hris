#!/bin/bash
# Alat runbook K-102 (migrasi Employee -> HRIS Employee).
# Pemakaian: bash runbook_k102.sh <perintah> <site> [argumen]
set -uo pipefail

BENCH=/home/it/erp
SITE_UJI="hris-uji.local"
LOG_DIR=/home/it/runbook_k102
SALIN_DIR=/home/it/cadangan_k102
MODUL="hris.hris_employee_data.services.migrasi_employee"
mkdir -p "$LOG_DIR" "$SALIN_DIR"

PERINTAH="${1:-}"
SITE="${2:-}"
ARG3="${3:-}"
WAKTU=$(date +%Y%m%d_%H%M%S)
QUERY_EMPLOYEE="SELECT COUNT(*) jumlah, MAX(modified) terakhir_diubah FROM tabEmployee;"

pakai() {
  cat <<TXT
Pemakaian: bash runbook_k102.sh <perintah> <site> [argumen]

  awal        <site>             catat kondisi awal (hanya baca)
  cadangan    <site>             backup lalu salin ke $SALIN_DIR
  restore     <site> <berkas>    pulihkan dari *-database.sql.gz (MENIMPA database)
  skema       <site>             bench migrate (minta konfirmasi)
  maintenance <site> on|off      mode maintenance
  cek         <site>             dry_run + latih (tidak meninggalkan data)
  jalankan    <site>             migrasi + verifikasi (MENULIS data, minta konfirmasi)
TXT
}

GAGAL() { echo "GAGAL: $*" >&2; exit 1; }

perlu_site() {
  [ -n "$SITE" ] || { pakai; exit 1; }
  [ -d "$BENCH/sites/$SITE" ] || GAGAL "site '$SITE' tidak ada di $BENCH/sites"
}

b() { (cd "$BENCH" && bench --site "$SITE" "$@"); }
sql() { b mariadb -e "$1"; }

konfirmasi() {
  local jawab
  read -r -p "Ketik persis '$1' untuk lanjut: " jawab
  [ "$jawab" = "$1" ] || { echo "Dibatalkan."; exit 1; }
}

peringatan_produksi() {
  if [ "$SITE" != "$SITE_UJI" ]; then
    echo "!!! $SITE BUKAN site uji. Ini produksi. !!!"
  fi
}

cmd_awal() {
  perlu_site
  local f="$LOG_DIR/awal_${SITE}_$WAKTU.txt"
  {
    echo "Waktu : $(date '+%Y-%m-%d %H:%M:%S %Z')"
    echo "Site  : $SITE"
    echo "--- Employee"
    sql "$QUERY_EMPLOYEE"
    echo "--- HRIS Employee (bila tabel sudah ada)"
    sql "SELECT COUNT(*) jumlah FROM \`tabHRIS Employee\`;" 2>&1 | tail -n 3
    echo "--- Versi"
    (cd "$BENCH" && bench version)
    echo "--- Disk"
    df -h "$BENCH" | tail -n 2
  } | tee "$f"
  echo "Log: $f"
}

cmd_cadangan() {
  perlu_site
  echo "Ruang disk:"; df -h "$BENCH" | tail -n 2
  b backup --with-files || GAGAL "backup"
  local dir="$BENCH/sites/$SITE/private/backups" terbaru awalan nama
  terbaru=$(ls -1t "$dir"/*-database.sql.gz 2>/dev/null | head -n 1)
  [ -n "$terbaru" ] || GAGAL "berkas cadangan tidak ditemukan di $dir"
  awalan="${terbaru%-database.sql.gz}"
  nama=$(basename "$terbaru")
  for f in "$awalan"-*; do cp -p "$f" "$SALIN_DIR/"; done
  echo "Disalin ke $SALIN_DIR:"
  ls -lh "$SALIN_DIR/$(basename "$awalan")"-*
  sha256sum "$SALIN_DIR/$nama" | tee "$LOG_DIR/sha256_$nama.txt"
  echo "$SALIN_DIR/$nama" > "$LOG_DIR/cadangan_terakhir_$SITE.path"
  echo
  echo "Berkas database untuk 'restore':"
  echo "  $SALIN_DIR/$nama"
  echo "CATATAN: salin juga ke mesin LAIN (mis. scp). Salinan di server yang sama"
  echo "tidak melindungi dari kerusakan disk."
}

cmd_restore() {
  perlu_site
  local berkas="$ARG3"
  [ -n "$berkas" ] && [ -f "$berkas" ] || GAGAL "sebutkan berkas yang ada: restore <site> <berkas-database.sql.gz>"
  case "$berkas" in
    *-database.sql.gz) ;;
    *) GAGAL "berkas harus berakhiran -database.sql.gz" ;;
  esac

  if [ "$SITE" = "$SITE_UJI" ]; then
    echo "Akan MENIMPA seluruh database $SITE (site uji) dengan:"
    echo "  $berkas"
    konfirmasi "RESET $SITE"
  else
    peringatan_produksi
    echo "Akan MENIMPA database produksi $SITE dengan:"
    echo "  $berkas"
    echo "Sebelumnya skrip membuat cadangan pengaman kondisi sekarang."
    konfirmasi "PULIHKAN $SITE DARI CADANGAN"
    b backup --with-files || GAGAL "cadangan pengaman gagal, restore dibatalkan"
    echo "Cadangan pengaman (terbaru):"
    ls -1t "$BENCH/sites/$SITE/private/backups"/*-database.sql.gz | head -n 1
  fi

  local pw="" args=()
  read -r -s -p "Password root MariaDB (Enter bila tidak diminta): " pw; echo
  if [ -n "$pw" ]; then args=(--db-root-username root --db-root-password "$pw"); fi
  b restore "$berkas" ${args[@]+"${args[@]}"} \
    || GAGAL "restore. Bila karena akses ditolak, jalankan ulang dan isi password root."
  pw=""

  if [ "$SITE" = "$SITE_UJI" ]; then
    echo "--- Pasca-restore site uji ---"
    b set-config mute_emails 1 || echo "(peringatan) mute_emails gagal diset"
    b migrate || GAGAL "migrate setelah restore"
    b clear-cache
    b scheduler disable 2>&1 || echo "(peringatan) 'scheduler disable' tidak berhasil; cek dokumentasi Frappe untuk versi Anda"
    echo "Pemeriksaan:"
    sql "SELECT COUNT(*) jumlah FROM \`tabHRIS Employee\`;"
    sql "SHOW COLUMNS FROM \`tabHRIS Employee\` WHERE Field IN ('data_status','data_note');"
    echo "Password Administrator site uji kini sama dengan produksi. Reset bila perlu:"
    echo "  bench --site $SITE set-admin-password '<PASSWORD-BARU>'"
  else
    echo "Restore produksi selesai. Matikan maintenance dan restart sesuai prosedur Anda,"
    echo "lalu jalankan: bash runbook_k102.sh awal $SITE"
  fi
}

cmd_skema() {
  perlu_site
  echo "Akan menjalankan: bench --site $SITE migrate"
  peringatan_produksi
  konfirmasi "MIGRATE $SITE"
  b migrate 2>&1 | tee "$LOG_DIR/skema_${SITE}_$WAKTU.txt"
  [ "${PIPESTATUS[0]}" -eq 0 ] || GAGAL "migrate (lihat log di $LOG_DIR)"
  b clear-cache
  sql "SELECT COUNT(*) jumlah FROM \`tabHRIS Employee\`;"
}

cmd_maintenance() {
  perlu_site
  case "$ARG3" in
    on|off) ;;
    *) GAGAL "gunakan: maintenance <site> on|off" ;;
  esac
  b set-maintenance-mode "$ARG3"
  echo "Maintenance $ARG3 untuk $SITE"
}

cmd_cek() {
  perlu_site
  local log="$LOG_DIR/cek_${SITE}_$WAKTU.txt" angka a z
  {
    echo "== dry_run =="
    b execute "$MODUL.dry_run"
    echo "== latih =="
    b execute "$MODUL.latih" --kwargs "{'konfirmasi': '$SITE'}"
  } 2>&1 | tee "$log"
  grep -q "^Hasil: SIAP" "$log" || GAGAL "dry_run tidak SIAP (lihat $log)"
  grep -q "Hasil latihan: SAMA" "$log" || GAGAL "latihan tidak SAMA (lihat $log)"
  angka=$(grep "sebelum latihan" "$log" | grep -o '[0-9]\+')
  a=$(echo "$angka" | sed -n 1p); z=$(echo "$angka" | sed -n 2p)
  { [ -n "$a" ] && [ "$a" = "$z" ]; } || GAGAL "jumlah HRIS Employee berubah setelah rollback ($a vs $z)"
  echo
  echo "CEK LULUS: dry_run SIAP, latihan SAMA, rollback bersih. Log: $log"
}

cmd_jalankan() {
  perlu_site
  local log="$LOG_DIR/jalankan_${SITE}_$WAKTU.txt" sebelum sesudah
  echo "Akan MENULIS data: membuat HRIS Employee dari Employee di $SITE."
  peringatan_produksi
  echo "Syarat: cadangan sudah dibuat dan 'cek' sudah lulus. Sebaiknya di luar jam kerja HRD."
  konfirmasi "MIGRASI $SITE"

  sebelum=$(sql "$QUERY_EMPLOYEE")
  {
    echo "== Employee sebelum =="; echo "$sebelum"
    echo "== migrasi =="
    b execute "$MODUL.migrasi" --kwargs "{'konfirmasi': '$SITE'}"
  } 2>&1 | tee "$log"
  grep -qx "selesai" "$log" || GAGAL "migrasi tidak selesai (lihat $log). Bila 'gagal', seluruhnya sudah di-rollback."

  {
    echo "== verifikasi (baca) =="
    b execute "$MODUL.verifikasi"
    echo "== verifikasi (terapkan Berhasil) =="
    b execute "$MODUL.verifikasi" --kwargs "{'terapkan': 1}"
    echo "== status sinkron =="
    sql "SELECT sync_status, COUNT(*) n FROM \`tabHRIS Employee\` GROUP BY sync_status;"
  } 2>&1 | tee -a "$log"

  sesudah=$(sql "$QUERY_EMPLOYEE")
  {
    echo "== Employee sesudah =="; echo "$sesudah"
    if [ "$sebelum" = "$sesudah" ]; then
      echo "SAMA: tabel Employee tidak berubah"
    else
      echo "BERBEDA: tabel Employee berubah! Pertimbangkan restore."
    fi
  } | tee -a "$log"

  [ "$(grep -c '^Hasil: SAMA' "$log")" -ge 2 ] || GAGAL "verifikasi tidak SAMA (lihat $log)"
  [ "$sebelum" = "$sesudah" ] || GAGAL "tabel Employee berubah (lihat $log)"
  echo
  echo "MIGRASI LULUS. Log: $log"
}

case "$PERINTAH" in
  awal) cmd_awal ;;
  cadangan) cmd_cadangan ;;
  restore) cmd_restore ;;
  skema) cmd_skema ;;
  maintenance) cmd_maintenance ;;
  cek) cmd_cek ;;
  jalankan) cmd_jalankan ;;
  *) pakai; exit 1 ;;
esac
