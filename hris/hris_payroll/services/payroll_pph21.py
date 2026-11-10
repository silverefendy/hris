"""PPh 21 TER bulanan pada HRIS Payroll Slip (K-134, langkah 4).

Dipotong sekali sebulan pada slip TERAKHIR yang tanggal bayarnya jatuh di bulan itu (bulan dari tanggal bayar).
Pengaturan: HRIS PPh21 Settings dan HRIS PPh21 TER Rate. Tarif resmi diisi HRD; kode tidak memuat angka pajak.
"""

from datetime import timedelta
from decimal import ROUND_FLOOR, ROUND_HALF_UP, Decimal

import frappe
from frappe import _
from frappe.utils import get_first_day, get_last_day, getdate

from hris.hris_payroll.services import payroll_bpjs as bp
from hris.hris_payroll.services.pph21_rate import find_rate

SETTINGS = "HRIS PPh21 Settings"
SLIP = "HRIS Payroll Slip"
ITEM = "HRIS Payroll Slip Item"
NAMA = "PPh 21"
BERWENANG = "HRD (HRIS HR Admin atau HRIS Employee Admin)"


def _dec(nilai):
    return Decimal(str(nilai if nilai is not None else 0))


def _teks(masalah, penyebab, tindakan, berwenang=BERWENANG):
    return _("Masalah: {0} Penyebab: {1} Tindakan: {2} Berwenang: {3}").format(masalah, penyebab, tindakan, berwenang)


def _lewati(pesan_teks):
    return {"komponen": [], "catatan": [], "dilewati": pesan_teks}


# ---------- data ----------
def _data_karyawan(he):
    # Query langsung agar tidak terhalang izin field (permlevel) pemanggil.
    return frappe.db.get_value("HRIS Employee", he.name, ["pph21_enrolled", "ptkp_status", "npwp"], as_dict=True) or {}


def _slip_terakhir(period):
    """True bila periode berikutnya dibayar di bulan lain (periode ini = slip terakhir bulan itu)."""
    params, offset, aturan = bp._jadwal(period)
    _awal, akhir_sesudah = bp.compute_period(params, getdate(period.period_end) + timedelta(days=1))
    bayar_sesudah = bp.compute_pay_date(akhir_sesudah, offset, aturan)
    return bp._ym(bayar_sesudah) != bp._ym(period.pay_date)


def _jumlah_slip_jadwal(period):
    """Jumlah periode jadwal ini yang tanggal bayarnya jatuh di bulan bayar slip ini; None bila gagal dihitung."""
    try:
        params, offset, aturan = bp._jadwal(period)
        ym = bp._ym(period.pay_date)
        jumlah = 1
        awal = getdate(period.period_start)
        for _n in range(12):
            awal_sebelum, akhir_sebelum = bp.compute_period(params, awal - timedelta(days=1))
            if bp._ym(bp.compute_pay_date(akhir_sebelum, offset, aturan)) != ym:
                break
            jumlah += 1
            awal = getdate(awal_sebelum)
        akhir = getdate(period.period_end)
        for _n in range(12):
            _a, akhir_sesudah = bp.compute_period(params, akhir + timedelta(days=1))
            if bp._ym(bp.compute_pay_date(akhir_sesudah, offset, aturan)) != ym:
                break
            jumlah += 1
            akhir = getdate(akhir_sesudah)
        return jumlah
    except Exception:
        return None


def _slip_saat_ini(he, period):
    """(nama slip bila sudah ada, bruto kena pajak dari baris Manual slip itu). Manual dipertahankan saat hitung ulang."""
    kunci = "{0}|{1}".format(period.name, he.name)
    nama = frappe.db.get_value(SLIP, {"unique_key": kunci}, "name")
    if not nama:
        return None, Decimal(0)
    baris = frappe.db.sql(
        "select amount from `tab{0}` where parent=%s and parenttype=%s and parentfield='components' "
        "and source='Manual' and component_type='Pendapatan' and taxable=1".format(ITEM),
        (nama, SLIP),
    )
    return nama, sum((_dec(b[0]) for b in baris), Decimal(0))


def _slip_lain(he, period, nama_ada, bebas):
    """Slip karyawan ini yang tanggal bayarnya di bulan yang sama, selain slip ini.

    Mengembalikan (jumlah slip, bruto kena pajak, nama slip yang sudah memuat PPh 21 atau None)."""
    awal_bulan = get_first_day(period.pay_date)
    akhir_bulan = get_last_day(period.pay_date)
    slip = frappe.get_all(
        SLIP,
        filters={"employee": he.name, "pay_date": ["between", [str(awal_bulan), str(akhir_bulan)]], "name": ["!=", nama_ada or ""]},
        pluck="name",
    )
    if not slip:
        return 0, Decimal(0), None
    baris = frappe.db.sql(
        "select parent, component, source, taxable, amount from `tab{0}` where parent in %s and parenttype=%s "
        "and parentfield='components' and component_type='Pendapatan'".format(ITEM),
        (tuple(slip), SLIP),
        as_dict=True,
    )
    bruto = Decimal(0)
    for b in baris:
        if b.source == "Otomatis":
            if (b.component or "").strip().lower() in bebas:
                continue
        elif not b.taxable:
            continue
        bruto += _dec(b.amount)
    pembawa = frappe.db.sql(
        "select parent from `tab{0}` where parent in %s and parenttype=%s and parentfield='components' "
        "and source='Otomatis' and component=%s limit 1".format(ITEM),
        (tuple(slip), SLIP, NAMA),
    )
    return len(slip), bruto, (pembawa[0][0] if pembawa else None)


# ---------- gabungan ----------
def hitung_pph21_slip(he, period, gaji, hasil):
    """Mengembalikan {"komponen", "catatan"}; bila data kurang ditambah kunci "dilewati" (pesan).

    he = baris HRIS Employee, period = dokumen HRIS Payroll Period, gaji = baris HRIS Employee Pay,
    hasil = keluaran hitung_komponen (komponen Otomatis slip ini, sudah termasuk BPJS).
    """
    kosong = {"komponen": [], "catatan": []}
    data = _data_karyawan(he) or {}
    if not data.get("pph21_enrolled"):
        return kosong

    bulan = getdate(period.pay_date).strftime("%m-%Y")
    st = frappe.get_doc(SETTINGS)
    if not st.enabled:
        return {
            "komponen": [],
            "catatan": [
                _("PPh 21 bulan {0} tidak dipotong: pengaturan HRIS PPh21 Settings belum diaktifkan, padahal karyawan ini ditandai Peserta PPh 21. HRD menyelesaikan pengaturan, lalu slip dihitung ulang.").format(bulan)
            ],
        }

    ptkp = (data.get("ptkp_status") or "").strip().upper()
    if not ptkp:
        return _lewati(_teks(
            _("Peserta PPh 21 dicentang tetapi Status PTKP kosong."),
            _("Status PTKP menentukan kategori tarif TER."),
            _("HRD mengisi Status PTKP di data karyawan, atau menghilangkan centang Peserta PPh 21, lalu slip dibuat atau dihitung ulang."),
        ))
    peta = {(r.ptkp_status or "").strip().upper(): (r.ter_category or "").strip().upper() for r in (st.ptkp_map or [])}
    kategori = peta.get(ptkp)
    if not kategori:
        return _lewati(_teks(
            _("Status PTKP {0} belum dipetakan ke kategori TER.").format(ptkp),
            _("Tabel Pemetaan di HRIS PPh21 Settings tidak memuat status ini."),
            _("HRD menambahkan pemetaan status itu di HRIS PPh21 Settings (setelah diverifikasi), lalu slip dihitung ulang."),
        ))

    bebas = {(r.component_name or "").strip().lower() for r in (st.exempt_components or [])}
    nama_ada, bruto_manual = _slip_saat_ini(he, period)

    if not _slip_terakhir(period):
        catatan = [
            _("PPh 21 bulan {0} tidak dipotong pada slip ini; dipotong sekali pada slip terakhir yang tanggal bayarnya jatuh di bulan itu.").format(bulan)
        ]
        _jml, _bruto, pembawa = _slip_lain(he, period, nama_ada, bebas)
        if pembawa:
            catatan.append(
                _("Peringatan: slip {0} sudah memuat PPh 21 bulan ini. Hitung ulang slip itu agar pajaknya mengikuti perubahan di slip ini.").format(pembawa)
            )
        return {"komponen": [], "catatan": catatan}

    jumlah_lain, bruto_lain, _pembawa = _slip_lain(he, period, nama_ada, bebas)
    bruto_sendiri = sum(
        (_dec(k["jumlah"]) for k in hasil["komponen"]
         if k["tipe"] == "Pendapatan" and (k["nama"] or "").strip().lower() not in bebas),
        Decimal(0),
    )
    bruto = bruto_sendiri + bruto_manual + bruto_lain
    n_slip = 1 + jumlah_lain

    baris_tarif = find_rate(kategori, float(bruto), period.pay_date)
    if not baris_tarif:
        return _lewati(_teks(
            _("Tarif TER tidak ditemukan untuk kategori {0}, bruto kena pajak {1}, tanggal bayar {2}.").format(
                kategori, bp._rp(bp._rupiah(bruto)), period.pay_date),
            _("Tabel HRIS PPh21 TER Rate tidak memuat rentang yang mencakup bruto ini pada tanggal berlaku tersebut."),
            _("HRD melengkapi tabel tarif (setelah diverifikasi) lalu slip dihitung ulang."),
        ))

    tarif = _dec(baris_tarif.rate_percent)
    punya_npwp = bool((data.get("npwp") or "").strip())
    pengali = Decimal(1) if punya_npwp else _dec(st.no_npwp_multiplier if st.no_npwp_multiplier else 1)
    mentah = bruto * tarif / Decimal(100) * pengali
    mode = ROUND_FLOOR if (st.rounding or "Ke Bawah") == "Ke Bawah" else ROUND_HALF_UP
    pajak = int(mentah.quantize(Decimal(1), rounding=mode))
    tarif_txt = format(tarif.normalize(), "f")
    pengali_txt = "" if pengali == 1 else _(" x pengali tanpa NPWP {0}").format(format(pengali.normalize(), "f"))

    komponen = []
    if pajak > 0:
        catatan = [
            _("PPh 21 bulan {0} dipotong pada slip ini (slip terakhir yang tanggal bayarnya jatuh di bulan itu). Bruto kena pajak {1} dari {2} slip, kategori TER {3} ({4}), tarif {5}%{6}, pajak {7}.").format(
                bulan, bp._rp(bp._rupiah(bruto)), n_slip, kategori, ptkp, tarif_txt, pengali_txt, bp._rp(pajak))
        ]
        komponen.append({
            "nama": NAMA, "tipe": "Potongan", "jumlah": pajak,
            "dasar": _("TER {0} {1}% x bruto kena pajak {2}").format(kategori, tarif_txt, bp._rp(bp._rupiah(bruto))),
        })
    else:
        catatan = [
            _("PPh 21 bulan {0}: tarif {1}% pada bruto kena pajak {2} (dari {3} slip, kategori TER {4}), sehingga tidak ada potongan.").format(
                bulan, tarif_txt, bp._rp(bp._rupiah(bruto)), n_slip, kategori)
        ]

    jadwal = _jumlah_slip_jadwal(period)
    if jadwal and n_slip < jadwal:
        catatan.append(
            _("Peringatan: bruto dihitung dari {0} slip, sedangkan jadwal gaji memuat {1} slip yang dibayar di bulan ini. Periksa apakah ada slip yang belum dibuat (atau karyawan baru masuk atau keluar), lalu hitung ulang slip ini.").format(n_slip, jadwal)
        )

    pendapatan = sum((_dec(k["jumlah"]) for k in hasil["komponen"] if k["tipe"] == "Pendapatan"), Decimal(0))
    potongan = sum((_dec(k["jumlah"]) for k in hasil["komponen"] if k["tipe"] == "Potongan"), Decimal(0))
    bersih = pendapatan - potongan - pajak
    if bersih < 0:
        catatan.append(
            _("Peringatan: gaji bersih dari komponen otomatis negatif ({0}) setelah PPh 21. Belum termasuk komponen Manual. Periksa sebelum Ditinjau.").format(
                bp._rp(bp._rupiah(bersih)))
        )
    return {"komponen": komponen, "catatan": catatan}
