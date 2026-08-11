frappe.ui.form.on('IC Project', {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__('Open Document Library'), () => {
				frappe.set_route('List', 'IC Customer Document Request', { project: frm.doc.name });
			}, __('Documents'));
		}
	}
});
