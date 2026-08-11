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
 * Customer Link dropdown + typeahead suggestions.
 * Click / focus / type to see suggested customers by name.
 */
instacertify.setup_customer_dropdown = function (frm, fieldname = "customer") {
	if (!frm.fields_dict[fieldname]) return;

	frm.set_df_property(fieldname, "only_select", 0);
	frm.set_df_property(fieldname, "placeholder", __("Type to see customer suggestions…"));

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

	const field = frm.get_field(fieldname);
	if (!field || !field.$input || field._ic_suggest_bound) return;
	field._ic_suggest_bound = true;

	// On focus: open suggestions immediately (empty search shows recent/all)
	field.$input.on("focus.ic_suggest", function () {
		if (field.$input.val()) return;
		// Trigger Link search with blank text so dropdown lists suggestions
		if (field.awesomplete) {
			setTimeout(() => {
				try {
					field.awesomplete.evaluate();
					field.$input.trigger("input");
				} catch (e) {
					/* ignore */
				}
			}, 50);
		}
	});
};

/**
 * Suggest existing customers while typing a company / customer name (Lead).
 */
instacertify.setup_customer_name_suggestions = function (frm, text_field = "company_name") {
	if (!frm.fields_dict[text_field]) return;
	const field = frm.get_field(text_field);
	if (!field || !field.$input || field._ic_name_suggest_bound) return;
	field._ic_name_suggest_bound = true;

	let timer = null;
	field.$input.attr("placeholder", __("Start typing — matching customers will be suggested"));

	field.$input.on("keyup.ic_suggest", function () {
		clearTimeout(timer);
		const q = (field.$input.val() || "").trim();
		if (q.length < 2) {
			frm.set_df_property(text_field, "description", "");
			return;
		}
		timer = setTimeout(() => {
			frappe.call({
				method: "instacertify.api.customer.suggest_customers",
				args: {
					txt: q,
					limit: 8,
					country: frm.doc.country || frm.doc.customer_country || null,
				},
				callback(r) {
					const rows = r.message || [];
					if (!rows.length) {
						frm.set_df_property(
							text_field,
							"description",
							__("No existing customer match — a new customer can be created later")
						);
						return;
					}
					const links = rows
						.map(
							(row) =>
								`<a href="#" class="ic-suggest-customer" data-customer="${frappe.utils.escape_html(
									row.value
								)}" data-label="${frappe.utils.escape_html(row.label)}">
									${frappe.utils.escape_html(row.label)}
									<span class="text-muted">(${frappe.utils.escape_html(row.description || row.value)})</span>
								</a>`
						)
						.join("<br>");
					frm.set_df_property(
						text_field,
						"description",
						`<div style="margin-top:4px"><b>${__("Suggested customers")}</b><br>${links}</div>`
					);
					// bind click
					setTimeout(() => {
						$(frm.fields_dict[text_field].$wrapper)
							.find("a.ic-suggest-customer")
							.off("click")
							.on("click", function (e) {
								e.preventDefault();
								const cust = $(this).data("customer");
								const label = $(this).data("label");
								if (frm.fields_dict.customer) {
									frm.set_value("customer", cust);
								}
								if (frm.fields_dict.company_name) {
									frm.set_value("company_name", label);
								}
								frappe.show_alert({
									message: __("Linked suggested customer: {0}", [label]),
									indicator: "green",
								});
							});
					}, 50);
				},
			});
		}, 300);
	});
};

// Apply dropdown + suggestions on all IC forms that pick a Customer
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
			if (doctype === "IC Lead") {
				instacertify.setup_customer_name_suggestions(frm, "company_name");
			}
		},
		refresh(frm) {
			instacertify.setup_customer_dropdown(frm, "customer");
			if (doctype === "IC Lead") {
				instacertify.setup_customer_name_suggestions(frm, "company_name");
			}
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
