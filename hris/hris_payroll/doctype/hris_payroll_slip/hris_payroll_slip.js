// Kolom tabel Komponen yang dikunci pada baris Otomatis (K-130).
// Kolom "source" dikunci di SEMUA baris: baris baru otomatis Manual, dan Manual tidak boleh diubah menjadi Otomatis.
const KOLOM_KOMPONEN = ["component", "component_type", "amount", "source", "basis", "reason"];

function kunci_komponen(frm) {
    const grid = frm.fields_dict.components && frm.fields_dict.components.grid;
    if (!grid || !grid.grid_rows) {
        return;
    }
    const draft = frm.doc.status === "Draft";
    // Slip bukan Draft: seluruh tabel terkunci (server sudah menolak; ini hanya tampilan).
    frm.set_df_property("components", "read_only", draft ? 0 : 1);
    if (!draft) {
        return;
    }
    grid.grid_rows.forEach((grid_row) => {
        const baris = grid_row.doc;
        if (!baris) {
            return;
        }
        const otomatis = baris.source === "Otomatis";
        KOLOM_KOMPONEN.forEach((fieldname) => {
            const bisa_diedit = fieldname === "source" ? false : !otomatis;
            grid_row.toggle_editable(fieldname, bisa_diedit);
        });
        // Baris Otomatis tidak boleh dipilih untuk dihapus.
        grid_row.wrapper.find(".grid-row-check").prop("disabled", otomatis);
    });
}

frappe.ui.form.on("HRIS Payroll Slip", {
    refresh(frm) {
        hris.audit.render(frm);
        if (frm.is_new()) {
            return;
        }
        const roles = frappe.user_roles || [];
        const adalah = (...daftar) => daftar.some((r) => roles.includes(r)) || frappe.session.user === "Administrator";
        const esc = frappe.utils.escape_html;
        const pesan = {
            Draft: __("Draft. Komponen Otomatis dihitung dari Working Hour dan gaji; Anda boleh menambah komponen Manual (alasan wajib)."),
            Ditinjau: __("Ditinjau. Slip terkunci. Untuk koreksi, kembalikan Periode Gaji ke Draft."),
            Final: __("Final. Slip terkunci. Untuk koreksi, Payroll Manager harus membuka kembali Periode Gaji."),
        };
        let isi = esc(pesan[frm.doc.status] || "");
        if (frm.doc.calc_notes) {
            isi += "<br>" + esc(frm.doc.calc_notes).replace(/\n/g, "<br>");
        }
        frm.set_intro(isi, frm.doc.status === "Final" ? "green" : "blue");

        if (frm.doc.status === "Draft" && adalah("HRIS Payroll Admin", "HRIS Payroll Manager")) {
            frm.add_custom_button(__("Hitung Ulang Slip"), () => {
                frappe.call({
                    method: "hris.hris_payroll.services.payroll_slip.hitung_ulang_slip",
                    args: { name: frm.doc.name },
                    freeze: true,
                    callback() {
                        frm.reload_doc();
                    },
                });
            });
        }

        // Grid dirender setelah refresh; panggil sekarang dan sekali lagi sesudah render selesai.
        kunci_komponen(frm);
        setTimeout(() => kunci_komponen(frm), 300);
    },
    components_add(frm) {
        setTimeout(() => kunci_komponen(frm), 100);
    },
});

frappe.ui.form.on("HRIS Payroll Slip Item", {
    form_render(frm) {
        kunci_komponen(frm);
    },
});
