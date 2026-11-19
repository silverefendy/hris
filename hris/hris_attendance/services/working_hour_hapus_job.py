"""K-6b tahap 2: hapus HRIS Working Hour per batch (background job).

Pengaman berlapis:
- saklar site hris_hapus_wh_aktif (bawaan mati)
- role System Manager / HRIS Direksi, dicek di server
- validasi ulang di server: jumlah yang dikonfirmasi harus sama, semua peringatan dikonfirmasi
- blokir (slip Final / Period Final) dicek ulang di setiap batch
- satu proses pada satu waktu

Memakai frappe.db.delete (tanpa salinan Deleted Document). Version dan Comment dokumen
ikut dibersihkan per batch. Catatan audit: HRIS Hapus WH Log.
"""

import frappe
from frappe import _
from frappe.utils import cint, get_datetime, now_datetime

from hris.hris_attendance.services import working_hour_hapus as svc

DT = svc.WH
LOG = "HRIS Hapus WH Log"
SAKLAR = "hris_hapus_wh_aktif"
BATCH = 1000
STATUS_KEY = "hris_wh_hapus_status"
STATUS_TTL = 3600
STALE_SECONDS = 1800


def _cache():
    cache = frappe.cache
    return cache() if callable(cache) else cache


def _set_status(data):
    try:
        data = dict(data, at=str(now_datetime()))
        _cache().set_value(STATUS_KEY, data, expires_in_sec=STATUS_TTL)
    except Exception:
        frappe.log_error(title="HRIS Hapus WH: gagal menyimpan status")


def _cek_saklar():
    if not cint(frappe.conf.get(SAKLAR)):
        frappe.throw(_("Hapus Working Hour belum diaktifkan di situs ini (saklar {0}).").format(SAKLAR))


def _log_buat(flt, total, konfirmasi, user):
    """Buat catatan audit Antre. Kembalikan nama, atau None bila gagal (tidak melempar)."""
    try:
        doc = frappe.get_doc(
            {
                "doctype": LOG,
                "status": "Antre",
                "requested_by": user,
                "date_from": flt["dari_tanggal"],
                "date_to": flt["sampai_tanggal"],
                "karyawan_filter": ", ".join(flt["karyawan"]),
                "status_filter": ", ".join(flt["status"]),
                "tanpa_gaji": flt["tanpa_gaji"],
                "total_cocok": total,
                "peringatan_dikonfirmasi": ", ".join(konfirmasi),
            }
        ).insert(ignore_permissions=True)
        frappe.db.commit()
        return doc.name
    except Exception:
        frappe.log_error(title="HRIS Hapus WH Log: gagal membuat catatan")
        return None


def _log_update(nama, nilai):
    if not nama:
        return
    try:
        frappe.db.set_value(LOG, nama, nilai, update_modified=True)
        frappe.db.commit()
    except Exception:
        frappe.log_error(title="HRIS Hapus WH Log: gagal memperbarui {0}".format(nama))


@frappe.whitelist()
def fitur_status():
    """Untuk UI: apakah fitur aktif di situs ini dan apakah pengguna berhak."""
    return {
        "aktif": bool(cint(frappe.conf.get(SAKLAR))),
        "berhak": bool(svc.HAK_HAPUS & set(frappe.get_roles())),
    }


@frappe.whitelist()
def enqueue_delete(date_from, date_to, karyawan=None, status=None, tanpa_gaji=0, confirm_total=None, konfirmasi=None):
    """Validasi ulang di server, lalu antrekan job hapus."""
    svc._check_access()
    _cek_saklar()
    where, p, flt = svc._siapkan(date_from, date_to, karyawan, status, tanpa_gaji)
    info = svc._hitung(where, p)

    if not info["total"]:
        return {"queued": False, "message": _("Tidak ada Working Hour yang cocok dengan filter.")}
    if info["blokir"]["jumlah"]:
        return {
            "queued": False,
            "message": _(
                "Ditolak: {0} dokumen berada di bawah slip atau periode Final. "
                "Buka kembali atau hapus slip terkait lebih dulu."
            ).format(info["blokir"]["jumlah"]),
        }
    if cint(confirm_total) != info["total"]:
        frappe.throw(
            _("Jumlah konfirmasi ({0}) tidak sama dengan jumlah dokumen yang akan dihapus ({1}).").format(
                cint(confirm_total), info["total"]
            )
        )
    wajib = {x["kode"] for x in info["peringatan"] if x.get("butuh_konfirmasi")}
    kurang = sorted(wajib - set(svc._daftar(konfirmasi)))
    if kurang:
        frappe.throw(_("Peringatan belum dikonfirmasi: {0}").format(", ".join(kurang)))

    cur = _cache().get_value(STATUS_KEY) or {}
    if cur.get("status") in ("Antre", "Berjalan") and cur.get("at"):
        umur = (now_datetime() - get_datetime(cur["at"])).total_seconds()
        if umur < STALE_SECONDS:
            return {"queued": False, "message": _("Masih ada penghapusan Working Hour yang berjalan.")}

    _set_status({"status": "Antre", "user": frappe.session.user, "total": info["total"]})
    log_name = _log_buat(flt, info["total"], sorted(wajib), frappe.session.user)
    frappe.enqueue(
        "hris.hris_attendance.services.working_hour_hapus_job.run_delete_job",
        queue="long",
        timeout=3600,
        date_from=flt["dari_tanggal"],
        date_to=flt["sampai_tanggal"],
        karyawan=flt["karyawan"],
        status=flt["status"],
        tanpa_gaji=flt["tanpa_gaji"],
        notify_user=frappe.session.user,
        log_name=log_name,
    )
    return {"queued": True, "total": info["total"], "log": log_name}


def run_delete_job(date_from, date_to, karyawan=None, status=None, tanpa_gaji=0, notify_user=None, log_name=None):
    _log_update(log_name, {"status": "Berjalan", "started_at": now_datetime()})
    terhapus = 0
    try:
        where, p, flt = svc._siapkan(date_from, date_to, karyawan, status, tanpa_gaji)
        total = svc._angka("select count(*) from `tabHRIS Working Hour` wh where " + where, p)
        _set_status({"status": "Berjalan", "user": notify_user, "total": total, "terhapus": 0})

        batas = total // BATCH + 5
        putaran = 0
        while True:
            putaran += 1
            if putaran > batas:
                raise frappe.ValidationError(
                    "Penghapusan dihentikan: jumlah putaran melebihi perkiraan "
                    "(kemungkinan ada dokumen baru yang muncul selama proses)."
                )
            names = [
                r[0]
                for r in frappe.db.sql(
                    "select wh.name from `tabHRIS Working Hour` wh where " + where
                    + " order by wh.work_date, wh.name limit " + str(BATCH),
                    p,
                )
            ]
            if not names:
                break

            terblokir = svc._angka(
                "select count(*) from `tabHRIS Working Hour` wh where wh.name in %(n)s and " + svc._TERBLOKIR,
                {"n": tuple(names)},
            )
            if terblokir:
                raise frappe.ValidationError(
                    "Dihentikan: {0} dokumen kini berada di bawah slip atau periode Final. "
                    "Sudah terhapus sebelumnya: {1}.".format(terblokir, terhapus)
                )

            frappe.db.delete(DT, {"name": ["in", names]})
            frappe.db.delete("Version", {"ref_doctype": DT, "docname": ["in", names]})
            frappe.db.delete("Comment", {"reference_doctype": DT, "reference_name": ["in", names]})
            frappe.db.commit()
            terhapus += len(names)
            _set_status({"status": "Berjalan", "user": notify_user, "total": total, "terhapus": terhapus})
            _log_update(log_name, {"jumlah_dihapus": terhapus})

        _log_update(log_name, {"status": "Selesai", "finished_at": now_datetime(), "jumlah_dihapus": terhapus})
        _set_status(
            {
                "status": "Selesai",
                "user": notify_user,
                "total": total,
                "terhapus": terhapus,
                "dari_tanggal": flt["dari_tanggal"],
                "sampai_tanggal": flt["sampai_tanggal"],
            }
        )
        return terhapus
    except Exception as exc:
        frappe.db.rollback()
        _set_status({"status": "Gagal", "user": notify_user, "terhapus": terhapus, "message": str(exc)[:500]})
        _log_update(
            log_name,
            {
                "status": "Gagal",
                "finished_at": now_datetime(),
                "jumlah_dihapus": terhapus,
                "pesan_error": str(exc)[:1000],
            },
        )
        frappe.log_error(title="HRIS Hapus WH gagal")
        raise


@frappe.whitelist()
def delete_status():
    """Status penghapusan terakhir (Antre, Berjalan, Selesai, Gagal); kosong bila lewat 1 jam."""
    svc._check_access()
    st = _cache().get_value(STATUS_KEY) or {}
    if st.get("at"):
        st["detik"] = int((now_datetime() - get_datetime(st["at"])).total_seconds())
    return st
