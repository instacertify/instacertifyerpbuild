# Copyright (c) 2026, InstaCertify and contributors
# For license information, please see license.txt

import secrets

import frappe
from frappe.model.document import Document


class ICProject(Document):
	def before_insert(self):
		if not self.portal_token:
			self.portal_token = secrets.token_urlsafe(24)
		if not self.customer_portal_link and self.portal_token:
			self.customer_portal_link = frappe.utils.get_url(f"/customer-project/{self.portal_token}")

	def validate(self):
		if self.progress_log:
			last = self.progress_log[-1]
			if last.percent_complete is not None:
				self.percent_complete = last.percent_complete
		if not self.certification_name and self.service:
			self.certification_name = self.service
		if self.portal_token and not self.customer_portal_link:
			self.customer_portal_link = frappe.utils.get_url(f"/customer-project/{self.portal_token}")

	def on_update(self):
		# When marked completed, credentials become visible on customer portal automatically
		if self.status == "Completed":
			frappe.publish_realtime(
				"ic_project_completed",
				{"project": self.name, "customer": self.customer},
				user=self.sales_person,
			)
