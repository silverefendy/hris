frappe.pages["konsol-mesin"].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("Konsol Mesin"),
        single_column: true,
    });
    const esc = frappe.utils.escape_html;
    const $body = $("<div class='konsol-mesin'></div>").appendTo(page.main);
    let devices = [];

    const FIELDS = [
        "name", "company", "device_type", "is_active", "use_pull", "use_agent",
        "last_pull_at", "last_agent_at",
    ];

    const fmt = (v) => (v ? frappe.datetime.str_to_user(v) : "-");
    const ago = (s) => (s < 90 ? s + " " + __("detik") : Math.round(s / 60) + " " + __("menit"));

    const statusText = (st) => {
        if (!st || !st.status) {
            return "<span class='text-muted'>-</span>";
        }
        const detik = st.detik || 0;
        if (st.status === "Selesai") {
            const r = st.result || {};
            return "<span class='text-success'>" + __("Selesai") + "</span> " +
                "<span class='text-muted'>(" + ago(detik) + " " + __("lalu") + ", " + __("baru") + " " + (r.baru || 0) + ")</span>";
        }
        if (st.status === "Gagal") {
            return "<span class='text-danger'>" + __("Gagal") + "</span> <span class='text-muted'>(" + ago(detik) + " " + __("lalu") + ")</span>";
        }
        return "<b>" + esc(__(st.status)) + "</b> <span class='text-muted'>(" + ago(detik) + ")</span>";
    };

    const actionsCell = (d) => {
        const n = esc(d.name);
        if (!d.is_active) {
            return "<span class='text-muted'>" + __("Tidak aktif") + "</span>";
        }
        if (d.use_pull) {
            return (
                "<button class='btn btn-xs btn-primary km-pull' data-name='" + n + "'>" + __("Tarik Log") + "</button> " +
                "<button class='btn btn-xs btn-default km-info' data-name='" + n + "'>" + __("Cek Koneksi") + "</button> " +
                "<button class='btn btn-xs btn-default km-status' data-name='" + n + "'>" + __("Status") + "</button>"
            );
        }
        if (d.use_agent) {
            return "<span class='text-muted'>" + __("via agen") + "</span>";
        }
        return "<span class='text-muted'>-</span>";
    };

    const render = () => {
        if (!devices.length) {
            $body.html("<p class='text-muted'>" + __("Belum ada mesin.") + "</p>");
            return;
        }
        let html =
            "<div class='table-responsive'><table class='table table-bordered'>" +
            "<thead><tr><th>" + __("Mesin") + "</th><th>" + __("Perusahaan") + "</th><th>" + __("Tipe") + "</th>" +
            "<th>" + __("Jalur") + "</th><th>" + __("Last Pull / Agen") + "</th><th>" + __("Status") + "</th>" +
            "<th>" + __("Aksi") + "</th></tr></thead><tbody>";
        devices.forEach((d) => {
            const jalur = [d.use_pull ? "Pull" : "", d.use_agent ? "Agen" : ""].filter(Boolean).join(" + ") || "-";
            const last = d.use_pull ? fmt(d.last_pull_at) : d.use_agent ? fmt(d.last_agent_at) : "-";
            html +=
                "<tr><td><a href='/desk/hris-device/" + encodeURIComponent(d.name) + "'><b>" + esc(d.name) + "</b></a></td>" +
                "<td>" + esc(d.company || "") + "</td><td>" + esc(d.device_type || "") + "</td>" +
                "<td>" + esc(jalur) + "</td><td>" + esc(last) + "</td>" +
                "<td class='km-status-cell' data-name='" + esc(d.name) + "'>" +
                (d.use_pull && d.is_active ? "<span class='text-muted'>...</span>" : "<span class='text-muted'>-</span>") + "</td>" +
                "<td>" + actionsCell(d) + "</td></tr>";
        });
        html += "</tbody></table></div>";
        $body.html(html);
    };

    const loadStatuses = () => {
        devices.filter((d) => d.use_pull && d.is_active).forEach((d) => {
            frappe
                .call({ method: "hris.hris_attendance.services.pull_device.pull_status", args: { device_name: d.name } })
                .then((r) => {
                    $body
                        .find(".km-status-cell")
                        .filter(function () { return $(this).attr("data-name") === d.name; })
                        .html(statusText(r.message || {}));
                });
        });
    };

    const load = () => {
        $body.html("<p class='text-muted'>" + __("Memuat...") + "</p>");
        frappe
            .call({
                method: "frappe.client.get_list",
                args: { doctype: "HRIS Device", fields: FIELDS, order_by: "name asc", limit_page_length: 100 },
            })
            .then((r) => {
                devices = r.message || [];
                render();
                loadStatuses();
            });
    };

    const find = (name) => devices.find((d) => d.name === name);
    const ready = () => {
        if (!hris.device || !hris.device.openPullDialog) {
            frappe.msgprint(__("Fungsi dialog belum termuat. Muat ulang browser dengan Ctrl+Shift+R."));
            return false;
        }
        return true;
    };

    $body.on("click", ".km-pull", function () {
        if (!ready()) { return; }
        const d = find($(this).attr("data-name"));
        hris.device.openPullDialog(d.name, d.last_pull_at, () => load());
    });
    $body.on("click", ".km-info", function () {
        if (!ready()) { return; }
        hris.device.fetchInfo($(this).attr("data-name"));
    });
    $body.on("click", ".km-status", function () {
        if (!ready()) { return; }
        hris.device.showStatus($(this).attr("data-name"), () => load());
    });

    page.set_secondary_action(__("Muat Ulang"), load);
    load();
};
