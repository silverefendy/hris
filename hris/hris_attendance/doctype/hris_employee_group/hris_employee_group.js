frappe.provide("hris.audit");

frappe.ui.form.on("HRIS Employee Group", {
    setup(frm) {
        frm.set_query("shift", "weekly_schedule", () => {
            const filters = { is_active: 1 };
            if (frm.doc.company) filters.company = frm.doc.company;
            return { filters };
        });
        frm.set_query("department", () => {
            const filters = {};
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
