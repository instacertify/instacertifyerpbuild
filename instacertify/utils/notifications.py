import frappe


def notify_quote_accepted(quotation_name: str):
	doc = frappe.get_doc("IC Quotation", quotation_name)
	recipients = set()
	if doc.sales_person:
		recipients.add(doc.sales_person)
	settings = frappe.get_single("IC Settings")
	if settings.notify_admin_on_quote_accept and settings.admin_notification_email:
		recipients.add(settings.admin_notification_email)
	# All IC Admins
	for user in frappe.get_all("Has Role", filters={"role": "IC Admin", "parenttype": "User"}, pluck="parent"):
		if user not in ("Guest", "Administrator"):
			recipients.add(user)

	recipients = [r for r in recipients if r]
	if not recipients:
		return

	subject = f"Quote Accepted: {doc.name} — {doc.customer_name or doc.customer}"
	message = frappe.render_template(
		"""
		<p>Hello,</p>
		<p>Customer has <b>accepted</b> quotation <b>{{ doc.name }}</b>.</p>
		<ul>
			<li>Customer: {{ doc.customer_name or doc.customer }}</li>
			<li>Service: {{ doc.service }}</li>
			<li>Grand Total: {{ doc.grand_total }} {{ doc.currency }}</li>
		</ul>
		<p>You can now start the project from the quotation.</p>
		""",
		{"doc": doc},
	)
	frappe.sendmail(recipients=list(recipients), subject=subject, message=message, delayed=False, now=True)


def notify_quote_changes_requested(quotation_name: str, remarks: str):
	doc = frappe.get_doc("IC Quotation", quotation_name)
	recipients = []
	if doc.sales_person:
		recipients.append(doc.sales_person)
	if not recipients:
		return
	frappe.sendmail(
		recipients=recipients,
		subject=f"Quote Changes Requested: {doc.name}",
		message=f"<p>Customer requested changes on {doc.name}.</p><p><b>Remarks:</b> {frappe.utils.escape_html(remarks)}</p>",
		now=True,
	)
