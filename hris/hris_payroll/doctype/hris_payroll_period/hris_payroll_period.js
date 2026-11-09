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
                        html += "<div class='text-muted'>" + __("Menampilkan {0} dari {1}. Selesaikan sebagian, lalu periksa kesiapan lagi untuk melihat sisanya.", [item.daftar.length, item.jumlah]) + "</div>";
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

const HPS_SVC = "hris.hris_payroll.services.payroll_slip.";

function hppHasilSlip(h) {
    const esc = frappe.utils.escape_html;
    if (h.state === "Gagal" || h.state === "Tidak Ada") {
        frappe.msgprint({ title: __("Proses slip gagal"), message: esc(h.message || __("Proses berhenti. Lihat Error Log.")), indicator: "red" });
        return;
    }
    let html = "<div>" + __("Dibuat: {0}, diperbarui: {1}, dilewati: {2}, gagal: {3}.", [h.dibuat || 0, h.diperbarui || 0, h.dilewati || 0, h.gagal || 0]) + "</div>";
    if (h.message) {
        html += "<div class='text-muted'>" + esc(h.message) + "</div>";
    }
    const alasan = h.alasan || {};
    const kunci = Object.keys(alasan);
    if (kunci.length) {
        html += "<div style='margin-top:10px'><b>" + __("Dilewati, beserta penyebabnya") + "</b></div>";
        html += "<table class='table table-bordered table-sm'><tbody>";
        kunci.forEach((k) => {
            html += "<tr><td>" + alasan[k].jumlah + "</td><td>" + esc(k) + "</td><td class='text-muted'>" + esc((alasan[k].contoh || []).join(", ")) + "</td></tr>";
        });
        html += "</tbody></table>";
    }
    if ((h.errors || []).length) {
        html += "<div style='margin-top:10px'><b>" + __("Galat") + "</b></div><div class='text-muted'>" + esc(h.errors.join("; ")) + "</div>";
    }
    frappe.msgprint({ title: __("Hasil Buat Slip"), message: html, indicator: h.gagal ? "orange" : "green" });
}

function hppPantauSlip(frm, runId) {
    const tick = () => {
        frappe.call({
            method: HPS_SVC + "get_status",
            args: { run_id: runId },
            callback(r) {
                const s = r.message || {};
                if (s.state === "Selesai" || s.state === "Gagal" || s.state === "Tidak Ada") {
                    frappe.hide_progress();
                    hppHasilSlip(s);
                    frm.reload_doc();
                    return;
                }
                frappe.show_progress(__("Menghitung slip"), s.done || 0, s.total || 1, s.warning || "");
                setTimeout(tick, 2500);
            },
        });
    };
    tick();
}

function hppBuatSlip(frm) {
    const dlg = new frappe.ui.Dialog({
        title: __("Buat Slip Gaji"),
        fields: [
            { fieldname: "cakupan", label: __("Cakupan"), fieldtype: "Select", options: "Semua\nKaryawan\nDepartment\nGrup", default: "Semua", reqd: 1 },
            { fieldname: "employee", label: __("Karyawan"), fieldtype: "Link", options: "HRIS Employee", depends_on: "eval:doc.cakupan=='Karyawan'", mandatory_depends_on: "eval:doc.cakupan=='Karyawan'" },
            { fieldname: "department", label: __("Department"), fieldtype: "Link", options: "Department", depends_on: "eval:doc.cakupan=='Department'", mandatory_depends_on: "eval:doc.cakupan=='Department'" },
            { fieldname: "employee_group", label: __("Grup Karyawan"), fieldtype: "Link", options: "HRIS Employee Group", depends_on: "eval:doc.cakupan=='Grup'", mandatory_depends_on: "eval:doc.cakupan=='Grup'" },
            { fieldtype: "HTML", fieldname: "info", options: "<div class='text-muted'>" + __("Slip yang sudah ada dihitung ulang (komponen Manual tetap). Karyawan yang belum bisa dihitung dilewati dan dijelaskan di hasil.") + "</div>" },
        ],
        primary_action_label: __("Buat"),
        primary_action(v) {
            dlg.hide();
            frappe.call({
                method: HPS_SVC + "buat_slip",
                args: { periode: frm.doc.name, cakupan: v.cakupan, employee: v.employee, department: v.department, employee_group: v.employee_group },
                freeze: true,
                freeze_message: __("Menghitung slip..."),
                callback(r) {
                    const h = r.message || {};
                    if (h.mode === "background") {
                        frappe.show_alert({ message: __("{0} karyawan diproses di background.", [h.total]), indicator: "blue" });
                        hppPantauSlip(frm, h.run_id);
                    } else {
                        hppHasilSlip(h);
                    }
                },
            });
        },
    });
    dlg.show();
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
        frm.add_custom_button(__("Lihat Slip"), () => frappe.set_route("List", "HRIS Payroll Slip", { payroll_period: frm.doc.name }));
        if (frm.doc.status === "Draft" && adalah("HRIS Payroll Admin", "HRIS Payroll Manager")) {
            frm.add_custom_button(__("Buat Slip"), () => hppBuatSlip(frm), __("Aksi"));
        }
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
