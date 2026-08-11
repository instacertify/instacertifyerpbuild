frappe.ui.form.on('IC Project', {
	refresh(frm) {
		if (frm.is_new()) return;

		frm.add_custom_button(__('Open Document Library'), () => {
			frappe.set_route('List', 'IC Customer Document Request', { project: frm.doc.name });
		}, __('Documents'));

		frm.add_custom_button(__('Share Customer Portal'), () => {
			frappe.call({
				method: 'instacertify.api.portal.share_project_portal',
				args: { project: frm.doc.name },
				callback(r) {
					if (r.message) {
						frappe.msgprint(__('Customer portal link:<br><a href="{0}" target="_blank">{0}</a>', [r.message]));
						frm.reload_doc();
					}
				}
			});
		}, __('Customer'));

		frm.add_custom_button(__('Create / Share Login Credentials'), () => {
			frappe.new_doc('IC Customer Portal Account', {
				customer: frm.doc.customer,
				project: frm.doc.name,
			});
		}, __('Customer'));

		if (frm.doc.status !== 'Completed') {
			frm.add_custom_button(__('Mark Completed'), () => {
				frm.set_value('status', 'Completed');
				frm.set_value('percent_complete', 100);
				frm.set_value('actual_end_date', frappe.datetime.get_today());
				frm.save();
			}, __('Actions'));
		}
	}
});
