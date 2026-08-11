frappe.ui.form.on('IC Customer Document Request', {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__('Share Upload Link'), () => {
				frappe.call({
					method: 'instacertify.api.documents.share_document_request',
					args: { name: frm.doc.name },
					callback(r) {
						if (r.message) {
							frappe.msgprint(__('Share link:<br><a href="{0}" target="_blank">{0}</a>', [r.message]));
							frm.reload_doc();
						}
					}
				});
			});
		}
	},
	service(frm) {
		if (!frm.doc.service) return;
		frappe.call({
			method: 'instacertify.api.documents.load_service_checklist',
			args: { service: frm.doc.service },
			callback(r) {
				frm.clear_table('checklist_items');
				(r.message || []).forEach((row) => frm.add_child('checklist_items', row));
				frm.refresh_field('checklist_items');
			}
		});
	}
});
