"""GST + multi-currency determination for InstaCertify invoices (ERPNext v16 compatible)."""

from __future__ import annotations

import re

import frappe

GSTIN_RE = re.compile(r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$")


def validate_gstin(gstin: str | None) -> tuple[bool, str]:
	if not gstin:
		return False, "GSTIN not provided"
	gstin = gstin.strip().upper()
	if not GSTIN_RE.match(gstin):
		return False, "Invalid GSTIN format"
	# Checksum validation (GSTIN last char)
	try:
		chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
		factor = [1, 2] * 8
		total = 0
		for i, ch in enumerate(gstin[:14]):
			code = chars.index(ch)
			prod = code * factor[i]
			total += (prod // 36) + (prod % 36)
		check = (36 - (total % 36)) % 36
		if chars[check] != gstin[14]:
			return False, "GSTIN checksum failed"
	except Exception:
		return False, "GSTIN validation error"
	return True, "GSTIN valid"


def determine_tax_profile(
	billing_country: str,
	billing_state: str | None,
	company_state: str | None,
	gst_category: str | None,
	customer_gstin: str | None,
	default_tax_rate: float = 18,
) -> dict:
	"""Return tax_type, rates, currency suggestion, reverse charge, place of supply."""
	country = (billing_country or "India").strip()
	gst_category = gst_category or "Registered"
	company_state = (company_state or "").strip()
	billing_state = (billing_state or "").strip()

	result = {
		"currency": "INR",
		"place_of_supply": billing_state or company_state,
		"tax_type": "CGST+SGST",
		"cgst_rate": 0,
		"sgst_rate": 0,
		"igst_rate": 0,
		"is_reverse_charge": 0,
		"default_tax_rate": default_tax_rate or 18,
		"gstin_valid": 0,
		"gstin_validation_message": "",
	}

	# Outside India → USD + export zero rated
	if country != "India":
		result.update(
			{
				"currency": "USD",
				"tax_type": "Export (Zero Rated)",
				"gst_category": "Export",
				"default_tax_rate": 0,
				"place_of_supply": "Other Territory",
				"gstin_validation_message": "Export supply — USD applied, GST zero rated",
			}
		)
		return result

	ok, msg = validate_gstin(customer_gstin) if gst_category == "Registered" else (True, "Not required")
	result["gstin_valid"] = 1 if ok else 0
	result["gstin_validation_message"] = msg

	if gst_category in ("Exempt",):
		result.update({"tax_type": "Exempt", "default_tax_rate": 0})
		return result

	if gst_category == "Unregistered":
		# Reverse charge may apply for B2B unregistered in some cases — flag for review
		result["is_reverse_charge"] = 1
		result["tax_type"] = "Reverse Charge"

	rate = float(default_tax_rate or 18)
	same_state = bool(company_state and billing_state and company_state.lower() == billing_state.lower())

	if same_state:
		half = rate / 2.0
		result.update(
			{
				"tax_type": "CGST+SGST" if not result["is_reverse_charge"] else "Reverse Charge",
				"cgst_rate": half,
				"sgst_rate": half,
				"igst_rate": 0,
				"default_tax_rate": rate,
			}
		)
	else:
		result.update(
			{
				"tax_type": "IGST" if not result["is_reverse_charge"] else "Reverse Charge",
				"cgst_rate": 0,
				"sgst_rate": 0,
				"igst_rate": rate,
				"default_tax_rate": rate,
			}
		)

	if gst_category in ("SEZ", "Export"):
		result.update(
			{
				"tax_type": "Export (Zero Rated)",
				"cgst_rate": 0,
				"sgst_rate": 0,
				"igst_rate": 0,
				"default_tax_rate": 0,
			}
		)

	return result


def apply_gst_and_currency(doc):
	"""Mutate IC Invoice document with GST + currency rules."""
	profile = determine_tax_profile(
		billing_country=doc.billing_country,
		billing_state=doc.billing_state,
		company_state=doc.company_state,
		gst_category=doc.gst_category,
		customer_gstin=doc.customer_gstin,
		default_tax_rate=doc.default_tax_rate or 18,
	)

	# Outside India force USD
	if doc.billing_country and doc.billing_country != "India":
		doc.currency = "USD"
		doc.gst_category = "Export"
	elif not doc.currency:
		doc.currency = profile["currency"]

	doc.tax_type = profile["tax_type"]
	doc.place_of_supply = profile["place_of_supply"]
	doc.cgst_rate = profile["cgst_rate"]
	doc.sgst_rate = profile["sgst_rate"]
	doc.igst_rate = profile["igst_rate"]
	doc.is_reverse_charge = profile["is_reverse_charge"]
	doc.gstin_valid = profile["gstin_valid"]
	doc.gstin_validation_message = profile["gstin_validation_message"]
	doc.default_tax_rate = profile["default_tax_rate"]

	# Apply default tax rate to items missing tax_rate / hsn
	for row in doc.items or []:
		if row.tax_rate in (None, ""):
			row.tax_rate = doc.default_tax_rate or 0
		if not row.hsn_sac:
			row.hsn_sac = "9983"  # default SAC for consulting/certification services
		row.currency = doc.currency
