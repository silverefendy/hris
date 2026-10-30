frappe.provide("hris.audit");
frappe.provide("hris.device");

frappe.ui.form.on("HRIS Device", {
    refresh(frm) {
        if (hris.audit.render) {
            hris.audit.render(frm);
        }
        if (!frm.is_new() && frm.doc.ip_address && frm.doc.port) {
            frm.add_custom_button(__("Ambil Info dari Mesin"), () => hris.device.fetchInfo(frm));
        }
    },
});

hris.device.fetchInfo = function (frm) {
    if (frm.is_dirty()) {
        frappe.msgprint(__("Simpan perubahan dulu, karena koneksi memakai IP dan Port yang tersimpan."));
        return;
    }
    frappe
        .call({
            method: "hris.hris_attendance.services.pull_device.fetch_device_info",
            args: { device_name: frm.doc.name },
            freeze: true,
            freeze_message: __("Menghubungi mesin..."),
        })
        .then((r) => {
            const info = r.message || {};
            const changes = {};
            ["serial_number", "firmware_version", "device_model"].forEach((field) => {
                if (info[field] && info[field] !== frm.doc[field]) {
                    changes[field] = info[field];
                }
            });
            const summary =
                __("Serial") + ": " + (info.serial_number || "-") + "<br>" +
                __("Firmware") + ": " + (info.firmware_version || "-") + "<br>" +
                __("Model") + ": " + (info.device_model || "-") + "<br>" +
                __("Jam mesin") + ": " + (info.device_time || "-");
            if (!Object.keys(changes).length) {
                frappe.msgprint(summary + "<br><br>" + __("Tidak ada perbedaan dengan data di form."));
                return;
            }
            frm.set_value(changes).then(() => {
                frappe.msgprint(summary + "<br><br>" + __("Nilai sudah diisi ke form tetapi belum disimpan. Klik Simpan bila sudah sesuai."));
            });
        });
};
