frappe.provide("hris.audit");

hris.audit.html = function (rows) {
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

hris.audit.render = function (frm) {
    const field = frm.fields_dict.audit_trail_html;
    if (!field || frm.is_new()) {
        return;
    }
    field.$wrapper.html(`<p class="text-muted">${__("Memuat audit trail...")}</p>`);
    frappe.call({
        method: "hris.hris_attendance.services.audit_trail.get_audit_trail",
        args: { doctype: frm.doctype, name: frm.doc.name },
        callback(r) {
            field.$wrapper.html(hris.audit.html(r.message || []));
        },
    });
};
