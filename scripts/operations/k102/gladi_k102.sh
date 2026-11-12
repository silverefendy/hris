#!/bin/bash
# Gladi resik runbook K-102 di site uji.
# Pemakaian: bash gladi_k102.sh fase1   |   bash gladi_k102.sh fase2
set -uo pipefail

RB=/home/it/runbook_k102/runbook_k102.sh
BENCH=/home/it/erp
PROD="erp.ciptamebel.co.id"
UJI="hris-uji.local"
LOG_DIR=/home/it/runbook_k102
PENANDA="$LOG_DIR/gladi_berkas.path"
TAHAP="${1:-}"

GAGAL() { echo; echo "GAGAL di gladi: $*" >&2; exit 1; }
judul() { echo; echo "================ $* ================"; }
hitung_hris() {
  (cd "$BENCH" && bench --site "$UJI" mariadb -N -e "SELECT COUNT(*) FROM \`tabHRIS Employee\`;" 2>/dev/null | tail -n 1)
}

[ -f "$RB" ] || GAGAL "$RB tidak ditemukan"
cd "$BENCH" || GAGAL "folder bench tidak ada"

case "$TAHAP" in
fase1)
  judul "Langkah 1/5: cadangan produksi ($PROD)"
  bash "$RB" cadangan "$PROD" || GAGAL "langkah 1 (cadangan)"
  [ -f "$LOG_DIR/cadangan_terakhir_$PROD.path" ] || GAGAL "jalur cadangan tidak tercatat"
  BERKAS=$(cat "$LOG_DIR/cadangan_terakhir_$PROD.path")
  [ -f "$BERKAS" ] || GAGAL "berkas cadangan tidak ada: $BERKAS"
  echo "$BERKAS" > "$PENANDA"
  echo "Berkas gladi dikunci: $BERKAS"

  judul "Langkah 2/5: restore ke $UJI (akan diminta konfirmasi dan password root)"
  bash "$RB" restore "$UJI" "$BERKAS" || GAGAL "langkah 2 (restore)"
  N=$(hitung_hris)
  echo "HRIS Employee setelah restore: $N"
  [ "$N" = "0" ] || GAGAL "diharapkan 0 HRIS Employee setelah restore + migrate, dapat: $N"

  judul "Langkah 2b: salin Department dan aturan akar (K-136)"
  bash "$RB" department "$UJI" coba || GAGAL "langkah 2b (department coba)"
  bash "$RB" department "$UJI" salin || GAGAL "langkah 2b (department salin)"

  judul "Langkah 3/5: kondisi awal $UJI"
  bash "$RB" awal "$UJI" || GAGAL "langkah 3 (awal)"

  judul "Langkah 4/5: cek (dry_run + latih)"
  bash "$RB" cek "$UJI" || GAGAL "langkah 4 (cek)"

  judul "Langkah 5/5: jalankan migrasi (akan diminta konfirmasi)"
  bash "$RB" jalankan "$UJI" || GAGAL "langkah 5 (jalankan)"

  judul "FASE 1 SELESAI"
  echo "Sekarang lakukan LANGKAH 6 di browser (hris-uji.local):"
  echo "  buka 3 HRIS Employee acak; cek data benar dan Audit Trail bersih."
  echo "Lalu jalankan: bash $0 fase2"
  ;;

fase2)
  [ -f "$PENANDA" ] || GAGAL "belum ada fase1 (penanda $PENANDA tidak ada)"
  BERKAS=$(cat "$PENANDA")
  [ -f "$BERKAS" ] || GAGAL "berkas cadangan hilang: $BERKAS"

  judul "Sebelum rollback"
  SEBELUM=$(hitung_hris)
  echo "HRIS Employee sekarang: $SEBELUM (harus > 0 bila fase1 berhasil)"
  [ -n "$SEBELUM" ] && [ "$SEBELUM" != "0" ] || echo "(peringatan) jumlah tidak > 0; fase1 mungkin belum menulis data"

  judul "Langkah 7: restore berkas yang SAMA (latihan rollback)"
  bash "$RB" restore "$UJI" "$BERKAS" || GAGAL "langkah 7 (restore ulang)"

  SESUDAH=$(hitung_hris)
  echo
  echo "HRIS Employee: sebelum rollback=$SEBELUM, sesudah rollback=$SESUDAH"
  [ "$SESUDAH" = "0" ] || GAGAL "rollback tidak mengembalikan ke 0 (dapat $SESUDAH)"

  judul "GLADI RESIK LULUS"
  echo "Bukti: migrasi menulis $SEBELUM HRIS Employee, restore mengembalikannya ke 0."
  echo "Pemulihan terbukti berfungsi. Kirim keluaran dan log di $LOG_DIR."
  ;;

*)
  echo "Pemakaian: bash $0 fase1 | fase2"
  exit 1
  ;;
esac
