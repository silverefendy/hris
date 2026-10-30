frappe.provide("hris.settings");

hris.settings.show_token = function (token) {
    const dialog = new frappe.ui.Dialog({
        title: __("Token Agen Baru"),
        fields: [
            {
                fieldtype: "HTML",
                options: `<p>${__("Salin token ini sekarang. Token hanya tampil sekali dan tidak dapat dilihat lagi.")}</p>`,
            },
            {
                fieldtype: "Small Text",
                fieldname: "token",
                label: __("Token"),
                read_only: 1,
                default: token,
            },
        ],
        primary_action_label: __("Salin"),
        primary_action() {
            frappe.utils.copy_to_clipboard(token);
            frappe.show_alert({ message: __("Token disalin"), indicator: "green" });
        },
    });
    dialog.show();
};

frappe.ui.form.on("HRIS Attendance Settings", {
    refresh(frm) {
        const active = frm.doc.agent_enabled && frm.doc.agent_token_prefix;
        frm.set_intro(
            active ? __("Endpoint agen AKTIF.") : __("Endpoint agen NONAKTIF."),
            active ? "green" : "orange"
        );
        frm.add_custom_button(__("Generate / Rotate Token"), () => {
            if (frm.is_dirty()) {
                frappe.msgprint(__("Simpan perubahan dulu sebelum membuat token."));
                return;
            }
            frappe.confirm(
                __("Token lama langsung tidak berlaku dan semua agen harus diperbarui. Lanjutkan?"),
                () => {
                    frappe.call({
                        method: "hris.hris_attendance.doctype.hris_attendance_settings.hris_attendance_settings.generate_agent_token",
                        freeze: true,
                        callback(r) {
                            if (r.message) {
                                hris.settings.show_token(r.message.token);
                                frm.reload_doc();
                            }
                        },
                    });
                }
            );
        });
    },
});
