import frappe
from frappe.model.document import Document


class HRISPullRun(Document):
	def before_insert(self):
		# autoname memakai {kode}; pastikan terisi sebelum penomoran.
		if not self.kode:
			self.kode = "DR" if self.jenis == "Hapus Raw Log" else "PR"
