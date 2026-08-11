# Copyright (c) 2026, InstaCertify and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ICQuotation(Document):
	def validate(self):
		self.calculate_totals()
		self.set_qr_payload()
		self._set_defaults_from_settings()

	def calculate_totals(self):
		consulting = lab = govt = other = revenue = 0
		for row in self.cost_lines or []:
			row.amount = (row.qty or 0) * (row.rate or 0)
			if row.cost_type == "Consulting":
				consulting += row.amount
				row.counts_as_revenue = 1
			elif row.cost_type == "Lab / Testing":
				lab += row.amount
				row.counts_as_revenue = 1
			elif row.cost_type == "Government Fees":
				govt += row.amount
			else:
				other += row.amount
			if row.counts_as_revenue:
				revenue += row.amount
		self.consulting_total = consulting
		self.lab_testing_total = lab
		self.government_fees_total = govt
		self.other_charges_total = other
		self.our_revenue_total = revenue
		self.grand_total = consulting + lab + govt + other

	def set_qr_payload(self):
		from instacertify.utils.qrcode import ensure_document_qr

		ensure_document_qr(self, "quotation")

	def _set_defaults_from_settings(self):
		if self.force_majeure and self.terms_and_conditions:
			return
		try:
			settings = frappe.get_single("IC Settings")
		except Exception:
			return
		if not self.force_majeure and settings.default_force_majeure:
			self.force_majeure = settings.default_force_majeure
		if not self.terms_and_conditions and settings.default_terms:
			self.terms_and_conditions = settings.default_terms
		if not self.valid_till and settings.quote_validity_days:
			self.valid_till = frappe.utils.add_days(frappe.utils.today(), settings.quote_validity_days)
		if not self.currency:
			self.currency = settings.default_currency or "INR"

	def on_submit(self):
		if self.status in (None, "", "Draft"):
			self.db_set("status", "Finalised")


def on_update_hooks(doc, method=None):
	"""Hook entrypoint from hooks.py"""
	pass
