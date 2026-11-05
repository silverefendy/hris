const ROLE_SINKRON = [
    "HRIS HR Admin",
    "HRIS Employee Admin",
    "HRIS Manager",
    "System Manager",
];

function tombol_sinkron(frm) {
    if (frm.is_new() || !ROLE_SINKRON.some((r) => frappe.user.has_role(r))) {
        return;
    }
    frm.add_custom_button(__("Sinkron Ulang"), () => {
        if (frm.is_dirty()) {
            frappe.msgprint(__("Simpan perubahan dulu sebelum Sinkron Ulang."));
            return;
        }
        frappe.call({
            method: "hris.hris_employee_data.services.employee_sync.sinkron_ulang",
            args: { nama: frm.doc.name },
            freeze: true,
            freeze_message: __("Menyinkronkan ke Employee ERPNext..."),
            callback(r) {
                const hasil = r.message || "";
                const gagal = hasil.startsWith("Gagal");
                frappe.show_alert(
                    { message: hasil, indicator: gagal ? "red" : "green" },
                    10
                );
                frm.reload_doc();
            },
        });
    });
}

frappe.ui.form.on("HRIS Employee", {
    refresh(frm) {
        hris.audit.render(frm);
        tombol_sinkron(frm);
    },
    after_save(frm) {
        frm.reload_doc();
    },
});
