# Copyright (c) 2026, InstaCertify and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.model.naming import make_autoname


class ICAsset(Document):
	def before_insert(self):
		if not self.asset_code:
			self.asset_code = make_autoname("IC-AST-.YYYY.-.####")

	def validate(self):
		if self.custodian and self.status == "Available":
			self.status = "Assigned"
		if not self.custodian and self.status == "Assigned":
			self.status = "Available"
