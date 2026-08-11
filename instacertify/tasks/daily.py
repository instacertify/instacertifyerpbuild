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


def invoice_reminders_and_recurring():
	"""Zoho-style automatic reminders + recurring invoice generation."""
	today = frappe.utils.today()

	# Overdue
	overdue = frappe.get_all(
		"IC Invoice",
		filters={
			"docstatus": 1,
			"status": ["in", ["Sent", "Partially Paid", "Approved"]],
			"due_date": ["<", today],
			"balance_due": [">", 0],
		},
		pluck="name",
	)
	for name in overdue:
		frappe.db.set_value("IC Invoice", name, "status", "Overdue")

	# Auto reminders
	remindable = frappe.get_all(
		"IC Invoice",
		filters={
			"docstatus": 1,
			"auto_reminders": 1,
			"status": ["in", ["Sent", "Partially Paid", "Overdue"]],
			"balance_due": [">", 0],
		},
		fields=["name", "due_date"],
	)
	for row in remindable:
		if not row.due_date:
			continue
		# remind on due date and every 7 days after
		days = frappe.utils.date_diff(today, row.due_date)
		if days < 0:
			continue
		if days == 0 or days % 7 == 0:
			try:
				from instacertify.api.invoice import send_reminder

				send_reminder(row.name)
			except Exception:
				frappe.log_error(frappe.get_traceback(), "IC Invoice Reminder")

	# Recurring
	recurring = frappe.get_all(
		"IC Invoice",
		filters={"docstatus": 1, "is_recurring": 1, "next_recur_date": ["<=", today], "is_credit_note": 0},
		pluck="name",
	)
	for name in recurring:
		src = frappe.get_doc("IC Invoice", name)
		clone = frappe.copy_doc(src)
		clone.status = "Draft"
		clone.payments = []
		clone.reminder_log = []
		clone.payment_link = None
		clone.payment_token = None
		clone.customer_portal_token = None
		clone.customer_portal_link = None
		clone.invoice_date = today
		clone.due_date = frappe.utils.add_days(today, 15)
		clone.title = f"{src.title} (Recurring)"
		clone.insert(ignore_permissions=True)
		src.db_set("next_recur_date", frappe.utils.add_days(today, src.recur_every_days or 30))
