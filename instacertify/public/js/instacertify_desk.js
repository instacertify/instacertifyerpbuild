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

/**
 * Make Customer a searchable dropdown (Link) on InstaCertify forms.
 * Click / type to see customer name list.
 */
instacertify.setup_customer_dropdown = function (frm, fieldname = "customer") {
	if (!frm.fields_dict[fieldname]) return;

	frm.set_df_property(fieldname, "only_select", 0);
	frm.set_df_property(fieldname, "placeholder", __("Select Customer"));

	frm.set_query(fieldname, () => {
		const filters = {};
		if (frm.doc.customer_country) {
			filters.customer_country = frm.doc.customer_country;
		} else if (frm.doc.billing_country) {
			filters.billing_country = frm.doc.billing_country;
		}
		return {
			query: "instacertify.api.customer.customer_link_query",
			filters,
		};
	});
};

// Apply dropdown behaviour on all IC forms that pick a Customer
const IC_CUSTOMER_FORMS = [
	"IC Quotation",
	"IC Invoice",
	"IC Project",
	"IC Lead",
	"IC Test Request",
	"IC Customer Document Request",
	"IC Customer Portal Account",
];

IC_CUSTOMER_FORMS.forEach((doctype) => {
	frappe.ui.form.on(doctype, {
		setup(frm) {
			instacertify.setup_customer_dropdown(frm, "customer");
		},
		onload(frm) {
			instacertify.setup_customer_dropdown(frm, "customer");
		},
		refresh(frm) {
			instacertify.setup_customer_dropdown(frm, "customer");
		},
		customer_country(frm) {
			if (frm.fields_dict.customer) {
				instacertify.setup_customer_dropdown(frm, "customer");
			}
		},
		billing_country(frm) {
			if (frm.fields_dict.customer) {
				instacertify.setup_customer_dropdown(frm, "customer");
			}
		},
	});
});

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
