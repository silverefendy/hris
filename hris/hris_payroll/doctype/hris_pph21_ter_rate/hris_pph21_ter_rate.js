frappe.ui.form.on("HRIS PPh21 TER Rate", {
refresh(frm) {
if (window.hris && hris.audit && hris.audit.render) {
hris.audit.render(frm);
}
},
});
