frappe.ui.form.on("HRIS BPJS Rate", {
    refresh(frm) {
        hris.audit.render(frm);
    },
});
