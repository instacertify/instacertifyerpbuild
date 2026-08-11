frappe.ui.form.on('IC Customer Portal Account', {
	refresh(frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__('Share Credentials Link'), () => {
				frappe.call({
					method: 'instacertify.api.portal.share_credentials',
					args: { name: frm.doc.name },
					callback(r) {
						if (r.message) {
							frappe.msgprint(__('Share this link:<br><a href="{0}" target="_blank">{0}</a>', [r.message]));
							frm.reload_doc();
						}
					}
				});
			});
		}
	}
});
