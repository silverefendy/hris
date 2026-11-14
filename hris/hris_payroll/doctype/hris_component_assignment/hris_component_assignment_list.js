frappe.listview_settings["HRIS Component Assignment"] = {
    add_fields: ["status", "is_active"],
    get_indicator(doc) {
        if (!cint(doc.is_active)) return [__("Nonaktif"), "gray", "is_active,=,0"];
        if (doc.status === "Berlaku") return [__("Berlaku"), "green", "status,=,Berlaku"];
        return [__("Tidak Berlaku"), "red", "status,=,Tidak Berlaku"];
    },
};
