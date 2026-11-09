frappe.ui.form.on("HRIS Payroll Slip", {
    refresh(frm) {
        hris.audit.render(frm);
        if (frm.is_new()) {
            return;
        }
        const roles = frappe.user_roles || [];
        const adalah = (...daftar) => daftar.some((r) => roles.includes(r)) || frappe.session.user === "Administrator";
        const esc = frappe.utils.escape_html;
        const pesan = {
            Draft: __("Draft. Komponen Otomatis dihitung dari Working Hour dan gaji; Anda boleh menambah komponen Manual (alasan wajib)."),
            Ditinjau: __("Ditinjau. Slip terkunci. Untuk koreksi, kembalikan Periode Gaji ke Draft."),
            Final: __("Final. Slip terkunci. Untuk koreksi, Payroll Manager harus membuka kembali Periode Gaji."),
        };
        let isi = esc(pesan[frm.doc.status] || "");
        if (frm.doc.calc_notes) {
            isi += "<br>" + esc(frm.doc.calc_notes).replace(/\n/g, "<br>");
        }
        frm.set_intro(isi, frm.doc.status === "Final" ? "green" : "blue");

        if (frm.doc.status === "Draft" && adalah("HRIS Payroll Admin", "HRIS Payroll Manager")) {
            frm.add_custom_button(__("Hitung Ulang Slip"), () => {
                frappe.call({
                    method: "hris.hris_payroll.services.payroll_slip.hitung_ulang_slip",
                    args: { name: frm.doc.name },
                    freeze: true,
                    callback() {
                        frm.reload_doc();
                    },
                });
            });
        }
    },
});
