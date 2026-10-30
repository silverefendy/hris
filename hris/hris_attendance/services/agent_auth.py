"""Autentikasi token untuk endpoint agen (middleware).

Token dibuat dari HRIS Attendance Settings. Yang disimpan hanya hash SHA-256 token,
jadi token lengkap tidak bisa dilihat lagi; bila hilang, buat ulang (rotate).
"""
import hashlib
import hmac
import ipaddress
import time

import frappe
from frappe import _
from frappe.utils import cint

SETTINGS = "HRIS Attendance Settings"
HEADER = "X-HRIS-Token"
FAIL_LIMIT = 10
FAIL_WINDOW = 600  # detik
LOGGER = "hris_agent"


def hash_token(token):
	return hashlib.sha256((token or "").encode("utf-8")).hexdigest()


def _cache():
	# Bentuk akses cache berbeda antar versi Frappe: objek langsung atau fungsi.
	c = frappe.cache
	if hasattr(c, "set_value"):
		return c
	return c()


def _fail_key(ip):
	return "hris_agent_fail:" + str(ip)


def _is_blocked(ip):
	state = _cache().get_value(_fail_key(ip))
	if not state:
		return False
	return state.get("n", 0) >= FAIL_LIMIT and time.time() - state.get("t0", 0) <= FAIL_WINDOW


def _register_failure(ip):
	now = time.time()
	state = _cache().get_value(_fail_key(ip)) or {}
	if not state or now - state.get("t0", 0) > FAIL_WINDOW:
		state = {"n": 0, "t0": now}
	state["n"] += 1
	_cache().set_value(_fail_key(ip), state, expires_in_sec=FAIL_WINDOW)


def _ip_allowed(ip, allowed_text):
	"""True bila daftar kosong atau IP termasuk salah satu alamat/rentang di daftar."""
	networks = []
	for line in (allowed_text or "").splitlines():
		line = line.strip()
		if line:
			networks.append(ipaddress.ip_network(line, strict=False))
	if not networks:
		return True
	try:
		address = ipaddress.ip_address(ip)
	except ValueError:
		return False
	return any(address in net for net in networks)


def _reject(ip, reason):
	# Alasan hanya masuk log server, tidak ke respons, supaya pesan ke penyerang seragam.
	frappe.logger(LOGGER).warning("ditolak ip=%s alasan=%s", ip, reason)
	if reason != "diblokir":
		_register_failure(ip)
	frappe.throw(_("Token agen tidak valid."), frappe.AuthenticationError)


def verify_agent_request():
	"""Periksa token agen pada permintaan saat ini. Melempar AuthenticationError bila gagal."""
	ip = getattr(frappe.local, "request_ip", None) or "?"
	if _is_blocked(ip):
		_reject(ip, "diblokir")

	settings = frappe.get_cached_doc(SETTINGS)
	token = frappe.get_request_header(HEADER) or ""
	stored = settings.agent_token_hash or ""

	if not cint(settings.agent_enabled):
		_reject(ip, "saklar mati")
	if not token or not stored:
		_reject(ip, "token kosong")
	if not hmac.compare_digest(hash_token(token), stored):
		_reject(ip, "token salah")
	try:
		allowed = _ip_allowed(ip, settings.allowed_ips)
	except ValueError:
		allowed = False
	if not allowed:
		_reject(ip, "ip tidak diizinkan")
