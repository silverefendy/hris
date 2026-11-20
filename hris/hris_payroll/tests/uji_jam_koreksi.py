"""Uji C4: modul jam_koreksi (murni, tanpa database), memakai compute_day asli.
  bench --site hris-uji.local execute hris.hris_payroll.tests.uji_jam_koreksi.jalankan
"""
from datetime import date, datetime, time

from hris.hris_attendance.services.jam_koreksi import cek_jam_koreksi, hitung_dengan_koreksi
from hris.hris_attendance.services.working_hour import compute_day

DAY = date(2026, 11, 6)
RULE = {
    "start_time": time(8, 0), "duration_minutes": 525, "break_minutes": 30,
    "window_before_min": 120, "late_limit_min": 120, "window_after_min": 180,
    "min_out_after_in_min": 60, "late_tolerance_min": 5, "early_leave_tolerance_min": 5,
    "overtime_min_minutes": 30, "deduction_block_min": 30, "deduction_hours_per_block": 0.5,
}


def T(h, m=0):
    return datetime(2026, 11, 6, h, m)


def P(nama, jam, menit=0):
    return {"name": nama, "time": T(jam, menit), "review_status": "Menunggu"}


class _Cek:
    def __init__(self):
        self.ok = 0
        self.total = 0

    def __call__(self, nama, kondisi, detail=""):
        self.total += 1
        if kondisi:
            self.ok += 1
            print("OK    %s" % nama)
        else:
            print("GAGAL %s | %s" % (nama, detail))


def _dekat(a, b):
    return abs(float(a) - float(b)) < 1e-9


def jalankan():
    cek = _Cek()
    pulang_asli = [P("RL-1", 16, 45)]
    masuk_asli = [P("RL-2", 8, 0)]

    f0 = compute_day(RULE, DAY, pulang_asli, 0)["fields"]
    cek("K0 fixture: hanya pulang = Tidak Lengkap", f0["status"] == "Tidak Lengkap", f0["status"])

    h, dipakai = hitung_dengan_koreksi(compute_day, RULE, DAY, pulang_asli, 0)
    cek("K1 tanpa jam koreksi: hasil sama dengan compute_day", h["fields"] == f0 and dipakai == [], str(dipakai))

    # K2: koreksi masuk 08:00 + pulang asli 16:45
    h, dipakai = hitung_dengan_koreksi(compute_day, RULE, DAY, pulang_asli, 0, masuk=T(8, 0))
    f = h["fields"]
    cek("K2 koreksi masuk: status Hadir", f["status"] == "Hadir", f["status"])
    cek("K2 jam efektif 8,25 dan tanpa telat", _dekat(f["effective_hours"], 8.25) and f["late_minutes"] == 0, str(f))
    cek("K2 check_in = jam koreksi, log masuk kosong, log pulang tetap RL-1",
        f["check_in"] == T(8, 0) and f["check_in_log"] is None and f["check_out_log"] == "RL-1", str(f))
    cek("K2 punch_count = 1 dan peran hanya RL-1", f["punch_count"] == 1 and h["roles"] == {"RL-1": "Pulang"}, "%s %s" % (f["punch_count"], h["roles"]))
    cek("K2 alasan menyebut dikoreksi", any("dikoreksi" in r for r in h["reasons"]), str(h["reasons"]))

    # K3: telat 20 menit
    h, _d = hitung_dengan_koreksi(compute_day, RULE, DAY, pulang_asli, 0, masuk=T(8, 20))
    f = h["fields"]
    cek("K3 koreksi masuk 08:20: telat 20 menit, potongan 0,5 jam, efektif 7,75",
        f["late_minutes"] == 20 and _dekat(f["late_deduction_hours"], 0.5) and _dekat(f["effective_hours"], 7.75), str(f))

    # K4: masuk asli + koreksi pulang 16:45
    h, _d = hitung_dengan_koreksi(compute_day, RULE, DAY, masuk_asli, 0, pulang=T(16, 45))
    f = h["fields"]
    cek("K4 koreksi pulang: Hadir, lembur 0, log pulang kosong",
        f["status"] == "Hadir" and f["overtime_minutes"] == 0 and f["check_out_log"] is None and f["check_in_log"] == "RL-2", str(f))

    # K5: pulang cepat 16:00
    h, _d = hitung_dengan_koreksi(compute_day, RULE, DAY, masuk_asli, 0, pulang=T(16, 0))
    f = h["fields"]
    cek("K5 koreksi pulang 16:00: pulang cepat 45 menit, efektif 7,25",
        f["early_leave_minutes"] == 45 and _dekat(f["effective_hours"], 7.25), str(f))

    # K6: lembur dari jam koreksi dipaksa 0 (tanpa lewat validasi)
    h, _d = hitung_dengan_koreksi(compute_day, RULE, DAY, masuk_asli, 0, pulang=T(18, 0))
    f = h["fields"]
    cek("K6 lembur dari jam koreksi dipaksa 0", f["overtime_minutes"] == 0 and f["has_overtime"] == 0 and f["overtime_type"] is None, str(f))

    # K7 dan K8: Tidak Hadir
    h, dipakai = hitung_dengan_koreksi(compute_day, RULE, DAY, [], 0, masuk=T(8, 0), pulang=T(16, 45))
    f = h["fields"]
    cek("K7 Tidak Hadir + dua jam koreksi: Hadir, punch_count 0, peran kosong",
        f["status"] == "Hadir" and f["punch_count"] == 0 and h["roles"] == {} and dipakai == ["masuk", "pulang"], str((f["status"], f["punch_count"], h["roles"], dipakai)))
    h, _d = hitung_dengan_koreksi(compute_day, RULE, DAY, [], 0, masuk=T(8, 0))
    cek("K8 Tidak Hadir + hanya jam masuk koreksi: tetap Tidak Lengkap", h["fields"]["status"] == "Tidak Lengkap", h["fields"]["status"])

    # K9: punch asli lengkap, koreksi diabaikan
    lengkap = [P("RL-3", 8, 0), P("RL-4", 16, 45)]
    f_lengkap = compute_day(RULE, DAY, lengkap, 0)["fields"]
    h, dipakai = hitung_dengan_koreksi(compute_day, RULE, DAY, lengkap, 0, masuk=T(9, 0))
    cek("K9 punch asli lengkap: koreksi diabaikan dan diberi alasan",
        h["fields"] == f_lengkap and dipakai == [] and any("diabaikan" in r for r in h["reasons"]), str(h["reasons"]))

    # Validasi
    cek("V1 masuk 07:00 (dalam jendela) valid", cek_jam_koreksi(RULE, DAY, masuk=T(7, 0)) == [])
    cek("V2 masuk 05:00 (sebelum jendela) ditolak", len(cek_jam_koreksi(RULE, DAY, masuk=T(5, 0))) == 1)
    cek("V3 masuk 10:30 (setelah batas masuk) ditolak", len(cek_jam_koreksi(RULE, DAY, masuk=T(10, 30))) == 1)
    cek("V4 pulang sebelum masuk ditolak", len(cek_jam_koreksi(RULE, DAY, masuk=T(9, 0), pulang=T(8, 30))) >= 1)
    cek("V5 pulang kurang dari 60 menit setelah masuk ditolak", len(cek_jam_koreksi(RULE, DAY, masuk=T(8, 0), pulang=T(8, 30))) == 1)
    g = cek_jam_koreksi(RULE, DAY, masuk=T(8, 0), pulang=T(18, 0))
    cek("V6 pulang melewati akhir shift ditolak dan menyebut lembur", len(g) == 1 and "lembur" in g[0], str(g))
    cek("V7 pulang saja dengan masuk asli sebagai acuan valid", cek_jam_koreksi(RULE, DAY, pulang=T(16, 45), masuk_asli=T(8, 0)) == [])
    cek("V8 tanpa jam koreksi: tanpa galat", cek_jam_koreksi(RULE, DAY) == [])

    print("Lulus %d dari %d" % (cek.ok, cek.total))
