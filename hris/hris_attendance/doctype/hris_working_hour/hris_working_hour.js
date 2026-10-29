frappe.provide("hris.audit");

frappe.ui.form.on("HRIS Working Hour", {
    refresh(frm) {
        if (hris.audit.render) {
            hris.audit.render(frm);
        }
        if (!frm.is_new() && frappe.user.has_role(["HRIS HR Admin", "HRIS Manager", "System Manager"])) {
            frm.add_custom_button(__("Hitung Ulang"), () => {
                frappe.call({
                    method: "hris.hris_attendance.services.working_hour_batch.recalculate_working_hours",
                    args: {
                        from_date: frm.doc.work_date,
                        to_date: frm.doc.work_date,
                        scope: "Karyawan",
                        employee: frm.doc.employee,
                        skip_reviewed: 0,
                    },
                    freeze: true,
                    freeze_message: __("Menghitung ulang..."),
                    callback(r) {
                        const m = r.message || {};
                        if (m.failed) {
                            frappe.msgprint({
                                title: __("Gagal"),
                                indicator: "red",
                                message: (m.errors || []).map((e) => frappe.utils.escape_html(e)).join("<br>"),
                            });
                        }
                        frm.reload_doc();
                    },
                });
            });
        }
    },
});
