frappe.provide("hris.raw_log");

hris.raw_log.EDITORS = ["HRIS HR Admin", "HRIS Manager", "System Manager"];
hris.raw_log.LOCKABLE = [
    "device",
    "device_user_id",
    "punch_time",
    "verify_mode",
    "punch_status_raw",
    "employee",
    "review_status",
    "review_note",
    "change_reason",
];

hris.raw_log.apply_lock = function (frm) {
    if (frm.is_new()) {
        return;
    }
    const can_edit = hris.raw_log.EDITORS.some((role) => frappe.user.has_role(role));
    const sent = frm.doc.review_status === "Terkirim";
    const locked = !can_edit || sent;
    hris.raw_log.LOCKABLE.forEach((fieldname) => {
        frm.set_df_property(fieldname, "read_only", locked ? 1 : 0);
    });
    if (sent) {
        frm.set_intro(__("Log sudah Terkirim dan tidak dapat diubah."), "orange");
    } else if (!can_edit) {
        frm.set_intro(__("Anda hanya dapat melihat log ini."), "yellow");
    } else {
        frm.set_intro(
            __("Mengubah data sumber wajib mengisi Alasan Perubahan yang baru."),
            "blue"
        );
    }
};

hris.raw_log.audit_html = function (rows) {
    if (!rows.length) {
        return `<p class="text-muted">${__("Belum ada riwayat.")}</p>`;
    }
    const esc = frappe.utils.escape_html;
    const body = rows
        .map(
            (r) => `<tr>
                <td>${esc(r.time)}</td>
                <td>${esc(r.user)}</td>
                <td>${esc(r.field)}</td>
                <td>${esc(r.old)}</td>
                <td>${esc(r.new)}</td>
                <td>${esc(r.reason)}</td>
            </tr>`
        )
        .join("");
    return `<div style="overflow-x:auto">
        <table class="table table-bordered table-sm">
            <thead><tr>
                <th>${__("Waktu (WIB)")}</th>
                <th>${__("Pengguna")}</th>
                <th>${__("Field")}</th>
                <th>${__("Nilai Lama")}</th>
                <th>${__("Nilai Baru")}</th>
                <th>${__("Alasan")}</th>
            </tr></thead>
            <tbody>${body}</tbody>
        </table>
    </div>`;
};

hris.raw_log.render_audit = function (frm) {
    const field = frm.fields_dict.audit_trail_html;
    if (!field || frm.is_new()) {
        return;
    }
    field.$wrapper.html(`<p class="text-muted">${__("Memuat audit trail...")}</p>`);
    frappe.call({
        method: "hris.hris_attendance.services.audit_trail.get_audit_trail",
        args: { doctype: frm.doctype, name: frm.doc.name },
        callback(r) {
            field.$wrapper.html(hris.raw_log.audit_html(r.message || []));
        },
    });
};

frappe.ui.form.on("HRIS Raw Log", {
    refresh(frm) {
        hris.raw_log.apply_lock(frm);
        hris.raw_log.render_audit(frm);
    },
});
