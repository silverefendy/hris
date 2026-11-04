frappe.ui.form.on("HRIS Employee", {
    refresh(frm) {
        hris.audit.render(frm);
    },
});
