"""Jenis gaji karyawan pada satu tanggal, dibaca dari HRIS Employee Pay (K-131).

Aman dipanggil di site yang belum punya tabel terkait: hasilnya None.
"""

import frappe

PAY = "HRIS Employee Pay"
EMP = "HRIS Employee"


def pay_type_on(employee, work_date):
	"""employee = ID Employee ERPNext. Mengembalikan 'Harian', 'Bulanan', atau None bila tidak ada baris gaji berlaku."""
	if not employee or not work_date:
		return None
	if not (frappe.db.table_exists(PAY) and frappe.db.table_exists(EMP)):
		return None
	baris = frappe.db.sql(
		"""
		select ep.pay_type
		from `tabHRIS Employee Pay` ep
		inner join `tabHRIS Employee` he on he.name = ep.employee
		where he.erpnext_employee = %(emp)s
		  and ep.effective_from <= %(d)s
		  and (ep.effective_to is null or ep.effective_to >= %(d)s)
		order by ep.effective_from desc
		limit 1
		""",
		{"emp": employee, "d": work_date},
	)
	return baris[0][0] if baris else None
