frappe.listview_settings["HRIS Employee Component"] = Object.assign(
    frappe.listview_settings["HRIS Employee Component"] || {},
    {
        onload(listview) {
            listview.page.add_inner_button(__("Terapkan ke Department atau Grup"), () => hris_hec_massal(listview));
        },
    }
);

function hris_hec_massal(listview) {
    const API = "hris.hris_payroll.services.hec_massal.";
    let siap = null;
    const esc = (t) => frappe.utils.escape_html(t == null ? "" : String(t));
    const kunci = (v) => JSON.stringify([v.component, v.mode, v.department, cint(v.termasuk_anak), v.employee_group, v.date_from, v.date_to]);
    const args = (v) => ({
        component: v.component,
        date_from: v.date_from,
        date_to: v.date_to,
        department: v.mode === "Department" ? v.department : null,
        termasuk_anak: v.mode === "Department" && v.termasuk_anak ? 1 : 0,
        employee_group: v.mode === "Grup" ? v.employee_group : null,
    });
    const tabel = (daftar, judul) => {
        if (!daftar || !daftar.length) return "";
        const baris = daftar
            .map((x) => `<tr><td>${esc(x.employee)} ${esc(x.nama)}</td><td>${esc(x.alasan)}</td></tr>`)
            .join("");
        return `<table class="table table-bordered table-sm"><thead><tr><th>${__("Karyawan")}</th><th>${judul}</th></tr></thead><tbody>${baris}</tbody></table>`;
    };
    const tampil = (html) => d.fields_dict.hasil.$wrapper.html(html);

    const d = new frappe.ui.Dialog({
        title: __("Terapkan Komponen ke Department atau Grup"),
        size: "large",
        fields: [
            { fieldname: "component", label: __("Komponen"), fieldtype: "Link", options: "HRIS Pay Component", reqd: 1,
              get_query: () => ({ filters: { is_active: 1 } }) },
            { fieldname: "mode", label: __("Berdasarkan"), fieldtype: "Select", options: "Department\nGrup", default: "Department", reqd: 1 },
            { fieldname: "department", label: __("Department"), fieldtype: "Link", options: "HRIS Department",
              depends_on: "eval:doc.mode=='Department'", mandatory_depends_on: "eval:doc.mode=='Department'" },
            { fieldname: "termasuk_anak", label: __("Termasuk Department di bawahnya"), fieldtype: "Check", default: 1,
              depends_on: "eval:doc.mode=='Department'" },
            { fieldname: "employee_group", label: __("Grup"), fieldtype: "Link", options: "HRIS Employee Group",
              depends_on: "eval:doc.mode=='Grup'", mandatory_depends_on: "eval:doc.mode=='Grup'" },
            { fieldtype: "Section Break" },
            { fieldname: "date_from", label: __("Berlaku Dari"), fieldtype: "Date", reqd: 1 },
            { fieldtype: "Column Break" },
            { fieldname: "date_to", label: __("Berlaku Sampai"), fieldtype: "Date", reqd: 1 },
            { fieldtype: "Section Break" },
            { fieldname: "amount", label: __("Nominal Khusus (opsional)"), fieldtype: "Currency",
              description: __("Kosong atau 0 berarti memakai nilai dasar komponen.") },
            { fieldname: "reason", label: __("Alasan"), fieldtype: "Small Text", reqd: 1 },
            { fieldtype: "Section Break" },
            { fieldname: "pratinjau", label: __("Pratinjau"), fieldtype: "Button",
              click: () => {
                  const v = d.get_values();
                  if (!v) return;
                  frappe.call({
                      method: API + "pratinjau",
                      args: args(v),
                      freeze: true,
                      freeze_message: __("Menghitung pratinjau..."),
                      callback: (r) => {
                          const m = r.message || {};
                          siap = kunci(v);
                          tampil(
                              `<p><b>${m.akan_dibuat}</b> ${__("karyawan akan dibuatkan penetapan")}, <b>${m.dilewati}</b> ${__("dilewati")} (${__("dari")} ${m.dipilih} ${__("karyawan aktif")}).</p>` +
                                  tabel(m.contoh_lewati, __("Alasan dilewati")) +
                                  (m.dilewati > (m.contoh_lewati || []).length
                                      ? `<p class="text-muted">${__("Dan")} ${m.dilewati - m.contoh_lewati.length} ${__("lainnya.")}</p>`
                                      : "")
                          );
                      },
                  });
              } },
            { fieldname: "hasil", fieldtype: "HTML" },
        ],
        primary_action_label: __("Terapkan"),
        primary_action: (v) => {
            if (siap !== kunci(v)) {
                frappe.msgprint(__("Klik Pratinjau dulu. Isian berubah sejak pratinjau terakhir."));
                return;
            }
            frappe.confirm(__("Buat penetapan Berlaku sesuai pratinjau?"), () => {
                frappe.call({
                    method: API + "terapkan",
                    args: Object.assign(args(v), { reason: v.reason, amount: v.amount || 0 }),
                    freeze: true,
                    freeze_message: __("Membuat penetapan..."),
                    callback: (r) => {
                        const m = r.message || {};
                        d.hide();
                        frappe.show_alert({ message: m.pesan, indicator: m.gagal ? "orange" : "green" }, 10);
                        if (m.gagal) {
                            frappe.msgprint({
                                title: __("Yang gagal dibuat"),
                                message: tabel(m.daftar_gagal, __("Alasan gagal")),
                                wide: true,
                            });
                        }
                        listview.refresh();
                    },
                });
            });
        },
    });
    d.show();
}
