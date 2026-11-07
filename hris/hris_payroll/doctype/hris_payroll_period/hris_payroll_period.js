const HPP_MODUL = "hris.hris_payroll.doctype.hris_payroll_period.hris_payroll_period.";

frappe.ui.form.on("HRIS Payroll Period", {
    setup(frm) {
        frm.set_query("payroll_schedule", () => ({ filters: { is_active: 1 } }));
    },
    refresh(frm) {
        hris.audit.render(frm);
        if (frm.is_new()) {
            return;
        }
        const roles = frappe.user_roles || [];
        const adalah = (...daftar) => daftar.some((r) => roles.includes(r)) || frappe.session.user === "Administrator";
        const panggil = (metode, args) => {
            frappe.call({
                method: HPP_MODUL + metode,
                args: Object.assign({ name: frm.doc.name }, args || {}),
                freeze: true,
                callback() {
                    frm.reload_doc();
                },
            });
        };
        const pesan = {
            Draft: __("Draft. Periksa kesiapan, lalu Tinjau."),
            Ditinjau: __("Ditinjau. Payroll Manager dapat memfinalkan bila semua syarat terpenuhi."),
            Final: __("Final. Working Hour dan gaji pada rentang ini terkunci. Untuk koreksi, Payroll Manager harus membuka kembali periode."),
        };
        frm.set_intro(pesan[frm.doc.status] || "", frm.doc.status === "Final" ? "green" : "blue");

        frm.add_custom_button(__("Periksa Kesiapan"), () => {
            frappe.call({
                method: HPP_MODUL + "get_readiness",
                args: { name: frm.doc.name },
                callback(r) {
                    const hasil = r.message || { ok: false, items: [] };
                    if (hasil.ok) {
                        frappe.msgprint(__("Semua syarat Final terpenuhi."));
                        return;
                    }
                    const html = hasil.items
                        .map((i) => "<li>" + frappe.utils.escape_html(i.pesan) +
                            (i.contoh && i.contoh.length ? "<br><small>" + frappe.utils.escape_html(i.contoh.slice(0, 5).join(", ")) + "</small>" : "") + "</li>")
                        .join("");
                    frappe.msgprint({ title: __("Belum siap difinalkan"), message: "<ul>" + html + "</ul>", indicator: "orange" });
                },
            });
        });
        if (frm.doc.status === "Draft" && adalah("HRIS Payroll Admin", "HRIS Payroll Manager")) {
            frm.add_custom_button(__("Tinjau"), () => panggil("tinjau"), __("Aksi"));
        }
        if (frm.doc.status === "Ditinjau" && adalah("HRIS Payroll Admin", "HRIS Payroll Manager")) {
            frm.add_custom_button(__("Kembalikan ke Draft"), () => panggil("kembalikan"), __("Aksi"));
        }
        if (frm.doc.status === "Ditinjau" && adalah("HRIS Payroll Manager")) {
            frm.add_custom_button(__("Finalkan"), () => {
                frappe.confirm(__("Finalkan periode ini? Data gaji dan working hour pada rentangnya akan terkunci."), () => panggil("finalkan"));
            }, __("Aksi"));
        }
        if (frm.doc.status === "Final" && adalah("HRIS Payroll Manager")) {
            frm.add_custom_button(__("Buka Kembali"), () => {
                frappe.prompt(
                    [{ fieldname: "alasan", label: __("Alasan"), fieldtype: "Small Text", reqd: 1 }],
                    (v) => panggil("buka_kembali", { alasan: v.alasan }),
                    __("Buka Kembali Periode"),
                    __("Buka Kembali")
                );
            }, __("Aksi"));
        }
    },
});
