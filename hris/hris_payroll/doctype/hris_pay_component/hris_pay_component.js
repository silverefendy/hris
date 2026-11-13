frappe.ui.form.on("HRIS Pay Component", {
    refresh(frm) {
        hris.audit.render(frm);
    },
});
