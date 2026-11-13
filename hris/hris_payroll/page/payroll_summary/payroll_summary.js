frappe.pages["payroll-summary"].on_page_load = function (wrapper) {
    const page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __("Payroll Summary"),
        single_column: true,
    });
    const esc = frappe.utils.escape_html;
    const API = "hris.hris_payroll.services.payroll_summary.ambil_data";
    const state = { halaman: 1, ukuran: 50, ready: false, data: null };
    const f = {};

    if (!$("#ps-style").length) {
        $(
            "<style id='ps-style'>" +
                ".ps-wrap table{font-size:12px}" +
                ".ps-wrap th{white-space:nowrap;background:#f5f5f5}" +
                ".ps-num{text-align:right;white-space:nowrap}" +
                ".ps-src{font-size:10px;color:#888}" +
                ".ps-janggal{background:#fdecea}" +
                ".ps-warn{background:#fff8e1}" +
                ".ps-row-janggal td:first-child{border-left:3px solid #e24c4c}" +
                ".ps-info{color:#666;margin:6px 0}" +
                ".ps-foot td{font-weight:bold;background:#fafafa}" +
                "</style>"
        ).appendTo(document.head);
    }

    const add = (df) => {
        f[df.fieldname] = page.add_field(df);
        return f[df.fieldname];
    };
    const reload = frappe.utils.debounce(() => {
        if (!state.ready) return;
        state.halaman = 1;
        load();
    }, 400);
    const toggle = () => {
        const periode = f.mode.get_value() === "Per Periode";
        f.tanggal.$wrapper.toggle(!periode);
        f.periode.$wrapper.toggle(periode);
    };

    add({ fieldname: "mode", label: __("Tampilan"), fieldtype: "Select", options: "Per Tanggal\nPer Periode", change: () => { toggle(); reload(); } });
    add({ fieldname: "tanggal", label: __("Tanggal"), fieldtype: "Date", change: reload });
    add({ fieldname: "periode", label: __("Periode Gaji"), fieldtype: "Link", options: "HRIS Payroll Period", change: reload });
    add({ fieldname: "company", label: __("Company"), fieldtype: "Link", options: "Company", change: reload });
    add({ fieldname: "department", label: __("Department"), fieldtype: "Link", options: "HRIS Department", change: reload });
    add({ fieldname: "employee_group", label: __("Grup"), fieldtype: "Link", options: "HRIS Employee Group", change: reload });
    add({ fieldname: "employee", label: __("Karyawan"), fieldtype: "Link", options: "HRIS Employee", change: reload });
    add({ fieldname: "pay_type", label: __("Jenis Gaji"), fieldtype: "Select", options: "\nBulanan\nHarian", change: reload });
    add({ fieldname: "nonaktif", label: __("Tampilkan komponen nonaktif"), fieldtype: "Check", change: reload });
    add({ fieldname: "resign", label: __("Termasuk Resign"), fieldtype: "Check", change: reload });

    f.mode.set_value("Per Tanggal");
    f.tanggal.set_value(frappe.datetime.get_today());
    toggle();

    const $body = $("<div class='ps-wrap'></div>").appendTo(page.main);

    const args = (semua) => ({
        mode: f.mode.get_value(),
        tanggal: f.tanggal.get_value(),
        periode: f.periode.get_value(),
        company: f.company.get_value(),
        department: f.department.get_value(),
        employee_group: f.employee_group.get_value(),
        employee: f.employee.get_value(),
        pay_type: f.pay_type.get_value(),
        tampilkan_nonaktif: f.nonaktif.get_value() ? 1 : 0,
        termasuk_resign: f.resign.get_value() ? 1 : 0,
        halaman: state.halaman,
        ukuran: state.ukuran,
        semua: semua ? 1 : 0,
    });

    const rp = (v) => (v === null || v === undefined ? "-" : frappe.format(v, { fieldtype: "Currency" }));

    const cell = (c) => {
        if (!c) return "<td class='text-muted'>-</td>";
        if (c.error) {
            return "<td class='ps-janggal' title='" + esc(c.error) + "'>" + __("galat") + "</td>";
        }
        const janggal = c.janggal && c.janggal.length;
        const warn = c.peringatan && c.peringatan.length;
        const cls = janggal ? "ps-janggal" : warn ? "ps-warn" : "";
        const tip = [c.dasar].concat(c.janggal || [], c.peringatan || []).filter(Boolean).join("\n");
        return (
            "<td class='ps-num " + cls + "' title='" + esc(tip) + "'>" +
            (janggal ? "&#9888; " : "") + rp(c.jumlah) +
            (c.sumber ? "<div class='ps-src'>" + esc(c.sumber) + "</div>" : "") +
            "</td>"
        );
    };

    const render = () => {
        const d = state.data;
        if (!d) return;
        let html = "";
        (d.info || []).forEach((t) => (html += "<div class='ps-info'>" + esc(t) + "</div>"));
        if (!d.komponen.length) {
            html += "<div class='ps-info'><b>" + __("Tidak ada komponen untuk ditampilkan. Aktifkan komponen di HRIS Pay Component, atau centang 'Tampilkan komponen nonaktif'.") + "</b></div>";
        }
        const periode = d.mode === "Per Periode";
        html += "<div class='table-responsive'><table class='table table-bordered table-sm'><thead><tr>" +
            "<th>" + __("Karyawan") + "</th><th>" + __("Department") + "</th><th>" + __("Grup") + "</th><th>" + __("Jenis") + "</th>" +
            "<th>" + __("Gaji Pokok") + "</th><th>" + __("Per Hari") + "</th><th>" + __("Per Jam") + "</th>" +
            "<th>" + (periode ? __("Hari Hadir") : __("Kehadiran")) + "</th>";
        d.komponen.forEach((k) => {
            html += "<th title='" + esc(k.basis || "") + "'>" + esc(k.nama) + (k.aktif ? "" : " (" + __("nonaktif") + ")") +
                "<div class='ps-src'>" + esc(k.basis || "") + "</div></th>";
        });
        html += "<th>" + __("Total Tunjangan") + "</th><th>" + __("Total Potongan Komponen") + "</th><th>" + __("Pajak") + "</th><th>" + __("Iuran BPJS") + "</th><th>" + __("Catatan") + "</th></tr></thead><tbody>";

        d.baris.forEach((b) => {
            html += "<tr class='" + (b.janggal ? "ps-row-janggal" : "") + "'>" +
                "<td><a href='/desk/hris-employee/" + encodeURIComponent(b.employee) + "'>" + esc(b.nama || b.employee) + "</a><div class='ps-src'>" + esc(b.employee) + "</div></td>" +
                "<td>" + esc(b.department || "") + "</td><td>" + esc(b.grup || "") + "</td><td>" + esc(b.pay_type || "-") + "</td>" +
                "<td class='ps-num'>" + rp(b.gaji_pokok) + "</td><td class='ps-num'>" + rp(b.per_hari) + "</td><td class='ps-num'>" + rp(b.per_jam) + "</td>" +
                "<td>" + esc(periode ? (b.hari_hadir === null ? "-" : b.hari_hadir) : (b.kehadiran || "-")) + "</td>";
            d.komponen.forEach((k) => (html += cell((b.sel || {})[k.kode])));
            html += "<td class='ps-num'>" + rp(b.total_pendapatan) + "</td><td class='ps-num'>" + rp(b.total_potongan) + "</td>" +
                "<td>" + esc(b.pajak) + "</td><td class='ps-num'>" + rp(b.bpjs || null) + "</td>" +
                "<td style='min-width:200px'>" + (b.catatan || []).map(esc).join("<br>") + "</td></tr>";
        });

        const t = d.total || {};
        html += "<tr class='ps-foot'><td colspan='8'>" + __("Total seluruh hasil filter") + " (" + d.jumlah_baris + " " + __("karyawan") + ")</td>";
        d.komponen.forEach((k) => (html += "<td class='ps-num'>" + rp((t.per_komponen || {})[k.kode]) + "</td>"));
        html += "<td class='ps-num'>" + rp(t.pendapatan) + "</td><td class='ps-num'>" + rp(t.potongan) + "</td><td></td><td></td><td>" +
            (d.jumlah_janggal ? __("Janggal") + ": " + d.jumlah_janggal : "") + "</td></tr>";
        html += "</tbody></table></div>";

        const halaman = Math.max(1, Math.ceil(d.jumlah_baris / state.ukuran));
        html += "<div style='margin:8px 0'>" +
            "<button class='btn btn-xs btn-default ps-prev' " + (state.halaman <= 1 ? "disabled" : "") + ">" + __("Sebelumnya") + "</button> " +
            "<span class='text-muted'>" + __("Halaman") + " " + state.halaman + " / " + halaman + "</span> " +
            "<button class='btn btn-xs btn-default ps-next' " + (state.halaman >= halaman ? "disabled" : "") + ">" + __("Berikutnya") + "</button></div>";
        $body.html(html);
        $body.find(".ps-prev").on("click", () => { state.halaman -= 1; load(); });
        $body.find(".ps-next").on("click", () => { state.halaman += 1; load(); });
    };

    const load = () => {
        if (f.mode.get_value() === "Per Periode" && !f.periode.get_value()) {
            $body.html("<p class='text-muted'>" + __("Pilih Periode Gaji.") + "</p>");
            return;
        }
        if (f.mode.get_value() === "Per Tanggal" && !f.tanggal.get_value()) {
            $body.html("<p class='text-muted'>" + __("Pilih Tanggal.") + "</p>");
            return;
        }
        frappe.call({
            method: API,
            args: args(false),
            freeze: true,
            freeze_message: __("Menghitung..."),
            callback: (r) => {
                state.data = r.message;
                render();
            },
        });
    };

    const exportCsv = () => {
        frappe.call({
            method: API,
            args: args(true),
            freeze: true,
            freeze_message: __("Menyiapkan berkas..."),
            callback: (r) => {
                const d = r.message;
                if (!d || !d.baris.length) {
                    frappe.msgprint(__("Tidak ada data untuk diekspor."));
                    return;
                }
                const q = (v) => '"' + String(v === null || v === undefined ? "" : v).replace(/"/g, '""') + '"';
                const periode = d.mode === "Per Periode";
                const head = ["Karyawan", "Nama", "Department", "Grup", "Jenis Gaji", "Gaji Pokok", "Per Hari", "Per Jam", periode ? "Hari Hadir" : "Kehadiran"];
                d.komponen.forEach((k) => { head.push(k.nama); head.push(k.nama + " (sumber)"); });
                head.push("Total Tunjangan", "Total Potongan Komponen", "Pajak", "Iuran BPJS", "Catatan");
                const rows = d.baris.map((b) => {
                    const x = [b.employee, b.nama, b.department, b.grup, b.pay_type, b.gaji_pokok, b.per_hari, b.per_jam, periode ? b.hari_hadir : b.kehadiran];
                    d.komponen.forEach((k) => {
                        const c = (b.sel || {})[k.kode] || {};
                        x.push(c.error ? "galat" : c.jumlah);
                        x.push(c.sumber || c.error || "");
                    });
                    x.push(b.total_pendapatan, b.total_potongan, b.pajak, b.bpjs, (b.catatan || []).join(" | "));
                    return x;
                });
                const csv = [head.map(q).join(",")].concat(rows.map((x) => x.map(q).join(","))).join("\r\n");
                const blob = new Blob(["\ufeff" + csv], { type: "text/csv;charset=utf-8;" });
                const a = document.createElement("a");
                a.href = URL.createObjectURL(blob);
                a.download = "payroll-summary-" + d.mode.replace(" ", "-").toLowerCase() + "-" + d.akhir + ".csv";
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(a.href);
            },
        });
    };

    page.set_primary_action(__("Tampilkan"), () => { state.halaman = 1; load(); });
    page.set_secondary_action(__("Ekspor CSV"), exportCsv);

    state.ready = true;
    load();
};
