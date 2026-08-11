// InstaCertify desk helpers — brand polish + export shortcut for admins

frappe.provide("instacertify");

instacertify.brand = {
	primary: "#0B5FFF",
	accent: "#FF7A00",
};

frappe.ready(function () {
	document.documentElement.style.setProperty("--ic-blue", instacertify.brand.primary);
	document.documentElement.style.setProperty("--ic-orange", instacertify.brand.accent);
});

instacertify.can_export = function () {
	return frappe.user.has_role("IC Admin") || frappe.user.has_role("IC All Ops Manager") || frappe.user.has_role("System Manager");
};

instacertify.add_excel_export = function (listview, doctype) {
	if (!instacertify.can_export()) return;
	listview.page.add_inner_button(__("Download Excel"), () => {
		frappe.call({
			method: "instacertify.api.export.export_doctype_excel",
			args: { doctype, filters: JSON.stringify(listview.filter_area.get() || []) },
			freeze: true,
			callback(r) {
				if (!r.message) return;
				const rows = r.message;
				if (!rows.length) {
					frappe.msgprint(__("No rows to export"));
					return;
				}
				const keys = Object.keys(rows[0]).filter((k) => !k.startsWith("_"));
				const csv = [keys.join(",")]
					.concat(
						rows.map((row) =>
							keys
								.map((k) => {
									let v = row[k];
									if (v === null || v === undefined) v = "";
									v = String(v).replaceAll('"', '""');
									return `"${v}"`;
								})
								.join(",")
						)
					)
					.join("\n");
				const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
				const url = URL.createObjectURL(blob);
				const a = document.createElement("a");
				a.href = url;
				a.download = `${doctype.replaceAll(" ", "_")}.csv`;
				a.click();
				URL.revokeObjectURL(url);
			},
		});
	});
};
