frappe.listview_settings["IC Test Request"] = {
	onload(listview) {
		if (typeof instacertify !== "undefined") {
			instacertify.add_excel_export(listview, "IC Test Request");
		}
	},
	get_indicator(doc) {
		const colors = {
			"Awaiting Sample": "gray",
			"Sample Received": "orange",
			"Dispatched to Lab": "cyan",
			"Testing In Process": "blue",
			"Report Available": "purple",
			"Report Uploaded": "green",
			"Shared with Customer": "green",
		};
		return [__(doc.sample_status), colors[doc.sample_status] || "blue", "sample_status,=," + doc.sample_status];
	},
};
