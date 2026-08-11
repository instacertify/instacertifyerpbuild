from frappe import _


def get_data():
	return {
		"fieldname": "quotation",
		"transactions": [
			{"label": _("Execution"), "items": ["IC Project", "IC Test Request"]},
		],
	}
