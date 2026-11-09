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
        const peran = frappe.user_roles || [];
        const bolehSemua =
            frappe.session.user === "Administrator" || peran.includes("HRIS Payroll Manager") || peran.includes("System Manager");
        if (frm.is_new() && !bolehSemua) {
            frm.set_df_property("pay_type", "options", "Harian");
            if (frm.doc.pay_type !== "Harian") {
                frm.set_value("pay_type", "Harian");
            }
            frm.set_df_property(
                "pay_type",
                "description",
                __("Anda hanya dapat membuat upah Harian. Jenis Bulanan hanya untuk HRIS Payroll Manager.")
            );
        }
        if (!frm.is_new()) {
            const df = frm.get_docfield("pay_type");
            if (df && (df.description || "").indexOf("Anda hanya dapat") === 0) {
                frm.set_df_property("pay_type", "description", "");
            }
            frm.disable_form();
            frm.set_intro(
                __("Baris gaji tidak dapat diubah. Untuk perubahan, buat baris baru dengan Berlaku Dari yang baru."),
                "blue"
            );
        }
    },
});
