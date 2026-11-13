frappe.query_reports["HRIS Biaya Tenaga Kerja"] = {
    filters: [
        { fieldname: "payroll_period", label: __("Payroll Period"), fieldtype: "Link", options: "HRIS Payroll Period", reqd: 1 },
        { fieldname: "group_by", label: __("Kelompokkan"), fieldtype: "Select", options: "Department\nEmployee Group", default: "Department" },
        { fieldname: "parent_department", label: __("Department Induk"), fieldtype: "Link", options: "HRIS Department" },
        { fieldname: "status", label: __("Status Slip"), fieldtype: "Select", options: "Semua\nDraft\nDitinjau\nFinal", default: "Semua" },
    ],
};
