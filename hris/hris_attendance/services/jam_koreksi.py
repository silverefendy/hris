"""Jam koreksi HRD (C4): jam masuk atau pulang yang diisi HRD untuk hari Tidak Lengkap atau Tidak Hadir.

Murni (tanpa database). Dipakai calculate_working_hour untuk menyuntik punch sintetis ke compute_day.
Aturan: jam koreksi hanya mengisi sisi yang kosong; lembur tidak pernah berasal dari jam koreksi.
"""
from datetime import datetime, timedelta

from frappe import _

AWALAN = "KOREKSI-"
NAMA_MASUK = AWALAN + "MASUK"
NAMA_PULANG = AWALAN + "PULANG"
STATUS_PUNCH = "Koreksi HRD"


def _fmt(dt):
    return dt.strftime("%d-%m-%Y %H:%M")


def jendela(rule, day):
    """Jendela waktu satu hari kerja; rumus sama dengan compute_day."""
    start = datetime.combine(day, rule["start_time"])
    end = start + timedelta(minutes=rule["duration_minutes"])
    return {
        "start": start,
        "end": end,
        "masuk_from": start - timedelta(minutes=rule["window_before_min"]),
        "masuk_to": start + timedelta(minutes=rule["late_limit_min"]),
        "pulang_to": end + timedelta(minutes=rule["window_after_min"]),
    }


def cek_jam_koreksi(rule, day, masuk=None, pulang=None, masuk_asli=None):
    """Daftar pesan galat (kosong bila valid). masuk_asli = jam masuk dari punch asli, bila ada."""
    galat = []
    if not masuk and not pulang:
        return galat
    w = jendela(rule, day)
    if masuk and not (w["masuk_from"] <= masuk <= w["masuk_to"]):
        galat.append(
            _("Jam Masuk Koreksi harus antara {0} dan {1} (jendela masuk shift hari itu).").format(
                _fmt(w["masuk_from"]), _fmt(w["masuk_to"]))
        )
    acuan = masuk or masuk_asli
    if pulang:
        if pulang > w["end"]:
            galat.append(
                _("Jam Pulang Koreksi tidak boleh melewati akhir shift ({0}); lembur tidak dapat dibuat lewat jam koreksi.").format(
                    _fmt(w["end"]))
            )
        if acuan is not None:
            if pulang <= acuan:
                galat.append(_("Jam Pulang Koreksi harus setelah jam masuk ({0}).").format(_fmt(acuan)))
            else:
                paling_awal = acuan + timedelta(minutes=rule["min_out_after_in_min"])
                if pulang < paling_awal:
                    galat.append(
                        _("Jam Pulang Koreksi terlalu dekat dengan jam masuk; paling awal {0}.").format(_fmt(paling_awal))
                    )
        elif pulang <= w["masuk_to"]:
            galat.append(_("Jam Pulang Koreksi harus setelah batas jam masuk ({0}).").format(_fmt(w["masuk_to"])))
    return galat


def hitung_dengan_koreksi(hitung, rule, day, punches, is_holiday=0, masuk=None, pulang=None):
    """hitung = compute_day. Mengembalikan (hasil, dipakai).

    dipakai = daftar sisi yang benar-benar diisi dari jam koreksi ("masuk", "pulang").
    Jam koreksi hanya mengisi sisi yang kosong pada hasil punch asli; sisi yang sudah ada diabaikan.
    """
    asli = hitung(rule, day, punches, is_holiday)
    if not masuk and not pulang:
        return asli, []
    f = asli["fields"]
    tambah = []
    dipakai = []
    if masuk and not f.get("check_in"):
        tambah.append({"name": NAMA_MASUK, "time": masuk, "review_status": STATUS_PUNCH})
        dipakai.append("masuk")
    if pulang and not f.get("check_out"):
        tambah.append({"name": NAMA_PULANG, "time": pulang, "review_status": STATUS_PUNCH})
        dipakai.append("pulang")
    if not tambah:
        asli["reasons"] = list(asli["reasons"]) + ["Jam koreksi diabaikan: punch asli sudah lengkap"]
        return asli, []

    gabung = sorted(list(punches) + tambah, key=lambda p: p["time"])
    hasil = hitung(rule, day, gabung, is_holiday)
    sintetis = {p["name"] for p in tambah}
    hasil["roles"] = {k: v for k, v in hasil["roles"].items() if k not in sintetis}
    h = hasil["fields"]
    for kolom in ("check_in_log", "check_out_log"):
        if h.get(kolom) in sintetis:
            h[kolom] = None
    h["punch_count"] = max(0, int(h.get("punch_count") or 0) - len(sintetis))
    if NAMA_PULANG in sintetis:
        # Lembur tidak boleh berasal dari jam koreksi (C4, Q-G).
        h["overtime_minutes"] = 0
        h["has_overtime"] = 0
        h["overtime_type"] = None
    hasil["reasons"] = list(hasil["reasons"]) + ["Jam {0} dikoreksi HRD".format(" dan ".join(dipakai))]
    return hasil, dipakai
