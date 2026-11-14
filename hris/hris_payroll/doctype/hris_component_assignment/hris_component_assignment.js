frappe.ui.form.on("HRIS Component Assignment", {
    refresh(frm) {
        if (hris.audit && hris.audit.render) {
            hris.audit.render(frm);
        }
        const baru = frm.is_new();
        ["scope_type", "department", "employee_group", "component"].forEach((f) => frm.set_df_property(f, "read_only", baru ? 0 : 1));
        if (!baru) {
            frm.set_intro(
                __("Untuk mengubah, ubah tanggal, status, atau nominal lalu isi Alasan yang baru. Untuk mengeluarkan seseorang, buat penetapan karyawan (HRIS Employee Component) dengan Status Tidak Berlaku. Untuk menghentikan penetapan ini, matikan Aktif."),
                "blue"
            );
        }
    },
    scope_type(frm) {
        if (frm.doc.scope_type === "Department") {
            frm.set_value("employee_group", null);
        } else {
            frm.set_value("department", null);
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
