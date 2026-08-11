frappe.ui.form.on('IC Test Request', {
	refresh(frm) {
		if (frm.doc.sample_status === 'Sample Received') {
			frm.add_custom_button(__('Generate Sample QR'), () => {
				frappe.call({
					method: 'instacertify.api.testing.generate_sample_qr',
					args: { name: frm.doc.name },
					callback(r) { frm.reload_doc(); }
				});
			}, __('Sample'));
		}
		if (frm.doc.sample_status === 'Report Uploaded' && frm.doc.report_file) {
			frm.add_custom_button(__('Share Report with Customer'), () => {
				frappe.call({
					method: 'instacertify.api.testing.share_report',
					args: { name: frm.doc.name },
					callback(r) {
						if (r.message) {
							frappe.msgprint(__('Report link:<br><a href="{0}" target="_blank">{0}</a>', [r.message]));
							frm.reload_doc();
						}
					}
				});
			}, __('Report'));
		}
		if (frm.doc.request_type === 'Test Request Form') {
			frm.add_custom_button(__('Share TRF with Customer'), () => {
				frappe.call({
					method: 'instacertify.api.testing.share_trf',
					args: { name: frm.doc.name },
					callback(r) {
						if (r.message) frappe.msgprint(__('TRF link:<br><a href="{0}" target="_blank">{0}</a>', [r.message]));
						frm.reload_doc();
					}
				});
			}, __('TRF'));
		}
	}
});
