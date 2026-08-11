#!/usr/bin/env python3
"""Generate portal + Zoho-style invoice DocTypes for InstaCertify."""

from __future__ import annotations

import json
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1] / "instacertify"


def perm(role, read=1, write=1, create=1, delete=0, submit=0, cancel=0, amend=0, report=1, export=0, print_=1, email=1, share=1):
	return {
		"role": role,
		"read": read,
		"write": write,
		"create": create,
		"delete": delete,
		"submit": submit,
		"cancel": cancel,
		"amend": amend,
		"report": report,
		"export": export,
		"print": print_,
		"email": email,
		"share": share,
	}


def field(fieldname, label, fieldtype, **kwargs):
	f = {"fieldname": fieldname, "label": label, "fieldtype": fieldtype}
	f.update(kwargs)
	return f


def section(label, fieldname=None):
	return field(fieldname or label.lower().replace(" ", "_") + "_section", label, "Section Break")


def col():
	import os
	return {"fieldname": "column_break_" + os.urandom(3).hex(), "fieldtype": "Column Break"}


def write_doctype(module_folder, module_name, meta, py_extra="\tpass\n", js_extra=None):
	name = meta["name"]
	slug = name.lower().replace(" ", "_")
	folder = ROOT / module_folder / "doctype" / slug
	folder.mkdir(parents=True, exist_ok=True)
	(folder / "__init__.py").write_text("")
	meta.setdefault("doctype", "DocType")
	meta.setdefault("module", module_name)
	meta.setdefault("engine", "InnoDB")
	meta.setdefault("track_changes", 1)
	meta.setdefault("creation", "2026-01-01 00:00:00.000000")
	meta.setdefault("modified", "2026-01-01 00:00:00.000000")
	meta.setdefault("modified_by", "Administrator")
	meta.setdefault("owner", "Administrator")
	meta.setdefault("sort_field", "modified")
	meta.setdefault("sort_order", "DESC")
	(folder / f"{slug}.json").write_text(json.dumps(meta, indent=1) + "\n")
	classname = name.replace(" ", "").replace("-", "")
	py = f'''# Copyright (c) 2026, InstaCertify and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class {classname}(Document):
{py_extra}'''
	(folder / f"{slug}.py").write_text(py)
	js = js_extra or dedent(
		f"""\
		frappe.ui.form.on('{name}', {{
			refresh(frm) {{}}
		}});
		"""
	)
	(folder / f"{slug}.js").write_text(js)
	print("Created", name)


staff_perms = [
	perm("IC Admin", delete=1, submit=1, cancel=1, amend=1, export=1),
	perm("System Manager", delete=1, submit=1, cancel=1, amend=1, export=1),
	perm("IC All Ops Manager", submit=1, cancel=1, export=1),
	perm("IC Operations Manager"),
	perm("IC Sales Person"),
	perm("IC Customer Manager"),
]


def main():
	# Ensure invoicing module
	(ROOT / "ic_invoicing" / "doctype").mkdir(parents=True, exist_ok=True)
	(ROOT / "ic_invoicing" / "__init__.py").write_text("")
	(ROOT / "ic_invoicing" / "doctype" / "__init__.py").write_text("")

	write_doctype(
		"ic_projects",
		"IC Projects",
		{
			"name": "IC Project Message",
			"istable": 1,
			"editable_grid": 1,
			"fields": [
				field("posted_on", "Posted On", "Datetime", default="Now", in_list_view=1),
				field("posted_by", "Posted By", "Link", options="User", default="__user", in_list_view=1),
				field("visible_to_customer", "Visible to Customer", "Check", default=1, in_list_view=1),
				field("message", "Message", "Small Text", reqd=1, in_list_view=1),
			],
			"permissions": [],
		},
	)

	write_doctype(
		"ic_projects",
		"IC Projects",
		{
			"name": "IC Project Report",
			"istable": 1,
			"editable_grid": 1,
			"fields": [
				field("report_name", "Report Name", "Data", reqd=1, in_list_view=1),
				field("report_file", "File", "Attach", reqd=1, in_list_view=1),
				field("visible_to_customer", "Visible to Customer", "Check", default=1, in_list_view=1),
				field("uploaded_on", "Uploaded On", "Datetime", default="Now", read_only=1),
			],
			"permissions": [],
		},
	)

	write_doctype(
		"ic_projects",
		"IC Projects",
		{
			"name": "IC Customer Portal Account",
			"autoname": "naming_series:",
			"naming_rule": 'By "Naming Series" field',
			"title_field": "customer_name",
			"search_fields": "customer,email,project,status",
			"fields": [
				field("naming_series", "Series", "Select", options="IC-CPA-.YYYY.-.####", default="IC-CPA-.YYYY.-.####", reqd=1),
				field("customer", "Customer", "Link", options="Customer", reqd=1, in_list_view=1),
				field("customer_name", "Customer Name", "Data", fetch_from="customer.customer_name", read_only=1),
				field("project", "Project", "Link", options="IC Project", reqd=1, in_list_view=1),
				col(),
				field("email", "Login Email", "Data", options="Email", reqd=1, in_list_view=1),
				field("temp_password", "Temporary Password", "Data", reqd=1),
				field("status", "Status", "Select", options="\nDraft\nShared\nActive\nRevoked", default="Draft", in_list_view=1),
				section("Sharing"),
				field("share_token", "Share Token", "Data", read_only=1, hidden=1),
				field("share_link", "Shareable Credentials Link", "Small Text", read_only=1),
				field("shared_by", "Shared By", "Link", options="User", read_only=1),
				field("shared_on", "Shared On", "Datetime", read_only=1),
				field("reveal_only_when_project_complete", "Reveal Login Only When Project Complete", "Check", default=1),
				section("Portal Access"),
				field("portal_user", "Linked Website User", "Link", options="User"),
				field("notes", "Notes", "Small Text"),
			],
			"permissions": staff_perms,
		},
		py_extra=dedent(
			"""
			\tdef before_insert(self):
				\tif not self.share_token:
					\timport secrets
					\tself.share_token = secrets.token_urlsafe(20)
			"""
		),
		js_extra=dedent(
			"""\
			frappe.ui.form.on('IC Customer Portal Account', {
				refresh(frm) {
					if (!frm.is_new()) {
						frm.add_custom_button(__('Share Credentials Link'), () => {
							frappe.call({
								method: 'instacertify.api.portal.share_credentials',
								args: { name: frm.doc.name },
								callback(r) {
									if (r.message) {
										frappe.msgprint(__('Share this link:<br><a href="{0}" target="_blank">{0}</a>', [r.message]));
										frm.reload_doc();
									}
								}
							});
						});
					}
				}
			});
			"""
		),
	)

	# Invoice child tables
	write_doctype(
		"ic_invoicing",
		"IC Invoicing",
		{
			"name": "IC Invoice Item",
			"istable": 1,
			"editable_grid": 1,
			"fields": [
				field("item_description", "Description", "Data", reqd=1, in_list_view=1),
				field("hsn_sac", "HSN/SAC", "Data", in_list_view=1),
				field("qty", "Qty", "Float", default=1, in_list_view=1),
				field("rate", "Rate", "Currency", options="currency", reqd=1, in_list_view=1),
				field("amount", "Amount", "Currency", options="currency", read_only=1, in_list_view=1),
				field("tax_rate", "Tax %", "Percent", in_list_view=1),
				field("tax_amount", "Tax Amount", "Currency", options="currency", read_only=1),
				field("currency", "Currency", "Link", options="Currency", default="INR"),
			],
			"permissions": [],
		},
	)

	write_doctype(
		"ic_invoicing",
		"IC Invoicing",
		{
			"name": "IC Invoice Payment",
			"istable": 1,
			"editable_grid": 1,
			"fields": [
				field("payment_date", "Date", "Date", default="Today", reqd=1, in_list_view=1),
				field("amount", "Amount", "Currency", options="currency", reqd=1, in_list_view=1),
				field("mode", "Mode", "Select", options="\nBank Transfer\nUPI\nCard\nCash\nPayment Link\nOther", default="Payment Link", in_list_view=1),
				field("reference", "Reference", "Data", in_list_view=1),
				field("currency", "Currency", "Link", options="Currency", default="INR"),
				field("notes", "Notes", "Small Text"),
			],
			"permissions": [],
		},
	)

	write_doctype(
		"ic_invoicing",
		"IC Invoicing",
		{
			"name": "IC Invoice Reminder",
			"istable": 1,
			"editable_grid": 1,
			"fields": [
				field("reminded_on", "Reminded On", "Datetime", default="Now", in_list_view=1),
				field("channel", "Channel", "Select", options="\nEmail\nSMS\nWhatsApp", default="Email", in_list_view=1),
				field("message", "Message", "Small Text", in_list_view=1),
				field("status", "Status", "Select", options="\nSent\nFailed", default="Sent", in_list_view=1),
			],
			"permissions": [],
		},
	)

	invoice_js = dedent(
		"""\
		frappe.ui.form.on('IC Invoice', {
			refresh(frm) {
				if (frm.doc.docstatus === 1 && ['Approved','Sent','Partially Paid'].includes(frm.doc.status)) {
					frm.add_custom_button(__('Send Payment Link'), () => {
						frappe.call({
							method: 'instacertify.api.invoice.send_payment_link',
							args: { name: frm.doc.name },
							callback(r) {
								if (r.message) frappe.msgprint(__('Payment link:<br><a href="{0}" target="_blank">{0}</a>', [r.message]));
								frm.reload_doc();
							}
						});
					}, __('Actions'));
					frm.add_custom_button(__('Send Reminder'), () => {
						frappe.call({
							method: 'instacertify.api.invoice.send_reminder',
							args: { name: frm.doc.name },
							callback() { frm.reload_doc(); }
						});
					}, __('Actions'));
				}
				if (frm.doc.docstatus === 0 && frm.doc.status === 'Pending Approval') {
					frm.add_custom_button(__('Approve Invoice'), () => {
						frappe.call({
							method: 'instacertify.api.invoice.approve_invoice',
							args: { name: frm.doc.name },
							callback() { frm.reload_doc(); }
						});
					}, __('Actions'));
				}
				if (frm.doc.docstatus === 1 && frm.doc.status !== 'Credited') {
					frm.add_custom_button(__('Create Credit Note'), () => {
						frappe.call({
							method: 'instacertify.api.invoice.create_credit_note',
							args: { name: frm.doc.name },
							callback(r) {
								if (r.message) frappe.set_route('Form', 'IC Invoice', r.message);
							}
						});
					}, __('Actions'));
				}
			},
			customer(frm) {
				if (!frm.doc.customer) return;
				frappe.call({
					method: 'instacertify.api.invoice.apply_customer_tax_defaults',
					args: { customer: frm.doc.customer, company_state: frm.doc.company_state },
					callback(r) {
						if (!r.message) return;
						Object.entries(r.message).forEach(([k, v]) => frm.set_value(k, v));
					}
				});
			}
		});

		frappe.ui.form.on('IC Invoice Item', {
			qty(frm, cdt, cdn) { recalc_row(frm, cdt, cdn); },
			rate(frm, cdt, cdn) { recalc_row(frm, cdt, cdn); },
			tax_rate(frm, cdt, cdn) { recalc_row(frm, cdt, cdn); }
		});

		function recalc_row(frm, cdt, cdn) {
			const row = locals[cdt][cdn];
			const amount = (row.qty || 0) * (row.rate || 0);
			frappe.model.set_value(cdt, cdn, 'amount', amount);
			frappe.model.set_value(cdt, cdn, 'tax_amount', amount * ((row.tax_rate || 0) / 100));
		}
		"""
	)

	invoice_py = dedent(
		"""
		\tdef validate(self):
			\tfrom instacertify.utils.gst import apply_gst_and_currency
			\tapply_gst_and_currency(self)
			\tself.calculate_totals()

		\tdef calculate_totals(self):
			\tsubtotal = tax = 0
			\tfor row in self.items or []:
				\trow.amount = (row.qty or 0) * (row.rate or 0)
				\trow.tax_amount = (row.amount or 0) * ((row.tax_rate or 0) / 100.0)
				\tsubtotal += row.amount or 0
				\ttax += row.tax_amount or 0
			\tself.subtotal = subtotal
			\tself.tax_total = tax
			\tself.grand_total = subtotal + tax - (self.discount_amount or 0)
			\tpaid = sum((p.amount or 0) for p in self.payments or [])
			\tself.paid_amount = paid
			\tself.balance_due = (self.grand_total or 0) - paid
			\tif self.is_credit_note:
				\treturn
			\tif self.balance_due <= 0 and self.grand_total:
				\tself.status = "Paid"
			\telif paid > 0:
				\tself.status = "Partially Paid"

		\tdef before_submit(self):
			\tif self.status == "Draft":
				\tself.status = "Pending Approval"

		\tdef on_submit(self):
			\tif self.status in ("Draft", "Pending Approval") and self.skip_approval:
				\tself.db_set("status", "Approved")
		"""
	)

	write_doctype(
		"ic_invoicing",
		"IC Invoicing",
		{
			"name": "IC Invoice",
			"autoname": "naming_series:",
			"naming_rule": 'By "Naming Series" field',
			"is_submittable": 1,
			"title_field": "title",
			"search_fields": "customer,status,currency,gst_category",
			"fields": [
				field("naming_series", "Series", "Select", options="IC-INV-.YYYY.-.####\nIC-CN-.YYYY.-.####", default="IC-INV-.YYYY.-.####", reqd=1),
				field("title", "Title", "Data", reqd=1, in_list_view=1),
				field("status", "Status", "Select", options="\nDraft\nPending Approval\nApproved\nSent\nPartially Paid\nPaid\nOverdue\nCredited\nCancelled", default="Draft", reqd=1, in_list_view=1, in_standard_filter=1),
				field("is_credit_note", "Is Credit Note", "Check", default=0),
				field("against_invoice", "Against Invoice", "Link", options="IC Invoice"),
				col(),
				field("invoice_date", "Invoice Date", "Date", default="Today", reqd=1),
				field("due_date", "Due Date", "Date"),
				field("project", "Project", "Link", options="IC Project"),
				field("quotation", "Quotation", "Link", options="IC Quotation"),
				section("Customer"),
				field("customer", "Customer", "Link", options="Customer", reqd=1, in_list_view=1),
				field("customer_name", "Customer Name", "Data", fetch_from="customer.customer_name", read_only=1),
				field("customer_gstin", "Customer GSTIN", "Data"),
				field("billing_country", "Billing Country", "Select", options="\nIndia\nOther", default="India", reqd=1),
				field("billing_state", "Billing State / Place of Supply", "Data"),
				col(),
				field("company_state", "Company State", "Data", default="Maharashtra"),
				field("currency", "Currency", "Link", options="Currency", default="INR", reqd=1, in_list_view=1),
				field("conversion_rate", "Exchange Rate", "Float", default=1),
				field("skip_approval", "Skip Approval (Auto Approve)", "Check", default=0),
				section("GST Determination"),
				field("gst_category", "GST Category", "Select", options="\nRegistered\nUnregistered\nExport\nSEZ\nExempt", default="Registered"),
				field("tax_type", "Tax Type", "Select", options="\nCGST+SGST\nIGST\nExport (Zero Rated)\nExempt\nReverse Charge", read_only=1),
				field("place_of_supply", "Place of Supply", "Data", read_only=1),
				field("is_reverse_charge", "Reverse Charge Applicable", "Check", default=0, read_only=1),
				col(),
				field("cgst_rate", "CGST %", "Percent", read_only=1),
				field("sgst_rate", "SGST %", "Percent", read_only=1),
				field("igst_rate", "IGST %", "Percent", read_only=1),
				field("default_tax_rate", "Default Tax Rate %", "Percent", default=18),
				field("gstin_valid", "GSTIN Valid", "Check", read_only=1),
				field("gstin_validation_message", "GSTIN Validation", "Small Text", read_only=1),
				section("Line Items"),
				field("items", "Items", "Table", options="IC Invoice Item"),
				section("Totals"),
				field("subtotal", "Subtotal", "Currency", options="currency", read_only=1),
				field("discount_amount", "Discount", "Currency", options="currency", default=0),
				field("tax_total", "Tax Total", "Currency", options="currency", read_only=1),
				col(),
				field("grand_total", "Grand Total", "Currency", options="currency", read_only=1, bold=1),
				field("paid_amount", "Paid Amount", "Currency", options="currency", read_only=1),
				field("balance_due", "Balance Due", "Currency", options="currency", read_only=1),
				section("Payments"),
				field("payments", "Payments", "Table", options="IC Invoice Payment"),
				field("payment_link", "Payment Link", "Small Text", read_only=1),
				field("payment_token", "Payment Token", "Data", read_only=1, hidden=1),
				section("Recurring"),
				field("is_recurring", "Recurring Invoice", "Check", default=0),
				field("recur_every_days", "Recur Every (Days)", "Int", default=30, depends_on="eval:doc.is_recurring"),
				field("next_recur_date", "Next Recur Date", "Date", depends_on="eval:doc.is_recurring"),
				section("Reminders"),
				field("auto_reminders", "Automatic Reminders", "Check", default=1),
				field("reminder_log", "Reminder Log", "Table", options="IC Invoice Reminder"),
				section("Portal & Notes"),
				field("customer_portal_token", "Customer Portal Token", "Data", read_only=1, hidden=1),
				field("customer_portal_link", "Customer Invoice Portal Link", "Small Text", read_only=1),
				field("terms", "Terms", "Text Editor"),
				field("notes", "Notes", "Small Text"),
			],
			"permissions": [
				perm("IC Admin", delete=1, submit=1, cancel=1, amend=1, export=1),
				perm("System Manager", delete=1, submit=1, cancel=1, amend=1, export=1),
				perm("IC All Ops Manager", submit=1, cancel=1, export=1),
				perm("IC Sales Person", submit=1),
				perm("IC Operations Manager", write=0, create=0, submit=0),
				perm("IC Customer Manager"),
			],
		},
		py_extra=invoice_py,
		js_extra=invoice_js,
	)


if __name__ == "__main__":
	main()
