frappe.listview_settings["HRIS Raw Log"] = {
    add_fields: ["review_status", "punch_role"],
    get_indicator(doc) {
        if (doc.punch_role === "Diabaikan Otomatis") {
            return [__("Diabaikan Otomatis"), "darkgrey", "punch_role,=,Diabaikan Otomatis"];
        }
        const colors = {
            "Menunggu": "gray",
            "Tidak Cocok": "red",
            "Disetujui": "green",
            "Ditolak": "purple",
            "Terkirim": "green",
        };
        const color = colors[doc.review_status] || "gray";
        return [__(doc.review_status), color, "review_status,=," + doc.review_status];
    },
};
