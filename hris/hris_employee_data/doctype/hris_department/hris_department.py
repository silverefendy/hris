import frappe
from frappe import _
from frappe.utils.nestedset import NestedSet, get_root_of


class HRISDepartment(NestedSet):
    nsm_parent_field = "parent_department"

    def autoname(self):
        if self.company:
            abbr = frappe.get_cached_value("Company", self.company, "abbr")
            self.name = "{0} - {1}".format(self.department_name, abbr)
        else:
            self.name = self.department_name

    def validate(self):
        self.department_name = (self.department_name or "").strip()
        self._cek_kunci_sinkron()
        if not self.parent_department:
            root = get_root_of("HRIS Department")
            if root and root != self.name:
                self.parent_department = root
        if self.parent_department:
            if not frappe.db.get_value("HRIS Department", self.parent_department, "is_group"):
                frappe.throw(
                    _("Induk {0} bukan Department berstatus Is Group.").format(self.parent_department)
                )
            if not self.company:
                frappe.throw(_("Company wajib diisi untuk Department selain akar."))

    def _cek_kunci_sinkron(self):
        if self.is_new() or not self.erpnext_department:
            return
        for kolom, label in (("department_name", "Nama Department"), ("company", "Company")):
            if self.has_value_changed(kolom):
                frappe.throw(
                    _("{0} tidak boleh diubah setelah tersinkron ke Department ERPNext.").format(label)
                )

    def on_update(self):
        super().on_update()
        if self.flags.skip_sync:
            return
        from hris.hris_employee_data.services.department_sync import sinkron_dokumen

        sinkron_dokumen(self)

    def on_trash(self):
        super().on_trash()


def on_doctype_update():
    frappe.db.add_index("HRIS Department", ["lft", "rgt"])
