#!/usr/bin/env bash
# Menjalankan diag_db_k102.py lewat bench execute (baca-saja)
SITE="${SITE_TARGET:-erp.ciptamebel.co.id}"
cd /home/it/erp || exit 1
echo "DIAG|site|$SITE"
bench --site "$SITE" execute "(__import__('sys').path.insert(0, '/home/it/runbook_k102'), __import__('diag_db_k102').jalankan())" 2>&1
