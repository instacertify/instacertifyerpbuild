// Shared GSTIN fetch helper (India Compliance)

frappe.provide("instacertify.gst");

instacertify.gst.fetch_and_apply = function (frm, gstin_field, opts = {}) {
	const gstin = frm.doc[gstin_field];
	if (!gstin) {
		frappe.msgprint(__("Enter GSTIN first"));
		return;
	}
	frappe.call({
		method: "instacertify.api.gst_compliance.fetch_gstin_details",
		args: { gstin, force_update: 1 },
		freeze: true,
		freeze_message: __("Fetching GSTIN from India Compliance…"),
		callback(r) {
			const d = r.message || {};
			if (opts.on_success) {
				opts.on_success(d);
				return;
			}
			if (d.state && frm.fields_dict.state) {
				frm.set_value("state", d.state);
			}
			if (d.state && frm.fields_dict.billing_state) {
				frm.set_value("billing_state", d.state);
			}
			if (d.legal_name && frm.fields_dict.gstin_legal_name) {
				frm.set_value("gstin_legal_name", d.legal_name);
			}
			if (d.legal_name && frm.fields_dict.company_name && !frm.doc.company_name) {
				frm.set_value("company_name", d.legal_name);
			}
			if (frm.fields_dict.customer_country) {
				frm.set_value("customer_country", "India");
			}
			if (frm.fields_dict.billing_country) {
				frm.set_value("billing_country", "India");
			}
			if (frm.fields_dict.gst_category && d.gst_category) {
				frm.set_value("gst_category", d.gst_category);
			}
			frappe.show_alert({
				message: __("GSTIN fetch: {0}", [d.message || d.status || "done"]),
				indicator: d.source === "india_compliance" ? "green" : "orange",
			});
		},
	});
};

instacertify.gst.add_fetch_button = function (frm, gstin_field) {
	if (!frm.fields_dict[gstin_field]) return;
	frm.add_custom_button(__("Fetch GSTIN Details"), () => {
		instacertify.gst.fetch_and_apply(frm, gstin_field);
	}, __("GST"));
};
