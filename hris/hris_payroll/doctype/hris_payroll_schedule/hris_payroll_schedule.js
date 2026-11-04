frappe.ui.form.on("HRIS Payroll Schedule", {
    refresh(frm) {
        hris.audit.render(frm);
    },
});
