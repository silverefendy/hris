frappe.provide("hris.audit");

frappe.ui.form.on("HRIS Shift Assignment", {
    setup(frm) {
        frm.set_query("shift", () => {
            const filters = { is_active: 1 };
            if (frm.doc.company) filters.company = frm.doc.company;
            return { filters };
        });
        frm.set_query("employee", () => ({ filters: { status: "Active" } }));
        frm.set_query("borrowed_for_group", () => ({ filters: { is_active: 1 } }));
    },
    refresh(frm) {
        if (hris.audit.render) {
            hris.audit.render(frm);
        }
    },
    from_date(frm) {
        if (frm.doc.from_date && !frm.doc.to_date) {
            frm.set_value("to_date", frm.doc.from_date);
        }
    },
});
