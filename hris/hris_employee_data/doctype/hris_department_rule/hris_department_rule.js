frappe.ui.form.on("HRIS Department Rule", {
    refresh(frm) {
        hris.audit.render(frm);
    },
});
