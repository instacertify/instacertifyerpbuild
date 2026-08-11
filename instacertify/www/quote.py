import frappe


def get_context(context):
	context.no_cache = 1
	context.token = frappe.form_dict.get("token") or ""
	# support /quote/<token> via path
	path = frappe.request.path if frappe.request else ""
	if path.startswith("/quote/"):
		context.token = path.split("/quote/", 1)[-1].strip("/")
