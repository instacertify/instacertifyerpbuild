import frappe


def _is_elevated():
	roles = set(frappe.get_roles())
	return bool(roles.intersection({"IC Admin", "IC All Ops Manager", "System Manager", "Administrator"}))


def _is_ops():
	return "IC Operations Manager" in frappe.get_roles()


def _is_sales():
	return "IC Sales Person" in frappe.get_roles()


def get_lead_query(user):
	if not user:
		user = frappe.session.user
	if _is_elevated() or user == "Administrator":
		return ""
	if _is_sales():
		return f"(`tabIC Lead`.assigned_to = {frappe.db.escape(user)} OR `tabIC Lead`.owner = {frappe.db.escape(user)})"
	return ""


def has_lead_permission(doc, ptype=None, user=None):
	if not user:
		user = frappe.session.user
	if _is_elevated() or user == "Administrator":
		return True
	if _is_sales():
		return doc.assigned_to == user or doc.owner == user
	return True


def get_quotation_query(user):
	if not user:
		user = frappe.session.user
	if _is_elevated() or user == "Administrator" or _is_ops():
		return ""
	if _is_sales():
		return f"(`tabIC Quotation`.sales_person = {frappe.db.escape(user)} OR `tabIC Quotation`.owner = {frappe.db.escape(user)})"
	return ""


def has_quotation_permission(doc, ptype=None, user=None):
	if not user:
		user = frappe.session.user
	if _is_elevated() or user == "Administrator" or _is_ops():
		return True
	if _is_sales():
		return doc.sales_person == user or doc.owner == user
	return True


def get_project_query(user):
	if not user:
		user = frappe.session.user
	if _is_elevated() or user == "Administrator" or _is_ops():
		return ""
	if _is_sales():
		return f"(`tabIC Project`.sales_person = {frappe.db.escape(user)} OR `tabIC Project`.owner = {frappe.db.escape(user)})"
	return ""


def has_project_permission(doc, ptype=None, user=None):
	if not user:
		user = frappe.session.user
	if _is_elevated() or user == "Administrator" or _is_ops():
		return True
	if _is_sales():
		return doc.sales_person == user or doc.owner == user
	return True


def get_test_request_query(user):
	if not user:
		user = frappe.session.user
	if _is_elevated() or user == "Administrator" or _is_ops():
		return ""
	if _is_sales():
		return f"(`tabIC Test Request`.sales_person = {frappe.db.escape(user)} OR `tabIC Test Request`.owner = {frappe.db.escape(user)})"
	return ""
