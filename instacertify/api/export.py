import frappe
from frappe import _


@frappe.whitelist()
def export_doctype_excel(doctype: str, filters: str | None = None):
	"""Admin / All Ops Manager excel export helper."""
	roles = set(frappe.get_roles())
	if not roles.intersection({"IC Admin", "IC All Ops Manager", "System Manager", "Administrator"}):
		frappe.throw(_("Not permitted to export"), frappe.PermissionError)

	allowed = {
		"IC Lead",
		"IC Quotation",
		"IC Project",
		"IC Test Request",
		"IC Asset",
		"IC Lab",
		"IC Consultant",
		"IC Service",
	}
	if doctype not in allowed:
		frappe.throw(_("Export not allowed for this DocType"))

	import json

	flt = json.loads(filters) if filters else []
	rows = frappe.get_all(doctype, filters=flt, fields=["*"], limit_page_length=5000)
	return rows
