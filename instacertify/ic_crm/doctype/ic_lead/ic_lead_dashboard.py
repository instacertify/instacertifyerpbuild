from frappe import _


def get_data():
	return {
		"fieldname": "lead",
		"transactions": [
			{"label": _("Quotations"), "items": ["IC Quotation"]},
		],
	}
