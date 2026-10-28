frappe.provide("hris.audit");

frappe.ui.form.on("HRIS Holiday", {
    refresh(frm) {
        if (hris.audit.render) {
            hris.audit.render(frm);
        }
    },
    holiday_type(frm) {
        if (frm.doc.holiday_type === "Khusus Perusahaan" && frm.doc.applies_to_all_companies) {
            frm.set_value("applies_to_all_companies", 0);
        }
    },
});
