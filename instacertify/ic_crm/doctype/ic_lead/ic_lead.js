frappe.ui.form.on('IC Lead', {
	refresh(frm) {
		if (frm.doc.country === 'India' && typeof instacertify !== 'undefined' && instacertify.gst) {
			instacertify.gst.add_fetch_button(frm, 'gstin');
		}
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
	gstin(frm) {
		if (frm.doc.country === 'India' && frm.doc.gstin && frm.doc.gstin.length === 15) {
			frappe.db.get_single_value('IC Settings', 'auto_fetch_gstin_on_lead').then((enabled) => {
				if (enabled && typeof instacertify !== 'undefined' && instacertify.gst) {
					instacertify.gst.fetch_and_apply(frm, 'gstin');
				}
			});
		}
	},
	lead_source(frm) {
		if (frm.doc.lead_source !== 'Consultant') frm.set_value('consultant', null);
	},
	country(frm) {
		if (frm.doc.country !== 'India') frm.set_value('state', null);
	}
});
