import frappe


def get_context(context):
	context.no_cache = 1
	context.token = frappe.form_dict.get("token") or ""
	path = frappe.request.path if frappe.request else ""
	if "/invoice-portal/" in path:
		context.token = path.split("/invoice-portal/", 1)[-1].strip("/")
