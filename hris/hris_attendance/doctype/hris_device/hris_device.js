frappe.provide("hris.audit");
frappe.provide("hris.device");

// Fungsi dialog (Tarik Log, Status, Ambil Info) ada di public/js/hris_device_actions.js.

frappe.ui.form.on("HRIS Device", {
    refresh(frm) {
        if (hris.audit.render) {
            hris.audit.render(frm);
        }
        // Cegah browser mengisi password tersimpan ke kolom Comm Key.
        const ck = frm.fields_dict.comm_key;
        if (ck && ck.$input) {
            ck.$input.attr("autocomplete", "new-password");
        }
        if (!hris.device.openPullDialog) {
            return; // file bersama belum termuat (belum build/refresh)
        }
        const name = frm.doc.name;
        const connectable = !frm.is_new() && frm.doc.ip_address && frm.doc.port;
        if (connectable) {
            frm.add_custom_button(__("Ambil Info dari Mesin"), () =>
                hris.device.ensureSaved(frm, () => hris.device.fetchInfo(name, frm))
            );
        }
        if (connectable && frm.doc.use_pull && frm.doc.is_active && hris.device.canPull()) {
            frm.add_custom_button(__("Tarik Log"), () =>
                hris.device.ensureSaved(frm, () =>
                    hris.device.openPullDialog(name, frm.doc.last_pull_at, (st) => hris.device.afterFinal(frm, st))
                )
            );
            frm.add_custom_button(__("Status Tarikan"), () =>
                hris.device.showStatus(name, (st) => hris.device.afterFinal(frm, st))
            );
        }
    },
});

hris.device.ensureSaved = function (frm, proceed) {
    if (!frm.is_dirty()) {
        proceed();
        return;
    }
    frappe.confirm(
        __("Form punya perubahan yang belum disimpan. Koneksi ke mesin memakai IP dan Port yang tersimpan di database, bukan yang tampil di layar. Lanjutkan?"),
        proceed
    );
};

hris.device.afterFinal = function (frm, st) {
    if (st && st.status === "Selesai" && !frm.is_dirty()) {
        frm.reload_doc();
    }
};
