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

hris.wh.HAPUS = "hris.hris_attendance.services.working_hour_hapus.";
hris.wh.HAPUS_JOB = "hris.hris_attendance.services.working_hour_hapus_job.";

hris.wh.hapus_html = function (r) {
    const esc = frappe.utils.escape_html;
    const fmt = (x) => (x || 0).toLocaleString("id-ID");
    let html = `<p><b>${__("Dokumen yang cocok")}: ${fmt(r.total)}</b></p>`;
    const rows = Object.keys(r.per_status || {})
        .map((k) => `<tr><td>${esc(__(k))}</td><td class="text-right">${fmt(r.per_status[k])}</td></tr>`)
        .join("");
    if (rows) {
        html += `<table class="table table-bordered table-sm">${rows}</table>`;
    }
    if (r.blokir && r.blokir.jumlah) {
        html += `<div class="alert alert-danger"><b>${__("DITOLAK")}:</b> ${__(
            "{0} dokumen berada di bawah slip atau periode Final. Buka kembali atau hapus slip terkait lebih dulu.",
            [fmt(r.blokir.jumlah)]
        )}<ul>${(r.blokir.slip || [])
            .map(
                (s) =>
                    `<li>${esc(s.name)} - ${esc(s.employee_name || "")} (${esc(String(s.period_start))} s/d ${esc(
                        String(s.period_end)
                    )}), ${fmt(s.jumlah)} ${__("dokumen")}</li>`
            )
            .join("")}</ul></div>`;
    }
    (r.peringatan || []).forEach((p) => {
        html += `<div class="alert alert-warning">${esc(p.pesan)}</div>`;
    });
    (r.info || []).forEach((p) => {
        html += `<p class="text-muted">${esc(p.pesan)}</p>`;
    });
    return html;
};

hris.wh.hapus_konfirmasi_html = function (r) {
    const esc = frappe.utils.escape_html;
    return (r.peringatan || [])
        .filter((p) => p.butuh_konfirmasi)
        .map(
            (p) =>
                `<div class="checkbox"><label><input type="checkbox" class="hris-konf" data-kode="${esc(p.kode)}"> ${__(
                    "Saya sudah membaca peringatan ini dan tetap ingin menghapus"
                )} (${esc(p.kode)})</label></div>`
        )
        .join("");
};

hris.wh.open_hapus_status = function (listview) {
    const d = new frappe.ui.Dialog({
        title: __("Status Hapus Working Hour"),
        fields: [{ fieldname: "body", fieldtype: "HTML" }],
    });
    let timer = null;
    const stop = () => {
        if (timer) {
            clearInterval(timer);
            timer = null;
        }
    };
    const render = (s) => {
        const esc = frappe.utils.escape_html;
        const warna = { Antre: "orange", Berjalan: "blue", Selesai: "green", Gagal: "red" };
        if (!s.status) {
            return `<p class="text-muted">${__("Tidak ada proses penghapusan yang tercatat (catatan status disimpan 1 jam).")}</p>`;
        }
        let html = `<p><span class="indicator-pill ${warna[s.status] || "gray"}">${esc(__(s.status))}</span></p>`;
        if (s.total) {
            const pct = Math.min(100, Math.round(((s.terhapus || 0) / s.total) * 100));
            html += `<div class="progress" style="height: 18px"><div class="progress-bar" style="width: ${pct}%">${pct}%</div></div>
                <p class="text-muted">${__("{0} dari {1} dokumen", [s.terhapus || 0, s.total])} | ${__(
                    "diperbarui {0} detik lalu",
                    [s.detik || 0]
                )}</p>`;
        }
        if (s.status === "Antre") {
            html += `<p class="text-muted">${__("Menunggu worker background memulai proses.")}</p>`;
        }
        if (s.message) {
            html += `<div class="alert alert-danger">${esc(s.message)}</div>`;
        }
        return html;
    };
    const tick = () =>
        frappe.call({
            method: hris.wh.HAPUS_JOB + "delete_status",
            callback(r) {
                const s = r.message || {};
                d.fields_dict.body.$wrapper.html(render(s));
                if (!["Antre", "Berjalan"].includes(s.status)) {
                    stop();
                    if (listview && listview.refresh) {
                        listview.refresh();
                    }
                }
            },
            error() {
                d.fields_dict.body.$wrapper.html(
                    `<div class="alert alert-danger">${__("Gagal membaca status dari server.")}</div>`
                );
            },
        });
    d.onhide = stop;
    d.show();
    tick();
    timer = setInterval(tick, 2000);
};

hris.wh.open_hapus = function (listview, defaults) {
    defaults = defaults || {};
    let hasil = null;
    let hasil_args = null;
    const opsi_status = ((frappe.meta.get_docfield("HRIS Working Hour", "status") || {}).options || "").trim();

    const nilai = () => {
        const v = d.get_values(true) || {};
        return {
            date_from: v.date_from,
            date_to: v.date_to,
            karyawan: v.employee ? [v.employee] : [],
            status: v.status ? [v.status] : [],
            tanpa_gaji: v.tanpa_gaji ? 1 : 0,
        };
    };

    const reset = () => {
        hasil = null;
        d.fields_dict.ringkasan.$wrapper.html("");
        d.set_df_property("confirm_total", "hidden", 1);
        d.set_value("confirm_total", "");
        d.set_primary_action(__("Cek Dulu"), cek);
        d.get_primary_btn().removeClass("btn-danger").addClass("btn-primary");
    };

    const hapus = () => {
        if (!hasil || !hasil.boleh) {
            return;
        }
        const ketik = parseInt(String(d.get_value("confirm_total") || "").replace(/\D/g, ""), 10) || 0;
        if (ketik !== hasil.total) {
            frappe.msgprint(
                __("Jumlah yang diketik ({0}) tidak sama dengan jumlah dokumen ({1}).", [ketik, hasil.total])
            );
            return;
        }
        const kode = [];
        let belum = false;
        d.fields_dict.ringkasan.$wrapper.find(".hris-konf").each(function () {
            if (this.checked) {
                kode.push($(this).data("kode"));
            } else {
                belum = true;
            }
        });
        if (belum) {
            frappe.msgprint(__("Centang semua peringatan terlebih dulu."));
            return;
        }
        frappe.call({
            method: hris.wh.HAPUS_JOB + "enqueue_delete",
            args: Object.assign({}, hasil_args, { confirm_total: ketik, konfirmasi: kode }),
            freeze: true,
            freeze_message: __("Mengantrekan penghapusan..."),
            callback(r) {
                const m = r.message || {};
                if (!m.queued) {
                    frappe.msgprint({
                        title: __("Tidak Diproses"),
                        indicator: "red",
                        message: frappe.utils.escape_html(m.message || ""),
                    });
                    return;
                }
                d.hide();
                hris.wh.open_hapus_status(listview);
            },
        });
    };

    const cek = () => {
        const a = nilai();
        if (!a.date_from || !a.date_to) {
            frappe.msgprint(__("Dari Tanggal dan Sampai Tanggal wajib diisi."));
            return;
        }
        frappe.call({
            method: hris.wh.HAPUS + "check_delete",
            args: a,
            freeze: true,
            freeze_message: __("Menghitung..."),
            callback(r) {
                hasil = r.message || null;
                hasil_args = a;
                if (!hasil) {
                    return;
                }
                d.fields_dict.ringkasan.$wrapper.html(
                    hris.wh.hapus_html(hasil) + hris.wh.hapus_konfirmasi_html(hasil)
                );
                d.set_df_property("confirm_total", "hidden", hasil.boleh ? 0 : 1);
                d.set_value("confirm_total", "");
                if (hasil.boleh) {
                    d.set_primary_action(__("Hapus"), hapus);
                    d.get_primary_btn().removeClass("btn-primary").addClass("btn-danger");
                } else {
                    d.set_primary_action(__("Cek Dulu"), cek);
                    d.get_primary_btn().removeClass("btn-danger").addClass("btn-primary");
                }
            },
        });
    };

    const d = new frappe.ui.Dialog({
        title: __("Hapus Massal Working Hour"),
        size: "large",
        fields: [
            { fieldname: "date_from", fieldtype: "Date", label: __("Dari Tanggal"), reqd: 1, default: defaults.date_from, change: () => reset() },
            { fieldname: "date_to", fieldtype: "Date", label: __("Sampai Tanggal"), reqd: 1, default: defaults.date_to, change: () => reset() },
            { fieldname: "employee", fieldtype: "Link", options: "Employee", label: __("Karyawan (opsional)"), default: defaults.employee, change: () => reset() },
            { fieldname: "status", fieldtype: "Select", label: __("Status (opsional)"), options: "\n" + opsi_status, default: defaults.status, change: () => reset() },
            { fieldname: "tanpa_gaji", fieldtype: "Check", label: __("Hanya karyawan tanpa baris gaji berlaku"), default: defaults.tanpa_gaji ? 1 : 0, change: () => reset() },
            { fieldname: "ringkasan", fieldtype: "HTML" },
            {
                fieldname: "confirm_total",
                fieldtype: "Data",
                label: __("Ketik jumlah dokumen yang akan dihapus untuk konfirmasi"),
                hidden: 1,
            },
        ],
        primary_action_label: __("Cek Dulu"),
        primary_action: () => cek(),
    });
    d.show();
};

hris.wh.tombol_hapus = function (listview) {
    frappe.call({
        method: hris.wh.HAPUS_JOB + "fitur_status",
        callback(r) {
            const m = r.message || {};
            if (!(m.aktif && m.berhak)) {
                return;
            }
            const grup = __("Hapus");
            listview.page.add_inner_button(__("Hapus Massal"), () => hris.wh.open_hapus(listview), grup);
            listview.page.add_inner_button(__("Status Hapus"), () => hris.wh.open_hapus_status(listview), grup);
        },
    });
};

frappe.listview_settings["HRIS Working Hour"] = {
    add_fields: ["status", "review_status", "needs_review"],
    get_indicator(doc) {
        const colors = {
            "Hadir": "green",
            "Tidak Lengkap": "orange",
            "Tidak Hadir": "red",
            "Libur": "gray",
            "Tidak Terjadwal": "light-gray",
        };
        if (!doc.status || !colors[doc.status]) {
            return null;
        }
        return [__(doc.status), colors[doc.status], "status,=," + doc.status];
    },
    onload(listview) {
        listview.page.add_inner_button(__("Perlu Ditinjau"), () => {
            frappe.set_route("List", "HRIS Working Hour", { review_status: "Menunggu" });
        });
        hris.wh.tombol_hapus(listview);
        if (!frappe.user.has_role(["HRIS HR Admin", "HRIS Manager", "System Manager"])) {
            return;
        }
        listview.page.add_inner_button(__("Hitung Periode"), () => hris.wh.open_dialog(listview));
        listview.page.add_inner_button(__("Status Hitung"), () => hris.wh.open_status(null));
    },
};
