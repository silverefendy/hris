frappe.ui.form.on("HRIS Employee Pay", {
    setup(frm) {
        frm.set_query("payroll_schedule", () => {
            const filters = { is_active: 1 };
            if (frm.doc.company) {
                filters.company = frm.doc.company;
            }
            return { filters };
        });
    },
    refresh(frm) {
        hris.audit.render(frm);
        if (!frm.is_new()) {
            frm.disable_form();
            frm.set_intro(
                __("Baris gaji tidak dapat diubah. Untuk perubahan, buat baris baru dengan Berlaku Dari yang baru."),
                "blue"
            );
        }
    },
});
