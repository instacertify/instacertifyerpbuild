frappe.ui.form.on('IC Lead', {
	refresh(frm) {
		if (!frm.is_new() && frm.doc.status !== 'Won' && !frm.doc.customer) {
			frm.add_custom_button(__('Convert to Customer'), () => {
				frappe.call({
					method: 'instacertify.api.lead.convert_lead_to_customer',
					args: { lead: frm.doc.name },
					freeze: true,
					callback(r) {
						if (r.message) {
							frm.reload_doc();
							frappe.set_route('Form', 'Customer', r.message);
						}
					}
				});
			}, __('Actions'));
		}
	},
	lead_source(frm) {
		if (frm.doc.lead_source !== 'Consultant') frm.set_value('consultant', null);
	},
	country(frm) {
		if (frm.doc.country !== 'India') frm.set_value('state', null);
	}
});
