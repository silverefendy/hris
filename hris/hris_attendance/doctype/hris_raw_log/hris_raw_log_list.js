frappe.listview_settings["HRIS Raw Log"] = {
    add_fields: ["review_status", "punch_role"],
    get_indicator(doc) {
        if (doc.punch_role === "Diabaikan Otomatis") {
            return [__("Diabaikan Otomatis"), "darkgrey", "punch_role,=,Diabaikan Otomatis"];
        }
        const colors = {
            "Menunggu": "gray",
            "Tidak Cocok": "red",
            "Disetujui": "green",
            "Ditolak": "purple",
            "Terkirim": "green",
        };
        const color = colors[doc.review_status] || "gray";
        return [__(doc.review_status), color, "review_status,=," + doc.review_status];
    },
};

// ---- HRIS_RAWLOG_DELETE: hapus Raw Log per mesin dan rentang tanggal ----
frappe.provide("hris.rawlog");
hris.rawlog.DELETE_ROLES = ["HRIS Manager", "System Manager"];
hris.rawlog.API = "hris.hris_attendance.services.delete_raw_log.";

(function () {
    const settings = (frappe.listview_settings["HRIS Raw Log"] = frappe.listview_settings["HRIS Raw Log"] || {});
    const previous = settings.onload;
    settings.onload = function (listview) {
        if (previous) {
            previous.call(this, listview);
        }
        if (hris.rawlog.DELETE_ROLES.some((role) => frappe.user.has_role(role))) {
            listview.page.add_inner_button(__("Hapus Log per Rentang"), () => hris.rawlog.openDialog(listview));
        }
    };
})();

hris.rawlog.openDialog = function (listview) {
    const d = new frappe.ui.Dialog({
        title: __("Hapus Raw Log per Rentang"),
        fields: [
            {
                fieldname: "info",
                fieldtype: "HTML",
                options:
                    "<p class='text-danger'><b>" +
                    __("Ini menghapus data di HRIS, bukan di mesin absensi.") +
                    "</b> " +
                    __("Data bisa ditarik ulang selama log masih tersimpan di mesin. Last Pull At tidak berubah.") +
                    "</p>",
            },
            { fieldname: "device", fieldtype: "Link", options: "HRIS Device", label: __("Mesin"), reqd: 1, onchange: () => (d._ok = false) },
            { fieldname: "date_from", fieldtype: "Date", label: __("Dari Tanggal"), reqd: 1, onchange: () => (d._ok = false) },
            { fieldname: "date_to", fieldtype: "Date", label: __("Sampai Tanggal"), reqd: 1, onchange: () => (d._ok = false) },
            { fieldname: "check_btn", fieldtype: "Button", label: __("Cek Dulu (tidak menghapus)"), click: () => hris.rawlog.runCheck(d) },
            { fieldname: "result", fieldtype: "HTML" },
            { fieldname: "confirm_name", fieldtype: "Data", label: __("Ketik nama mesin untuk menyetujui") },
        ],
        primary_action_label: __("Hapus"),
        primary_action: () => hris.rawlog.runDelete(d, listview),
    });
    d._ok = false;
    d.show();
};

hris.rawlog.args = function (d) {
    const v = d.get_values();
    if (!v) {
        return null;
    }
    if (v.date_to < v.date_from) {
        frappe.msgprint(__("Sampai Tanggal tidak boleh lebih awal dari Dari Tanggal."));
        return null;
    }
    return { device_name: v.device, date_from: v.date_from, date_to: v.date_to };
};

hris.rawlog.runCheck = function (d) {
    const args = hris.rawlog.args(d);
    if (!args) {
        return;
    }
    d._ok = false;
    d.fields_dict.result.$wrapper.html("");
    frappe
        .call({ method: hris.rawlog.API + "check_delete", args: args, freeze: true, freeze_message: __("Menghitung...") })
        .then((r) => {
            const m = r.message || {};
            const esc = frappe.utils.escape_html;
            const row = (k, v) => "<tr><td>" + esc(__(k)) + "</td><td><b>" + esc(String(v)) + "</b></td></tr>";
            let html =
                "<table class='table table-bordered table-sm'>" +
                row("Mesin", m.mesin) +
                row("Rentang", m.dari_tanggal + " s/d " + m.sampai_tanggal) +
                row("Raw Log yang akan dihapus", m.total) +
                Object.keys(m.per_status || {}).map((k) => row("Status: " + k, m.per_status[k])).join("") +
                row("Dipakai Working Hour", m.dipakai_working_hour) +
                "</table>";
            if (m.masalah && m.masalah.length) {
                html += "<div class='text-danger'><ul>" + m.masalah.map((x) => "<li>" + esc(x) + "</li>").join("") + "</ul></div>";
            } else {
                html += "<div class='text-success'><b>" + __("Boleh dihapus. Ketik nama mesin lalu klik Hapus.") + "</b></div>";
                d._ok = true;
            }
            d.fields_dict.result.$wrapper.html(html);
        });
};

hris.rawlog.runDelete = function (d, listview) {
    const args = hris.rawlog.args(d);
    if (!args) {
        return;
    }
    if (!d._ok) {
        frappe.msgprint(__("Klik Cek Dulu lebih dulu (dan ulangi bila mesin atau tanggal berubah)."));
        return;
    }
    const confirmName = (d.get_value("confirm_name") || "").trim();
    if (confirmName !== args.device_name) {
        frappe.msgprint(__("Nama mesin pada konfirmasi tidak cocok."));
        return;
    }
    const btn = d.get_primary_btn();
    btn.prop("disabled", true);
    args.confirm_name = confirmName;
    frappe
        .call({ method: hris.rawlog.API + "enqueue_delete", args: args })
        .then((r) => {
            const m = r.message || {};
            if (m.queued) {
                d.hide();
                hris.rawlog.showStatus(args.device_name, listview);
            } else {
                btn.prop("disabled", false);
                frappe.msgprint(m.message || __("Penghapusan tidak diantrekan."));
            }
        })
        .catch(() => btn.prop("disabled", false));
};

hris.rawlog.showStatus = function (name, listview) {
    let stopped = false;
    let ticks = 0;
    const esc = frappe.utils.escape_html;
    const d = new frappe.ui.Dialog({
        title: __("Status Hapus Raw Log: {0}", [name]),
        fields: [{ fieldname: "body", fieldtype: "HTML" }],
        primary_action_label: __("Tutup"),
        primary_action: () => d.hide(),
    });
    d.onhide = () => {
        stopped = true;
    };
    d.show();
    const body = d.fields_dict.body.$wrapper;
    body.html("<p class='text-muted'>" + __("Memeriksa status...") + "</p>");

    const render = (st) => {
        if (!st || !st.status) {
            body.html("<p class='text-muted'>" + __("Tidak ada catatan dalam 1 jam terakhir.") + "</p>");
            return true;
        }
        const detik = st.detik || 0;
        if (st.status === "Antre" || st.status === "Berjalan") {
            let html = "<p><b>" + esc(__(st.status)) + "</b> (" + detik + " " + __("detik") + ")</p>";
            if (st.status === "Berjalan") {
                html += "<p>" + __("Terhapus") + ": <b>" + (st.terhapus || 0) + " / " + (st.total || 0) + "</b></p>";
            } else if (detik > 60) {
                html += "<p class='text-danger'>" + __("Belum diambil lebih dari 60 detik. Periksa bench worker.") + "</p>";
            }
            body.html(html);
            return false;
        }
        if (st.status === "Gagal") {
            body.html("<p class='text-danger'><b>" + __("Gagal") + "</b></p><p>" + esc(String(st.message || "")) + "</p>");
            return true;
        }
        body.html(
            "<p class='text-success'><b>" + __("Selesai") + "</b></p>" +
            "<p>" + __("Rentang") + ": " + esc((st.dari_tanggal || "-") + " s/d " + (st.sampai_tanggal || "-")) + "<br>" +
            __("Dihapus") + ": <b>" + (st.terhapus || 0) + "</b> " + __("baris di HRIS (mesin tidak disentuh).") + "</p>"
        );
        return true;
    };

    const tick = () => {
        if (stopped) {
            return;
        }
        frappe
            .call({ method: hris.rawlog.API + "delete_status", args: { device_name: name } })
            .then((r) => {
                const isFinal = render(r.message || {});
                if (isFinal) {
                    stopped = true;
                    listview.refresh();
                    return;
                }
                ticks += 1;
                if (ticks > 1800) {
                    body.html("<p class='text-danger'>" + __("Pemantauan dihentikan. Cek Error Log.") + "</p>");
                    return;
                }
                setTimeout(tick, 2000);
            })
            .catch(() => {
                stopped = true;
            });
    };
    tick();
};
