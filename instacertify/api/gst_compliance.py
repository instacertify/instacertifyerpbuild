"""India Compliance GST data fetching helpers for InstaCertify."""

from __future__ import annotations

import frappe
from frappe import _


def is_india_compliance_installed() -> bool:
	return "india_compliance" in frappe.get_installed_apps()


def is_gst_fetch_enabled() -> bool:
	try:
		return bool(frappe.db.get_single_value("IC Settings", "enable_india_compliance_gst_fetch"))
	except Exception:
		return True


@frappe.whitelist()
def get_india_compliance_status():
	"""Status panel for IC Settings / setup checklist."""
	installed = is_india_compliance_installed()
	gst_settings_exists = bool(frappe.db.exists("DocType", "GST Settings"))
	api_enabled = False
	sandbox = False
	validate_gstin = False
	message = ""

	if installed and gst_settings_exists:
		try:
			settings = frappe.get_cached_doc("GST Settings")
			# Field names vary slightly across versions — best effort
			api_enabled = bool(
				getattr(settings, "enable_api", None)
				or getattr(settings, "api_enabled", None)
				or getattr(settings, "enable_e_invoice", None)
			)
			sandbox = bool(getattr(settings, "sandbox_mode", 0))
			validate_gstin = bool(getattr(settings, "validate_gstin_status", 0))
			message = _("India Compliance installed. Configure GST Settings for API credentials.")
		except Exception:
			message = _("India Compliance installed but GST Settings could not be read.")
	elif not installed:
		message = _(
			"India Compliance is not installed. Install from "
			"https://github.com/resilient-tech/india-compliance and follow "
			"https://docs.indiacompliance.app/docs/configuration/gst_setup"
		)
	else:
		message = _("GST Settings DocType not found. Complete India Compliance setup.")

	return {
		"installed": installed,
		"gst_settings_exists": gst_settings_exists,
		"api_enabled": api_enabled,
		"sandbox_mode": sandbox,
		"validate_gstin_status": validate_gstin,
		"fetch_enabled_in_ic_settings": is_gst_fetch_enabled(),
		"docs_url": "https://docs.indiacompliance.app/docs/configuration/gst_setup",
		"api_docs_url": "https://docs.indiacompliance.app/docs/ewaybill-and-einvoice/gst_settings",
		"message": message,
	}


@frappe.whitelist()
def fetch_gstin_details(gstin: str, force_update: int = 1):
	"""
	Fetch GSTIN details using India Compliance when available.
	Falls back to local format/checksum validation.
	"""
	gstin = (gstin or "").strip().upper()
	if not gstin:
		frappe.throw(_("GSTIN is required"))

	if not is_gst_fetch_enabled():
		frappe.throw(_("GST data fetching is disabled in IC Settings"))

	result = {
		"gstin": gstin,
		"source": "local",
		"status": None,
		"legal_name": None,
		"trade_name": None,
		"registration_date": None,
		"gst_category": None,
		"state": None,
		"address": None,
		"raw": None,
		"valid": False,
		"message": "",
	}

	# Local validation always
	from instacertify.utils.gst import validate_gstin

	ok, msg = validate_gstin(gstin)
	result["valid"] = ok
	result["message"] = msg
	if ok and len(gstin) >= 2:
		# First 2 digits = state code mapping (best effort)
		result["state"] = _state_from_gstin_code(gstin[:2])

	if not is_india_compliance_installed():
		result["message"] = (
			(msg + " · ") if msg else ""
		) + _(
			"Install India Compliance for live GSTIN fetch: "
			"https://docs.indiacompliance.app/docs/configuration/gst_setup"
		)
		return result

	# Prefer India Compliance APIs
	status_doc = None
	err = None
	try:
		from india_compliance.gst_india.doctype.gstin.gstin import get_gstin_status

		status_doc = get_gstin_status(gstin=gstin, force_update=bool(int(force_update)))
	except Exception as e:
		err = e
		status_doc = None

	if not status_doc:
		try:
			from india_compliance.gst_india.utils.gstin_info import fetch_gstin_status

			status_doc = fetch_gstin_status(gstin=gstin, throw=False)
		except Exception as e:
			err = e
			status_doc = None

	if not status_doc:
		result["message"] = _("No GSTIN data returned. Check GST Settings API credentials. {0}").format(
			str(err) if err else ""
		)
		return result

	# status_doc may be Document or dict
	data = status_doc.as_dict() if hasattr(status_doc, "as_dict") else frappe._dict(status_doc)
	result.update(
		{
			"source": "india_compliance",
			"status": data.get("status"),
			"legal_name": data.get("legal_name") or data.get("taxpayer_name") or data.get("lgnm"),
			"trade_name": data.get("trade_name") or data.get("tradeName") or data.get("trade_name"),
			"registration_date": data.get("registration_date") or data.get("registration_date"),
			"gst_category": data.get("gst_category") or data.get("taxpayer_type"),
			"raw": {k: data.get(k) for k in data if k not in ("name", "owner", "creation", "modified")},
			"valid": True if data.get("status") in (None, "Active", "Valid") or data.get("gstin") else result["valid"],
			"message": _("Fetched via India Compliance"),
		}
	)
	if not result.get("state") and data.get("gst_state"):
		result["state"] = data.get("gst_state")
	return result


@frappe.whitelist()
def apply_gstin_to_customer(customer: str, gstin: str):
	"""Fetch GSTIN and update Customer + primary Address when possible."""
	details = fetch_gstin_details(gstin, force_update=1)
	if not details.get("gstin"):
		return details

	cust = frappe.get_doc("Customer", customer)
	if hasattr(cust, "gstin"):
		cust.gstin = details["gstin"]
	if details.get("legal_name") and hasattr(cust, "customer_name") and not cust.customer_name:
		cust.customer_name = details["legal_name"]
	# gst_category on customer if present
	if details.get("gst_category") and hasattr(cust, "gst_category"):
		cust.gst_category = details["gst_category"]
	cust.save(ignore_permissions=True)

	addr_name = frappe.db.get_value(
		"Dynamic Link",
		{"link_doctype": "Customer", "link_name": customer, "parenttype": "Address"},
		"parent",
	)
	if addr_name:
		addr = frappe.get_doc("Address", addr_name)
		if hasattr(addr, "gstin"):
			addr.gstin = details["gstin"]
		if details.get("state") and hasattr(addr, "state"):
			addr.state = details["state"]
		if details.get("state") and hasattr(addr, "gst_state"):
			addr.gst_state = details["state"]
		addr.save(ignore_permissions=True)

	return details


def _state_from_gstin_code(code: str) -> str | None:
	STATES = {
		"01": "Jammu and Kashmir",
		"02": "Himachal Pradesh",
		"03": "Punjab",
		"04": "Chandigarh",
		"05": "Uttarakhand",
		"06": "Haryana",
		"07": "Delhi",
		"08": "Rajasthan",
		"09": "Uttar Pradesh",
		"10": "Bihar",
		"11": "Sikkim",
		"12": "Arunachal Pradesh",
		"13": "Nagaland",
		"14": "Manipur",
		"15": "Mizoram",
		"16": "Tripura",
		"17": "Meghalaya",
		"18": "Assam",
		"19": "West Bengal",
		"20": "Jharkhand",
		"21": "Odisha",
		"22": "Chhattisgarh",
		"23": "Madhya Pradesh",
		"24": "Gujarat",
		"26": "Dadra and Nagar Haveli and Daman and Diu",
		"27": "Maharashtra",
		"29": "Karnataka",
		"30": "Goa",
		"31": "Lakshadweep",
		"32": "Kerala",
		"33": "Tamil Nadu",
		"34": "Puducherry",
		"35": "Andaman and Nicobar Islands",
		"36": "Telangana",
		"37": "Andhra Pradesh",
		"38": "Ladakh",
	}
	return STATES.get(code)
