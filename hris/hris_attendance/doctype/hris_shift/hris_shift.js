frappe.provide("hris.audit");

frappe.ui.form.on("HRIS Shift", {
    refresh(frm) {
        if (hris.audit.render) {
            hris.audit.render(frm);
        }
    },
});
