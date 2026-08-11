# Copyright (c) 2026, InstaCertify and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ICInvoice(Document):
	def validate(self):
		from instacertify.utils.gst import apply_gst_and_currency

		apply_gst_and_currency(self)
		self.calculate_totals()

	def calculate_totals(self):
		subtotal = tax = 0
		for row in self.items or []:
			row.amount = (row.qty or 0) * (row.rate or 0)
			row.tax_amount = (row.amount or 0) * ((row.tax_rate or 0) / 100.0)
			subtotal += row.amount or 0
			tax += row.tax_amount or 0
		self.subtotal = subtotal
		self.tax_total = tax
		self.grand_total = subtotal + tax - (self.discount_amount or 0)
		paid = sum((p.amount or 0) for p in self.payments or [])
		self.paid_amount = paid
		self.balance_due = (self.grand_total or 0) - paid
		if self.is_credit_note:
			return
		if self.docstatus == 1:
			if self.balance_due <= 0 and self.grand_total:
				self.status = "Paid"
			elif paid > 0 and self.status not in ("Credited", "Cancelled"):
				self.status = "Partially Paid"

	def before_submit(self):
		if self.status == "Draft":
			self.status = "Pending Approval"

	def on_submit(self):
		if self.skip_approval and self.status in ("Draft", "Pending Approval"):
			self.db_set("status", "Approved")
