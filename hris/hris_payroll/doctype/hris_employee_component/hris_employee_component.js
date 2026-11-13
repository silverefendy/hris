frappe.ui.form.on("HRIS Employee Component", {
    refresh(frm) {
        hris.audit.render(frm);
        const baru = frm.is_new();
        frm.set_df_property("employee", "read_only", baru ? 0 : 1);
        frm.set_df_property("component", "read_only", baru ? 0 : 1);
        if (!baru) {
            frm.set_intro(
                __("Untuk mengubah, ubah tanggal, status, atau nominal lalu isi Alasan yang baru. Untuk membatalkan, matikan Aktif."),
                "blue"
            );
        }
    },
    status(frm) {
        if (frm.doc.status === "Tidak Berlaku") {
            frm.set_value("amount", 0);
        }
    },
    date_from(frm) {
        if (frm.doc.date_from && !frm.doc.date_to) {
            frm.set_value("date_to", frm.doc.date_from);
        }
    },
});
