app_name = "instacertify"
app_title = "InstaCertify ERP"
app_publisher = "InstaCertify"
app_description = "Consulting, certification, testing and operations ERP for InstaCertify"
app_email = "nikhil@instacertify.com"
app_license = "mit"
app_version = "1.0.0"

# InstaCertify brand colors injected into Desk
app_include_css = ["/assets/instacertify/css/instacertify.css"]
app_include_js = [
	"/assets/instacertify/js/instacertify_desk.js",
	"/assets/instacertify/js/gst_fetch.js",
]

web_include_css = ["/assets/instacertify/css/instacertify_web.css"]

after_install = "instacertify.ic_setup.install.after_install"
after_migrate = "instacertify.ic_setup.install.after_migrate"

# Fixtures shipped with the app
fixtures = [
	{
		"dt": "Role",
		"filters": [
			[
				"name",
				"in",
				[
					"IC Admin",
					"IC All Ops Manager",
					"IC Sales Person",
					"IC Operations Manager",
					"IC Customer Manager",
					"IC HR",
				],
			]
		],
	},
]

# Document events
doc_events = {
	"IC Quotation": {
		"on_update": "instacertify.ic_quotation.doctype.ic_quotation.ic_quotation.on_update_hooks",
	},
	"IC Lead": {
		"validate": "instacertify.ic_crm.doctype.ic_lead.ic_lead.validate_hooks",
	},
}

# Permission query conditions — sales see own / assigned records
permission_query_conditions = {
	"IC Lead": "instacertify.permissions.get_lead_query",
	"IC Quotation": "instacertify.permissions.get_quotation_query",
	"IC Project": "instacertify.permissions.get_project_query",
	"IC Test Request": "instacertify.permissions.get_test_request_query",
}

has_permission = {
	"IC Lead": "instacertify.permissions.has_lead_permission",
	"IC Quotation": "instacertify.permissions.has_quotation_permission",
	"IC Project": "instacertify.permissions.has_project_permission",
}

# Website route rules for public customer portals
website_route_rules = [
	{"from_route": "/quote/<path:token>", "to_route": "quote"},
	{"from_route": "/docs-upload/<path:token>", "to_route": "docs_upload"},
	{"from_route": "/report/<path:token>", "to_route": "report_view"},
	{"from_route": "/trf/<path:token>", "to_route": "trf_form"},
	{"from_route": "/sample/<path:code>", "to_route": "sample_track"},
	{"from_route": "/customer-project/<path:token>", "to_route": "customer_project"},
	{"from_route": "/customer-credentials/<path:token>", "to_route": "customer_credentials"},
	{"from_route": "/pay-invoice/<path:token>", "to_route": "pay_invoice"},
	{"from_route": "/invoice-portal/<path:token>", "to_route": "invoice_portal"},
]

# Scheduler
scheduler_events = {
	"daily": [
		"instacertify.tasks.daily.expire_quotes",
		"instacertify.tasks.daily.invoice_reminders_and_recurring",
	]
}

default_mail_footer = """
	<div style="padding: 12px 0; color: #0B5FFF; font-family: 'Segoe UI', sans-serif;">
		<strong>InstaCertify</strong> — Certification & Consulting
	</div>
"""
