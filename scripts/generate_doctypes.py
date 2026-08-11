#!/usr/bin/env python3
"""Generate InstaCertify ERPNext DocType files from definitions."""

from __future__ import annotations

import json
import os
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1] / "instacertify"

ROLES_ALL = [
	"IC Admin",
	"IC All Ops Manager",
	"IC Sales Person",
	"IC Operations Manager",
	"IC HR",
	"System Manager",
]


def perm(role, read=1, write=1, create=1, delete=0, submit=0, cancel=0, amend=0, report=1, export=0, import_=0, print_=1, email=1, share=1):
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
		"import": import_,
		"print": print_,
		"email": email,
		"share": share,
	}


def admin_full():
	return [
		perm("IC Admin", delete=1, submit=1, cancel=1, amend=1, export=1, import_=1),
		perm("System Manager", delete=1, submit=1, cancel=1, amend=1, export=1, import_=1),
		perm("IC All Ops Manager", delete=0, submit=1, cancel=1, amend=1, export=1),
		perm("IC Operations Manager", delete=0, submit=0, export=0),
		perm("IC Sales Person", delete=0, submit=0, export=0),
		perm("IC HR", read=1, write=0, create=0, delete=0, export=0),
	]


def field(fieldname, label, fieldtype, **kwargs):
	f = {"fieldname": fieldname, "label": label, "fieldtype": fieldtype}
	f.update(kwargs)
	return f


def section(label, fieldname=None, collapsible=0):
	return field(fieldname or label.lower().replace(" ", "_") + "_section", label, "Section Break", collapsible=collapsible)


def col():
	return {"fieldname": "column_break_" + str(os.urandom(3).hex()), "fieldtype": "Column Break"}


def write_doctype(module_folder: str, module_name: str, meta: dict, py_extra: str = "", js_extra: str = ""):
	name = meta["name"]
	slug = name.lower().replace(" ", "_")
	folder = ROOT / module_folder / "doctype" / slug
	folder.mkdir(parents=True, exist_ok=True)
	(folder / "__init__.py").write_text("")

	meta.setdefault("doctype", "DocType")
	meta.setdefault("module", module_name)
	meta.setdefault("engine", "InnoDB")
	meta.setdefault("track_changes", 1)
	meta.setdefault("editable_grid", 1 if meta.get("istable") else 0)
	meta.setdefault("sort_field", "modified")
	meta.setdefault("sort_order", "DESC")
	meta.setdefault("creation", "2026-01-01 00:00:00.000000")
	meta.setdefault("modified", "2026-01-01 00:00:00.000000")
	meta.setdefault("modified_by", "Administrator")
	meta.setdefault("owner", "Administrator")

	(folder / f"{slug}.json").write_text(json.dumps(meta, indent=1) + "\n")

	class_name = "".join(p.title() for p in name.replace("-", " ").split())
	py = dedent(
		f'''\
		# Copyright (c) 2026, InstaCertify and contributors
		# For license information, please see license.txt

		import frappe
		from frappe.model.document import Document


		class {class_name}(Document):
			pass
		'''
	)
	if py_extra:
		py = py.replace("\tpass\n", py_extra)
	(folder / f"{slug}.py").write_text(py)

	js = (
		js_extra
		or dedent(
			f"""\
			// Copyright (c) 2026, InstaCertify and contributors
			// For license information, please see license.txt

			frappe.ui.form.on('{name}', {{
				refresh(frm) {{}}
			}});
			"""
		)
	)
	(folder / f"{slug}.js").write_text(js)


# ---------------------------------------------------------------------------
# DocType definitions
# ---------------------------------------------------------------------------

DOCTYPES = []


def add(module_folder, module_name, meta, py_extra="", js_extra=""):
	DOCTYPES.append((module_folder, module_name, meta, py_extra, js_extra))


# === Setup / Masters ===
add(
	"setup",
	"IC Setup",
	{
		"name": "IC Settings",
		"issingle": 1,
		"fields": [
			section("Company Branding"),
			field("company_name", "Company Name", "Data", default="InstaCertify"),
			field("primary_color", "Primary Blue", "Color", default="#0B5FFF"),
			field("accent_color", "Accent Orange", "Color", default="#FF7A00"),
			col(),
			field("default_currency", "Default Currency", "Link", options="Currency", default="INR"),
			field("enable_multi_currency", "Enable Multi Currency", "Check", default=1),
			section("Quotation Defaults"),
			field("default_force_majeure", "Default Force Majeure", "Text Editor"),
			field("default_terms", "Default Terms and Conditions", "Text Editor"),
			field("quote_validity_days", "Quote Validity (Days)", "Int", default=30),
			section("Notifications"),
			field("notify_admin_on_quote_accept", "Notify Admin on Quote Accept", "Check", default=1),
			field("admin_notification_email", "Admin Notification Email", "Data", options="Email"),
		],
		"permissions": [
			perm("IC Admin", delete=1, export=1),
			perm("System Manager", delete=1, export=1),
			perm("IC All Ops Manager", write=0, create=0, delete=0),
		],
	},
)

add(
	"setup",
	"IC Setup",
	{
		"name": "IC Service",
		"autoname": "field:service_name",
		"naming_rule": "By fieldname",
		"title_field": "service_name",
		"search_fields": "service_code,category",
		"fields": [
			field("service_name", "Service Name", "Data", reqd=1, unique=1),
			field("service_code", "Service Code", "Data"),
			field("category", "Category", "Select", options="\nCertification\nTesting\nConsulting\nRenewal\nAudit\nTraining\nOther", reqd=1),
			col(),
			field("is_active", "Is Active", "Check", default=1),
			field("typical_timeline_days", "Typical Timeline (Days)", "Int"),
			section("Description"),
			field("description", "Description", "Text Editor"),
			section("Default Document Checklist"),
			field("document_checklist", "Document Checklist", "Table", options="IC Service Checklist Item"),
			section("Certification Info"),
			field("certification_timeline_notes", "Certification Timeline Notes", "Text"),
		],
		"permissions": admin_full(),
	},
)

add(
	"setup",
	"IC Setup",
	{
		"name": "IC Service Checklist Item",
		"istable": 1,
		"fields": [
			field("document_name", "Document Name", "Data", reqd=1, in_list_view=1),
			field("is_mandatory", "Mandatory", "Check", default=1, in_list_view=1),
			field("instructions", "Instructions", "Small Text", in_list_view=1),
			field("allowed_formats", "Allowed Formats", "Data", default="PDF,JPG,PNG", in_list_view=1),
		],
		"permissions": [],
	},
)

add(
	"crm",
	"IC CRM",
	{
		"name": "IC Consultant",
		"autoname": "field:consultant_name",
		"naming_rule": "By fieldname",
		"title_field": "consultant_name",
		"fields": [
			field("consultant_name", "Consultant Name", "Data", reqd=1, unique=1),
			field("organization", "Organization", "Data"),
			col(),
			field("email", "Email", "Data", options="Email"),
			field("phone", "Phone", "Data"),
			field("is_active", "Is Active", "Check", default=1),
			section("Notes"),
			field("notes", "Notes", "Small Text"),
		],
		"permissions": admin_full(),
	},
)

# === CRM Lead ===
INDIAN_STATES = "\n".join(
	[
		"",
		"Andhra Pradesh",
		"Arunachal Pradesh",
		"Assam",
		"Bihar",
		"Chhattisgarh",
		"Goa",
		"Gujarat",
		"Haryana",
		"Himachal Pradesh",
		"Jharkhand",
		"Karnataka",
		"Kerala",
		"Madhya Pradesh",
		"Maharashtra",
		"Manipur",
		"Meghalaya",
		"Mizoram",
		"Nagaland",
		"Odisha",
		"Punjab",
		"Rajasthan",
		"Sikkim",
		"Tamil Nadu",
		"Telangana",
		"Tripura",
		"Uttar Pradesh",
		"Uttarakhand",
		"West Bengal",
		"Andaman and Nicobar Islands",
		"Chandigarh",
		"Dadra and Nagar Haveli and Daman and Diu",
		"Delhi",
		"Jammu and Kashmir",
		"Ladakh",
		"Lakshadweep",
		"Puducherry",
	]
)

add(
	"crm",
	"IC CRM",
	{
		"name": "IC Lead",
		"autoname": "naming_series:",
		"naming_rule": "By \"Naming Series\" field",
		"title_field": "company_name",
		"search_fields": "contact_person,email,phone,lead_source,status",
		"track_seen": 1,
		"fields": [
			field("naming_series", "Series", "Select", options="IC-LEAD-.YYYY.-.####", default="IC-LEAD-.YYYY.-.####", reqd=1),
			field("status", "Status", "Select", options="\nOpen\nContacted\nQualified\nQuotation Sent\nWon\nLost\nNurture", default="Open", reqd=1, in_list_view=1, in_standard_filter=1),
			section("Contact"),
			field("contact_person", "Name of Person", "Data", reqd=1, in_list_view=1),
			field("company_name", "Company Name", "Data", reqd=1, in_list_view=1),
			col(),
			field("email", "Email Address", "Data", options="Email", reqd=1),
			field("phone", "Contact Number", "Data", reqd=1),
			section("Request Type"),
			field("request_type", "Request Type", "Select", options="\nService Request\nTesting Request\nBoth", reqd=1, in_list_view=1, in_standard_filter=1),
			field("service", "Service", "Link", options="IC Service", depends_on="eval:doc.request_type=='Service Request' || doc.request_type=='Both'"),
			field("company_size", "Company Size", "Select", options="\nMicro\nSmall\nMedium\nLarge", reqd=1, in_standard_filter=1),
			col(),
			field("country", "Country", "Select", options="\nIndia\nOther", default="India", reqd=1),
			field("state", "State", "Select", options=INDIAN_STATES, depends_on="eval:doc.country=='India'"),
			field("other_country", "Other Country", "Data", depends_on="eval:doc.country=='Other'"),
			section("Lead Source"),
			field("lead_source", "Lead Source", "Select", options="\nGoogle\nDirect Call\nLead Generated\nReferral by Existing Customer\nIndiaMART\nConsultant", reqd=1, in_list_view=1, in_standard_filter=1),
			field("consultant", "Consultant", "Link", options="IC Consultant", depends_on="eval:doc.lead_source=='Consultant'"),
			field("expected_timeline", "Expected Timeline", "Data"),
			col(),
			field("assigned_to", "Assigned Sales Person", "Link", options="User", in_standard_filter=1),
			field("customer", "Linked Customer", "Link", options="Customer"),
			section("Optional Details", collapsible=1),
			field("address", "Address of Company", "Small Text"),
			field("gstin", "GST Details", "Data"),
			field("remarks", "Remarks", "Text"),
			section("Meta"),
			field("converted_on", "Converted On", "Datetime", read_only=1),
		],
		"permissions": [
			perm("IC Admin", delete=1, export=1, import_=1),
			perm("System Manager", delete=1, export=1, import_=1),
			perm("IC All Ops Manager", export=1),
			perm("IC Sales Person"),
			perm("IC Operations Manager", write=0, create=0),
		],
	},
	py_extra=dedent(
		"""
		\tdef validate(self):
			\tif self.lead_source == "Consultant" and not self.consultant:
				\tfrappe.throw("Please select a Consultant for this lead source")
			\tif self.country == "India" and not self.state:
				\tfrappe.throw("Please select State for India leads")
		"""
	),
	js_extra=dedent(
		"""\
		frappe.ui.form.on('IC Lead', {
			refresh(frm) {
				if (!frm.is_new() && frm.doc.status !== 'Won' && !frm.doc.customer) {
					frm.add_custom_button(__('Convert to Customer'), () => {
						frappe.call({
							method: 'instacertify.api.lead.convert_lead_to_customer',
							args: { lead: frm.doc.name },
							freeze: true,
							callback(r) {
								if (r.message) {
									frm.reload_doc();
									frappe.set_route('Form', 'Customer', r.message);
								}
							}
						});
					}, __('Actions'));
				}
			},
			lead_source(frm) {
				if (frm.doc.lead_source !== 'Consultant') frm.set_value('consultant', null);
			},
			country(frm) {
				if (frm.doc.country !== 'India') frm.set_value('state', null);
			}
		});
		"""
	),
)

# === Quotation ===
add(
	"quotation",
	"IC Quotation",
	{
		"name": "IC Quotation Template",
		"autoname": "field:template_name",
		"naming_rule": "By fieldname",
		"title_field": "template_name",
		"fields": [
			field("template_name", "Template Name", "Data", reqd=1, unique=1),
			field("service", "Service", "Link", options="IC Service", reqd=1, in_list_view=1),
			field("category", "Category", "Select", options="\nCertification\nTesting\nConsulting\nRenewal\nAudit\nTraining\nOther", in_list_view=1),
			col(),
			field("is_active", "Is Active", "Check", default=1),
			field("currency", "Currency", "Link", options="Currency", default="INR", reqd=1),
			section("Scope"),
			field("scope_of_work", "Scope of Work", "Text Editor"),
			field("certification_timeline", "Certification / Delivery Timeline", "Text"),
			section("Cost Lines"),
			field("cost_lines", "Cost Lines", "Table", options="IC Quotation Cost Line"),
			section("Testing Details", collapsible=1),
			field("include_testing", "Include Testing Block", "Check"),
			field("default_lab", "Default Lab", "Link", options="IC Lab"),
			field("applicable_standard", "Applicable Standard", "Data"),
			field("no_of_samples", "No. of Samples", "Int", default=1),
			field("testing_timeline", "Testing Timeline", "Data"),
			section("Legal"),
			field("force_majeure", "Force Majeure", "Text Editor"),
			field("terms_and_conditions", "Terms and Conditions", "Text Editor"),
			section("Source Quote"),
			field("source_quotation", "Created From Quotation", "Link", options="IC Quotation", read_only=1),
		],
		"permissions": [
			perm("IC Admin", delete=1, export=1),
			perm("System Manager", delete=1, export=1),
			perm("IC All Ops Manager", export=1),
			perm("IC Sales Person", delete=0),
			perm("IC Operations Manager", write=0, create=0),
		],
	},
)

add(
	"quotation",
	"IC Quotation",
	{
		"name": "IC Quotation Cost Line",
		"istable": 1,
		"fields": [
			field("cost_type", "Cost Type", "Select", options="\nConsulting\nLab / Testing\nGovernment Fees\nCertification Fees\nTravel\nOther", reqd=1, in_list_view=1),
			field("description", "Description", "Data", reqd=1, in_list_view=1),
			field("qty", "Qty", "Float", default=1, in_list_view=1),
			field("rate", "Rate", "Currency", options="currency", reqd=1, in_list_view=1),
			field("amount", "Amount", "Currency", options="currency", read_only=1, in_list_view=1),
			field("payable_to", "Payable To", "Select", options="\nInstaCertify\nGovernment Portal\nLab Directly\nCustomer Direct", default="InstaCertify", in_list_view=1),
			field("counts_as_revenue", "Counts as Our Revenue", "Check", default=0, in_list_view=1),
			field("currency", "Currency", "Link", options="Currency", default="INR"),
		],
		"permissions": [],
	},
)

add(
	"quotation",
	"IC Quotation",
	{
		"name": "IC Quotation Testing Line",
		"istable": 1,
		"fields": [
			field("test_name", "Test Name", "Data", reqd=1, in_list_view=1),
			field("applicable_standard", "Applicable Standard", "Data", in_list_view=1),
			field("no_of_samples", "No. of Samples", "Int", default=1, in_list_view=1),
			field("testing_charges", "Testing Charges", "Currency", options="currency", in_list_view=1),
			field("lab", "Testing Lab", "Link", options="IC Lab", in_list_view=1),
			field("accreditation", "Lab Accreditation", "Data"),
			field("testing_timeline", "Testing Timeline", "Data", in_list_view=1),
			field("currency", "Currency", "Link", options="Currency", default="INR"),
		],
		"permissions": [],
	},
)

QUOTE_PY = dedent(
	"""
	\tdef validate(self):
		\tself.calculate_totals()
		\tself.set_qr_payload()

	\tdef calculate_totals(self):
		\tconsulting = lab = govt = other = revenue = 0
		\tfor row in self.cost_lines or []:
			\trow.amount = (row.qty or 0) * (row.rate or 0)
			\tif row.cost_type == "Consulting":
				\tconsulting += row.amount
				\trow.counts_as_revenue = 1
			\telif row.cost_type == "Lab / Testing":
				\tlab += row.amount
				\trow.counts_as_revenue = 1
			\telif row.cost_type == "Government Fees":
				\tgovt += row.amount
			\telse:
				\tother += row.amount
			\tif row.counts_as_revenue:
				\trevenue += row.amount
		\tself.consulting_total = consulting
		\tself.lab_testing_total = lab
		\tself.government_fees_total = govt
		\tself.other_charges_total = other
		\tself.our_revenue_total = revenue
		\tself.grand_total = consulting + lab + govt + other

	\tdef set_qr_payload(self):
		\tfrom instacertify.utils.qrcode import ensure_document_qr
		\tensure_document_qr(self, "quotation")

	\tdef on_update_after_submit(self):
		\tpass

	\tdef on_submit(self):
		\tself.status = self.status if self.status not in ("Draft",) else "Finalised"
	"""
)

QUOTE_JS = dedent(
	"""\
	frappe.ui.form.on('IC Quotation', {
		refresh(frm) {
			frm.set_query('quotation_template', () => ({
				filters: { is_active: 1 }
			}));
			if (frm.doc.docstatus === 1 && ['Finalised', 'Shared', 'Changes Requested'].includes(frm.doc.status)) {
				frm.add_custom_button(__('Share with Customer'), () => {
					frappe.call({
						method: 'instacertify.api.quotation.share_quote',
						args: { quotation: frm.doc.name },
						freeze: true,
						callback(r) {
							if (r.message) {
								frappe.msgprint({
									title: __('Quote Link'),
									message: __('Share this link with the customer:<br><a href="{0}" target="_blank">{0}</a>', [r.message]),
									indicator: 'blue'
								});
								frm.reload_doc();
							}
						}
					});
				}, __('Actions'));
			}
			if (frm.doc.docstatus === 1 && frm.doc.status === 'Accepted') {
				frm.add_custom_button(__('Start Project'), () => {
					frappe.call({
						method: 'instacertify.api.quotation.start_project',
						args: { quotation: frm.doc.name },
						freeze: true,
						callback(r) {
							if (r.message) frappe.set_route('Form', 'IC Project', r.message);
						}
					});
				}, __('Actions'));
				frm.add_custom_button(__('Save as Template'), () => {
					frappe.prompt({
						label: 'Template Name',
						fieldname: 'template_name',
						fieldtype: 'Data',
						reqd: 1
					}, (values) => {
						frappe.call({
							method: 'instacertify.api.quotation.save_as_template',
							args: { quotation: frm.doc.name, template_name: values.template_name },
							freeze: true,
							callback(r) {
								if (r.message) frappe.set_route('Form', 'IC Quotation Template', r.message);
							}
						});
					}, __('Create Quotation Template'));
				}, __('Actions'));
			}
		},
		quotation_template(frm) {
			if (!frm.doc.quotation_template) return;
			frappe.call({
				method: 'instacertify.api.quotation.apply_template',
				args: { template: frm.doc.quotation_template, quotation: frm.doc.name || null },
				callback(r) {
					if (!r.message) return;
					const d = r.message;
					['service', 'category', 'scope_of_work', 'certification_timeline', 'force_majeure', 'terms_and_conditions', 'currency']
						.forEach((k) => { if (d[k] !== undefined) frm.set_value(k, d[k]); });
					frm.clear_table('cost_lines');
					(d.cost_lines || []).forEach((row) => {
						frm.add_child('cost_lines', row);
					});
					frm.clear_table('testing_lines');
					(d.testing_lines || []).forEach((row) => {
						frm.add_child('testing_lines', row);
					});
					frm.refresh_fields();
				}
			});
		},
		service(frm) {
			if (frm.doc.service) {
				frappe.db.get_doc('IC Service', frm.doc.service).then((svc) => {
					if (svc.certification_timeline_notes && !frm.doc.certification_timeline) {
						frm.set_value('certification_timeline', svc.certification_timeline_notes);
					}
					if (svc.category) frm.set_value('category', svc.category);
				});
			}
		}
	});

	frappe.ui.form.on('IC Quotation Cost Line', {
		qty(frm, cdt, cdn) { recalc(frm, cdt, cdn); },
		rate(frm, cdt, cdn) { recalc(frm, cdt, cdn); },
		cost_type(frm, cdt, cdn) {
			const row = locals[cdt][cdn];
			if (['Consulting', 'Lab / Testing'].includes(row.cost_type)) {
				frappe.model.set_value(cdt, cdn, 'counts_as_revenue', 1);
				frappe.model.set_value(cdt, cdn, 'payable_to', 'InstaCertify');
			} else if (row.cost_type === 'Government Fees') {
				frappe.model.set_value(cdt, cdn, 'counts_as_revenue', 0);
				frappe.model.set_value(cdt, cdn, 'payable_to', 'Government Portal');
			}
			recalc(frm, cdt, cdn);
		}
	});

	function recalc(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, 'amount', (row.qty || 0) * (row.rate || 0));
		frm.trigger('calculate_totals');
	}
	"""
)

add(
	"quotation",
	"IC Quotation",
	{
		"name": "IC Quotation",
		"autoname": "naming_series:",
		"naming_rule": "By \"Naming Series\" field",
		"is_submittable": 1,
		"title_field": "title",
		"search_fields": "customer,service,status,sales_person",
		"track_seen": 1,
		"fields": [
			field("naming_series", "Series", "Select", options="IC-QTN-.YYYY.-.####", default="IC-QTN-.YYYY.-.####", reqd=1),
			field("title", "Title", "Data", reqd=1, in_list_view=1),
			field("status", "Status", "Select", options="\nDraft\nFinalised\nShared\nAccepted\nChanges Requested\nRejected\nProject Started", default="Draft", reqd=1, in_list_view=1, in_standard_filter=1),
			col(),
			field("quotation_template", "Quotation Template", "Link", options="IC Quotation Template"),
			field("currency", "Currency", "Link", options="Currency", default="INR", reqd=1),
			field("conversion_rate", "Conversion Rate", "Float", default=1),
			section("Customer & Service"),
			field("lead", "Lead", "Link", options="IC Lead"),
			field("customer", "Customer", "Link", options="Customer", reqd=1, in_list_view=1),
			field("customer_name", "Customer Name", "Data", fetch_from="customer.customer_name", read_only=1),
			col(),
			field("service", "Service", "Link", options="IC Service", reqd=1, in_list_view=1),
			field("category", "Category", "Select", options="\nCertification\nTesting\nConsulting\nRenewal\nAudit\nTraining\nOther", reqd=1),
			field("is_renewal", "Is Renewal / Certificate Edit", "Check"),
			field("sales_person", "Sales Person", "Link", options="User", default="__user", in_standard_filter=1),
			section("Scope & Timeline"),
			field("scope_of_work", "Scope of Work / Service Details", "Text Editor"),
			field("certification_timeline", "Certification Timeline", "Text"),
			section("Costing"),
			field("cost_lines", "Cost Lines", "Table", options="IC Quotation Cost Line"),
			section("Totals"),
			field("consulting_total", "Consulting Total (Revenue)", "Currency", options="currency", read_only=1),
			field("lab_testing_total", "Lab / Testing Total (Revenue)", "Currency", options="currency", read_only=1),
			col(),
			field("government_fees_total", "Government Fees", "Currency", options="currency", read_only=1),
			field("other_charges_total", "Other Charges", "Currency", options="currency", read_only=1),
			field("our_revenue_total", "Our Revenue Total", "Currency", options="currency", read_only=1),
			field("grand_total", "Grand Total", "Currency", options="currency", read_only=1, bold=1),
			section("Testing Requirements"),
			field("testing_lines", "Testing Lines", "Table", options="IC Quotation Testing Line"),
			section("Legal"),
			field("force_majeure", "Force Majeure", "Text Editor"),
			field("terms_and_conditions", "Terms and Conditions", "Text Editor"),
			section("Sharing & QR"),
			field("unique_barcode", "Unique Quote Barcode", "Data", read_only=1),
			field("qr_code", "QR Code", "Attach Image", read_only=1),
			field("share_token", "Share Token", "Data", read_only=1, hidden=1),
			field("share_link", "Customer Share Link", "Small Text", read_only=1),
			field("shared_on", "Shared On", "Datetime", read_only=1),
			field("customer_response_on", "Customer Response On", "Datetime", read_only=1),
			field("customer_remarks", "Customer Change Remarks", "Text", read_only=1),
			section("Links"),
			field("project", "Project", "Link", options="IC Project", read_only=1),
			field("valid_till", "Valid Till", "Date"),
		],
		"permissions": [
			perm("IC Admin", delete=1, submit=1, cancel=1, amend=1, export=1),
			perm("System Manager", delete=1, submit=1, cancel=1, amend=1, export=1),
			perm("IC All Ops Manager", submit=1, cancel=1, amend=1, export=1),
			perm("IC Sales Person", submit=1),
			perm("IC Operations Manager", write=0, create=0, submit=0),
		],
	},
	py_extra=QUOTE_PY,
	js_extra=QUOTE_JS,
)

# === Projects ===
add(
	"projects",
	"IC Projects",
	{
		"name": "IC Project Progress",
		"istable": 1,
		"fields": [
			field("progress_date", "Date", "Date", reqd=1, default="Today", in_list_view=1),
			field("remarks", "Remarks", "Small Text", reqd=1, in_list_view=1),
			field("percent_complete", "% Complete", "Percent", in_list_view=1),
			field("updated_by", "Updated By", "Link", options="User", default="__user", in_list_view=1),
		],
		"permissions": [],
	},
)

add(
	"projects",
	"IC Projects",
	{
		"name": "IC Project Document",
		"istable": 1,
		"fields": [
			field("document_type", "Document Type", "Select", options="\nDeliverable\nPDF\nImage\nInvoice\nQuote\nOther", default="Deliverable", in_list_view=1),
			field("title", "Title", "Data", reqd=1, in_list_view=1),
			field("attachment", "File (PDF/Image)", "Attach", reqd=1, in_list_view=1),
			field("remarks", "Remarks", "Small Text"),
			field("uploaded_on", "Uploaded On", "Datetime", default="Now", read_only=1),
		],
		"permissions": [],
	},
)

add(
	"projects",
	"IC Projects",
	{
		"name": "IC Project Credential",
		"istable": 1,
		"fields": [
			field("system_name", "System / Portal", "Data", reqd=1, in_list_view=1),
			field("username", "Username / Login", "Data", in_list_view=1),
			field("password", "Password", "Password", in_list_view=1),
			field("url", "URL", "Data"),
			field("notes", "Notes", "Small Text"),
		],
		"permissions": [],
	},
)

add(
	"projects",
	"IC Projects",
	{
		"name": "IC Project Incident",
		"istable": 1,
		"fields": [
			field("incident_date", "Date", "Date", default="Today", reqd=1, in_list_view=1),
			field("incident_type", "Type", "Select", options="\nCommitment\nIncident\nRisk\nEscalation", default="Commitment", in_list_view=1),
			field("description", "Description", "Small Text", reqd=1, in_list_view=1),
			field("status", "Status", "Select", options="\nOpen\nIn Progress\nClosed", default="Open", in_list_view=1),
		],
		"permissions": [],
	},
)

add(
	"projects",
	"IC Projects",
	{
		"name": "IC Working Hour",
		"istable": 1,
		"fields": [
			field("work_date", "Date", "Date", reqd=1, default="Today", in_list_view=1),
			field("employee", "Employee", "Link", options="User", default="__user", reqd=1, in_list_view=1),
			field("hours", "Hours", "Float", reqd=1, in_list_view=1),
			field("activity", "Activity", "Data", in_list_view=1),
			field("notes", "Notes", "Small Text"),
		],
		"permissions": [],
	},
)

add(
	"projects",
	"IC Projects",
	{
		"name": "IC Project Invoice Link",
		"istable": 1,
		"fields": [
			field("invoice", "Sales Invoice", "Link", options="Sales Invoice", in_list_view=1),
			field("quotation", "Quotation", "Link", options="IC Quotation", in_list_view=1),
			field("amount", "Amount", "Currency", in_list_view=1),
			field("status", "Status", "Data", in_list_view=1),
		],
		"permissions": [],
	},
)

PROJECT_JS = dedent(
	"""\
	frappe.ui.form.on('IC Project', {
		refresh(frm) {
			if (!frm.is_new()) {
				frm.add_custom_button(__('Open Document Library'), () => {
					frappe.set_route('List', 'IC Customer Document Request', { project: frm.doc.name });
				}, __('Documents'));
			}
		}
	});
	"""
)

add(
	"projects",
	"IC Projects",
	{
		"name": "IC Project",
		"autoname": "naming_series:",
		"naming_rule": "By \"Naming Series\" field",
		"title_field": "project_name",
		"search_fields": "customer,service,status,sales_person",
		"track_seen": 1,
		"fields": [
			field("naming_series", "Series", "Select", options="IC-PRJ-.YYYY.-.####", default="IC-PRJ-.YYYY.-.####", reqd=1),
			field("project_name", "Project Name", "Data", reqd=1, in_list_view=1),
			field("status", "Status", "Select", options="\nOpen\nIn Progress\nOn Hold\nCompleted\nCancelled", default="Open", reqd=1, in_list_view=1, in_standard_filter=1),
			field("percent_complete", "Progress %", "Percent", in_list_view=1),
			col(),
			field("customer", "Customer", "Link", options="Customer", reqd=1, in_list_view=1),
			field("quotation", "Source Quotation", "Link", options="IC Quotation"),
			field("service", "Service", "Link", options="IC Service", reqd=1),
			field("sales_person", "Sales Person", "Link", options="User", in_standard_filter=1),
			field("operations_manager", "Operations Manager", "Link", options="User"),
			section("Timeline"),
			field("start_date", "Start Date", "Date", default="Today"),
			field("expected_end_date", "Expected End Date", "Date"),
			field("actual_end_date", "Actual End Date", "Date"),
			section("Progress Remarks"),
			field("progress_log", "Progress Log", "Table", options="IC Project Progress"),
			section("Working Hours"),
			field("working_hours", "Working Hours", "Table", options="IC Working Hour"),
			section("Delivered Records (PDF / Image)"),
			field("documents", "Documents", "Table", options="IC Project Document"),
			section("Login Credentials"),
			field("credentials", "Credentials", "Table", options="IC Project Credential"),
			section("Commitments / Incidents"),
			field("incidents", "Incidents & Commitments", "Table", options="IC Project Incident"),
			section("Quotes & Invoicing"),
			field("billing_links", "Quotes & Invoices", "Table", options="IC Project Invoice Link"),
			section("Notes"),
			field("notes", "Notes", "Text Editor"),
		],
		"permissions": [
			perm("IC Admin", delete=1, export=1),
			perm("System Manager", delete=1, export=1),
			perm("IC All Ops Manager", export=1),
			perm("IC Operations Manager"),
			perm("IC Sales Person", write=0, create=0),
		],
	},
	js_extra=PROJECT_JS,
)

add(
	"projects",
	"IC Projects",
	{
		"name": "IC Customer Document Request",
		"autoname": "naming_series:",
		"naming_rule": "By \"Naming Series\" field",
		"title_field": "title",
		"fields": [
			field("naming_series", "Series", "Select", options="IC-DOC-.YYYY.-.####", default="IC-DOC-.YYYY.-.####", reqd=1),
			field("title", "Title", "Data", reqd=1),
			field("project", "Project", "Link", options="IC Project", reqd=1, in_list_view=1),
			field("customer", "Customer", "Link", options="Customer", reqd=1),
			field("service", "Service", "Link", options="IC Service"),
			field("request_type", "Request Type", "Select", options="\nGeneral\nTest Request Form\nChecklist Upload", default="Checklist Upload"),
			col(),
			field("status", "Status", "Select", options="\nOpen\nShared\nPartially Uploaded\nCompleted", default="Open", in_list_view=1),
			field("share_token", "Share Token", "Data", read_only=1, hidden=1),
			field("share_link", "Customer Upload Link", "Small Text", read_only=1),
			field("requested_by", "Requested By", "Link", options="User", default="__user"),
			section("Checklist"),
			field("checklist_items", "Checklist Items", "Table", options="IC Document Checklist Row"),
			section("QR"),
			field("qr_code", "QR Code", "Attach Image", read_only=1),
		],
		"permissions": [
			perm("IC Admin", delete=1, export=1),
			perm("System Manager", delete=1, export=1),
			perm("IC All Ops Manager", export=1),
			perm("IC Operations Manager"),
			perm("IC Sales Person"),
		],
	},
	py_extra=dedent(
		"""
		\tdef before_insert(self):
			\tif not self.share_token:
				\timport secrets
				\tself.share_token = secrets.token_urlsafe(24)
		"""
	),
	js_extra=dedent(
		"""\
		frappe.ui.form.on('IC Customer Document Request', {
			refresh(frm) {
				if (!frm.is_new()) {
					frm.add_custom_button(__('Share Upload Link'), () => {
						frappe.call({
							method: 'instacertify.api.documents.share_document_request',
							args: { name: frm.doc.name },
							callback(r) {
								if (r.message) {
									frappe.msgprint(__('Share link:<br><a href="{0}" target="_blank">{0}</a>', [r.message]));
									frm.reload_doc();
								}
							}
						});
					});
				}
			},
			service(frm) {
				if (!frm.doc.service) return;
				frappe.call({
					method: 'instacertify.api.documents.load_service_checklist',
					args: { service: frm.doc.service },
					callback(r) {
						frm.clear_table('checklist_items');
						(r.message || []).forEach((row) => frm.add_child('checklist_items', row));
						frm.refresh_field('checklist_items');
					}
				});
			}
		});
		"""
	),
)

add(
	"projects",
	"IC Projects",
	{
		"name": "IC Document Checklist Row",
		"istable": 1,
		"fields": [
			field("document_name", "Document Name", "Data", reqd=1, in_list_view=1),
			field("is_mandatory", "Mandatory", "Check", default=1, in_list_view=1),
			field("instructions", "Instructions", "Small Text"),
			field("uploaded_file", "Uploaded File", "Attach", in_list_view=1),
			field("uploaded_on", "Uploaded On", "Datetime", read_only=1),
			field("status", "Status", "Select", options="\nPending\nUploaded\nVerified\nRejected", default="Pending", in_list_view=1),
			field("reviewer_remarks", "Reviewer Remarks", "Small Text"),
		],
		"permissions": [],
	},
)

# === Testing / Labs ===
add(
	"testing",
	"IC Testing",
	{
		"name": "IC Lab",
		"autoname": "field:lab_name",
		"naming_rule": "By fieldname",
		"title_field": "lab_name",
		"search_fields": "location,accreditation",
		"fields": [
			field("lab_name", "Lab Name", "Data", reqd=1, unique=1, in_list_view=1),
			field("location", "Location", "Data", in_list_view=1),
			field("accreditation", "Testing Accreditation", "Data", in_list_view=1),
			col(),
			field("contact_person", "Contact Person", "Data"),
			field("email", "Email", "Data", options="Email"),
			field("phone", "Phone", "Data"),
			field("is_active", "Is Active", "Check", default=1),
			section("Commercial"),
			field("currency", "Currency", "Link", options="Currency", default="INR"),
			field("test_prices", "Test Prices / Cost", "Table", options="IC Lab Test Price"),
			section("Documents (Download on Request)"),
			field("scope_sheet", "Lab Scope Sheet", "Attach"),
			field("accreditation_certificate", "Lab Accreditation Certificate", "Attach"),
			field("other_documents", "Other Documents", "Attach"),
			section("Notes"),
			field("notes", "Notes", "Text"),
		],
		"permissions": [
			perm("IC Admin", delete=1, export=1),
			perm("System Manager", delete=1, export=1),
			perm("IC All Ops Manager", export=1),
			perm("IC Sales Person"),
			perm("IC Operations Manager"),
		],
	},
)

add(
	"testing",
	"IC Testing",
	{
		"name": "IC Lab Test Price",
		"istable": 1,
		"fields": [
			field("test_name", "Test Name", "Data", reqd=1, in_list_view=1),
			field("standard", "Standard", "Data", in_list_view=1),
			field("price", "Price", "Currency", options="currency", reqd=1, in_list_view=1),
			field("turnaround_days", "Turnaround (Days)", "Int", in_list_view=1),
			field("currency", "Currency", "Link", options="Currency", default="INR"),
			field("remarks", "Remarks", "Small Text"),
		],
		"permissions": [],
	},
)

SAMPLE_STATUSES = "\nAwaiting Sample\nSample Received\nDispatched to Lab\nTesting In Process\nReport Available\nReport Uploaded\nShared with Customer"

TEST_REQ_PY = dedent(
	"""
	\tdef validate(self):
		\tfrom instacertify.utils.qrcode import ensure_document_qr
		\tensure_document_qr(self, "test_request")

	\tdef on_update(self):
		\tif self.sample_status == "Sample Received" and not self.sample_qr_code:
			\tfrom instacertify.utils.qrcode import generate_sample_qr
			\tgenerate_sample_qr(self)
	"""
)

TEST_REQ_JS = dedent(
	"""\
	frappe.ui.form.on('IC Test Request', {
		refresh(frm) {
			if (frm.doc.sample_status === 'Sample Received') {
				frm.add_custom_button(__('Generate Sample QR'), () => {
					frappe.call({
						method: 'instacertify.api.testing.generate_sample_qr',
						args: { name: frm.doc.name },
						callback(r) { frm.reload_doc(); }
					});
				}, __('Sample'));
			}
			if (frm.doc.sample_status === 'Report Uploaded' && frm.doc.report_file) {
				frm.add_custom_button(__('Share Report with Customer'), () => {
					frappe.call({
						method: 'instacertify.api.testing.share_report',
						args: { name: frm.doc.name },
						callback(r) {
							if (r.message) {
								frappe.msgprint(__('Report link:<br><a href="{0}" target="_blank">{0}</a>', [r.message]));
								frm.reload_doc();
							}
						}
					});
				}, __('Report'));
			}
			if (frm.doc.request_type === 'Test Request Form') {
				frm.add_custom_button(__('Share TRF with Customer'), () => {
					frappe.call({
						method: 'instacertify.api.testing.share_trf',
						args: { name: frm.doc.name },
						callback(r) {
							if (r.message) frappe.msgprint(__('TRF link:<br><a href="{0}" target="_blank">{0}</a>', [r.message]));
							frm.reload_doc();
						}
					});
				}, __('TRF'));
			}
		}
	});
	"""
)

add(
	"testing",
	"IC Testing",
	{
		"name": "IC Test Request",
		"autoname": "naming_series:",
		"naming_rule": "By \"Naming Series\" field",
		"title_field": "title",
		"search_fields": "customer,lab,sample_status",
		"fields": [
			field("naming_series", "Series", "Select", options="IC-TR-.YYYY.-.####", default="IC-TR-.YYYY.-.####", reqd=1),
			field("title", "Title", "Data", reqd=1, in_list_view=1),
			field("request_type", "Type", "Select", options="\nTesting\nTest Request Form", default="Testing"),
			field("sample_status", "Sample / Testing Status", "Select", options=SAMPLE_STATUSES, default="Awaiting Sample", reqd=1, in_list_view=1, in_standard_filter=1),
			col(),
			field("customer", "Customer", "Link", options="Customer", reqd=1, in_list_view=1),
			field("project", "Project", "Link", options="IC Project"),
			field("quotation", "Quotation", "Link", options="IC Quotation"),
			field("sales_person", "Sales Person", "Link", options="User"),
			section("Test Details"),
			field("test_name", "Test / Parameter", "Data", reqd=1),
			field("applicable_standard", "Applicable Standard", "Data"),
			field("no_of_samples", "No. of Samples", "Int", default=1),
			field("testing_charges", "Testing Charges", "Currency", options="currency"),
			field("currency", "Currency", "Link", options="Currency", default="INR"),
			col(),
			field("lab", "Testing Lab", "Link", options="IC Lab"),
			field("accreditation", "Lab Accreditation", "Data", fetch_from="lab.accreditation"),
			field("testing_timeline", "Testing Timeline", "Data"),
			field("expected_report_date", "Expected Report Date", "Date"),
			section("Sample Tracking"),
			field("sample_received_on", "Sample Received On", "Datetime"),
			field("dispatched_to_lab_on", "Dispatched to Lab On", "Datetime"),
			field("testing_started_on", "Testing Started On", "Datetime"),
			field("report_available_on", "Report Available On", "Datetime"),
			field("sample_qr_code", "Sample QR Code", "Attach Image", read_only=1),
			field("sample_tracking_code", "Sample Tracking Code", "Data", read_only=1),
			section("Report"),
			field("report_file", "Report File", "Attach"),
			field("report_share_token", "Report Share Token", "Data", read_only=1, hidden=1),
			field("report_share_link", "Report Share Link", "Small Text", read_only=1),
			field("trf_share_link", "TRF Share Link", "Small Text", read_only=1),
			section("Document QR"),
			field("unique_barcode", "Unique Barcode", "Data", read_only=1),
			field("qr_code", "QR Code", "Attach Image", read_only=1),
			section("Notes"),
			field("remarks", "Remarks", "Text"),
		],
		"permissions": [
			perm("IC Admin", delete=1, export=1),
			perm("System Manager", delete=1, export=1),
			perm("IC All Ops Manager", export=1),
			perm("IC Operations Manager"),
			perm("IC Sales Person"),
		],
	},
	py_extra=TEST_REQ_PY,
	js_extra=TEST_REQ_JS,
)

# === Assets ===
ASSET_PY = dedent(
	"""
	\tdef before_insert(self):
		\tif not self.asset_code:
			\tself.asset_code = frappe.model.naming.make_autoname("IC-AST-.YYYY.-.####")

	\tdef validate(self):
		\tif self.asset_code and not self.name:
			\tpass
	"""
)

add(
	"assets_mgmt",
	"IC Assets",
	{
		"name": "IC Asset",
		"autoname": "field:asset_code",
		"naming_rule": "By fieldname",
		"title_field": "asset_name",
		"search_fields": "asset_code,custodian,status",
		"fields": [
			field("asset_code", "Asset Code", "Data", reqd=1, unique=1, in_list_view=1),
			field("asset_name", "Asset Name", "Data", reqd=1, in_list_view=1),
			field("asset_category", "Category", "Data"),
			col(),
			field("status", "Status", "Select", options="\nAvailable\nAssigned\nUnder Maintenance\nDisposed", default="Available", in_list_view=1),
			field("acquisition_date", "Acquisition Date", "Date", default="Today"),
			field("asset_value", "Asset Value", "Currency", options="currency", in_list_view=1),
			field("currency", "Currency", "Link", options="Currency", default="INR"),
			section("Custody"),
			field("custodian", "Who Has the Asset", "Link", options="User", in_list_view=1),
			field("location", "Location", "Data"),
			field("registered_by", "Registered By", "Link", options="User", default="__user"),
			section("Details"),
			field("serial_number", "Serial Number", "Data"),
			field("description", "Description", "Small Text"),
			field("attachment", "Photo / Document", "Attach"),
		],
		"permissions": [
			perm("IC Admin", delete=1, export=1),
			perm("System Manager", delete=1, export=1),
			perm("IC All Ops Manager", export=1),
			perm("IC Operations Manager"),
			perm("IC Sales Person"),
			perm("IC HR"),
		],
	},
	py_extra=ASSET_PY,
)

# === HR Portal extras ===
add(
	"hr_portal",
	"IC HR Portal",
	{
		"name": "IC Employee Profile",
		"autoname": "field:user",
		"naming_rule": "By fieldname",
		"title_field": "employee_name",
		"fields": [
			field("user", "User", "Link", options="User", reqd=1, unique=1),
			field("employee_name", "Employee Name", "Data", reqd=1),
			field("employee_id", "Employee ID", "Data"),
			col(),
			field("department", "Department", "Data"),
			field("designation", "Designation", "Data"),
			field("date_of_joining", "Date of Joining", "Date"),
			section("Documents"),
			field("joining_letter", "Joining Letter", "Attach"),
			field("joining_letter_qr", "Joining Letter QR", "Attach Image", read_only=1),
			field("salary_slip_folder_note", "Salary Slips Note", "Small Text", default="View salary slips from My Profile / Salary Slip list."),
			section("HR"),
			field("hr_owner", "HR Owner", "Link", options="User"),
			field("status", "Status", "Select", options="\nActive\nInactive", default="Active"),
		],
		"permissions": [
			perm("IC Admin", delete=1, export=1),
			perm("System Manager", delete=1, export=1),
			perm("IC HR"),
			perm("IC All Ops Manager", write=0, create=0, export=0),
			perm("IC Sales Person", write=0, create=0),
			perm("IC Operations Manager", write=0, create=0),
		],
	},
	py_extra=dedent(
		"""
		\tdef validate(self):
			\tif self.joining_letter and not self.joining_letter_qr:
				\tfrom instacertify.utils.qrcode import attach_qr_for_value
				\tself.joining_letter_qr = attach_qr_for_value(
					\t\tf"JOINING|{self.name}|{self.employee_name}|{self.date_of_joining or ''}",
					\t\tfolder="Home/IC QR Codes",
					\t\tfilename=f"joining-{self.name}.png",
					\t)
		"""
	),
)


def main():
	# ensure module __init__ and doctype packages
	for mod in ["crm", "quotation", "projects", "testing", "assets_mgmt", "hr_portal", "setup"]:
		(ROOT / mod / "doctype").mkdir(parents=True, exist_ok=True)
		(ROOT / mod / "doctype" / "__init__.py").write_text("")
		(ROOT / mod / "__init__.py").write_text("")

	for module_folder, module_name, meta, py_extra, js_extra in DOCTYPES:
		write_doctype(module_folder, module_name, meta, py_extra, js_extra)
		print(f"Created: {meta['name']}")

	print(f"\nTotal DocTypes: {len(DOCTYPES)}")


if __name__ == "__main__":
	main()
