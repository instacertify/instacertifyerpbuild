import frappe
from frappe import _
from frappe.desk.reportview import get_filters_cond, get_match_cond


@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def customer_link_query(doctype, txt, searchfield, start, page_len, filters):
	"""Searchable Customer dropdown — shows customer name + ID."""
	filters = filters or {}
	conditions = []

	# Optional country filter: India / Other (from quotation / invoice)
	country = filters.pop("customer_country", None) or filters.pop("billing_country", None)
	country_join = ""
	country_cond = ""
	if country in ("India", "Other"):
		country_join = """
			LEFT JOIN `tabDynamic Link` dl
				ON dl.link_doctype = 'Customer' AND dl.link_name = cust.name AND dl.parenttype = 'Address'
			LEFT JOIN `tabAddress` addr ON addr.name = dl.parent
		"""
		if country == "India":
			country_cond = " AND (addr.country IS NULL OR addr.country = '' OR addr.country = 'India') "
		else:
			country_cond = " AND addr.country IS NOT NULL AND addr.country != '' AND addr.country != 'India' "

	txt = txt or ""
	# Link dropdown: value = name, description = suggested label
	return frappe.db.sql(
		f"""
		SELECT DISTINCT
			cust.name,
			CONCAT(
				cust.customer_name,
				CASE
					WHEN IFNULL(cust.customer_group, '') != '' THEN CONCAT(' · ', cust.customer_group)
					ELSE ''
				END
			) AS description
		FROM `tabCustomer` cust
		{country_join}
		WHERE cust.docstatus < 2
			AND cust.disabled = 0
			AND (
				%(txt)s = ''
				OR cust.name LIKE %(txt)s
				OR cust.customer_name LIKE %(txt)s
				OR IFNULL(cust.customer_group, '') LIKE %(txt)s
			)
			{country_cond}
			{get_filters_cond("Customer", filters, conditions, ignore_permissions=True)}
			{get_match_cond("Customer")}
		ORDER BY
			CASE WHEN cust.customer_name LIKE %(exact)s THEN 0 ELSE 1 END,
			cust.customer_name ASC
		LIMIT %(start)s, %(page_len)s
		""",
		{
			"txt": f"%{txt}%" if txt else "",
			"exact": f"{txt}%",
			"start": start,
			"page_len": page_len or 20,
		},
	)


@frappe.whitelist()
def suggest_customers(txt: str | None = None, limit: int = 10, country: str | None = None):
	"""Typeahead suggestions for customer pickers and lead company name."""
	txt = (txt or "").strip()
	limit = min(int(limit or 10), 50)
	kwargs = {
		"filters": {"disabled": 0},
		"fields": ["name", "customer_name", "customer_group", "territory"],
		"order_by": "customer_name asc",
		"limit_page_length": limit,
	}
	if txt:
		kwargs["or_filters"] = [
			["customer_name", "like", f"%{txt}%"],
			["name", "like", f"%{txt}%"],
		]
	rows = frappe.get_all("Customer", **kwargs)

	# Optional country filter via address
	if country in ("India", "Other") and rows:
		filtered = []
		for row in rows:
			addr_country = frappe.db.get_value(
				"Address",
				{
					"name": (
						frappe.db.get_value(
							"Dynamic Link",
							{"link_doctype": "Customer", "link_name": row.name, "parenttype": "Address"},
							"parent",
						)
						or ""
					)
				},
				"country",
			)
			is_india = (not addr_country) or addr_country == "India"
			if country == "India" and is_india:
				filtered.append(row)
			elif country == "Other" and addr_country and addr_country != "India":
				filtered.append(row)
		rows = filtered

	return [
		{
			"value": r.name,
			"label": r.customer_name or r.name,
			"description": " · ".join([x for x in [r.customer_group, r.territory, r.name] if x]),
			"customer_name": r.customer_name,
		}
		for r in rows
	]


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
