"""Aturan potongan gaji untuk hari Tidak Hadir yang diklasifikasi HRD (K-131).

Murni (tanpa database). Aturan lain menyusul bersama HRIS Absence.
"""

KELAS = ("Mangkir", "Cuti", "Sakit", "Izin", "Lainnya")
FIELD_CEK = ("has_doctor_note", "has_supervisor_instruction", "annual_leave_exhausted", "absence_deducted")
FIELD_TEKS = ("absence_class", "absence_note")


def dipotong(kelas, ada_surat_dokter=0, ada_instruksi_atasan=0, cuti_tahunan_habis=0, manual=0):
	"""Mengembalikan 1 bila hari itu memotong gaji Bulanan, 0 bila tidak."""
	if kelas == "Mangkir":
		return 1
	if kelas == "Cuti":
		return 1 if cuti_tahunan_habis else 0
	if kelas == "Izin":
		return 0 if ada_instruksi_atasan else 1
	if kelas == "Sakit":
		return 0 if ada_surat_dokter else 1
	if kelas == "Lainnya":
		return 1 if manual else 0
	return 0
