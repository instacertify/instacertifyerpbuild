import secrets

import frappe
from frappe import _


def _can_share_credentials():
	roles = set(frappe.get_roles())
	return bool(
		roles.intersection(
			{
				"IC Admin",
				"IC All Ops Manager",
				"IC Operations Manager",
				"IC Sales Person",
				"IC Customer Manager",
				"System Manager",
				"Administrator",
			}
		)
	)


@frappe.whitelist()
def share_project_portal(project: str):
	"""Generate / refresh customer project portal link."""
	if not _can_share_credentials():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	doc = frappe.get_doc("IC Project", project)
	if not doc.portal_token:
		doc.db_set("portal_token", secrets.token_urlsafe(24))
		doc.reload()
	link = frappe.utils.get_url(f"/customer-project/{doc.portal_token}")
	doc.db_set("customer_portal_link", link)
	return link


@frappe.whitelist()
def share_credentials(name: str):
	if not _can_share_credentials():
		frappe.throw(_("Not permitted to share customer credentials"), frappe.PermissionError)
	doc = frappe.get_doc("IC Customer Portal Account", name)
	if not doc.share_token:
		doc.db_set("share_token", secrets.token_urlsafe(20))
		doc.reload()
	link = frappe.utils.get_url(f"/customer-credentials/{doc.share_token}")
	doc.db_set(
		{
			"share_link": link,
			"shared_by": frappe.session.user,
			"shared_on": frappe.utils.now_datetime(),
			"status": "Shared",
		}
	)
	return link


@frappe.whitelist(allow_guest=True)
def get_customer_project(token: str):
	name = frappe.db.get_value("IC Project", {"portal_token": token}, "name")
	if not name:
		frappe.throw(_("Invalid project link"), frappe.PermissionError)
	doc = frappe.get_doc("IC Project", name)
	customer_name = frappe.db.get_value("Customer", doc.customer, "customer_name") or doc.customer
	cert = doc.certification_name or doc.service

	# Documents from linked checklist request + project documents
	documents = []
	reqs = frappe.get_all(
		"IC Customer Document Request",
		filters={"project": doc.name},
		fields=["name"],
		limit=5,
	)
	for req in reqs:
		rdoc = frappe.get_doc("IC Customer Document Request", req.name)
		for row in rdoc.checklist_items or []:
			documents.append(
				{
					"name": row.document_name,
					"status": row.status,
					"uploaded_file": row.uploaded_file,
					"idx": row.idx,
					"request": rdoc.name,
					"mandatory": row.is_mandatory,
				}
			)

	reports = [
		{
			"report_name": r.report_name,
			"report_file": r.report_file,
			"uploaded_on": r.uploaded_on,
		}
		for r in (doc.reports or [])
		if r.visible_to_customer
	]

	messages = [
		{"message": m.message, "posted_on": m.posted_on, "posted_by": m.posted_by}
		for m in (doc.messages or [])
		if m.visible_to_customer
	]

	credentials = []
	if doc.status == "Completed" and doc.show_credentials_when_complete:
		for row in doc.credentials or []:
			credentials.append(
				{
					"system_name": row.system_name,
					"username": row.username,
					"password": row.get_password("password") if row.password else "",
					"url": row.url,
					"notes": row.notes,
				}
			)
		# Also pull portal accounts
		for acc in frappe.get_all(
			"IC Customer Portal Account",
			filters={"project": doc.name, "status": ["in", ["Shared", "Active"]]},
			fields=["email", "temp_password", "status"],
		):
			credentials.append(
				{
					"system_name": "InstaCertify Customer Login",
					"username": acc.email,
					"password": acc.temp_password if doc.status == "Completed" else "••••••••",
					"url": "/customer-project/" + (doc.portal_token or ""),
					"notes": "Visible after project completion",
				}
			)

	return {
		"project": doc.name,
		"brand": "INSTACERTIFY",
		"customer_name": customer_name,
		"certification_name": cert,
		"percent_complete": doc.percent_complete or 0,
		"status": doc.status,
		"documents": documents,
		"reports": reports,
		"messages": messages,
		"credentials": credentials,
		"project_complete": doc.status == "Completed",
	}


@frappe.whitelist(allow_guest=True)
def upload_project_document(token: str, document_name: str, file_url: str, request: str | None = None):
	name = frappe.db.get_value("IC Project", {"portal_token": token}, "name")
	if not name:
		frappe.throw(_("Invalid project link"), frappe.PermissionError)

	# Prefer checklist request row
	filters = {"project": name}
	if request:
		filters["name"] = request
	reqs = frappe.get_all("IC Customer Document Request", filters=filters, pluck="name")
	updated = False
	for req_name in reqs:
		doc = frappe.get_doc("IC Customer Document Request", req_name)
		for row in doc.checklist_items:
			if row.document_name == document_name and row.status in ("Pending", "Rejected"):
				row.uploaded_file = file_url
				row.uploaded_on = frappe.utils.now_datetime()
				row.status = "Uploaded"
				updated = True
		if updated:
			pending = [r for r in doc.checklist_items if r.status == "Pending"]
			doc.status = "Partially Uploaded" if pending else "Completed"
			doc.save(ignore_permissions=True)
			break

	if not updated:
		# store on project documents table
		project = frappe.get_doc("IC Project", name)
		project.append(
			"documents",
			{
				"document_type": "PDF",
				"title": document_name,
				"attachment": file_url,
				"remarks": "Uploaded via customer portal",
			},
		)
		project.save(ignore_permissions=True)

	return {"ok": True}


@frappe.whitelist(allow_guest=True)
def get_shared_credentials(token: str):
	name = frappe.db.get_value("IC Customer Portal Account", {"share_token": token}, "name")
	if not name:
		frappe.throw(_("Invalid credentials link"), frappe.PermissionError)
	doc = frappe.get_doc("IC Customer Portal Account", name)
	project_status = frappe.db.get_value("IC Project", doc.project, "status")
	reveal = True
	if doc.reveal_only_when_project_complete and project_status != "Completed":
		reveal = False
	return {
		"customer_name": doc.customer_name,
		"project": doc.project,
		"email": doc.email,
		"password": doc.temp_password if reveal else None,
		"reveal": reveal,
		"project_status": project_status,
		"message": (
			"Login credentials are available."
			if reveal
			else "Credentials will be visible once the project is marked Completed."
		),
		"portal_link": frappe.db.get_value("IC Project", doc.project, "customer_portal_link"),
	}
