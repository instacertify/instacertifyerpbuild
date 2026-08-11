"""Dummy evaluation data for InstaCertify demo use-cases (ERPNext v16)."""

from __future__ import annotations

import secrets

import frappe


def seed_demo_data(force: bool = False):
	"""Create sample customers, project portal, invoices for evaluation."""
	if frappe.db.exists("IC Project", {"project_name": "ABC Electronics — BIS CRS"}) and not force:
		return {"ok": True, "message": "Demo data already present"}

	_ensure_service()
	customers = _ensure_customers()
	project = _ensure_abc_project(customers["abc"])
	_ensure_portal_account(project, customers["abc"])
	_ensure_invoices(customers, project)
	_ensure_extra_projects(customers)
	return {"ok": True, "project": project, "portal": frappe.db.get_value("IC Project", project, "customer_portal_link")}


def _ensure_service():
	if not frappe.db.exists("IC Service", "BIS CRS Certification"):
		frappe.get_doc(
			{
				"doctype": "IC Service",
				"service_name": "BIS CRS Certification",
				"service_code": "BISCRS",
				"category": "Certification",
				"typical_timeline_days": 60,
				"certification_timeline_notes": "BIS CRS typical timeline 45–60 days depending on test reports.",
				"document_checklist": [
					{"document_name": "Company Registration", "is_mandatory": 1},
					{"document_name": "Authorization Letter", "is_mandatory": 1},
					{"document_name": "Test Report", "is_mandatory": 1},
					{"document_name": "Product Specification", "is_mandatory": 1},
					{"document_name": "Trademark Certificate", "is_mandatory": 0},
				],
			}
		).insert(ignore_permissions=True)


def _ensure_customers():
	out = {}
	specs = [
		("abc", "ABC Electronics", "India", "Maharashtra", "27AAAAA0000A1Z5"),
		("nova", "Nova Labs GmbH", "Other", "", ""),
		("green", "GreenChem India", "India", "Karnataka", "29AAAAA0000A1Z5"),
	]
	for key, name, country, state, gstin in specs:
		existing = frappe.db.get_value("Customer", {"customer_name": name}, "name")
		if existing:
			out[key] = existing
			continue
		doc = frappe.get_doc(
			{
				"doctype": "Customer",
				"customer_name": name,
				"customer_type": "Company",
				"territory": "All Territories",
				"customer_group": "Commercial",
			}
		)
		if hasattr(doc, "gstin") and gstin:
			doc.gstin = gstin
		doc.insert(ignore_permissions=True)
		out[key] = doc.name
		# store meta on a comment for tax helper fallbacks via Address if possible
		try:
			addr = frappe.get_doc(
				{
					"doctype": "Address",
					"address_title": name,
					"address_type": "Billing",
					"address_line1": "Demo Street 1",
					"city": "Mumbai" if country == "India" else "Berlin",
					"country": "India" if country == "India" else "Germany",
					"state": state or "",
					"links": [{"link_doctype": "Customer", "link_name": doc.name}],
				}
			)
			if hasattr(addr, "gstin") and gstin:
				addr.gstin = gstin
			addr.insert(ignore_permissions=True)
		except Exception:
			pass
	return out


def _ensure_abc_project(customer):
	existing = frappe.db.get_value("IC Project", {"project_name": "ABC Electronics — BIS CRS"}, "name")
	if existing:
		return existing

	token = secrets.token_urlsafe(24)
	link = frappe.utils.get_url(f"/customer-project/{token}")
	project = frappe.get_doc(
		{
			"doctype": "IC Project",
			"project_name": "ABC Electronics — BIS CRS",
			"customer": customer,
			"service": "BIS CRS Certification",
			"certification_name": "BIS CRS Certification",
			"status": "In Progress",
			"percent_complete": 65,
			"sales_person": "Administrator",
			"operations_manager": "Administrator",
			"customer_manager": "Administrator",
			"portal_token": token,
			"customer_portal_link": link,
			"show_credentials_when_complete": 1,
			"messages": [
				{
					"message": "Please provide updated Product Specification and Trademark Certificate to proceed.",
					"visible_to_customer": 1,
				}
			],
			"reports": [
				{"report_name": "Test Report", "report_file": "/files/demo-test-report.pdf", "visible_to_customer": 1},
				{"report_name": "Application Report", "report_file": "/files/demo-application-report.pdf", "visible_to_customer": 1},
			],
			"credentials": [
				{
					"system_name": "BIS Portal",
					"username": "abc.electronics",
					"password": "Demo@BIS2026",
					"url": "https://www.crsbis.in",
					"notes": "Shown to customer when project is Completed",
				}
			],
			"progress_log": [
				{"remarks": "Kickoff completed", "percent_complete": 20},
				{"remarks": "Documents partially received", "percent_complete": 45},
				{"remarks": "Testing in progress", "percent_complete": 65},
			],
		}
	)
	project.insert(ignore_permissions=True)

	# Document checklist request matching mockup
	req = frappe.get_doc(
		{
			"doctype": "IC Customer Document Request",
			"title": "BIS CRS Documents — ABC Electronics",
			"project": project.name,
			"customer": customer,
			"service": "BIS CRS Certification",
			"request_type": "Checklist Upload",
			"status": "Shared",
			"checklist_items": [
				{"document_name": "Company Registration", "is_mandatory": 1, "status": "Verified"},
				{"document_name": "Authorization Letter", "is_mandatory": 1, "status": "Uploaded"},
				{"document_name": "Test Report", "is_mandatory": 1, "status": "Uploaded"},
				{"document_name": "Product Specification", "is_mandatory": 1, "status": "Pending"},
				{"document_name": "Trademark Certificate", "is_mandatory": 0, "status": "Pending"},
			],
		}
	)
	req.insert(ignore_permissions=True)
	return project.name


def _ensure_portal_account(project, customer):
	if frappe.db.exists("IC Customer Portal Account", {"project": project}):
		return
	token = secrets.token_urlsafe(20)
	frappe.get_doc(
		{
			"doctype": "IC Customer Portal Account",
			"customer": customer,
			"project": project,
			"email": "portal@abcelectronics.demo",
			"temp_password": "Welcome@IC2026",
			"status": "Shared",
			"share_token": token,
			"share_link": frappe.utils.get_url(f"/customer-credentials/{token}"),
			"shared_by": "Administrator",
			"reveal_only_when_project_complete": 1,
		}
	).insert(ignore_permissions=True)


def _ensure_invoices(customers, project):
	# INR domestic invoice
	if not frappe.db.exists("IC Invoice", {"title": "BIS CRS Consulting — ABC Electronics"}):
		inv = frappe.get_doc(
			{
				"doctype": "IC Invoice",
				"title": "BIS CRS Consulting — ABC Electronics",
				"customer": customers["abc"],
				"project": project,
				"billing_country": "India",
				"billing_state": "Maharashtra",
				"company_state": "Maharashtra",
				"customer_gstin": "27AAAAA0000A1Z5",
				"gst_category": "Registered",
				"currency": "INR",
				"status": "Approved",
				"skip_approval": 1,
				"due_date": frappe.utils.add_days(frappe.utils.today(), 15),
				"items": [
					{
						"item_description": "BIS CRS Consulting",
						"hsn_sac": "9983",
						"qty": 1,
						"rate": 75000,
						"tax_rate": 18,
					},
					{
						"item_description": "Testing Coordination",
						"hsn_sac": "9983",
						"qty": 1,
						"rate": 18000,
						"tax_rate": 18,
					},
				],
				"auto_reminders": 1,
			}
		)
		inv.insert(ignore_permissions=True)
		inv.submit()

	# USD export invoice
	if not frappe.db.exists("IC Invoice", {"title": "Consulting Export — Nova Labs"}):
		inv = frappe.get_doc(
			{
				"doctype": "IC Invoice",
				"title": "Consulting Export — Nova Labs",
				"customer": customers["nova"],
				"billing_country": "Other",
				"billing_state": "",
				"company_state": "Maharashtra",
				"gst_category": "Export",
				"currency": "USD",
				"status": "Sent",
				"skip_approval": 1,
				"due_date": frappe.utils.add_days(frappe.utils.today(), 20),
				"items": [
					{
						"item_description": "ISO Consulting Package",
						"hsn_sac": "9983",
						"qty": 1,
						"rate": 2200,
						"tax_rate": 0,
					}
				],
				"payments": [
					{
						"payment_date": frappe.utils.today(),
						"amount": 1000,
						"mode": "Payment Link",
						"reference": "DEMO-PARTIAL-1",
						"currency": "USD",
					}
				],
				"auto_reminders": 1,
			}
		)
		inv.insert(ignore_permissions=True)
		inv.submit()
		from instacertify.api.invoice import send_payment_link

		send_payment_link(inv.name)


def _ensure_extra_projects(customers):
	# data for person chart
	samples = [
		("Nova Labs Testing", customers["nova"], "Product Testing", 40, "Open", "Administrator"),
		("GreenChem ISO 9001", customers["green"], "ISO 9001 Certification", 80, "In Progress", "Administrator"),
	]
	for name, customer, service, pct, status, owner in samples:
		if frappe.db.exists("IC Project", {"project_name": name}):
			continue
		if not frappe.db.exists("IC Service", service):
			continue
		frappe.get_doc(
			{
				"doctype": "IC Project",
				"project_name": name,
				"customer": customer,
				"service": service,
				"certification_name": service,
				"percent_complete": pct,
				"status": status,
				"sales_person": owner,
				"operations_manager": owner,
			}
		).insert(ignore_permissions=True)


@frappe.whitelist()
def run_seed_demo():
	if "System Manager" not in frappe.get_roles() and "IC Admin" not in frappe.get_roles() and frappe.session.user != "Administrator":
		frappe.throw("Not permitted", frappe.PermissionError)
	return seed_demo_data(force=False)
