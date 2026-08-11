# Copyright (c) 2026, InstaCertify and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ICEmployeeProfile(Document):
	def validate(self):
		if self.joining_letter and not self.joining_letter_qr:
			from instacertify.utils.qrcode import attach_qr_for_value

			self.joining_letter_qr = attach_qr_for_value(
				f"JOINING|{self.name}|{self.employee_name}|{self.date_of_joining or ''}",
				folder="Home/IC QR Codes",
				filename=f"joining-{self.name}.png",
			)
