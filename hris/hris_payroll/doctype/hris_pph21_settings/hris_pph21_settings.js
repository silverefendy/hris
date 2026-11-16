frappe.ui.form.on("HRIS PPh21 Settings", {
refresh(frm) {
frm.add_custom_button(__("Tarif TER"), () => frappe.set_route("List", "HRIS PPh21 TER Rate"));
frm.add_custom_button(__("Tarif Pasal 17"), () => frappe.set_route("List", "HRIS PPh21 Pasal17 Rate"));
frappe.call({
method: "hris.hris_payroll.doctype.hris_pph21_settings.hris_pph21_settings.kategori_ter",
callback(r) {
const daftar = r.message || [];
if (!daftar.length) { return; }
const grid = frm.fields_dict.ptkp_map.grid;
grid.update_docfield_property("ter_category", "fieldtype", "Select");
grid.update_docfield_property("ter_category", "options", [""].concat(daftar).join("\n"));
grid.refresh();
},
});
if (window.hris && hris.audit && hris.audit.render) {
hris.audit.render(frm);
}
},
});
