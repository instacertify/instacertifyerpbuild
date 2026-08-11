frappe.listview_settings["IC Lead"] = {
	onload(listview) {
		if (typeof instacertify !== "undefined") {
			instacertify.add_excel_export(listview, "IC Lead");
		}
	},
	get_indicator(doc) {
		const colors = {
			Open: "orange",
			Contacted: "blue",
			Qualified: "cyan",
			"Quotation Sent": "purple",
			Won: "green",
			Lost: "red",
			Nurture: "gray",
		};
		return [__(doc.status), colors[doc.status] || "blue", "status,=," + doc.status];
	},
};
