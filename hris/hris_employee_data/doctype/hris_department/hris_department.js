frappe.ui.form.on("HRIS Department", {
setup(frm) {
frm.set_query("parent_department", () => ({ filters: { is_group: 1 } }));
},
});
