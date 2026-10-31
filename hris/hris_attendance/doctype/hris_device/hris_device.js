frappe.provide("hris.audit");
frappe.provide("hris.device");

hris.device.PULL_ROLES = ["HRIS HR Admin", "HRIS Manager", "System Manager"];
hris.device.PULL_API = "hris.hris_attendance.services.pull_device.";

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
        const connectable = !frm.is_new() && frm.doc.ip_address && frm.doc.port;
        if (connectable) {
            frm.add_custom_button(__("Ambil Info dari Mesin"), () =>
                hris.device.ensureSaved(frm, () => hris.device.fetchInfo(frm))
            );
        }
        if (connectable && frm.doc.use_pull && frm.doc.is_active && hris.device.canPull()) {
            frm.add_custom_button(__("Tarik Log"), () =>
                hris.device.ensureSaved(frm, () => hris.device.openPullDialog(frm))
            );
            frm.add_custom_button(__("Status Tarikan"), () => hris.device.showStatus(frm));
        }
    },
});

hris.device.canPull = function () {
    return hris.device.PULL_ROLES.some((role) => frappe.user.has_role(role));
};

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

// ------------------------------------------------------------ Ambil Info

hris.device.fetchInfo = function (frm) {
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

// ------------------------------------------------------------ Tarik Log

hris.device.openPullDialog = function (frm) {
    const lastPull = frm.doc.last_pull_at ? frappe.datetime.str_to_user(frm.doc.last_pull_at) : __("belum pernah");

    const d = new frappe.ui.Dialog({
        title: __("Tarik Log dari {0}", [frm.doc.name]),
        fields: [
            {
                fieldname: "mode",
                fieldtype: "Select",
                label: __("Mode"),
                options: ["Otomatis", "Rentang Tanggal"],
                default: "Otomatis",
                reqd: 1,
            },
            {
                fieldname: "auto_info",
                fieldtype: "HTML",
                depends_on: "eval:doc.mode=='Otomatis'",
                options:
                    "<p class='text-muted'>" +
                    __("Menarik sejak 1 hari sebelum tarikan terakhir ({0}). Mode ini memajukan Last Pull At.", [lastPull]) +
                    "</p>",
            },
            {
                fieldname: "date_from",
                fieldtype: "Date",
                label: __("Dari Tanggal"),
                depends_on: "eval:doc.mode=='Rentang Tanggal'",
            },
            {
                fieldname: "date_to",
                fieldtype: "Date",
                label: __("Sampai Tanggal"),
                depends_on: "eval:doc.mode=='Rentang Tanggal'",
            },
            {
                fieldname: "range_info",
                fieldtype: "HTML",
                depends_on: "eval:doc.mode=='Rentang Tanggal'",
                options:
                    "<p class='text-muted'>" +
                    __("Dua tanggal wajib diisi. Mode ini tidak memajukan Last Pull At. Aman diulang: data yang sudah ada tidak digandakan.") +
                    "</p>",
            },
            {
                fieldname: "check_btn",
                fieldtype: "Button",
                label: __("Cek Dulu (tidak menyimpan)"),
                click: () => hris.device.runCheck(d),
            },
            { fieldname: "result", fieldtype: "HTML" },
        ],
        primary_action_label: __("Tarik Sekarang"),
        primary_action: () => hris.device.runPull(frm, d),
    });
    d.frm_name = frm.doc.name;
    d.show();
};

hris.device.readArgs = function (d) {
    const v = d.get_values();
    if (!v) {
        return null;
    }
    if (v.mode !== "Rentang Tanggal") {
        return { device_name: d.frm_name, date_from: null, date_to: null };
    }
    if (!v.date_from || !v.date_to) {
        frappe.msgprint(__("Isi Dari Tanggal dan Sampai Tanggal."));
        return null;
    }
    if (v.date_to < v.date_from) {
        frappe.msgprint(__("Sampai Tanggal tidak boleh lebih awal dari Dari Tanggal."));
        return null;
    }
    if (v.date_to > frappe.datetime.get_today()) {
        frappe.msgprint(__("Sampai Tanggal tidak boleh melewati hari ini."));
        return null;
    }
    return { device_name: d.frm_name, date_from: v.date_from, date_to: v.date_to };
};

hris.device.runCheck = function (d) {
    const args = hris.device.readArgs(d);
    if (!args) {
        return;
    }
    d.fields_dict.result.$wrapper.html("");
    frappe
        .call({
            method: hris.device.PULL_API + "check_pull",
            args: args,
            freeze: true,
            freeze_message: __("Menghubungi mesin dan membaca log (bisa beberapa detik)..."),
        })
        .then((r) => {
            const m = r.message || {};
            const esc = frappe.utils.escape_html;
            const row = (k, v) => "<tr><td>" + esc(__(k)) + "</td><td><b>" + esc(String(v)) + "</b></td></tr>";
            let html =
                "<table class='table table-bordered table-sm'>" +
                row("Mesin merespons", m.mesin_merespons ? __("Ya") : __("Tidak")) +
                row("Serial cocok", m.serial_cocok ? __("Ya") : __("Tidak")) +
                row("Rentang", (m.dari_tanggal || "-") + " s/d " + (m.sampai_tanggal || __("sekarang"))) +
                row("Total punch di mesin", m.total_punch_di_mesin) +
                row("Punch dalam rentang", m.punch_dalam_rentang) +
                row("Akan masuk sebagai baru", m.akan_masuk_sebagai_baru) +
                row("Sudah ada di Raw Log", m.sudah_ada_di_raw_log) +
                row("ID pengguna unik", m.user_id_unik) +
                row("Punch terbaru dalam rentang", m.waktu_terbaru || "-") +
                "</table>";
            if (m.masalah && m.masalah.length) {
                html +=
                    "<div class='text-danger'><b>" + __("Perlu diperbaiki sebelum menarik:") + "</b><ul>" +
                    m.masalah.map((x) => "<li>" + esc(x) + "</li>").join("") +
                    "</ul></div>";
            } else {
                html += "<div class='text-success'><b>" + __("Siap ditarik.") + "</b></div>";
            }
            d.fields_dict.result.$wrapper.html(html);
        });
};

hris.device.runPull = function (frm, d) {
    const args = hris.device.readArgs(d);
    if (!args) {
        return;
    }
    const btn = d.get_primary_btn();
    btn.prop("disabled", true);
    frappe
        .call({ method: hris.device.PULL_API + "enqueue_pull", args: args })
        .then((r) => {
            const m = r.message || {};
            if (m.queued) {
                d.hide();
                hris.device.showStatus(frm);
            } else {
                btn.prop("disabled", false);
                frappe.msgprint(m.message || __("Tarikan tidak diantrekan."));
            }
        })
        .catch(() => btn.prop("disabled", false));
};

// ------------------------------------------------------------ Status Tarikan

hris.device.renderStatus = function (body, st) {
    // Kembalikan true bila status sudah final (tidak perlu polling lagi).
    const esc = frappe.utils.escape_html;
    const ago = (s) => (s < 90 ? s + " " + __("detik") : Math.round(s / 60) + " " + __("menit"));

    if (!st || !st.status) {
        body.html("<p class='text-muted'>" + __("Tidak ada tarikan tercatat dalam 1 jam terakhir.") + "</p>");
        return true;
    }
    const detik = st.detik || 0;

    if (st.status === "Antre" || st.status === "Berjalan") {
        let html = "<p><b>" + esc(__(st.status)) + "</b> (" + ago(detik) + ")</p>";
        if (st.status === "Antre") {
            html += "<p class='text-muted'>" + __("Menunggu worker mengambil job.") + "</p>";
            if (detik > 60) {
                html += "<p class='text-danger'>" + __("Sudah lebih dari 60 detik belum diambil. Periksa apakah bench worker berjalan.") + "</p>";
            }
        } else {
            html +=
                "<p class='text-muted'>" +
                __("Membaca seluruh log mesin lalu menyimpan. Dialog ini boleh ditutup; hasil bisa dilihat lagi lewat tombol Status Tarikan.") +
                "</p>";
        }
        body.html(html);
        return false;
    }

    if (st.status === "Gagal") {
        body.html(
            "<p class='text-danger'><b>" + __("Gagal") + "</b> (" + ago(detik) + " " + __("lalu") + ")</p>" +
            "<p>" + esc(String(st.message || "")) + "</p>"
        );
        return true;
    }

    const r = st.result || {};
    const row = (k, v) => "<tr><td>" + esc(__(k)) + "</td><td><b>" + esc(String(v)) + "</b></td></tr>";
    let html =
        "<p class='text-success'><b>" + __("Selesai") + "</b> (" + ago(detik) + " " + __("lalu") + ")</p>" +
        "<table class='table table-bordered table-sm'>" +
        row("Rentang", (r.dari_tanggal || "-") + " s/d " + (r.sampai_tanggal || __("sekarang"))) +
        row("Punch dalam rentang", r.punch_dalam_rentang) +
        row("Baru", r.baru || 0) +
        row("Sudah ada", r.sudah_ada || 0) +
        row("Gagal", r.gagal || 0) +
        row("Last Pull At diperbarui", r.last_pull_at_diperbarui ? __("Ya") : __("Tidak")) +
        "</table>";
    if (r.contoh_error && r.contoh_error.length) {
        html += "<p class='text-danger'>" + r.contoh_error.slice(0, 3).map((x) => esc(String(x))).join("<br>") + "</p>";
    }
    body.html(html);
    return true;
};

hris.device.showStatus = function (frm) {
    const name = frm.doc.name;
    let stopped = false;
    let ticks = 0;

    const d = new frappe.ui.Dialog({
        title: __("Status Tarikan: {0}", [name]),
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

    const tick = () => {
        if (stopped) {
            return;
        }
        frappe
            .call({ method: hris.device.PULL_API + "pull_status", args: { device_name: name } })
            .then((r) => {
                const isFinal = hris.device.renderStatus(body, r.message || {});
                if (isFinal) {
                    stopped = true;
                    if (r.message && r.message.status === "Selesai" && !frm.is_dirty()) {
                        frm.reload_doc();
                    }
                    return;
                }
                ticks += 1;
                if (ticks > 900) {
                    body.html("<p class='text-danger'>" + __("Pemantauan dihentikan setelah 30 menit. Cek tab Activity atau Error Log.") + "</p>");
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
