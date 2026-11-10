frappe.ui.form.on("HRIS PPh21 Settings", {
refresh(frm) {
if (window.hris && hris.audit && hris.audit.render) {
hris.audit.render(frm);
}
},
});
