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

// C4-JAM-KOREKSI: nama hari dan Hitung Ulang otomatis setelah jam koreksi disimpan
(function () {
const HARI = ["Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"];

function tampilkan_hari(frm) {
if (!frm.doc.work_date) {
return;
}
const d = frappe.datetime.str_to_obj(frm.doc.work_date);
frm.set_df_property("work_date", "description", "Hari: <b>" + HARI[d.getDay()] + "</b>");
}

frappe.ui.form.on("HRIS Working Hour", {
refresh(frm) {
tampilkan_hari(frm);
},
work_date(frm) {
tampilkan_hari(frm);
},
manual_check_in(frm) {
frm._c4_koreksi_berubah = true;
},
manual_check_out(frm) {
frm._c4_koreksi_berubah = true;
},
after_save(frm) {
if (!frm._c4_koreksi_berubah) {
return;
}
frm._c4_koreksi_berubah = false;
setTimeout(function () {
const tombol = frm.custom_buttons && frm.custom_buttons["Hitung Ulang"];
if (tombol) {
tombol.trigger("click");
} else {
frappe.show_alert({
message: "Jam koreksi tersimpan. Tekan Hitung Ulang untuk memperbarui hari.",
indicator: "orange",
});
}
}, 700);
},
});
})();
