import frappe
from frappe import _


@frappe.whitelist()
def get_home_dashboard():
	user = frappe.session.user
	roles = set(frappe.get_roles(user))
	full_name = frappe.db.get_value("User", user, "full_name") or user
	hour = frappe.utils.now_datetime().hour
	if hour < 12:
		greeting = _("Good morning")
	elif hour < 17:
		greeting = _("Good afternoon")
	else:
		greeting = _("Good evening")

	elevated = bool(roles.intersection({"IC Admin", "IC All Ops Manager", "System Manager", "Administrator"}))
	is_sales = "IC Sales Person" in roles
	is_ops = "IC Operations Manager" in roles

	def count(doctype, filters=None):
		try:
			return frappe.db.count(doctype, filters or {})
		except Exception:
			return 0

	lead_filters = {}
	quote_filters = {}
	project_filters = {}
	if is_sales and not elevated:
		lead_filters = [["assigned_to", "=", user]]
		quote_filters = [["sales_person", "=", user]]
		project_filters = [["sales_person", "=", user]]

	pending_quotes = count(
		"IC Quotation",
		{**(dict(quote_filters),), "status": ["in", ["Shared", "Changes Requested", "Finalised"]]},
	)
	# frappe.db.count doesn't take dict with list ops that way easily — use get_all
	def count_status(doctype, status_list, owner_field=None):
		filters = [["status", "in", status_list]]
		if owner_field and is_sales and not elevated:
			filters.append([owner_field, "=", user])
		return len(frappe.get_all(doctype, filters=filters, limit=500))

	cards = [
		{
			"label": _("Open Leads"),
			"value": count_status("IC Lead", ["Open", "Contacted", "Qualified"], "assigned_to"),
			"color": "#0B5FFF",
			"route": "/app/ic-lead",
		},
		{
			"label": _("Pending Quotes"),
			"value": count_status(
				"IC Quotation", ["Draft", "Finalised", "Shared", "Changes Requested"], "sales_person"
			),
			"color": "#FF7A00",
			"route": "/app/ic-quotation",
		},
		{
			"label": _("Active Projects"),
			"value": count_status("IC Project", ["Open", "In Progress"], "sales_person"),
			"color": "#128C7E",
			"route": "/app/ic-project",
		},
		{
			"label": _("Samples In Lab"),
			"value": count_status(
				"IC Test Request",
				["Sample Received", "Dispatched to Lab", "Testing In Process"],
				"sales_person",
			),
			"color": "#6C5CE7",
			"route": "/app/ic-test-request",
		},
	]

	tasks = []
	# Pending quote responses
	for q in frappe.get_all(
		"IC Quotation",
		filters=(
			[["status", "in", ["Shared", "Changes Requested"]]]
			+ ([[ "sales_person", "=", user]] if is_sales and not elevated else [])
		),
		fields=["name", "title", "status", "customer_name", "modified"],
		limit=8,
		order_by="modified desc",
	):
		tasks.append(
			{
				"type": "Quotation",
				"title": q.title or q.name,
				"status": q.status,
				"subtitle": q.customer_name,
				"route": f"/app/ic-quotation/{q.name}",
				"color": "#FF7A00",
			}
		)

	for p in frappe.get_all(
		"IC Project",
		filters=(
			[["status", "in", ["Open", "In Progress"]]]
			+ (
				[["sales_person", "=", user]]
				if is_sales and not elevated
				else ([["operations_manager", "=", user]] if is_ops and not elevated else [])
			)
		),
		fields=["name", "project_name", "status", "percent_complete", "customer"],
		limit=8,
		order_by="modified desc",
	):
		tasks.append(
			{
				"type": "Project",
				"title": p.project_name,
				"status": f"{p.status} · {p.percent_complete or 0}%",
				"subtitle": p.customer,
				"route": f"/app/ic-project/{p.name}",
				"color": "#0B5FFF",
			}
		)

	return {
		"greeting": f"{greeting}, {full_name}",
		"roles": list(roles),
		"cards": cards,
		"tasks": tasks,
		"brand": {"primary": "#0B5FFF", "accent": "#FF7A00"},
	}
