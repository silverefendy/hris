frappe.provide("hris.audit");

frappe.ui.form.on("HRIS Device", {
    refresh(frm) {
        if (hris.audit.render) {
            hris.audit.render(frm);
        }
    },
});
