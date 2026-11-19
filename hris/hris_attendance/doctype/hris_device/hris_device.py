import ipaddress
import re

import frappe
from frappe import _
from frappe.model.document import Document

HOSTNAME_RE = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?$")


class HRISDevice(Document):
	def validate(self):
		self.device_name = (self.device_name or "").strip()
		self.serial_number = (self.serial_number or "").strip()
		self.set_device_code()
		self.validate_network()

	def set_device_code(self):
		code = (self.device_code or "").strip().upper()
		if not code:
			code = self.make_device_code()
		if not re.fullmatch(r"[A-Z0-9_]+", code):
			frappe.throw(_("Device Code hanya boleh huruf, angka, dan garis bawah (_). Tanpa spasi atau tanda minus (-)."))
		if frappe.db.exists("HRIS Device", {"device_code": code, "name": ["!=", self.name or ""]}):
			frappe.throw(_("Device Code {0} sudah dipakai device lain.").format(code))
		self.device_code = code

	def make_device_code(self):
		words = re.findall(r"[A-Za-z0-9]+", self.device_name or "")
		if len(words) == 1:
			base = words[0][:4].upper()
		else:
			base = "".join(w[0] for w in words).upper()
		base = base or "DEV"
		code, n = base, 1
		while frappe.db.exists("HRIS Device", {"device_code": code, "name": ["!=", self.name or ""]}):
			n += 1
			code = f"{base}{n}"
		return code

	def validate_network(self):
		host = (self.ip_address or "").strip()
		self.ip_address = host
		if self.connection_mode == "Pull (IP)" or self.use_pull:
			if not host:
				frappe.throw(_("IP Address / hostname wajib diisi untuk mode Pull (IP) atau jalur Via Pull (pyzk)."))
			if not self.port:
				frappe.throw(_("Port wajib diisi untuk mode Pull (IP) atau jalur Via Pull (pyzk)."))
		if host:
			looks_numeric = re.fullmatch(r"[\d.]+", host)
			try:
				ipaddress.ip_address(host)
			except ValueError:
				if looks_numeric or not HOSTNAME_RE.match(host):
					frappe.throw(_("IP Address / hostname tidak valid: {0}").format(host))
		if self.port and not (1 <= int(self.port) <= 65535):
			frappe.throw(_("Port harus antara 1 dan 65535."))
