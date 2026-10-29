frappe.query_reports["HRIS Working Hour Ringkasan"] = {
    filters: [
        {
            fieldname: "from_date",
            label: __("Dari Tanggal"),
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.add_days(frappe.datetime.get_today(), -30),
        },
        {
            fieldname: "to_date",
            label: __("Sampai Tanggal"),
            fieldtype: "Date",
            reqd: 1,
            default: frappe.datetime.add_days(frappe.datetime.get_today(), -1),
        },
        { fieldname: "company", label: __("Company"), fieldtype: "Link", options: "Company" },
        { fieldname: "department", label: __("Department"), fieldtype: "Link", options: "Department" },
        { fieldname: "employee_group", label: __("Grup"), fieldtype: "Link", options: "HRIS Employee Group" },
        { fieldname: "employee", label: __("Karyawan"), fieldtype: "Link", options: "Employee" },
    ],
};
