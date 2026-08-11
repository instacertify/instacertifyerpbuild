import secrets

import frappe
from frappe import _


@frappe.whitelist()
def load_service_checklist(service: str):
	if not frappe.db.exists("IC Service", service):
		return []
	svc = frappe.get_doc("IC Service", service)
	return [
		{
			"document_name": row.document_name,
			"is_mandatory": row.is_mandatory,
			"instructions": row.instructions,
			"status": "Pending",
		}
		for row in svc.document_checklist or []
	]


@frappe.whitelist()
def share_document_request(name: str):
	doc = frappe.get_doc("IC Customer Document Request", name)
	if not doc.share_token:
		doc.db_set("share_token", secrets.token_urlsafe(24))
		doc.reload()
	link = frappe.utils.get_url(f"/docs-upload/{doc.share_token}")
	doc.db_set({"share_link": link, "status": "Shared"})
	return link


@frappe.whitelist(allow_guest=True)
def get_document_request(token: str):
	name = frappe.db.get_value("IC Customer Document Request", {"share_token": token}, "name")
	if not name:
		frappe.throw(_("Invalid document link"), frappe.PermissionError)
	doc = frappe.get_doc("IC Customer Document Request", name)
	return {
		"name": doc.name,
		"title": doc.title,
		"customer": doc.customer,
		"service": doc.service,
		"status": doc.status,
		"items": [
			{
				"idx": row.idx,
				"document_name": row.document_name,
				"is_mandatory": row.is_mandatory,
				"instructions": row.instructions,
				"status": row.status,
				"uploaded_file": row.uploaded_file,
			}
			for row in doc.checklist_items or []
		],
	}


@frappe.whitelist(allow_guest=True)
def upload_checklist_file(token: str, idx: int, file_url: str):
	name = frappe.db.get_value("IC Customer Document Request", {"share_token": token}, "name")
	if not name:
		frappe.throw(_("Invalid document link"), frappe.PermissionError)
	doc = frappe.get_doc("IC Customer Document Request", name)
	updated = False
	for row in doc.checklist_items:
		if row.idx == int(idx):
			row.uploaded_file = file_url
			row.uploaded_on = frappe.utils.now_datetime()
			row.status = "Uploaded"
			updated = True
			break
	if not updated:
		frappe.throw(_("Checklist row not found"))
	pending = [r for r in doc.checklist_items if r.status == "Pending"]
	doc.status = "Partially Uploaded" if pending else "Completed"
	doc.save(ignore_permissions=True)
	return {"status": doc.status}
