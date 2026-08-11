import frappe


def get_context(context):
	context.no_cache = 1
	context.code = frappe.form_dict.get("code") or ""
	path = frappe.request.path if frappe.request else ""
	if "/sample/" in path:
		context.code = path.split("/sample/", 1)[-1].strip("/")
