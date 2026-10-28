import frappe
from frappe import _
from frappe.model.document import Document


class HRISHoliday(Document):
	def validate(self):
		self.holiday_name = (self.holiday_name or "").strip()
		self.normalize_company_scope()
		self.validate_duplicate()

	def normalize_company_scope(self):
		# Company bisa terisi otomatis dari default pengguna. Jadi "semua company"
		# ditentukan oleh centang, bukan oleh field company yang kosong.
		if self.holiday_type == "Khusus Perusahaan" and self.applies_to_all_companies:
			frappe.throw(
				_("Jenis 'Khusus Perusahaan' tidak boleh berlaku untuk semua company. Matikan centang dan pilih Company.")
			)
		if self.applies_to_all_companies:
			self.company = None
		elif not self.company:
			frappe.throw(_("Pilih Company, atau aktifkan 'Berlaku untuk Semua Company'."))

	def validate_duplicate(self):
		if not self.holiday_date:
			return
		rows = frappe.get_all(
			"HRIS Holiday",
			filters={"holiday_date": self.holiday_date, "name": ["!=", self.name or ""]},
			fields=["name", "company", "holiday_name"],
		)
		for r in rows:
			if (not r.company) or (not self.company) or r.company == self.company:
				frappe.throw(
					_("Tanggal {0} sudah terdaftar sebagai '{1}' (berlaku untuk {2}).").format(
						self.holiday_date, r.holiday_name, r.company or "semua company"
					)
				)
