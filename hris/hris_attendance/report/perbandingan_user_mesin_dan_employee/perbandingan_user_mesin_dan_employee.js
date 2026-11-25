frappe.query_reports["Perbandingan User Mesin dan Employee"] = {
filters: [
{
fieldname: "kategori",
label: __("Kategori"),
fieldtype: "Select",
options: ["", "A", "B", "C", "D", "E", "F"].join("\n"),
},
],
};
