frappe.ui.form.on("HRIS Component Assignment", {
    refresh(frm) {
        if (hris.audit && hris.audit.render) {
            hris.audit.render(frm);
        }
        const baru = frm.is_new();
        ["scope_type", "department", "employee_group", "component"].forEach((f) => frm.set_df_property(f, "read_only", baru ? 0 : 1));
        if (!baru) {
            frm.add_custom_button(__("Lihat karyawan terkena"), () => hris_hca_pratinjau(frm));
            frm.set_intro(
                __("Untuk mengubah, ubah tanggal, status, atau nominal lalu isi Alasan yang baru. Untuk mengeluarkan seseorang, buat penetapan karyawan (HRIS Employee Component) dengan Status Tidak Berlaku. Untuk menghentikan penetapan ini, matikan Aktif."),
                "blue"
            );
        }
    },
    department(frm) {
        hris_hca_isi_company(frm, "HRIS Department", frm.doc.department);
    },
    employee_group(frm) {
        hris_hca_isi_company(frm, "HRIS Employee Group", frm.doc.employee_group);
    },
    scope_type(frm) {
        if (frm.doc.scope_type === "Department") {
            frm.set_value("employee_group", null);
        } else {
            frm.set_value("department", null);
        }
    },
    status(frm) {
        if (frm.doc.status === "Tidak Berlaku") {
            frm.set_value("amount", 0);
        }
    },
    date_from(frm) {
        if (frm.doc.date_from && !frm.doc.date_to) {
            frm.set_value("date_to", frm.doc.date_from);
        }
    },
});

function hris_hca_pratinjau(frm) {
    const esc = (t) => frappe.utils.escape_html(t == null ? "" : String(t));
    frappe.call({
        method: "hris.hris_payroll.services.hca_pratinjau.pratinjau",
        args: { name: frm.doc.name },
        freeze: true,
        freeze_message: __("Menghitung karyawan terkena..."),
        callback: (r) => {
            const m = r.message || {};
            const j = m.jumlah || {};
            const tabel = (daftar, ket) => {
                if (!daftar || !daftar.length) return "";
                const baris = daftar
                    .map((x) => `<tr><td>${esc(x.name)} ${esc(x.employee_name)}</td><td>${esc(ket)}${x.punya_hec ? " - " + __("punya penetapan karyawan sendiri (menang)") : ""}</td></tr>`)
                    .join("");
                return `<table class="table table-bordered table-sm"><tbody>${baris}</tbody></table>`;
            };
            const peringatan = (m.peringatan || []).map((t) => `<li>${esc(t)}</li>`).join("");
            frappe.msgprint({
                title: __("Karyawan terkena {0}", [frm.doc.name]),
                wide: true,
                message:
                    `<p><b>${j.dapat || 0}</b> ${__("menerima")}, <b>${j.ikut_department || 0}</b> ${__("ikut Department")}, <b>${j.tertutup_grup || 0}</b> ${__("tertutup penetapan Grup")}, ${__("dan")} <b>${j.punya_hec || 0}</b> ${__("di antara yang menerima punya penetapan karyawan sendiri")}.</p>` +
                    (peringatan ? `<ul>${peringatan}</ul>` : "") +
                    tabel((m.contoh || {}).dapat, __("menerima")) +
                    tabel((m.contoh || {}).ikut_department, __("ikut Department")) +
                    tabel((m.contoh || {}).tertutup_grup, __("tertutup penetapan Grup")) +
                    `<p class="text-muted">${__("Maksimal 40 nama per kelompok ditampilkan. Penetapan karyawan (HRIS Employee Component) selalu menang atas penetapan ini.")}</p>`,
            });
        },
    });
}

function hris_hca_isi_company(frm, doctype, nama) {
    if (!nama) {
        frm.set_value("company", null);
        return;
    }
    frappe.db.get_value(doctype, nama, "company").then((r) => {
        frm.set_value("company", (r.message || {}).company || null);
    });
}
