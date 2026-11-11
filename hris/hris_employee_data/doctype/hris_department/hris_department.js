frappe.ui.form.on("HRIS Department", {
    setup(frm) {
        frm.set_query("parent_department", () => ({ filters: { is_group: 1 } }));
    },
    refresh(frm) {
        if (frm.is_new()) {
            return;
        }
        frm.add_custom_button(__("Sinkron Ulang"), () => {
            if (frm.is_dirty()) {
                frappe.msgprint(__("Simpan perubahan dulu sebelum Sinkron Ulang."));
                return;
            }
            frappe.call({
                method: "hris.hris_employee_data.services.department_sync.sinkron_ulang",
                args: { nama: frm.doc.name },
                freeze: true,
                callback(r) {
                    frappe.show_alert({ message: r.message, indicator: "blue" });
                    frm.reload_doc();
                },
            });
        });
        if (frm.doc.sync_status === "Gagal") {
            const galat = frappe.utils.escape_html(frm.doc.sync_error || "-");
            frm.set_intro(
                __("Sinkron ke Department ERPNext GAGAL: {0}. Perbaiki lalu Simpan, atau tekan Sinkron Ulang.", [galat]),
                "orange"
            );
            frm._hris_intro_sinkron = true;
        } else if (frm._hris_intro_sinkron) {
            frm.set_intro("");
            frm._hris_intro_sinkron = false;
        }
        hris.audit.render(frm);
    },
});
