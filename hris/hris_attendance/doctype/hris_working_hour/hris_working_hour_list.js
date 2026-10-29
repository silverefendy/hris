frappe.provide("hris.wh");

hris.wh.API = "hris.hris_attendance.services.working_hour_batch.";

hris.wh.summary_html = function (r) {
    const esc = frappe.utils.escape_html;
    let html = `<table class="table table-bordered table-sm">
        <tr><td>${__("Total karyawan-hari")}</td><td>${r.total || 0}</td></tr>
        <tr><td>${__("Berhasil dihitung")}</td><td>${r.ok || 0}</td></tr>
        <tr><td>${__("Dilewati (sudah ditinjau atau disesuaikan HRD)")}</td><td>${r.skipped_reviewed || 0}</td></tr>
        <tr><td>${__("Dilewati (sebelum tanggal masuk karyawan)")}</td><td>${r.skipped_joining || 0}</td></tr>
        <tr><td>${__("Gagal")}</td><td class="${r.failed ? "text-danger" : ""}">${r.failed || 0}</td></tr>
    </table>`;
    if (r.errors && r.errors.length) {
        html += `<div class="text-danger"><b>${__("Yang gagal")}:</b><ul>${r.errors
            .map((e) => `<li>${esc(e)}</li>`)
            .join("")}</ul><p>${__("Detail lengkap ada di Error Log.")}</p></div>`;
    }
    return html;
};

hris.wh.status_html = function (s) {
    const esc = frappe.utils.escape_html;
    const colors = { Antre: "orange", Berjalan: "blue", Selesai: "green", Gagal: "red", "Tidak Ada": "gray" };
    const state = s.state || "Tidak Ada";
    let html = `<p><span class="indicator-pill ${colors[state] || "gray"}">${esc(state)}</span></p>`;
    if (s.message) {
        html += `<p>${esc(s.message)}</p>`;
    }
    if (s.total) {
        const pct = Math.min(100, Math.round(((s.done || 0) / s.total) * 100));
        html += `<div class="progress" style="height: 18px"><div class="progress-bar" style="width: ${pct}%">${pct}%</div></div>
            <p class="text-muted">${__("{0} dari {1} karyawan-hari", [s.done || 0, s.total])} | ${__("diperbarui {0} detik lalu", [s.age_seconds || 0])}</p>`;
        html += hris.wh.summary_html(s);
    }
    if (s.warning) {
        html += `<div class="alert alert-danger">${esc(s.warning)}</div>`;
    }
    return html;
};

hris.wh.open_status = function (run_id) {
    const d = new frappe.ui.Dialog({
        title: __("Status Hitung Working Hour"),
        fields: [{ fieldname: "body", fieldtype: "HTML" }],
    });
    let timer = null;
    const stop = () => {
        if (timer) {
            clearInterval(timer);
            timer = null;
        }
    };
    const tick = () =>
        frappe.call({
            method: hris.wh.API + "get_recalc_status",
            args: { run_id: run_id || null },
            callback(r) {
                const s = r.message || {};
                run_id = s.run_id || run_id;
                d.fields_dict.body.$wrapper.html(hris.wh.status_html(s));
                if (!["Antre", "Berjalan"].includes(s.state)) {
                    stop();
                }
            },
            error() {
                d.fields_dict.body.$wrapper.html(
                    `<div class="alert alert-danger">${__("Gagal membaca status dari server. Server mungkin bermasalah atau koneksi terputus.")}</div>`
                );
            },
        });
    d.onhide = stop;
    d.show();
    tick();
    timer = setInterval(tick, 2000);
};

hris.wh.open_dialog = function (listview) {
    const yesterday = frappe.datetime.add_days(frappe.datetime.get_today(), -1);
    const d = new frappe.ui.Dialog({
        title: __("Hitung Working Hour"),
        fields: [
            { fieldname: "from_date", fieldtype: "Date", label: __("Dari Tanggal"), reqd: 1, default: yesterday },
            {
                fieldname: "to_date",
                fieldtype: "Date",
                label: __("Sampai Tanggal"),
                reqd: 1,
                default: yesterday,
                description: __("Paling lambat kemarin, maksimal 31 hari."),
            },
            {
                fieldname: "scope",
                fieldtype: "Select",
                label: __("Cakupan"),
                options: "Semua\nKaryawan\nDepartment\nGrup",
                default: "Semua",
                reqd: 1,
            },
            { fieldname: "employee", fieldtype: "Link", options: "Employee", label: __("Karyawan"), depends_on: "eval:doc.scope=='Karyawan'" },
            { fieldname: "department", fieldtype: "Link", options: "Department", label: __("Department"), depends_on: "eval:doc.scope=='Department'" },
            { fieldname: "employee_group", fieldtype: "Link", options: "HRIS Employee Group", label: __("Grup"), depends_on: "eval:doc.scope=='Grup'" },
            { fieldname: "company", fieldtype: "Link", options: "Company", label: __("Company (opsional)") },
            {
                fieldname: "skip_reviewed",
                fieldtype: "Check",
                label: __("Lewati baris yang sudah ditinjau atau disesuaikan HRD"),
                default: 1,
            },
        ],
        primary_action_label: __("Hitung"),
        primary_action(values) {
            d.hide();
            frappe.call({
                method: hris.wh.API + "recalculate_working_hours",
                args: values,
                freeze: true,
                freeze_message: __("Sedang menghitung..."),
                callback(r) {
                    const m = r.message || {};
                    if (m.mode === "background") {
                        hris.wh.open_status(m.run_id);
                        return;
                    }
                    frappe.msgprint({
                        title: __("Hasil Hitung"),
                        indicator: m.failed ? "red" : "green",
                        message: (m.message ? `<p>${frappe.utils.escape_html(m.message)}</p>` : "") + hris.wh.summary_html(m),
                    });
                    if (listview && listview.refresh) {
                        listview.refresh();
                    }
                },
            });
        },
    });
    d.show();
};

frappe.listview_settings["HRIS Working Hour"] = {
    onload(listview) {
        if (!frappe.user.has_role(["HRIS HR Admin", "HRIS Manager", "System Manager"])) {
            return;
        }
        listview.page.add_inner_button(__("Hitung Periode"), () => hris.wh.open_dialog(listview));
        listview.page.add_inner_button(__("Status Hitung"), () => hris.wh.open_status(null));
    },
};
