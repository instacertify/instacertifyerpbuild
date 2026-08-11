import frappe


ROLES = [
	"IC Admin",
	"IC All Ops Manager",
	"IC Sales Person",
	"IC Operations Manager",
	"IC Customer Manager",
	"IC HR",
]

DEFAULT_SERVICES = [
	{
		"service_name": "ISO 9001 Certification",
		"service_code": "ISO9001",
		"category": "Certification",
		"typical_timeline_days": 90,
		"certification_timeline_notes": "Typical certification cycle: Stage-1 → Stage-2 → Certificate issuance in 60–90 days depending on readiness.",
		"document_checklist": [
			{"document_name": "Company Registration / GST", "is_mandatory": 1},
			{"document_name": "Organization Chart", "is_mandatory": 1},
			{"document_name": "Quality Manual / Procedures", "is_mandatory": 0},
		],
	},
	{
		"service_name": "Product Testing",
		"service_code": "TEST",
		"category": "Testing",
		"typical_timeline_days": 21,
		"certification_timeline_notes": "Sample receipt → lab testing → report. Timeline depends on standard and sample condition.",
		"document_checklist": [
			{"document_name": "Test Request Form", "is_mandatory": 1},
			{"document_name": "Product Specs / Datasheet", "is_mandatory": 1},
			{"document_name": "Sample Photos", "is_mandatory": 0},
		],
	},
	{
		"service_name": "Certificate Renewal",
		"service_code": "RENEW",
		"category": "Renewal",
		"typical_timeline_days": 30,
		"certification_timeline_notes": "Renewal processing typically 15–30 days prior to expiry.",
		"document_checklist": [
			{"document_name": "Existing Certificate", "is_mandatory": 1},
			{"document_name": "Surveillance / Audit Report", "is_mandatory": 0},
		],
	},
]


def after_install():
	_create_roles()
	_ensure_currency()
	_seed_settings()
	_seed_services()
	_create_workspace()
	frappe.clear_cache()


def after_migrate():
	_create_roles()
	_ensure_currency()
	_seed_settings()
	_create_workspace()


def _create_roles():
	for role in ROLES:
		if not frappe.db.exists("Role", role):
			frappe.get_doc({"doctype": "Role", "role_name": role, "desk_access": 1}).insert(ignore_permissions=True)


def _ensure_currency():
	if not frappe.db.exists("Currency", "INR"):
		return
	try:
		frappe.db.set_single_value("System Settings", "currency", "INR")
	except Exception:
		pass
	# Company default if present
	companies = frappe.get_all("Company", pluck="name")
	for company in companies:
		try:
			frappe.db.set_value("Company", company, "default_currency", "INR")
		except Exception:
			pass


def _seed_settings():
	if not frappe.db.exists("DocType", "IC Settings"):
		return
	doc = frappe.get_single("IC Settings")
	changed = False
	if not doc.company_name:
		doc.company_name = "InstaCertify"
		changed = True
	if not doc.primary_color:
		doc.primary_color = "#0B5FFF"
		changed = True
	if not doc.accent_color:
		doc.accent_color = "#FF7A00"
		changed = True
	if not doc.default_currency:
		doc.default_currency = "INR"
		changed = True
	if not doc.default_terms:
		doc.default_terms = (
			"<p>Payment terms: 50% advance, balance before certificate / report release.</p>"
			"<p>Validity: 30 days from quotation date.</p>"
			"<p>Government fees / portal charges are payable as indicated and may change without notice.</p>"
		)
		changed = True
	if not doc.default_force_majeure:
		doc.default_force_majeure = (
			"<p>InstaCertify shall not be liable for delays or failure due to circumstances beyond reasonable control "
			"including acts of God, government actions, lab backlog, pandemics, or supply disruptions.</p>"
		)
		changed = True
	if changed:
		doc.save(ignore_permissions=True)


def _seed_services():
	if not frappe.db.exists("DocType", "IC Service"):
		return
	for svc in DEFAULT_SERVICES:
		if frappe.db.exists("IC Service", svc["service_name"]):
			continue
		frappe.get_doc({"doctype": "IC Service", **svc}).insert(ignore_permissions=True)


def _create_workspace():
	"""Create / update InstaCertify workspace with colorful shortcuts."""
	if not frappe.db.exists("DocType", "Workspace"):
		return

	content = [
		{"type": "header", "data": {"text": "InstaCertify Operations", "col": 12}},
		{"type": "shortcut", "data": {"shortcut_name": "My Dashboard", "col": 4}},
		{"type": "shortcut", "data": {"shortcut_name": "Leads", "col": 4}},
		{"type": "shortcut", "data": {"shortcut_name": "Quotations", "col": 4}},
		{"type": "shortcut", "data": {"shortcut_name": "Projects", "col": 4}},
		{"type": "shortcut", "data": {"shortcut_name": "Test Requests", "col": 4}},
		{"type": "shortcut", "data": {"shortcut_name": "Labs", "col": 4}},
		{"type": "shortcut", "data": {"shortcut_name": "Assets", "col": 4}},
		{"type": "shortcut", "data": {"shortcut_name": "My Profile", "col": 4}},
		{"type": "shortcut", "data": {"shortcut_name": "Holiday Calendar", "col": 4}},
		{"type": "shortcut", "data": {"shortcut_name": "Salary Slips", "col": 4}},
		{"type": "shortcut", "data": {"shortcut_name": "Invoices", "col": 4}},
	]

	shortcuts = [
		{"label": "My Dashboard", "link_type": "Page", "link_to": "ic-dashboard", "color": "Blue"},
		{"label": "Leads", "link_type": "DocType", "link_to": "IC Lead", "color": "Orange"},
		{"label": "Quotations", "link_type": "DocType", "link_to": "IC Quotation", "color": "Blue"},
		{"label": "Projects", "link_type": "DocType", "link_to": "IC Project", "color": "Green"},
		{"label": "Test Requests", "link_type": "DocType", "link_to": "IC Test Request", "color": "Purple"},
		{"label": "Labs", "link_type": "DocType", "link_to": "IC Lab", "color": "Cyan"},
		{"label": "Assets", "link_type": "DocType", "link_to": "IC Asset", "color": "Yellow"},
		{"label": "My Profile", "link_type": "DocType", "link_to": "IC Employee Profile", "color": "Blue"},
		{"label": "Holiday Calendar", "link_type": "DocType", "link_to": "Holiday List", "color": "Orange"},
		{"label": "Salary Slips", "link_type": "DocType", "link_to": "Salary Slip", "color": "Green"},
		{"label": "Invoices", "link_type": "DocType", "link_to": "IC Invoice", "color": "Purple"},
	]

	name = "InstaCertify"
	if frappe.db.exists("Workspace", name):
		ws = frappe.get_doc("Workspace", name)
		ws.shortcuts = []
		for s in shortcuts:
			ws.append("shortcuts", s)
		ws.content = frappe.as_json(content)
		ws.public = 1
		ws.module = "IC Setup"
		ws.save(ignore_permissions=True)
	else:
		ws = frappe.get_doc(
			{
				"doctype": "Workspace",
				"name": name,
				"label": name,
				"title": name,
				"public": 1,
				"module": "IC Setup",
				"content": frappe.as_json(content),
				"shortcuts": shortcuts,
			}
		)
		ws.insert(ignore_permissions=True)
