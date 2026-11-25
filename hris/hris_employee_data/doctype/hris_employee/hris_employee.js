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

const ROLE_ID_FINGER = ["HRIS Employee Admin", "HRIS HR Admin", "System Manager"];

function tombol_id_finger(frm) {
    if (frm.doc.attendance_device_id || !ROLE_ID_FINGER.some((r) => frappe.user.has_role(r))) {
        return;
    }
    frm.add_custom_button(__("Buat ID Finger"), () => {
        frappe.call({
            method: "hris.hris_employee_data.services.id_finger.ambil_id_berikutnya",
            freeze: true,
            freeze_message: __("Menghitung ID berikutnya..."),
            callback(r) {
                const h = r.message;
                if (!h) {
                    return;
                }
                const baris = h.sumber
                    .map((s) => `<li>${frappe.utils.escape_html(s.nama)}: ${s.terbesar}</li>`)
                    .join("");
                let html =
                    `<p>ID Finger berikutnya: <b>${h.berikutnya}</b></p>` +
                    `<p>Angka terbesar saat ini:</p><ul>${baris}</ul>`;
                if (h.bukan_angka) {
                    html += `<p>${h.bukan_angka} ID bukan angka diabaikan.</p>`;
                }
                frappe.confirm(html, () => {
                    frm.set_value("attendance_device_id", h.berikutnya);
                    frm.remove_custom_button(__("Buat ID Finger"));
                    frappe.msgprint({
                        title: __("Daftarkan ID di mesin"),
                        indicator: "orange",
                        message: __("ID {0} baru terisi di form ini. Simpan dokumen, lalu daftarkan ID yang sama di mesin absensi.", [h.berikutnya]),
                    });
                });
            },
        });
    });
}

frappe.ui.form.on("HRIS Employee", {
    refresh(frm) {
        hris.audit.render(frm);
        tombol_sinkron(frm);
        tombol_id_finger(frm);
    },
    after_save(frm) {
        frm.reload_doc();
    },
});
