"""India → INR, Outside India → USD for InstaCertify quotes & invoices."""

from __future__ import annotations

import frappe


def currency_for_country(country: str | None) -> str:
	"""Return INR for India, USD for everywhere else."""
	if (country or "India").strip() == "India":
		return "INR"
	return "USD"


def resolve_customer_country(customer: str | None = None, lead: str | None = None, explicit: str | None = None) -> str:
	"""Best-effort country: explicit field → lead → customer address → India."""
	if explicit in ("India", "Other"):
		return explicit

	if lead and frappe.db.exists("IC Lead", lead):
		lead_country = frappe.db.get_value("IC Lead", lead, "country")
		if lead_country in ("India", "Other"):
			return lead_country

	if customer:
		addr_name = frappe.db.get_value(
			"Dynamic Link",
			{"link_doctype": "Customer", "link_name": customer, "parenttype": "Address"},
			"parent",
		)
		if addr_name:
			country = frappe.db.get_value("Address", addr_name, "country")
			if country and country != "India":
				return "Other"
			if country == "India":
				return "India"

	return "India"


def apply_quote_currency(doc):
	"""Force quotation currency from customer country. Sync child row currencies."""
	country = resolve_customer_country(
		customer=getattr(doc, "customer", None),
		lead=getattr(doc, "lead", None),
		explicit=getattr(doc, "customer_country", None),
	)
	doc.customer_country = country
	doc.currency = currency_for_country(country)
	for row in getattr(doc, "cost_lines", None) or []:
		row.currency = doc.currency
	for row in getattr(doc, "testing_lines", None) or []:
		row.currency = doc.currency
