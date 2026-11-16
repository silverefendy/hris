frappe.ui.form.on("HRIS PPh21 Settings", {
refresh(frm) {
frm.add_custom_button(__("Tarif TER"), () => frappe.set_route("List", "HRIS PPh21 TER Rate"));
frm.add_custom_button(__("Tarif Pasal 17"), () => frappe.set_route("List", "HRIS PPh21 Pasal17 Rate"));
if (window.hris && hris.audit && hris.audit.render) {
hris.audit.render(frm);
}
},
});
