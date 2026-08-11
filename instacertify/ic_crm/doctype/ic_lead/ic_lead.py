# Copyright (c) 2026, InstaCertify and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ICLead(Document):
	def validate(self):
		if self.lead_source == "Consultant" and not self.consultant:
			frappe.throw("Please select a Consultant for this lead source")
		if self.country == "India" and not self.state:
			frappe.throw("Please select State for India leads")


def validate_hooks(doc, method=None):
	doc.validate()
