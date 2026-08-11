# Copyright (c) 2026, InstaCertify and contributors
# For license information, please see license.txt

import secrets

import frappe
from frappe.model.document import Document


class ICCustomerDocumentRequest(Document):
	def before_insert(self):
		if not self.share_token:
			self.share_token = secrets.token_urlsafe(24)
