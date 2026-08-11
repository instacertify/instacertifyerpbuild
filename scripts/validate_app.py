#!/usr/bin/env python3
"""Static validation for the InstaCertify Frappe app (no bench required)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "instacertify"
errors: list[str] = []


def main():
	modules = [m.strip() for m in (ROOT / "modules.txt").read_text().splitlines() if m.strip()]
	for mod in modules:
		folder = ROOT / mod.lower().replace(" ", "_")
		if not folder.is_dir():
			errors.append(f"Missing module folder for {mod}: {folder.name}")

	doctypes = 0
	for meta_path in ROOT.rglob("*.json"):
		if "/doctype/" not in str(meta_path):
			continue
		meta = json.loads(meta_path.read_text())
		if meta.get("doctype") != "DocType":
			continue
		doctypes += 1
		name = meta["name"]
		expected = name.replace(" ", "").replace("-", "")
		py = meta_path.with_suffix(".py")
		if f"class {expected}(" not in py.read_text():
			errors.append(f"Class mismatch for {name}")
		if meta.get("module") not in modules:
			errors.append(f"{name} module {meta.get('module')} not in modules.txt")
		for f in meta.get("fields", []):
			if f.get("fieldtype") == "Table" and not f.get("options"):
				errors.append(f"{name}.{f.get('fieldname')} Table missing options")

	required_apis = [
		ROOT / "api/quotation.py",
		ROOT / "api/lead.py",
		ROOT / "api/documents.py",
		ROOT / "api/testing.py",
		ROOT / "api/dashboard.py",
		ROOT / "hooks.py",
		ROOT / "permissions.py",
		ROOT / "public/css/instacertify.css",
		ROOT / "page/ic_dashboard/ic_dashboard.js",
		ROOT / "www/quote.html",
	]
	for p in required_apis:
		if not p.exists():
			errors.append(f"Missing required file {p.relative_to(ROOT.parent)}")

	print(f"DocTypes: {doctypes}")
	print(f"Modules: {', '.join(modules)}")
	if errors:
		print("FAILED:")
		for e in errors:
			print(" -", e)
		sys.exit(1)
	print("OK")


if __name__ == "__main__":
	main()
