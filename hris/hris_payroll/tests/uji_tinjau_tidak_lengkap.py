"""Uji C1: alur tinjauan Tidak Lengkap di HRIS Working Hour (controller). Semua perubahan di-rollback.
  bench --site hris-uji.local execute hris.hris_payroll.tests.uji_tinjau_tidak_lengkap.jalankan
"""
import frappe

WH = "HRIS Working Hour"
SITE = "hris-uji.local"


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


def _baca(n):
    return frappe.db.get_value(WH, n, ["status", "review_status", "incomplete_outcome", "reviewed_by"], as_dict=True)


def _tolak(fn, kata):
    try:
        fn()
    except frappe.ValidationError as e:
        return kata in str(e)
    return False


def jalankan():
    if frappe.local.site != SITE:
        print("Site bukan %s; berhenti." % SITE)
        return
    cek = _Cek()
    ada = frappe.get_meta(WH).has_field("incomplete_outcome")
    cek("D0 field incomplete_outcome ada di DocType", ada, "jalankan migrate situs uji dulu")
    if not ada:
        print("Lulus %d dari %d" % (cek.ok, cek.total))
        return
    try:
        nama = None
        kandidat = [r.name for r in frappe.get_all(
            WH, filters={"status": "Tidak Lengkap", "review_status": "Menunggu"}, fields=["name"], limit=30)]
        for n in kandidat:
            doc = frappe.get_doc(WH, n)
            doc.review_status = "Sudah Ditinjau"
            try:
                doc.save()
            except frappe.ValidationError as e:
                if "Hasil Tinjauan" in str(e):
                    nama = n
                    cek("D1 Sudah Ditinjau tanpa hasil ditolak", True)
                    break
                continue  # penyebab lain (mis. periode terkunci): coba kandidat berikutnya
            nama = n
            cek("D1 Sudah Ditinjau tanpa hasil ditolak", False, "tersimpan tanpa hasil")
            break
        if not nama:
            print("Tidak ada dokumen Tidak Lengkap (Menunggu) yang bisa dipakai di situs uji.")
            print("Lulus %d dari %d" % (cek.ok, cek.total))
            return

        doc = frappe.get_doc(WH, nama)
        doc.incomplete_outcome = "Dihitung Hadir"
        doc.review_note = ""
        cek("D2 hasil tanpa catatan ditolak", _tolak(doc.save, "Catatan Tinjauan"))

        doc = frappe.get_doc(WH, nama)
        doc.incomplete_outcome = "Dihitung Hadir"
        doc.review_note = "Lupa tap pulang (data uji)"
        doc.save()
        d = _baca(nama)
        cek("D3 hasil dan catatan tersimpan, otomatis Sudah Ditinjau", d.review_status == "Sudah Ditinjau" and d.incomplete_outcome == "Dihitung Hadir", str(d))
        cek("D4 Ditinjau Oleh terisi", bool(d.reviewed_by), str(d))

        doc = frappe.get_doc(WH, nama)
        doc.incomplete_outcome = "Dihitung Tidak Hadir"
        doc.save()
        cek("D5 hasil diubah ke Dihitung Tidak Hadir", _baca(nama).incomplete_outcome == "Dihitung Tidak Hadir", str(_baca(nama)))

        doc = frappe.get_doc(WH, nama)
        doc.review_status = "Menunggu"
        doc.save()
        d = _baca(nama)
        cek("D6 kembali ke Menunggu mengosongkan hasil", d.review_status == "Menunggu" and not d.incomplete_outcome, str(d))
    finally:
        frappe.db.rollback()
    print("Lulus %d dari %d" % (cek.ok, cek.total))
