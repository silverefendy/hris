#!/bin/bash
# Alat produksi K-102. Membungkus runbook_k102.sh.
# Pemakaian: bash produksi_k102.sh cadangan | siap | mulai | pulihkan
# Site target bisa diganti untuk gladi: SITE_TARGET=hris-uji.local bash produksi_k102.sh siap
set -uo pipefail

BENCH=/home/it/erp
LOG_DIR=/home/it/runbook_k102
RB="$LOG_DIR/runbook_k102.sh"
PROD="${SITE_TARGET:-erp.ciptamebel.co.id}"
STATE="$LOG_DIR/produksi_kondisi_${PROD}.txt"
PERINTAH="${1:-}"

GAGAL() { echo; echo "GAGAL: $*" >&2; exit 1; }
judul() { echo; echo "================ $* ================"; }
baris() { printf '%-48s %s\n' "$1" "$2"; }
tanya() { local j; read -r -p "$1 (ketik 'ya'): " j; [ "$j" = "ya" ]; }
konfirmasi() {
  local j; read -r -p "Ketik persis '$1' untuk lanjut: " j
  [ "$j" = "$1" ] || { echo "Dibatalkan."; exit 1; }
}
kondisi_employee() {
  (cd "$BENCH" && bench --site "$PROD" mariadb -N -e "SELECT COUNT(*), MAX(modified) FROM tabEmployee;" 2>/dev/null | tail -n 1)
}
henti() {
  echo
  echo "BERHENTI di tahap: $1. Maintenance MASIH ON."
  echo "Jangan lanjut. Kirim keluaran dan log di $LOG_DIR."
  echo "Bila tahap ini 'jalankan' dan tabel Employee BERBEDA atau hasil tidak jelas:"
  echo "  bash $0 pulihkan"
  exit 1
}

[ -f "$RB" ] || GAGAL "$RB tidak ditemukan"
[ -d "$BENCH/sites/$PROD" ] || GAGAL "site $PROD tidak ada di $BENCH/sites"

cmd_cadangan() {
  local s berkas
  s=$(kondisi_employee)
  [ -n "$s" ] || GAGAL "tidak bisa membaca tabEmployee di $PROD"
  bash "$RB" cadangan "$PROD" || GAGAL "cadangan"
  berkas=$(cat "$LOG_DIR/cadangan_terakhir_$PROD.path" 2>/dev/null)
  [ -f "$berkas" ] || GAGAL "berkas cadangan tidak ditemukan"
  printf '%s\n%s\n' "$berkas" "$s" > "$STATE"
  echo
  echo "Kondisi Employee saat cadangan: $s"
  echo "Berkas: $berkas"
  echo "Langkah berikut: salin ke mesin lain, cocokkan sha256, lalu: bash $0 siap"
}

cmd_siap() {
  local ok=1 berkas tercatat sekarang cabang belum avail sha
  judul "Pemeriksaan kesiapan: $PROD"
  baris "Waktu sekarang" "$(TZ=Asia/Jakarta date '+%a %d-%m-%Y %H:%M WIB')"
  [ -f "$STATE" ] || { echo "GAGAL: belum ada cadangan tercatat. Jalankan: cadangan"; return 1; }
  berkas=$(sed -n 1p "$STATE"); tercatat=$(sed -n 2p "$STATE")

  cabang=$(cd "$BENCH/apps/hris" && git rev-parse --abbrev-ref HEAD)
  if [ "$cabang" = "main" ]; then baris "hris di cabang main" OK; else baris "hris di cabang main" "GAGAL ($cabang)"; ok=0; fi

  belum=$(cd "$BENCH/apps/hris" && git rev-list --count origin/main..HEAD 2>/dev/null || echo "?")
  if [ "$belum" = "0" ]; then baris "semua commit hris sudah di-push" OK; else baris "semua commit hris sudah di-push" "GAGAL/tidak pasti ($belum)"; ok=0; fi
  baris "commit hris" "$(cd "$BENCH/apps/hris" && git rev-parse --short HEAD)"

  if [ -f "$berkas" ]; then baris "berkas cadangan ada" OK; else baris "berkas cadangan ada" "GAGAL"; ok=0; fi
  sha="$LOG_DIR/sha256_$(basename "$berkas").txt"
  if [ -f "$sha" ] && sha256sum -c --status "$sha" 2>/dev/null; then baris "sha256 cadangan cocok" OK; else baris "sha256 cadangan cocok" "GAGAL"; ok=0; fi
  if find "$berkas" -mmin -360 2>/dev/null | grep -q .; then baris "cadangan berumur < 6 jam" OK; else baris "cadangan berumur < 6 jam" "GAGAL (buat baru)"; ok=0; fi

  sekarang=$(kondisi_employee)
  if [ "$sekarang" = "$tercatat" ]; then baris "Employee sama dengan saat cadangan" OK
  else baris "Employee sama dengan saat cadangan" "GAGAL (dulu: $tercatat | kini: $sekarang)"; ok=0; fi

  avail=$(df -BG --output=avail "$BENCH" | tail -n 1 | tr -dc '0-9')
  if [ "${avail:-0}" -ge 5 ]; then baris "ruang disk >= 5G" "OK (${avail}G)"; else baris "ruang disk >= 5G" "GAGAL (${avail}G)"; ok=0; fi

  echo
  if [ "$ok" = "1" ]; then echo "SIAP: semua pemeriksaan lulus."; return 0; fi
  echo "TIDAK SIAP: perbaiki yang GAGAL lalu ulangi."; return 1
}

cmd_mulai() {
  cmd_siap || GAGAL "pemeriksaan kesiapan tidak lulus"
  echo
  tanya "Cadangan sudah disalin ke mesin LAIN dan sha256-nya cocok?" || { echo "Dibatalkan."; exit 1; }
  tanya "Sekarang di luar jam kerja HRD dan HRD sudah diberi tahu?" || { echo "Dibatalkan."; exit 1; }
  if [ "$PROD" != "hris-uji.local" ]; then echo "!!! $PROD BUKAN site uji. Ini produksi. !!!"; fi
  konfirmasi "MULAI PRODUKSI $PROD"

  judul "1/6 Maintenance ON"
  bash "$RB" maintenance "$PROD" on || GAGAL "maintenance on"

  judul "2/6 Skema (migrate)"
  bash "$RB" skema "$PROD" || henti "skema"

  judul "3/6 Restart"
  echo "Restart $PROD sesuai prosedur Anda (skrip tidak tahu setup produksi)."
  read -r -p "Tekan Enter setelah situs di-restart dan hidup: " _

  judul "4/6 Kondisi awal dan cek"
  bash "$RB" awal "$PROD" || henti "awal"
  bash "$RB" cek "$PROD" || henti "cek"

  judul "5/6 Jalankan migrasi"
  bash "$RB" jalankan "$PROD" || henti "jalankan"

  judul "6/6 Maintenance OFF"
  tanya "Semua LULUS. Matikan maintenance sekarang?" || { echo "Maintenance tetap ON. Matikan nanti: bash $RB maintenance $PROD off"; exit 0; }
  bash "$RB" maintenance "$PROD" off || GAGAL "maintenance off"

  judul "SELESAI"
  echo "Uji asap: ubah telepon satu karyawan di HRIS Employee, Simpan, cek di Employee."
  echo "Lalu: bash $RB awal $PROD (bandingkan dengan kondisi awal)."
}

cmd_pulihkan() {
  local berkas sha
  [ -f "$STATE" ] || GAGAL "tidak ada catatan cadangan ($STATE)"
  berkas=$(sed -n 1p "$STATE")
  [ -f "$berkas" ] || GAGAL "berkas cadangan tidak ada: $berkas"
  sha="$LOG_DIR/sha256_$(basename "$berkas").txt"
  sha256sum -c "$sha" || GAGAL "sha256 cadangan TIDAK cocok; jangan dipulihkan"
  echo "Pemulihan akan MENIMPA database $PROD dengan:"
  echo "  $berkas"
  bash "$RB" restore "$PROD" "$berkas" || GAGAL "restore"
  echo
  echo "Skema database kini kembali ke sebelum migrate, sedangkan kode hris di disk sudah versi baru."
  if tanya "Jalankan migrate agar skema cocok dengan kode (seperti di gladi; HRIS Employee kosong)?"; then
    bash "$RB" skema "$PROD" || GAGAL "skema setelah restore"
  fi
  echo
  echo "Langkah akhir manual: restart situs, matikan maintenance bila masih ON:"
  echo "  bash $RB maintenance $PROD off"
  echo "  bash $RB awal $PROD"
}

case "$PERINTAH" in
  cadangan) cmd_cadangan ;;
  siap) cmd_siap ;;
  mulai) cmd_mulai ;;
  pulihkan) cmd_pulihkan ;;
  *) echo "Pemakaian: bash $0 cadangan | siap | mulai | pulihkan"; exit 1 ;;
esac
