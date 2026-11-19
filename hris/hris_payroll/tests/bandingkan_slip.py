"""Snapshot dan perbandingan slip satu periode. HANYA untuk site uji.
  bench --site hris-uji.local execute hris.hris_payroll.tests.bandingkan_slip.buat --kwargs '{"periode": "NAMA", "label": "sebelum"}'
  bench --site hris-uji.local execute hris.hris_payroll.tests.bandingkan_slip.banding --kwargs '{"a": "sebelum", "b": "sesudah"}'
"""
import json
import os
from collections import Counter

import frappe

from hris.hris_payroll.services import payroll_slip as ps

PERIODE = "HRIS Payroll Period"
FOLDER = os.path.expanduser("~/backup_hris")
ABAIKAN = {
    "name", "owner", "creation", "modified", "modified_by", "docstatus", "idx", "doctype",
    "parent", "parentfield", "parenttype", "calculated_on", "calculated_by",
}


def _rapikan(nilai):
    if isinstance(nilai, dict):
        return {k: _rapikan(v) for k, v in nilai.items() if k not in ABAIKAN and not str(k).startswith("__")}
    if isinstance(nilai, (list, tuple)):
        return [_rapikan(v) for v in nilai]
    if nilai is None or isinstance(nilai, (int, float, str)):
        return nilai
    return str(nilai)


def _berkas(label):
    return os.path.join(FOLDER, "snap_slip_%s.json" % label)


def buat(periode, label):
    p = frappe.get_doc(PERIODE, periode)
    if p.status == "Final":
        print("Periode %s berstatus Final (slip terkunci). Pilih periode lain." % periode)
        return
    daftar = frappe.get_all("HRIS Employee", filters={"company": p.company, "status": "Aktif"}, pluck="name", order_by="name")
    print("Periode %s | %s s/d %s | status %s | karyawan Aktif: %d" % (
        periode, p.period_start, p.period_end, p.status, len(daftar)))
    hitung, alasan = {}, {}
    for he in daftar:
        frappe.db.savepoint("bandingkan")
        try:
            jenis, info = ps.proses_karyawan(p, he)
        except Exception as exc:
            frappe.db.rollback(save_point="bandingkan")
            jenis, info = "galat", str(exc)
        hitung[jenis] = hitung.get(jenis, 0) + 1
        if jenis not in ("dibuat", "diperbarui"):
            k = str(info)[:110]
            alasan[k] = alasan.get(k, 0) + 1
    frappe.db.commit()

    data = {}
    for nama in frappe.get_all(ps.SLIP, filters={"payroll_period": p.name}, pluck="name"):
        d = frappe.get_doc(ps.SLIP, nama)
        data[d.employee] = _rapikan(d.as_dict())
    os.makedirs(FOLDER, exist_ok=True)
    with open(_berkas(label), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, sort_keys=True, indent=1, default=str)
    print("\nHasil proses:", hitung)
    for k, n in sorted(alasan.items(), key=lambda x: -x[1])[:10]:
        print("  %4d x %s" % (n, k))
    print("\nSlip tersimpan di snapshot: %d" % len(data))
    print("Berkas:", _berkas(label))


def _muat(label):
    with open(_berkas(label), encoding="utf-8") as f:
        return json.load(f)


def banding(a, b):
    A, B = _muat(a), _muat(b)
    beda_n, per_tipe = 0, Counter()
    for emp in sorted(set(A) | set(B)):
        if emp not in A or emp not in B:
            print("%s: hanya ada di %s" % (emp, b if emp in B else a))
            beda_n += 1
            continue
        sa, sb = A[emp], B[emp]
        field = {
            k: (sa.get(k), sb.get(k))
            for k in set(sa) | set(sb)
            if k != "components" and sa.get(k) != sb.get(k)
        }
        ca = Counter(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in sa.get("components", []))
        cb = Counter(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in sb.get("components", []))
        hanya_a, hanya_b = ca - cb, cb - ca
        if not (field or hanya_a or hanya_b):
            continue
        beda_n += 1
        per_tipe[sa.get("pay_type", "?")] += 1
        if beda_n <= 30:
            print("\n== %s (%s, %s) ==" % (emp, sa.get("employee_name"), sa.get("pay_type")))
            for k, (x, y) in sorted(field.items()):
                print("  %s: %s  ->  %s" % (k, str(x)[:200], str(y)[:200]))
            for r in hanya_a:
                print("  - komponen (%s): %s" % (a, r[:230]))
            for r in hanya_b:
                print("  + komponen (%s): %s" % (b, r[:230]))
    print("\nTotal slip dibandingkan: %d (A=%d, B=%d)" % (len(set(A) | set(B)), len(A), len(B)))
    print("Slip yang berbeda: %d %s" % (beda_n, dict(per_tipe)))
    if beda_n > 30:
        print("(detail hanya 30 pertama)")
