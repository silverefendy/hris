frappe.provide("hris.audit");

frappe.ui.form.on("HRIS Working Hour", {
    refresh(frm) {
        if (hris.audit.render) {
            hris.audit.render(frm);
        }
    },
});
