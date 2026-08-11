frappe.listview_settings["IC Project"] = {
	onload(listview) {
		if (typeof instacertify !== "undefined") {
			instacertify.add_excel_export(listview, "IC Project");
		}
	},
	get_indicator(doc) {
		const colors = {
			Open: "orange",
			"In Progress": "blue",
			"On Hold": "yellow",
			Completed: "green",
			Cancelled: "red",
		};
		return [__(doc.status), colors[doc.status] || "blue", "status,=," + doc.status];
	},
};
