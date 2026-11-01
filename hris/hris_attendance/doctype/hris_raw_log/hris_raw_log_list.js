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

// ---- HRIS_RAWLOG_REMATCH: Cocokkan Ulang baris Tidak Cocok ----
hris.rawlog.REMATCH_ROLES = ["HRIS HR Admin", "HRIS Manager", "System Manager"];
hris.rawlog.REMATCH_API = "hris.hris_attendance.services.rematch_raw_log.";

(function () {
    const settings = (frappe.listview_settings["HRIS Raw Log"] = frappe.listview_settings["HRIS Raw Log"] || {});
    const previous = settings.onload;
    settings.onload = function (listview) {
        if (previous) {
            previous.call(this, listview);
        }
        if (hris.rawlog.REMATCH_ROLES.some((role) => frappe.user.has_role(role))) {
            listview.page.add_inner_button(__("Cocokkan Ulang"), () => hris.rawlog.openRematch(listview));
        }
    };
})();

hris.rawlog.openRematch = function (listview) {
    const d = new frappe.ui.Dialog({
        title: __("Cocokkan Ulang Raw Log"),
        fields: [
            {
                fieldname: "info",
                fieldtype: "HTML",
                options:
                    "<p>" +
                    __("Hanya menyentuh baris berstatus Tidak Cocok. Klik Cek Dulu untuk melihat ID mana yang bisa dicocokkan dan mana yang bermasalah.") +
                    "</p>",
            },
            {
                fieldname: "device_user_id",
                fieldtype: "Data",
                label: __("ID Mesin (kosongkan untuk semua)"),
                onchange: () => (d._ok = false),
            },
            { fieldname: "check_btn", fieldtype: "Button", label: __("Cek Dulu (tidak mengubah)"), click: () => hris.rawlog.runRematchCheck(d) },
            { fieldname: "result", fieldtype: "HTML" },
        ],
        primary_action_label: __("Cocokkan"),
        primary_action: () => hris.rawlog.runRematch(d, listview),
    });
    d._ok = false;
    d.show();
};

hris.rawlog.runRematchCheck = function (d) {
    d._ok = false;
    d.fields_dict.result.$wrapper.html("");
    frappe
        .call({
            method: hris.rawlog.REMATCH_API + "check_rematch",
            args: { device_user_id: d.get_value("device_user_id") || "" },
            freeze: true,
            freeze_message: __("Menghitung..."),
        })
        .then((r) => {
            const m = r.message || {};
            const esc = frappe.utils.escape_html;
            const rows = (m.ids || []).map((x) => {
                const ok = x.kategori === "Bisa dicocokkan";
                return (
                    "<tr><td>" + esc(String(x.id)) + "</td><td>" + esc(String(x.n)) + "</td><td>" +
                    esc(x.dari + " s/d " + x.sampai) + "</td><td class='" + (ok ? "text-success" : "text-danger") + "'><b>" +
                    esc(x.kategori) + "</b></td><td>" + esc(x.employee || "-") + "</td></tr>"
                );
            });
            let html =
                "<p>" + esc(__("Baris Tidak Cocok tanpa Employee")) + ": <b>" + esc(String(m.total || 0)) + "</b> | " +
                esc(__("bisa dicocokkan")) + ": <b>" + esc(String(m.bisa_baris || 0)) + "</b> | " +
                esc(__("perlu tindakan")) + ": <b>" + esc(String(m.tindakan_baris || 0)) + "</b></p>";
            if (rows.length) {
                html +=
                    "<table class='table table-bordered table-sm'><thead><tr><th>" +
                    [__("ID Mesin"), __("Baris"), __("Rentang"), __("Status"), __("Employee")].map(esc).join("</th><th>") +
                    "</th></tr></thead><tbody>" + rows.join("") + "</tbody></table>";
            }
            if (m.terpotong) {
                html += "<p class='text-muted'>" + esc(__("Daftar dipotong 100 ID pertama; isi ID Mesin untuk menyaring.")) + "</p>";
            }
            if (m.bisa_baris > 0) {
                d._ok = true;
                html += "<div class='text-success'><b>" + esc(__("Klik Cocokkan (maksimal 500 baris per klik).")) + "</b></div>";
            } else {
                html += "<div class='text-danger'><b>" + esc(__("Tidak ada yang bisa dicocokkan sekarang. Perbaiki ID berstatus merah dulu, lalu Cek Dulu lagi.")) + "</b></div>";
            }
            d.fields_dict.result.$wrapper.html(html);
        });
};

hris.rawlog.runRematch = function (d, listview) {
    if (!d._ok) {
        frappe.msgprint(__("Klik Cek Dulu lebih dulu (dan ulangi bila ID mesin berubah)."));
        return;
    }
    const btn = d.get_primary_btn();
    btn.prop("disabled", true);
    frappe
        .call({
            method: hris.rawlog.REMATCH_API + "run_rematch",
            args: { device_user_id: d.get_value("device_user_id") || "" },
            freeze: true,
            freeze_message: __("Mencocokkan..."),
        })
        .then((r) => {
            const m = r.message || {};
            const esc = frappe.utils.escape_html;
            d.hide();
            let html = "<p>" + esc(__("Dicocokkan")) + ": <b>" + esc(String(m.dicocokkan || 0)) + "</b> " + esc(__("baris")) + "</p>";
            if ((m.ringkas || []).length) {
                html +=
                    "<table class='table table-bordered table-sm'><thead><tr><th>" +
                    [__("ID Mesin"), __("Employee"), __("Baris"), __("Rentang")].map(esc).join("</th><th>") +
                    "</th></tr></thead><tbody>" +
                    m.ringkas.map((x) =>
                        "<tr><td>" + esc(String(x.id)) + "</td><td>" + esc(x.employee) + "</td><td>" + esc(String(x.jumlah)) +
                        "</td><td>" + esc(x.dari + " s/d " + x.sampai) + "</td></tr>"
                    ).join("") + "</tbody></table>";
            }
            if ((m.gagal || []).length) {
                html += "<div class='text-danger'><b>" + esc(__("Gagal")) + ":</b><ul>" + m.gagal.map((x) => "<li>" + esc(x) + "</li>").join("") + "</ul></div>";
            }
            html +=
                "<p>" + esc(__("Sisa bisa dicocokkan")) + ": <b>" + esc(String(m.sisa_bisa || 0)) + "</b> | " +
                esc(__("sisa perlu tindakan")) + ": <b>" + esc(String(m.sisa_tindakan || 0)) + "</b></p>";
            frappe.msgprint({
                title: __("Hasil Cocokkan Ulang"),
                message: html,
                indicator: (m.gagal || []).length ? "orange" : "green",
            });
            listview.refresh();
        })
        .catch(() => btn.prop("disabled", false));
};
