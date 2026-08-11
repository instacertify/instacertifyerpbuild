import frappe
from frappe import _


@frappe.whitelist()
def convert_lead_to_customer(lead: str):
	doc = frappe.get_doc("IC Lead", lead)
	if doc.customer:
		return doc.customer

	customer = frappe.get_doc(
		{
			"doctype": "Customer",
			"customer_name": doc.company_name,
			"customer_type": "Company",
			"territory": "All Territories",
			"customer_group": "Commercial",
		}
	)
	# Optional custom fields if present
	for src, dst in [
		("gstin", "gstin"),
		("email", "email_id"),
		("phone", "mobile_no"),
	]:
		if hasattr(customer, dst) and doc.get(src):
			customer.set(dst, doc.get(src))

	customer.insert(ignore_permissions=True)
	doc.db_set(
		{
			"customer": customer.name,
			"status": "Won",
			"converted_on": frappe.utils.now_datetime(),
		}
	)
	frappe.msgprint(_("Customer {0} created").format(customer.name))
	return customer.name
