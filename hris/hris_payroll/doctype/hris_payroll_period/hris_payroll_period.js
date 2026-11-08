const HPP_MODUL = "hris.hris_payroll.doctype.hris_payroll_period.hris_payroll_period.";

function hppTampilkanKesiapan(frm) {
    frappe.call({
        method: HPP_MODUL + "get_readiness",
        args: { name: frm.doc.name },
        callback(r) {
            const hasil = r.message || { ok: false, items: [] };
            if (hasil.ok) {
                frappe.msgprint({ title: __("Kesiapan Final"), message: __("Semua syarat Final terpenuhi."), indicator: "green" });
                return;
            }
            const esc = frappe.utils.escape_html;
            const tautan = [];
            let html = "";
            hasil.items.forEach((item) => {
                html += "<div style='margin-bottom:16px'>";
                html += "<div><b>" + esc(item.pesan) + "</b></div>";
                if (item.penyebab) {
                    html += "<div class='text-muted'>" + __("Penyebab") + ": " + esc(item.penyebab) + "</div>";
                }
                if (item.tindakan) {
                    html += "<div>" + __("Tindakan") + ": " + esc(item.tindakan) + "</div>";
                }
                if (item.berwenang) {
                    html += "<div class='text-muted'>" + __("Berwenang") + ": " + esc(item.berwenang) + "</div>";
                }
                (item.tautan || []).forEach((t) => {
                    tautan.push(t);
                    html += "<div><a href='#' class='hpp-lihat' data-i='" + (tautan.length - 1) + "'>" + esc(t.label) + "</a></div>";
                });
                if (item.daftar && item.daftar.length) {
                    html += "<div style='max-height:240px;overflow:auto;margin-top:6px'>";
                    html += "<table class='table table-bordered table-sm'><tbody>";
                    item.daftar.forEach((d) => {
                        const sel = d.doctype && d.name
                            ? frappe.utils.get_form_link(d.doctype, d.name, true, esc(d.label || d.name))
                            : esc(d.label || "");
                        const aksi = d.aksi === "buat_gaji" && d.name
                            ? "<a href='#' class='hpp-gaji' data-he='" + esc(d.name) + "'>" + __("Buat Baris Gaji") + "</a>"
                            : "";
                        html += "<tr><td>" + sel + "</td><td>" + esc(d.info || "") + "</td><td>" + aksi + "</td></tr>";
                    });
                    html += "</tbody></table></div>";
                    if (item.terpotong) {
                        html += "<div class='text-muted'>" + __("Menampilkan {0} dari {1}. Gunakan tautan 'Lihat semua' untuk sisanya.", [item.daftar.length, item.jumlah]) + "</div>";
                    }
                }
                html += "</div>";
            });
            const dlg = new frappe.ui.Dialog({
                title: __("Belum siap difinalkan"),
                size: "large",
                fields: [{ fieldtype: "HTML", fieldname: "isi" }],
            });
            dlg.fields_dict.isi.$wrapper.html(html);
            dlg.$wrapper.on("click", ".hpp-lihat", (e) => {
                e.preventDefault();
                const t = tautan[parseInt($(e.currentTarget).attr("data-i"), 10)];
                dlg.hide();
                frappe.set_route("List", t.doctype, t.filters);
            });
            dlg.$wrapper.on("click", ".hpp-gaji", (e) => {
                e.preventDefault();
                const he = $(e.currentTarget).attr("data-he");
                dlg.hide();
                frappe.new_doc("HRIS Employee Pay", { employee: he });
            });
            dlg.show();
        },
    });
}

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

        frm.add_custom_button(__("Periksa Kesiapan"), () => hppTampilkanKesiapan(frm));
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
