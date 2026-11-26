// HRIS Employee: Kartu Profil v2 (baca bertab + edit per bagian).
// Hanya tampilan. Simpan lewat frm.set_value + frm.save, jadi validasi dan hook tetap jalan.
// Izin mengikuti permlevel (server tidak mengirim field permlevel 1 ke peran lain).
(function () {
    "use strict";

    const DOCTYPE = "HRIS Employee";
    const PREF_KEY = "hris_employee_view";
    const KOSONG = '<span class="hk-empty">&mdash;</span>';
    let tab_aktif = { nama: null, id: "profil" };
    let peta_seksi = {};

    // ---------- Util ----------
    function esc(v) {
        return frappe.utils.escape_html(v === null || v === undefined ? "" : String(v));
    }
    function ada(v) {
        return v !== null && v !== undefined && String(v).trim() !== "";
    }
    function norm(v) {
        return v === null || v === undefined ? "" : String(v);
    }
    function teks(v) {
        return ada(v) ? esc(v) : KOSONG;
    }
    function tgl(v) {
        return ada(v) ? esc(frappe.datetime.str_to_user(v)) : KOSONG;
    }
    function rupiah(v) {
        const n = Number(v);
        if (!ada(v) || isNaN(n)) {
            return KOSONG;
        }
        return "Rp " + n.toLocaleString("id-ID");
    }
    function badge(label, nada) {
        return `<span class="hk-badge hk-${nada}">${esc(label)}</span>`;
    }
    function ya_tidak(v) {
        return Number(v) ? badge("Ya", "ok") : badge("Tidak", "muted");
    }

    // Pembuat item. f = nama field (null = nilai turunan/dikunci, tidak bisa diubah).
    function T(f, label, opt) {
        opt = opt || {};
        return { f: f, label: label, wide: !!opt.wide, h: opt.h || ((d) => teks(d[f])) };
    }
    function Tg(f, label) {
        return T(f, label, { h: (d) => tgl(d[f]) });
    }
    function Cb(f, label) {
        return T(f, label, { h: (d) => ya_tidak(d[f]) });
    }
    function Rp(f, label) {
        return T(f, label, { h: (d) => rupiah(d[f]) });
    }
    function X(label, h, wide) {
        return { f: null, label: label, wide: !!wide, h: h };
    }

    function baca_pref() {
        try {
            return window.localStorage.getItem(PREF_KEY) === "form" ? "form" : "kartu";
        } catch (e) {
            return "kartu";
        }
    }
    function simpan_pref(mode) {
        try {
            window.localStorage.setItem(PREF_KEY, mode);
        } catch (e) {
            /* abaikan */
        }
    }

    // ---------- Nilai turunan ----------
    function umur(v) {
        if (!ada(v)) {
            return "";
        }
        const t = moment().diff(moment(v), "years");
        return t >= 0 ? ` <span class="hk-sub">(${t} th)</span>` : "";
    }
    function masa_kerja(d) {
        if (!ada(d.date_of_joining)) {
            return "";
        }
        const akhir = d.status === "Resign" && ada(d.resign_date) ? moment(d.resign_date) : moment();
        const bln = akhir.diff(moment(d.date_of_joining), "months");
        if (bln < 0) {
            return "";
        }
        const th = Math.floor(bln / 12);
        return (th ? th + " th " : "") + (bln % 12) + " bln";
    }
    function kontrak(d) {
        if (!ada(d.contract_end_date)) {
            return KOSONG;
        }
        let tambah = "";
        if (d.status !== "Resign") {
            const sisa = moment(d.contract_end_date).diff(moment().startOf("day"), "days");
            if (sisa < 0) {
                tambah = " " + badge("Sudah berakhir", "err");
            } else if (sisa <= 30) {
                tambah = " " + badge("Berakhir " + sisa + " hari lagi", "warn");
            }
        }
        return tgl(d.contract_end_date) + tambah;
    }
    function telepon(v) {
        if (!ada(v)) {
            return KOSONG;
        }
        let n = String(v).replace(/\D/g, "");
        if (n.startsWith("0")) {
            n = "62" + n.slice(1);
        }
        const wa =
            /^628\d{7,12}$/.test(n)
                ? ` <a class="hk-link" href="https://wa.me/${n}" target="_blank" rel="noopener noreferrer">WhatsApp</a>`
                : "";
        return esc(v) + wa;
    }
    function surel(v) {
        return ada(v) ? `<a class="hk-link" href="mailto:${esc(v)}">${esc(v)}</a>` : KOSONG;
    }

    // ---------- Izin ----------
    function boleh_payroll(frm) {
        return !!(frm.perm && frm.perm[1] && frm.perm[1].read);
    }
    function boleh_ubah(frm) {
        return !!(frm.perm && frm.perm[0] && frm.perm[0].write);
    }
    function boleh_field(frm, f) {
        const fo = frm.fields_dict && frm.fields_dict[f];
        if (!fo || !fo.df) {
            return false;
        }
        const df = fo.df;
        if (df.read_only) {
            return false;
        }
        const lv = df.permlevel || 0;
        return !!(frm.perm && frm.perm[lv] && frm.perm[lv].write);
    }

    // ---------- Definisi section per tab ----------
    function seksi_profil() {
        return [
            {
                id: "identitas", judul: "Identitas", warna: "#3b82f6",
                items: [
                    T("employee_name", "Nama Lengkap"),
                    T("birth_place", "Tempat Lahir"),
                    T("birth_date", "Tanggal Lahir", { h: (d) => tgl(d.birth_date) + umur(d.birth_date) }),
                    T("gender", "Jenis Kelamin"),
                    T("religion", "Agama"),
                    T("marital_status", "Status Perkawinan"),
                    T("blood_type", "Golongan Darah"),
                    T("education", "Pendidikan"),
                ],
            },
            {
                id: "kontak", judul: "Kontak", warna: "#14b8a6",
                items: [
                    T("phone", "No Telepon", { h: (d) => telepon(d.phone) }),
                    T("email", "Email", { h: (d) => surel(d.email) }),
                    T("postal_code", "Kode Pos"),
                    T("address", "Alamat", { wide: true }),
                ],
            },
        ];
    }

    function seksi_pekerjaan() {
        return [
            {
                id: "penempatan", judul: "Penempatan", warna: "#3b82f6",
                items: [
                    T("company", "Perusahaan"),
                    T("branch", "Branch"),
                    T("department", "Department"),
                    T("employee_group", "Grup Karyawan"),
                    T("rule_follow", "Aturan Mengikuti"),
                ],
            },
            {
                id: "masakerja", judul: "Masa Kerja", warna: "#22c55e",
                items: [
                    Tg("date_of_joining", "Tanggal Bergabung"),
                    X("Masa Kerja", (d) => (ada(masa_kerja(d)) ? esc(masa_kerja(d)) : KOSONG)),
                    Tg("probation_passed_date", "Tanggal Lulus Probation"),
                    T("contract_end_date", "Tanggal Akhir Perjanjian Kerja", { h: (d) => kontrak(d) }),
                ],
            },
            {
                id: "absensi", judul: "Absensi", warna: "#c9a227",
                items: [
                    T("attendance_device_id", "ID Finger"),
                    T("fingerprint_method", "Metode Fingerprint"),
                    T("legacy_payroll_code", "Kode di Aplikasi Gaji Lama"),
                ],
            },
        ];
    }

    function seksi_payroll(d) {
        const peserta = [
            Cb("bpjs_kes_enrolled", "BPJS Kesehatan"),
            Cb("bpjs_tk_enrolled", "BPJS Ketenagakerjaan (satu angka)"),
            Cb("bpjs_jht_enrolled", "JHT"),
            Cb("bpjs_jp_enrolled", "JP"),
            Cb("bpjs_jkk_enrolled", "JKK"),
            Cb("bpjs_jkm_enrolled", "JKM"),
            Cb("pph21_enrolled", "PPh 21"),
        ];
        if (Number(d.pph21_enrolled)) {
            peserta.push(T("ptkp_status", "Status PTKP"));
        }
        const iuran_def = [
            ["bpjs_kes_enrolled", "bpjs_kes_amount", "Iuran BPJS Kesehatan"],
            ["bpjs_tk_enrolled", "bpjs_tk_amount", "Iuran BPJS Ketenagakerjaan"],
            ["bpjs_jht_enrolled", "bpjs_jht_amount", "Iuran JHT"],
            ["bpjs_jp_enrolled", "bpjs_jp_amount", "Iuran JP"],
            ["bpjs_jkk_enrolled", "bpjs_jkk_amount", "Iuran JKK"],
            ["bpjs_jkm_enrolled", "bpjs_jkm_amount", "Iuran JKM"],
        ];
        const iuran = iuran_def.filter((x) => Number(d[x[0]])).map((x) => Rp(x[1], x[2]));
        if (!iuran.length) {
            iuran.push(X("Iuran", () => '<span class="hk-empty">Tidak ada kepesertaan BPJS</span>', true));
        }
        return [
            {
                id: "sensitif", judul: "Data Sensitif", warna: "#ef4444",
                items: [
                    T("ktp_number", "No KTP"),
                    T("npwp", "NPWP"),
                    T("bpjs_tk_no", "No BPJS TK"),
                    T("bpjs_kes_no", "No BPJS Kesehatan"),
                    T("bank_name", "Nama Bank"),
                    T("bank_account_holder", "Atas Nama Rekening"),
                    T("bank_account_number", "Nomor Rekening"),
                ],
            },
            { id: "peserta", judul: "Kepesertaan BPJS dan Pajak", warna: "#22c55e", items: peserta },
            { id: "iuran", judul: "Iuran BPJS Karyawan per Bulan", warna: "#c9a227", items: iuran },
        ];
    }

    function seksi_status(d) {
        const nada_sinkron = d.sync_status === "Berhasil" ? "ok" : d.sync_status === "Gagal" ? "err" : "muted";
        return [
            {
                id: "status", judul: "Status", warna: "#3b82f6",
                items: [
                    T("status", "Status", {
                        h: (x) => (ada(x.status) ? badge(x.status, x.status === "Resign" ? "err" : "ok") : KOSONG),
                    }),
                    Tg("resign_date", "Tanggal Resign"),
                    T("user", "Akun Login"),
                    T("resign_reason", "Alasan Resign", { wide: true }),
                ],
            },
            {
                id: "kelengkapan", judul: "Kelengkapan Data", warna: "#22c55e",
                items: [
                    X(
                        "Status Kelengkapan",
                        (x) => (ada(x.data_status) ? badge(x.data_status, x.data_status === "Lengkap" ? "ok" : "warn") : KOSONG)
                    ),
                    X("Catatan", (x) => teks(x.data_note), true),
                ],
            },
            {
                id: "sinkron", judul: "Sinkron ke Employee ERPNext", warna: "#c9a227",
                items: [
                    X("Employee ERPNext", (x) =>
                        ada(x.erpnext_employee) ? frappe.utils.get_form_link("Employee", x.erpnext_employee, true) : KOSONG
                    ),
                    X("Status Sinkron", (x) => (ada(x.sync_status) ? badge(x.sync_status, nada_sinkron) : KOSONG)),
                    X("Sinkron Terakhir", (x) => tgl(x.last_sync)),
                    X("Pesan Error", (x) => teks(x.sync_error), true),
                ],
            },
        ];
    }

    // ---------- HTML ----------
    function item_html(i, d) {
        return (
            `<div class="hk-item${i.wide ? " hk-wide" : ""}">` +
            `<div class="hk-l">${esc(i.label)}</div><div class="hk-v">${typeof i.h === "function" ? i.h(d) : i.h}</div></div>`
        );
    }
    function seksi_html(frm, s) {
        peta_seksi[s.id] = s;
        const bisa = s.items.some((i) => i.f && boleh_field(frm, i.f));
        const tombol = bisa ? '<button type="button" class="hk-pen" title="Ubah bagian ini">Ubah</button>' : "";
        return (
            `<section class="hk-sec" data-sec="${esc(s.id)}" style="--acc:${s.warna}">` +
            `<div class="hk-sh"><h5>${esc(s.judul)}</h5><span class="hk-acts">${tombol}</span></div>` +
            `<div class="hk-grid">${s.items.map((i) => item_html(i, frm.doc)).join("")}</div></section>`
        );
    }
    function panel_html(frm, daftar) {
        return daftar.map((s) => seksi_html(frm, s)).join("");
    }

    function header(frm) {
        const d = frm.doc;
        const nama = d.employee_name || "";
        const inisial =
            nama.split(/\s+/).filter(Boolean).slice(0, 2).map((s) => s[0]).join("").toUpperCase() || "?";
        const foto = ada(d.image)
            ? `<img class="hk-foto" src="${esc(d.image)}" alt="">`
            : `<div class="hk-foto hk-inisial">${esc(inisial)}</div>`;
        const ganti = boleh_field(frm, "image") ? '<button type="button" class="hk-ganti">Ganti foto</button>' : "";
        const lencana =
            (ada(d.status) ? badge(d.status, d.status === "Resign" ? "err" : "ok") : "") +
            (ada(d.data_status) ? badge(d.data_status, d.data_status === "Lengkap" ? "ok" : "warn") : "");
        const meta = [
            ["ID Finger", d.attendance_device_id],
            ["Department", d.department],
            ["Grup", d.employee_group],
            ["Masa kerja", masa_kerja(d)],
        ]
            .filter((m) => ada(m[1]))
            .map((m) => `<span class="hk-meta"><b>${esc(m[0])}</b>${esc(m[1])}</span>`)
            .join("");
        const form = boleh_ubah(frm) ? '<button type="button" class="hk-edit">Form lengkap</button>' : "";
        return (
            `<div class="hk-head"><div class="hk-fotobox">${foto}${ganti}</div>` +
            `<div class="hk-id"><h3 class="hk-nama">${esc(nama)}</h3>` +
            `<div class="hk-badges">${lencana}</div><div class="hk-metas">${meta}</div></div>${form}</div>`
        );
    }

    function bangun(frm) {
        const d = frm.doc;
        peta_seksi = {};
        const tabs = [
            { id: "profil", label: "Profil", html: panel_html(frm, seksi_profil()) + ringkas_html() },
            { id: "pekerjaan", label: "Pekerjaan", html: panel_html(frm, seksi_pekerjaan()) },
        ];
        if (boleh_payroll(frm)) {
            tabs.push({ id: "payroll", label: "Payroll dan BPJS", html: panel_html(frm, seksi_payroll(d)) });
        }
        tabs.push({ id: "status", label: "Status dan Sinkron", html: panel_html(frm, seksi_status(d)) });
        tabs.push({
            id: "riwayat",
            label: "Riwayat",
            html: '<div class="hk-sec" style="--acc:#8b5cf6"><div class="hk-riw-full"><span class="hk-empty">Memuat riwayat...</span></div></div>',
        });

        if (tab_aktif.nama !== d.name || !tabs.some((t) => t.id === tab_aktif.id)) {
            tab_aktif = { nama: d.name, id: "profil" };
        }
        const bar_tab = tabs
            .map(
                (t) =>
                    `<button type="button" class="hk-tab${t.id === tab_aktif.id ? " aktif" : ""}" data-tab="${t.id}">${esc(t.label)}</button>`
            )
            .join("");
        const panel = tabs
            .map(
                (t) =>
                    `<div class="hk-panel" data-tab="${t.id}"${t.id === tab_aktif.id ? "" : ' style="display:none"'}>${t.html}</div>`
            )
            .join("");
        const peringatan = frm.is_dirty()
            ? '<div class="hk-warnbar">Ada perubahan yang belum disimpan. Kartu menampilkan nilai yang sedang diedit.</div>'
            : "";
        return (
            `<div class="hk-kartu">${header(frm)}` +
            `<div class="hk-card">${peringatan}<div class="hk-tabs">${bar_tab}</div>${panel}</div></div>`
        );
    }

    // ---------- Edit per bagian ----------
    function edit_seksi(frm, $kartu, $sec) {
        if ($kartu.find(".hk-ctl").length) {
            frappe.show_alert({ message: __("Simpan atau batalkan dulu bagian yang sedang diedit"), indicator: "orange" });
            return;
        }
        const s = peta_seksi[$sec.attr("data-sec")];
        if (!s) {
            return;
        }
        const boleh = s.items.filter((i) => i.f && boleh_field(frm, i.f));
        if (!boleh.length) {
            return;
        }
        // Salinan dokumen: kontrol menulis ke salinan ini, bukan ke frm.doc, sampai Simpan ditekan.
        const salinan = Object.assign({}, frm.doc);
        const $grid = $sec.find(".hk-grid").empty();
        const daftar = [];

        boleh.forEach((i) => {
            const fo = frm.fields_dict[i.f];
            const df = Object.assign({}, fo.df, { hidden: 0, depends_on: "", mandatory_depends_on: "", read_only: 0 });
            const $w = $('<div class="hk-ctl"></div>').appendTo($grid);
            if (i.wide || ["Small Text", "Text", "Long Text"].includes(df.fieldtype)) {
                $w.addClass("hk-wide");
            }
            const c = frappe.ui.form.make_control({
                df: df,
                parent: $w,
                doc: salinan,
                doctype: frm.doctype,
                render_input: true,
            });
            if (fo.get_query && !c.get_query) {
                c.get_query = fo.get_query;
            }
            c.set_input(frm.doc[i.f]);
            daftar.push({ f: i.f, c: c });
        });

        $sec.find(".hk-acts").html(
            '<button type="button" class="hk-btn hk-simpan">Simpan</button>' +
                '<button type="button" class="hk-btn hk-batal">Batal</button>'
        );
        $sec.find(".hk-batal").on("click", () => render(frm));
        $sec.find(".hk-simpan").on("click", () => {
            const ubah = {};
            daftar.forEach((x) => {
                const v = x.c.get_value();
                if (norm(v) !== norm(frm.doc[x.f])) {
                    ubah[x.f] = v === undefined ? null : v;
                }
            });
            if (!Object.keys(ubah).length) {
                render(frm);
                return;
            }
            frm.set_value(ubah)
                .then(() => frm.save())
                .catch(() => paksa_form(frm));
        });
    }

    function ganti_foto(frm) {
        try {
            new frappe.ui.FileUploader({
                doctype: frm.doctype,
                docname: frm.docname,
                fieldname: "image",
                folder: "Home/Attachments",
                restrictions: { allowed_file_types: ["image/*"] },
                on_success(file) {
                    frm.set_value("image", file.file_url).then(() => frm.save());
                },
            });
        } catch (e) {
            console.error("HRIS Kartu Profil: ganti foto gagal", e);
            paksa_form(frm);
        }
    }

    // ---------- Riwayat (audit trail) ----------
    let cache_riw = { kunci: null, rows: null };

    function potong(v, n) {
        const t = String(v === null || v === undefined ? "" : v);
        return t.length > n ? t.slice(0, n) + "..." : t;
    }
    function muat_riwayat(frm) {
        const kunci = frm.doc.name + "|" + frm.doc.modified;
        if (cache_riw.kunci === kunci && cache_riw.rows) {
            return Promise.resolve(cache_riw.rows);
        }
        return frappe
            .call({
                method: "hris.hris_attendance.services.audit_trail.get_audit_trail",
                args: { doctype: frm.doctype, name: frm.doc.name },
            })
            .then((r) => {
                const rows = (r && r.message) || [];
                cache_riw = { kunci: kunci, rows: rows };
                return rows;
            });
    }
    function ringkas_html() {
        return (
            '<section class="hk-sec" style="--acc:#8b5cf6">' +
            '<div class="hk-sh"><h5>Riwayat Terakhir</h5><span class="hk-acts">' +
            '<button type="button" class="hk-btn hk-lihat">Lihat semua</button></span></div>' +
            '<div class="hk-ring"><span class="hk-empty">Memuat riwayat...</span></div></section>'
        );
    }
    function baris_ringkas(r) {
        let isi = esc(r.field);
        if (ada(r.old) || ada(r.new)) {
            isi +=
                `: <span class="hk-sub">${esc(ada(r.old) ? potong(r.old, 60) : "kosong")}</span>` +
                ` &rarr; <b>${esc(ada(r.new) ? potong(r.new, 60) : "kosong")}</b>`;
        }
        const alasan = ada(r.reason) ? `<div class="hk-sub">Alasan: ${esc(r.reason)}</div>` : "";
        return (
            `<li class="hk-rw"><div class="hk-rw-t">${esc(r.time)} &middot; ${esc(r.user)}</div>` +
            `<div>${isi}</div>${alasan}</li>`
        );
    }
    function masih_ada($el) {
        return $el.length && $.contains(document.documentElement, $el[0]);
    }
    function isi_ringkas(frm, $kartu) {
        const $w = $kartu.find(".hk-ring");
        if (!$w.length) {
            return;
        }
        muat_riwayat(frm)
            .then((rows) => {
                if (!masih_ada($w)) {
                    return;
                }
                $w.html(
                    rows.length
                        ? '<ul class="hk-rwl">' + rows.slice(0, 5).map(baris_ringkas).join("") + "</ul>"
                        : '<span class="hk-empty">Belum ada riwayat</span>'
                );
            })
            .catch((e) => {
                console.error("HRIS Kartu Profil: riwayat gagal dimuat", e);
                if (masih_ada($w)) {
                    $w.html('<span class="hk-empty">Riwayat tidak dapat dimuat</span>');
                }
            });
    }
    function isi_penuh(frm, $kartu) {
        const $w = $kartu.find(".hk-riw-full");
        if (!$w.length || $w.attr("data-ok") === "1") {
            return;
        }
        muat_riwayat(frm)
            .then((rows) => {
                if (!masih_ada($w)) {
                    return;
                }
                if (!rows.length) {
                    $w.html('<span class="hk-empty">Belum ada riwayat</span>');
                    return;
                }
                const batas = 300;
                const baris = rows
                    .slice(0, batas)
                    .map(
                        (r) =>
                            `<tr><td>${esc(r.time)}</td><td>${esc(r.user)}</td><td>${esc(r.field)}</td>` +
                            `<td>${esc(r.old)}</td><td>${esc(r.new)}</td><td>${esc(r.reason)}</td></tr>`
                    )
                    .join("");
                const catatan =
                    rows.length > batas
                        ? `<div class="hk-sub">Menampilkan ${batas} dari ${rows.length} baris. Selengkapnya di Form Edit, tab Audit Trail HRIS.</div>`
                        : "";
                $w.html(
                    '<div class="hk-tblwrap"><table class="hk-tbl"><thead><tr><th>Waktu</th><th>Oleh</th>' +
                        "<th>Field</th><th>Lama</th><th>Baru</th><th>Alasan</th></tr></thead><tbody>" +
                        baris +
                        "</tbody></table></div>" +
                        catatan
                );
                $w.attr("data-ok", "1");
            })
            .catch((e) => {
                console.error("HRIS Kartu Profil: riwayat gagal dimuat", e);
                if (masih_ada($w)) {
                    $w.html('<span class="hk-empty">Riwayat tidak dapat dimuat</span>');
                }
            });
    }

    function pasang_aksi(frm, $kartu) {
        $kartu.on("click", ".hk-tab", function () {
            const id = $(this).attr("data-tab");
            tab_aktif = { nama: frm.doc.name, id: id };
            $kartu.find(".hk-tab").removeClass("aktif");
            $(this).addClass("aktif");
            $kartu.find(".hk-panel").hide().filter('[data-tab="' + id + '"]').show();
            if (id === "riwayat") {
                isi_penuh(frm, $kartu);
            }
        });
        $kartu.on("click", ".hk-edit", () => tampil(frm, "form"));
        $kartu.on("click", ".hk-ganti", () => ganti_foto(frm));
        $kartu.on("click", ".hk-lihat", () => $kartu.find('.hk-tab[data-tab="riwayat"]').trigger("click"));
        isi_ringkas(frm, $kartu);
        $kartu.on("click", ".hk-pen", function () {
            edit_seksi(frm, $kartu, $(this).closest(".hk-sec"));
        });
    }

    // ---------- Render ----------
    function atur_kelas(frm, aktif) {
        try {
            $(frm.page.wrapper).toggleClass("hk-mode-kartu", !!aktif && !frm.is_dirty());
        } catch (e) {
            /* abaikan */
        }
    }
    function paksa_form(frm) {
        const $induk = $(frm.wrapper);
        $induk.find(".hk-kartu").remove();
        $induk.find(".form-layout").first().show();
        atur_kelas(frm, false);
    }

    function render(frm) {
        const $induk = $(frm.wrapper);
        const $layout = $induk.find(".form-layout").first();
        $induk.find(".hk-kartu").remove();
        if (!$layout.length) {
            return;
        }
        if (frm.is_new() || baca_pref() === "form") {
            $layout.show();
            atur_kelas(frm, false);
            return;
        }
        try {
            const $kartu = $(bangun(frm));
            $layout.before($kartu);
            $layout.hide();
            pasang_aksi(frm, $kartu);
            atur_kelas(frm, true);
        } catch (e) {
            console.error("HRIS Kartu Profil gagal, kembali ke form biasa", e);
            paksa_form(frm);
        }
    }

    function tampil(frm, mode) {
        simpan_pref(mode);
        render(frm);
    }

    function tombol_tampilan(frm) {
        if (frm.is_new()) {
            return;
        }
        frm.add_custom_button(__("Kartu Profil"), () => tampil(frm, "kartu"), __("Tampilan"));
        frm.add_custom_button(__("Form Edit"), () => tampil(frm, "form"), __("Tampilan"));
    }

    frappe.ui.form.on(DOCTYPE, {
        refresh(frm) {
            $(frm.wrapper).addClass("hk-form-warna");
            tombol_tampilan(frm);
            render(frm);
        },
    });
})();
