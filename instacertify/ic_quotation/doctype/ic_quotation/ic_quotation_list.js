frappe.listview_settings["IC Quotation"] = {
	onload(listview) {
		if (typeof instacertify !== "undefined") {
			instacertify.add_excel_export(listview, "IC Quotation");
		}
	},
	get_indicator(doc) {
		const colors = {
			Draft: "gray",
			Finalised: "blue",
			Shared: "orange",
			Accepted: "green",
			"Changes Requested": "yellow",
			Rejected: "red",
			"Project Started": "purple",
		};
		return [__(doc.status), colors[doc.status] || "blue", "status,=," + doc.status];
	},
};
