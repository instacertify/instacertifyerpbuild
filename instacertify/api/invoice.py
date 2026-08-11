import secrets

import frappe
from frappe import _

from instacertify.utils.gst import determine_tax_profile


@frappe.whitelist()
def apply_customer_tax_defaults(customer: str, company_state: str | None = None):
	cust = frappe.get_doc("Customer", customer)
	# Best-effort country/state/gstin from standard or custom fields
	country = getattr(cust, "territory", None)
	billing_country = "India"
	billing_state = ""
	gstin = getattr(cust, "gstin", None) or ""

	# Try primary address
	addr_name = frappe.db.get_value(
		"Dynamic Link",
		{"link_doctype": "Customer", "link_name": customer, "parenttype": "Address"},
		"parent",
	)
	if addr_name:
		addr = frappe.get_doc("Address", addr_name)
		if addr.country and addr.country != "India":
			billing_country = "Other"
		billing_state = addr.state or ""
		if getattr(addr, "gstin", None):
			gstin = addr.gstin

	profile = determine_tax_profile(
		billing_country=billing_country,
		billing_state=billing_state,
		company_state=company_state or "Maharashtra",
		gst_category="Export" if billing_country != "India" else ("Registered" if gstin else "Unregistered"),
		customer_gstin=gstin,
		default_tax_rate=18,
	)
	return {
		"billing_country": billing_country,
		"billing_state": billing_state,
		"customer_gstin": gstin,
		"currency": profile["currency"],
		"gst_category": "Export" if billing_country != "India" else ("Registered" if gstin else "Unregistered"),
		"tax_type": profile["tax_type"],
		"place_of_supply": profile["place_of_supply"],
		"cgst_rate": profile["cgst_rate"],
		"sgst_rate": profile["sgst_rate"],
		"igst_rate": profile["igst_rate"],
		"is_reverse_charge": profile["is_reverse_charge"],
		"default_tax_rate": profile["default_tax_rate"],
		"gstin_valid": profile["gstin_valid"],
		"gstin_validation_message": profile["gstin_validation_message"],
	}


@frappe.whitelist()
def approve_invoice(name: str):
	roles = set(frappe.get_roles())
	if not roles.intersection({"IC Admin", "IC All Ops Manager", "System Manager", "Administrator"}):
		frappe.throw(_("Only Admin / All Ops Manager can approve invoices"), frappe.PermissionError)
	doc = frappe.get_doc("IC Invoice", name)
	doc.db_set("status", "Approved")
	return {"status": "Approved"}


@frappe.whitelist()
def send_payment_link(name: str):
	doc = frappe.get_doc("IC Invoice", name)
	if doc.docstatus != 1:
		frappe.throw(_("Submit the invoice first"))
	if not doc.payment_token:
		doc.db_set("payment_token", secrets.token_urlsafe(20))
		doc.reload()
	if not doc.customer_portal_token:
		doc.db_set("customer_portal_token", secrets.token_urlsafe(20))
		doc.reload()
	pay = frappe.utils.get_url(f"/pay-invoice/{doc.payment_token}")
	portal = frappe.utils.get_url(f"/invoice-portal/{doc.customer_portal_token}")
	doc.db_set({"payment_link": pay, "customer_portal_link": portal, "status": "Sent"})
	# email if possible
	email = frappe.db.get_value("Customer", doc.customer, "email_id")
	if email:
		frappe.sendmail(
			recipients=[email],
			subject=f"Invoice {doc.name} from InstaCertify",
			message=f"<p>Please view and pay your invoice.</p><p><a href='{pay}'>Pay now</a> · <a href='{portal}'>Invoice portal</a></p>",
			now=True,
		)
	return pay


@frappe.whitelist()
def send_reminder(name: str):
	doc = frappe.get_doc("IC Invoice", name)
	msg = f"Reminder: Invoice {doc.name} has balance due {doc.balance_due} {doc.currency}."
	doc.append("reminder_log", {"channel": "Email", "message": msg, "status": "Sent"})
	doc.save(ignore_permissions=True)
	email = frappe.db.get_value("Customer", doc.customer, "email_id")
	if email:
		frappe.sendmail(recipients=[email], subject=f"Payment reminder — {doc.name}", message=f"<p>{msg}</p><p>{doc.payment_link or ''}</p>", now=True)
	return {"ok": True}


@frappe.whitelist()
def create_credit_note(name: str):
	src = frappe.get_doc("IC Invoice", name)
	cn = frappe.copy_doc(src)
	cn.naming_series = "IC-CN-.YYYY.-.####"
	cn.is_credit_note = 1
	cn.against_invoice = src.name
	cn.status = "Draft"
	cn.payments = []
	cn.reminder_log = []
	cn.payment_link = None
	cn.payment_token = None
	cn.customer_portal_token = None
	cn.customer_portal_link = None
	cn.title = f"Credit Note for {src.name}"
	cn.insert()
	src.db_set("status", "Credited")
	return cn.name


@frappe.whitelist(allow_guest=True)
def get_invoice_portal(token: str):
	name = frappe.db.get_value("IC Invoice", {"customer_portal_token": token}, "name")
	if not name:
		frappe.throw(_("Invalid invoice link"), frappe.PermissionError)
	doc = frappe.get_doc("IC Invoice", name)
	return _serialize_invoice(doc)


@frappe.whitelist(allow_guest=True)
def get_payment_invoice(token: str):
	name = frappe.db.get_value("IC Invoice", {"payment_token": token}, "name")
	if not name:
		frappe.throw(_("Invalid payment link"), frappe.PermissionError)
	doc = frappe.get_doc("IC Invoice", name)
	return _serialize_invoice(doc)


@frappe.whitelist(allow_guest=True)
def record_portal_payment(token: str, amount: float, reference: str | None = None):
	name = frappe.db.get_value("IC Invoice", {"payment_token": token}, "name")
	if not name:
		frappe.throw(_("Invalid payment link"), frappe.PermissionError)
	doc = frappe.get_doc("IC Invoice", name)
	amount = float(amount or 0)
	if amount <= 0:
		frappe.throw(_("Enter a valid amount"))
	if amount > (doc.balance_due or 0) + 0.001:
		frappe.throw(_("Amount exceeds balance due"))
	doc.append(
		"payments",
		{
			"payment_date": frappe.utils.today(),
			"amount": amount,
			"mode": "Payment Link",
			"reference": reference or f"PORTAL-{secrets.token_hex(4).upper()}",
			"currency": doc.currency,
		},
	)
	doc.save(ignore_permissions=True)
	return _serialize_invoice(frappe.get_doc("IC Invoice", name))


def _serialize_invoice(doc):
	return {
		"name": doc.name,
		"title": doc.title,
		"customer_name": doc.customer_name,
		"status": doc.status,
		"currency": doc.currency,
		"invoice_date": doc.invoice_date,
		"due_date": doc.due_date,
		"tax_type": doc.tax_type,
		"place_of_supply": doc.place_of_supply,
		"gst_category": doc.gst_category,
		"subtotal": doc.subtotal,
		"tax_total": doc.tax_total,
		"grand_total": doc.grand_total,
		"paid_amount": doc.paid_amount,
		"balance_due": doc.balance_due,
		"payment_link": doc.payment_link,
		"items": [
			{
				"item_description": r.item_description,
				"hsn_sac": r.hsn_sac,
				"qty": r.qty,
				"rate": r.rate,
				"amount": r.amount,
				"tax_rate": r.tax_rate,
			}
			for r in doc.items or []
		],
		"payments": [
			{"payment_date": p.payment_date, "amount": p.amount, "mode": p.mode, "reference": p.reference}
			for p in doc.payments or []
		],
	}
