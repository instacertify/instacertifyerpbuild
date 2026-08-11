# Copyright (c) 2026, InstaCertify and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ICTestRequest(Document):
	def validate(self):
		from instacertify.utils.qrcode import ensure_document_qr

		ensure_document_qr(self, "test_request")
		self._stamp_status_dates()

	def on_update(self):
		if self.sample_status == "Sample Received" and not self.sample_qr_code:
			from instacertify.utils.qrcode import generate_sample_qr

			generate_sample_qr(self)

	def _stamp_status_dates(self):
		now = frappe.utils.now_datetime()
		mapping = {
			"Sample Received": "sample_received_on",
			"Dispatched to Lab": "dispatched_to_lab_on",
			"Testing In Process": "testing_started_on",
			"Report Available": "report_available_on",
		}
		field = mapping.get(self.sample_status)
		if field and not self.get(field):
			self.set(field, now)
		if self.report_file and self.sample_status in ("Report Available", "Testing In Process"):
			self.sample_status = "Report Uploaded"
