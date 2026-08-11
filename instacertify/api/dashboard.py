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

	def count_status(doctype, status_list, owner_field=None):
		filters = [["status", "in", status_list]]
		if owner_field and is_sales and not elevated:
			filters.append([owner_field, "=", user])
		try:
			return len(frappe.get_all(doctype, filters=filters, limit=500))
		except Exception:
			return 0

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
			"label": _("Open Invoices"),
			"value": count_status(
				"IC Invoice", ["Approved", "Sent", "Partially Paid", "Overdue", "Pending Approval"], None
			),
			"color": "#6C5CE7",
			"route": "/app/ic-invoice",
		},
	]

	tasks = []
	for q in frappe.get_all(
		"IC Quotation",
		filters=(
			[["status", "in", ["Shared", "Changes Requested"]]]
			+ ([["sales_person", "=", user]] if is_sales and not elevated else [])
		),
		fields=["name", "title", "status", "customer_name", "modified"],
		limit=6,
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

	project_filters = [["status", "in", ["Open", "In Progress"]]]
	if is_sales and not elevated:
		project_filters.append(["sales_person", "=", user])
	elif is_ops and not elevated:
		project_filters.append(["operations_manager", "=", user])

	projects = frappe.get_all(
		"IC Project",
		filters=project_filters,
		fields=[
			"name",
			"project_name",
			"status",
			"percent_complete",
			"customer",
			"sales_person",
			"operations_manager",
			"customer_manager",
		],
		limit=20,
		order_by="modified desc",
	)

	for p in projects[:8]:
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

	# Person chart — workload by assignee
	person_map = {}
	for p in projects:
		for field in ("sales_person", "operations_manager", "customer_manager"):
			person = p.get(field)
			if not person:
				continue
			bucket = person_map.setdefault(
				person, {"user": person, "projects": 0, "avg_progress": 0, "_progress_sum": 0}
			)
			bucket["projects"] += 1
			bucket["_progress_sum"] += p.percent_complete or 0
	person_chart = []
	for user_id, bucket in person_map.items():
		label = frappe.db.get_value("User", user_id, "full_name") or user_id
		avg = round(bucket["_progress_sum"] / bucket["projects"], 1) if bucket["projects"] else 0
		person_chart.append(
			{
				"user": user_id,
				"label": label,
				"projects": bucket["projects"],
				"avg_progress": avg,
			}
		)
	person_chart.sort(key=lambda x: x["projects"], reverse=True)

	project_progress = [
		{
			"name": p.name,
			"label": p.project_name,
			"progress": p.percent_complete or 0,
			"owner": frappe.db.get_value("User", p.sales_person, "full_name") if p.sales_person else "—",
			"status": p.status,
		}
		for p in projects
	]

	return {
		"greeting": f"{greeting}, {full_name}",
		"roles": list(roles),
		"cards": cards,
		"tasks": tasks,
		"person_chart": person_chart,
		"project_progress": project_progress,
		"brand": {"primary": "#0B5FFF", "accent": "#FF7A00"},
	}
