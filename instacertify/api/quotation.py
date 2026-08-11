import secrets

import frappe
from frappe import _

from instacertify.utils.currency import currency_for_country, resolve_customer_country


@frappe.whitelist()
def resolve_quote_currency(customer: str | None = None, lead: str | None = None, customer_country: str | None = None):
	"""India → INR, Outside India → USD."""
	country = resolve_customer_country(customer=customer, lead=lead, explicit=customer_country)
	return {"customer_country": country, "currency": currency_for_country(country)}


@frappe.whitelist()
def apply_template(template: str, quotation: str | None = None):
	tpl = frappe.get_doc("IC Quotation Template", template)
	data = {
		"service": tpl.service,
		"category": tpl.category,
		"scope_of_work": tpl.scope_of_work,
		"certification_timeline": tpl.certification_timeline,
		"force_majeure": tpl.force_majeure,
		"terms_and_conditions": tpl.terms_and_conditions,
		# Currency is decided by customer country, not template
		"cost_lines": [],
		"testing_lines": [],
	}
	for row in tpl.cost_lines or []:
		data["cost_lines"].append(
			{
				"cost_type": row.cost_type,
				"description": row.description,
				"qty": row.qty,
				"rate": row.rate,
				"amount": row.amount,
				"payable_to": row.payable_to,
				"counts_as_revenue": row.counts_as_revenue,
				"currency": row.currency or tpl.currency or "INR",
			}
		)
	if tpl.include_testing:
		data["testing_lines"].append(
			{
				"test_name": tpl.service,
				"applicable_standard": tpl.applicable_standard,
				"no_of_samples": tpl.no_of_samples or 1,
				"lab": tpl.default_lab,
				"testing_timeline": tpl.testing_timeline,
				"currency": tpl.currency or "INR",
			}
		)
	return data


@frappe.whitelist()
def share_quote(quotation: str):
	doc = frappe.get_doc("IC Quotation", quotation)
	if doc.docstatus != 1:
		frappe.throw(_("Please submit / finalise the quotation before sharing"))
	if not doc.share_token:
		doc.db_set("share_token", secrets.token_urlsafe(24))
		doc.reload()
	link = frappe.utils.get_url(f"/quote/{doc.share_token}")
	doc.db_set(
		{
			"share_link": link,
			"shared_on": frappe.utils.now_datetime(),
			"status": "Shared",
		}
	)
	return link


@frappe.whitelist(allow_guest=True)
def get_public_quote(token: str):
	name = frappe.db.get_value("IC Quotation", {"share_token": token}, "name")
	if not name:
		frappe.throw(_("Invalid or expired quote link"), frappe.PermissionError)
	doc = frappe.get_doc("IC Quotation", name)
	return {
		"name": doc.name,
		"title": doc.title,
		"customer_name": doc.customer_name or doc.customer,
		"service": doc.service,
		"category": doc.category,
		"scope_of_work": doc.scope_of_work,
		"certification_timeline": doc.certification_timeline,
		"cost_lines": [
			{
				"cost_type": r.cost_type,
				"description": r.description,
				"qty": r.qty,
				"rate": r.rate,
				"amount": r.amount,
				"payable_to": r.payable_to,
			}
			for r in doc.cost_lines or []
		],
		"testing_lines": [
			{
				"test_name": r.test_name,
				"applicable_standard": r.applicable_standard,
				"no_of_samples": r.no_of_samples,
				"testing_charges": r.testing_charges,
				"lab": r.lab,
				"accreditation": r.accreditation,
				"testing_timeline": r.testing_timeline,
			}
			for r in doc.testing_lines or []
		],
		"consulting_total": doc.consulting_total,
		"lab_testing_total": doc.lab_testing_total,
		"government_fees_total": doc.government_fees_total,
		"other_charges_total": doc.other_charges_total,
		"our_revenue_total": doc.our_revenue_total,
		"grand_total": doc.grand_total,
		"currency": doc.currency,
		"force_majeure": doc.force_majeure,
		"terms_and_conditions": doc.terms_and_conditions,
		"qr_code": doc.qr_code,
		"unique_barcode": doc.unique_barcode,
		"status": doc.status,
		"customer_remarks": doc.customer_remarks,
		"valid_till": doc.valid_till,
	}


@frappe.whitelist(allow_guest=True)
def respond_to_quote(token: str, action: str, remarks: str | None = None):
	name = frappe.db.get_value("IC Quotation", {"share_token": token}, "name")
	if not name:
		frappe.throw(_("Invalid quote link"), frappe.PermissionError)
	doc = frappe.get_doc("IC Quotation", name)
	if doc.status in ("Accepted", "Project Started"):
		frappe.throw(_("This quotation is already accepted"))

	action = (action or "").lower()
	if action == "accept":
		doc.db_set(
			{
				"status": "Accepted",
				"customer_response_on": frappe.utils.now_datetime(),
				"customer_remarks": remarks or "",
			}
		)
		from instacertify.utils.notifications import notify_quote_accepted

		notify_quote_accepted(doc.name)
		return {"status": "Accepted"}
	elif action == "request_changes":
		if not remarks:
			frappe.throw(_("Please provide remarks for the changes required"))
		doc.db_set(
			{
				"status": "Changes Requested",
				"customer_response_on": frappe.utils.now_datetime(),
				"customer_remarks": remarks,
			}
		)
		from instacertify.utils.notifications import notify_quote_changes_requested

		notify_quote_changes_requested(doc.name, remarks)
		return {"status": "Changes Requested"}
	elif action == "reject":
		doc.db_set(
			{
				"status": "Rejected",
				"customer_response_on": frappe.utils.now_datetime(),
				"customer_remarks": remarks or "",
			}
		)
		return {"status": "Rejected"}
	frappe.throw(_("Unknown action"))


@frappe.whitelist()
def start_project(quotation: str):
	doc = frappe.get_doc("IC Quotation", quotation)
	if doc.status != "Accepted":
		frappe.throw(_("Only accepted quotations can start a project"))
	if doc.project:
		return doc.project

	project = frappe.get_doc(
		{
			"doctype": "IC Project",
			"project_name": f"{doc.customer_name or doc.customer} — {doc.service}",
			"customer": doc.customer,
			"quotation": doc.name,
			"service": doc.service,
			"sales_person": doc.sales_person,
			"status": "Open",
			"start_date": frappe.utils.today(),
			"billing_links": [{"quotation": doc.name, "amount": doc.grand_total, "status": "Accepted"}],
		}
	)
	project.insert(ignore_permissions=True)

	# Seed document library from service checklist
	if doc.service and frappe.db.exists("IC Service", doc.service):
		svc = frappe.get_doc("IC Service", doc.service)
		if svc.document_checklist:
			req = frappe.get_doc(
				{
					"doctype": "IC Customer Document Request",
					"title": f"Documents for {project.project_name}",
					"project": project.name,
					"customer": doc.customer,
					"service": doc.service,
					"request_type": "Checklist Upload",
					"checklist_items": [
						{
							"document_name": row.document_name,
							"is_mandatory": row.is_mandatory,
							"instructions": row.instructions,
							"status": "Pending",
						}
						for row in svc.document_checklist
					],
				}
			)
			req.insert(ignore_permissions=True)

	doc.db_set({"project": project.name, "status": "Project Started"})
	return project.name


@frappe.whitelist()
def save_as_template(quotation: str, template_name: str):
	doc = frappe.get_doc("IC Quotation", quotation)
	if frappe.db.exists("IC Quotation Template", template_name):
		frappe.throw(_("Template name already exists"))

	tpl = frappe.get_doc(
		{
			"doctype": "IC Quotation Template",
			"template_name": template_name,
			"service": doc.service,
			"category": doc.category,
			"currency": doc.currency,
			"scope_of_work": doc.scope_of_work,
			"certification_timeline": doc.certification_timeline,
			"force_majeure": doc.force_majeure,
			"terms_and_conditions": doc.terms_and_conditions,
			"source_quotation": doc.name,
			"is_active": 1,
			"cost_lines": [
				{
					"cost_type": r.cost_type,
					"description": r.description,
					"qty": r.qty,
					"rate": r.rate,
					"amount": r.amount,
					"payable_to": r.payable_to,
					"counts_as_revenue": r.counts_as_revenue,
					"currency": r.currency,
				}
				for r in doc.cost_lines or []
			],
			"include_testing": 1 if doc.testing_lines else 0,
		}
	)
	if doc.testing_lines:
		first = doc.testing_lines[0]
		tpl.default_lab = first.lab
		tpl.applicable_standard = first.applicable_standard
		tpl.no_of_samples = first.no_of_samples
		tpl.testing_timeline = first.testing_timeline
	tpl.insert()
	return tpl.name
