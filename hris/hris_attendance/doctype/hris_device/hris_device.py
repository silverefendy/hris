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
		self.validate_network()

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
