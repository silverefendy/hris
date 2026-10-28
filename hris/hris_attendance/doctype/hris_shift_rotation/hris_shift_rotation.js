frappe.provide("hris.audit");

frappe.ui.form.on("HRIS Shift Rotation", {
    setup(frm) {
        frm.set_query("shift", "pattern", () => {
            const filters = { is_active: 1 };
            if (frm.doc.company) filters.company = frm.doc.company;
            return { filters };
        });
    },
    refresh(frm) {
        if (hris.audit.render) {
            hris.audit.render(frm);
        }
    },
});
