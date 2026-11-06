// K-126 (V3): banner oranye bila sinkron ke Employee ERPNext Gagal.
// File terpisah supaya hris_employee.js yang sudah ada tidak tersentuh.
frappe.ui.form.on("HRIS Employee", {
	refresh(frm) {
		if (frm.is_new()) return;
		if (frm.doc.sync_status === "Gagal") {
			const galat = frappe.utils.escape_html(frm.doc.sync_error || "-");
			frm.set_intro(
				__(
					"Sinkron ke Employee ERPNext GAGAL: {0}. Perbaiki data lalu Simpan, atau tekan Sinkron Ulang. Rincian ada di bagian bawah tab Penjelasan.",
					[galat]
				),
				"orange"
			);
			frm._hris_intro_sinkron = true;
		} else if (frm._hris_intro_sinkron) {
			frm.set_intro("");
			frm._hris_intro_sinkron = false;
		}
	},
});
