import secrets

import frappe
from frappe import _


@frappe.whitelist()
def generate_sample_qr(name: str):
	doc = frappe.get_doc("IC Test Request", name)
	from instacertify.utils.qrcode import generate_sample_qr as _gen

	_gen(doc)
	return {"sample_tracking_code": doc.sample_tracking_code, "sample_qr_code": doc.sample_qr_code}


@frappe.whitelist()
def share_report(name: str):
	doc = frappe.get_doc("IC Test Request", name)
	if not doc.report_file:
		frappe.throw(_("Please upload the report first"))
	if not doc.report_share_token:
		doc.db_set("report_share_token", secrets.token_urlsafe(24))
		doc.reload()
	link = frappe.utils.get_url(f"/report/{doc.report_share_token}")
	doc.db_set({"report_share_link": link, "sample_status": "Shared with Customer"})
	return link


@frappe.whitelist()
def share_trf(name: str):
	doc = frappe.get_doc("IC Test Request", name)
	if not doc.report_share_token:
		doc.db_set("report_share_token", secrets.token_urlsafe(24))
		doc.reload()
	link = frappe.utils.get_url(f"/trf/{doc.report_share_token}")
	doc.db_set("trf_share_link", link)
	return link


@frappe.whitelist(allow_guest=True)
def get_report(token: str):
	name = frappe.db.get_value("IC Test Request", {"report_share_token": token}, "name")
	if not name:
		frappe.throw(_("Invalid report link"), frappe.PermissionError)
	doc = frappe.get_doc("IC Test Request", name)
	return {
		"name": doc.name,
		"title": doc.title,
		"customer": doc.customer,
		"test_name": doc.test_name,
		"lab": doc.lab,
		"report_file": doc.report_file,
		"sample_status": doc.sample_status,
		"qr_code": doc.qr_code,
	}


@frappe.whitelist(allow_guest=True)
def get_sample(code: str):
	name = frappe.db.get_value("IC Test Request", {"sample_tracking_code": code}, "name")
	if not name:
		frappe.throw(_("Sample not found"), frappe.DoesNotExistError)
	doc = frappe.get_doc("IC Test Request", name)
	return {
		"tracking_code": doc.sample_tracking_code,
		"title": doc.title,
		"test_name": doc.test_name,
		"sample_status": doc.sample_status,
		"lab": doc.lab,
		"sample_received_on": doc.sample_received_on,
		"dispatched_to_lab_on": doc.dispatched_to_lab_on,
		"testing_started_on": doc.testing_started_on,
		"report_available_on": doc.report_available_on,
	}


@frappe.whitelist(allow_guest=True)
def get_trf(token: str):
	name = frappe.db.get_value("IC Test Request", {"report_share_token": token}, "name")
	if not name:
		frappe.throw(_("Invalid TRF link"), frappe.PermissionError)
	doc = frappe.get_doc("IC Test Request", name)
	return {
		"name": doc.name,
		"title": doc.title,
		"customer": doc.customer,
		"test_name": doc.test_name,
		"applicable_standard": doc.applicable_standard,
		"no_of_samples": doc.no_of_samples,
		"lab": doc.lab,
		"accreditation": doc.accreditation,
		"testing_timeline": doc.testing_timeline,
		"remarks": doc.remarks,
	}
