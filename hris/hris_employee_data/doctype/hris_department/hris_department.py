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

def on_update(self):
super().on_update()

def on_trash(self):
super().on_trash()


def on_doctype_update():
frappe.db.add_index("HRIS Department", ["lft", "rgt"])
