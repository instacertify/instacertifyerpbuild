import frappe
from frappe import _


@frappe.whitelist()
def get_customer_history(customer: str):
	"""Past quotes, projects, deliverables for a customer (sales/ops/admin)."""
	if not customer:
		frappe.throw(_("Customer is required"))

	roles = set(frappe.get_roles())
	elevated = bool(roles.intersection({"IC Admin", "IC All Ops Manager", "System Manager", "Administrator"}))
	user = frappe.session.user

	quote_filters = {"customer": customer}
	project_filters = {"customer": customer}
	if "IC Sales Person" in roles and not elevated:
		# sales can see history for customers on their quotes/leads
		owned = frappe.get_all(
			"IC Quotation",
			filters={"customer": customer, "sales_person": user},
			limit=1,
		)
		lead_owned = frappe.get_all(
			"IC Lead",
			filters={"customer": customer, "assigned_to": user},
			limit=1,
		)
		if not owned and not lead_owned:
			frappe.throw(_("Not permitted for this customer"), frappe.PermissionError)
		quote_filters["sales_person"] = user

	quotes = frappe.get_all(
		"IC Quotation",
		filters=quote_filters,
		fields=["name", "title", "status", "grand_total", "currency", "service", "shared_on", "modified"],
		order_by="modified desc",
		limit=50,
	)
	projects = frappe.get_all(
		"IC Project",
		filters=project_filters,
		fields=["name", "project_name", "status", "percent_complete", "service", "modified"],
		order_by="modified desc",
		limit=50,
	)

	deliverables = []
	for p in projects:
		doc = frappe.get_doc("IC Project", p.name)
		for row in doc.documents or []:
			deliverables.append(
				{
					"project": p.name,
					"title": row.title,
					"document_type": row.document_type,
					"attachment": row.attachment,
					"uploaded_on": row.uploaded_on,
				}
			)

	invoices = []
	for p in projects:
		doc = frappe.get_doc("IC Project", p.name)
		for row in doc.billing_links or []:
			invoices.append(
				{
					"project": p.name,
					"invoice": row.invoice,
					"quotation": row.quotation,
					"amount": row.amount,
					"status": row.status,
				}
			)

	return {
		"customer": customer,
		"quotes": quotes,
		"projects": projects,
		"deliverables": deliverables,
		"billing": invoices,
	}
