import frappe


def expire_quotes():
	"""Mark shared quotes past valid_till as needing follow-up (status unchanged, create todo)."""
	today = frappe.utils.today()
	quotes = frappe.get_all(
		"IC Quotation",
		filters={"status": "Shared", "valid_till": ["<", today]},
		fields=["name", "sales_person", "title"],
	)
	for q in quotes:
		if not q.sales_person:
			continue
		exists = frappe.db.exists(
			"ToDo",
			{"reference_type": "IC Quotation", "reference_name": q.name, "status": "Open"},
		)
		if exists:
			continue
		frappe.get_doc(
			{
				"doctype": "ToDo",
				"description": f"Follow up expired quote: {q.title or q.name}",
				"allocated_to": q.sales_person,
				"reference_type": "IC Quotation",
				"reference_name": q.name,
				"status": "Open",
				"priority": "Medium",
			}
		).insert(ignore_permissions=True)
