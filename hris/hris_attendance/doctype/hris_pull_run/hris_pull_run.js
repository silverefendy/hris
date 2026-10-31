frappe.ui.form.on("HRIS Pull Run", {
	refresh(frm) {
		hris.audit.render(frm);
	},
});
