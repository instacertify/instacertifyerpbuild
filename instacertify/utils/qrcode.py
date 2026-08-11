import io
import secrets

import frappe


def _make_qr_png_bytes(value: str) -> bytes:
	try:
		import qrcode
	except ImportError:
		# Minimal fallback PNG placeholder when qrcode lib is unavailable at build time
		return _placeholder_png()

	qr = qrcode.QRCode(version=2, box_size=6, border=2)
	qr.add_data(value)
	qr.make(fit=True)
	img = qr.make_image(fill_color="black", back_color="white")
	buf = io.BytesIO()
	img.save(buf, format="PNG")
	return buf.getvalue()


def _placeholder_png() -> bytes:
	# 1x1 transparent PNG
	import base64

	return base64.b64decode(
		"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO2X2ZcAAAAASUVORK5CYII="
	)


def attach_qr_for_value(value: str, folder: str = "Home/IC QR Codes", filename: str | None = None) -> str:
	frappe.db.exists("File", {"folder": folder})  # touch
	_ensure_folder(folder)
	filename = filename or f"qr-{secrets.token_hex(6)}.png"
	content = _make_qr_png_bytes(value)
	file_doc = frappe.get_doc(
		{
			"doctype": "File",
			"file_name": filename,
			"content": content,
			"is_private": 0,
			"folder": folder,
		}
	)
	file_doc.save(ignore_permissions=True)
	return file_doc.file_url


def _ensure_folder(folder_path: str):
	# folder_path like Home/IC QR Codes
	parts = folder_path.split("/")
	parent = parts[0]
	for part in parts[1:]:
		current = f"{parent}/{part}"
		if not frappe.db.exists("File", {"file_name": part, "folder": parent, "is_folder": 1}):
			frappe.get_doc(
				{
					"doctype": "File",
					"file_name": part,
					"is_folder": 1,
					"folder": parent,
				}
			).insert(ignore_permissions=True)
		parent = current


def ensure_document_qr(doc, kind: str):
	if not doc.unique_barcode:
		doc.unique_barcode = f"IC-{kind.upper()}-{secrets.token_hex(8).upper()}"
	payload = f"{kind}|{doc.name}|{doc.unique_barcode}"
	if not doc.qr_code:
		doc.qr_code = attach_qr_for_value(payload, filename=f"{kind}-{doc.name}.png")


def generate_sample_qr(doc):
	if not doc.sample_tracking_code:
		doc.sample_tracking_code = f"SMP-{secrets.token_hex(6).upper()}"
	url = frappe.utils.get_url(f"/sample/{doc.sample_tracking_code}")
	doc.sample_qr_code = attach_qr_for_value(url, filename=f"sample-{doc.name}.png")
	doc.db_set(
		{
			"sample_tracking_code": doc.sample_tracking_code,
			"sample_qr_code": doc.sample_qr_code,
		},
		update_modified=False,
	)
