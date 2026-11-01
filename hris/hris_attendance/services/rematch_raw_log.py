import frappe
from frappe import _
from frappe.utils import add_days, getdate

DT = "HRIS Raw Log"
ROLES = ["HRIS HR Admin", "HRIS Manager", "System Manager"]
MAX_PER_KLIK = 500
MAX_ID_TAMPIL = 100
BISA = "Bisa dicocokkan"


def _rentang(date_from, date_to):
	"""Dua tanggal opsional menjadi batas punch_time: awal (termasuk) dan akhir (tidak termasuk)."""
	awal = getdate(date_from) if date_from else None
	akhir = getdate(date_to) if date_to else None
	if awal and akhir and akhir < awal:
		frappe.throw(_("Sampai Tanggal tidak boleh lebih awal dari Dari Tanggal."))
	return awal, (add_days(akhir, 1) if akhir else None)


def _kategori(device_user_id, company):
	"""Kategori satu ID mesin untuk satu company. Aturan sama dengan HRISRawLog.match_employee."""
	rows = frappe.get_all(
		"Employee",
		filters={"attendance_device_id": device_user_id},
		fields=["name", "company", "status"],
	)
	if not rows:
		return "Tidak ada Employee", None
	cocok = [r for r in rows if r.company == company and r.status == "Active"]
	if len(cocok) == 1:
		return BISA, cocok[0].name
	if len(cocok) > 1:
		return "Ambigu (lebih dari satu Employee)", None
	if any(r.company == company for r in rows):
		return "Employee tidak Active", rows[0].name
	return "Employee beda company", rows[0].name


def _kelompok(device_user_id, awal=None, akhir=None):
	syarat = "review_status = 'Tidak Cocok' and ifnull(employee, '') = ''"
	nilai = []
	if device_user_id:
		syarat += " and device_user_id = %s"
		nilai.append(device_user_id)
	if awal:
		syarat += " and punch_time >= %s"
		nilai.append(awal)
	if akhir:
		syarat += " and punch_time < %s"
		nilai.append(akhir)
	return frappe.db.sql(
		"select device_user_id, company, count(*) as n, min(punch_time) as dari, max(punch_time) as sampai "
		"from `tabHRIS Raw Log` where " + syarat + " group by device_user_id, company",
		tuple(nilai),
		as_dict=True,
	)


def _periksa(device_user_id, awal=None, akhir=None):
	ids = []
	total = bisa = tindakan = 0
	for g in _kelompok(device_user_id, awal, akhir):
		kategori, emp = _kategori(g.device_user_id, g.company)
		total += g.n
		if kategori == BISA:
			bisa += g.n
		else:
			tindakan += g.n
		ids.append({
			"id": g.device_user_id,
			"company": g.company,
			"n": g.n,
			"dari": str(g.dari)[:10],
			"sampai": str(g.sampai)[:10],
			"kategori": kategori,
			"employee": emp,
		})
	# yang bermasalah di atas, lalu yang paling banyak barisnya
	ids.sort(key=lambda x: (x["kategori"] == BISA, -x["n"]))
	return {"total": total, "bisa_baris": bisa, "tindakan_baris": tindakan, "ids": ids}


def _jalankan(device_user_id, commit, date_from=None, date_to=None):
	awal, akhir = _rentang(date_from, date_to)
	sisa = MAX_PER_KLIK
	dicocokkan = 0
	gagal = []
	ringkas = []
	for g in _periksa(device_user_id, awal, akhir)["ids"]:
		if g["kategori"] != BISA:
			continue
		if sisa <= 0:
			break
		filters = [
			["review_status", "=", "Tidak Cocok"],
			["device_user_id", "=", g["id"]],
			["company", "=", g["company"]],
			["employee", "is", "not set"],
		]
		if awal:
			filters.append(["punch_time", ">=", awal])
		if akhir:
			filters.append(["punch_time", "<", akhir])
		names = frappe.get_all(DT, filters=filters, pluck="name", order_by="punch_time asc", limit=sisa)
		ok = 0
		for name in names:
			frappe.db.savepoint("rematch_row")
			try:
				doc = frappe.get_doc(DT, name)
				doc.match_employee()
				if not doc.employee:
					continue
				doc.change_reason = "Cocokkan Ulang: ID mesin {0} cocok dengan {1}".format(g["id"], doc.employee)
				doc.flags.ignore_permissions = True
				doc.save()
				ok += 1
			except Exception as ex:
				frappe.db.rollback(save_point="rematch_row")
				if len(gagal) < 10:
					gagal.append("{0}: {1}".format(g["id"], str(ex)[:120]))
		sisa -= len(names)
		dicocokkan += ok
		if ok:
			ringkas.append({
				"id": g["id"],
				"employee": g["employee"],
				"jumlah": ok,
				"dari": g["dari"],
				"sampai": g["sampai"],
			})
	if commit:
		frappe.db.commit()
	sesudah = _periksa(device_user_id, awal, akhir)
	return {
		"dicocokkan": dicocokkan,
		"gagal": gagal,
		"ringkas": ringkas,
		"sisa_bisa": sesudah["bisa_baris"],
		"sisa_tindakan": sesudah["tindakan_baris"],
	}


@frappe.whitelist()
def check_rematch(device_user_id=None, date_from=None, date_to=None):
	"""Baca-saja: kelompokkan baris Tidak Cocok per ID mesin dan beri status tiap ID."""
	frappe.only_for(ROLES)
	awal, akhir = _rentang(date_from, date_to)
	hasil = _periksa((device_user_id or "").strip(), awal, akhir)
	hasil["jumlah_id"] = len(hasil["ids"])
	hasil["terpotong"] = len(hasil["ids"]) > MAX_ID_TAMPIL
	hasil["ids"] = [
		{k: v for k, v in x.items() if k != "company"} for x in hasil["ids"][:MAX_ID_TAMPIL]
	]
	return hasil


@frappe.whitelist()
def run_rematch(device_user_id=None, date_from=None, date_to=None):
	"""Cocokkan baris Tidak Cocok yang berstatus Bisa dicocokkan (maksimal MAX_PER_KLIK baris)."""
	frappe.only_for(ROLES)
	return _jalankan((device_user_id or "").strip(), True, date_from, date_to)
