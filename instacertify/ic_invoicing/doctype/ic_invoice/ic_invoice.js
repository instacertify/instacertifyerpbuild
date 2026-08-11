frappe.ui.form.on('IC Invoice', {
	refresh(frm) {
		if (frm.doc.billing_country === 'India' && typeof instacertify !== 'undefined' && instacertify.gst) {
			instacertify.gst.add_fetch_button(frm, 'customer_gstin');
		}
		if (frm.doc.docstatus === 1 && ['Approved','Sent','Partially Paid'].includes(frm.doc.status)) {
			frm.add_custom_button(__('Send Payment Link'), () => {
				frappe.call({
					method: 'instacertify.api.invoice.send_payment_link',
					args: { name: frm.doc.name },
					callback(r) {
						if (r.message) frappe.msgprint(__('Payment link:<br><a href="{0}" target="_blank">{0}</a>', [r.message]));
						frm.reload_doc();
					}
				});
			}, __('Actions'));
			frm.add_custom_button(__('Send Reminder'), () => {
				frappe.call({
					method: 'instacertify.api.invoice.send_reminder',
					args: { name: frm.doc.name },
					callback() { frm.reload_doc(); }
				});
			}, __('Actions'));
		}
		if (frm.doc.docstatus === 0 && frm.doc.status === 'Pending Approval') {
			frm.add_custom_button(__('Approve Invoice'), () => {
				frappe.call({
					method: 'instacertify.api.invoice.approve_invoice',
					args: { name: frm.doc.name },
					callback() { frm.reload_doc(); }
				});
			}, __('Actions'));
		}
		if (frm.doc.docstatus === 1 && frm.doc.status !== 'Credited') {
			frm.add_custom_button(__('Create Credit Note'), () => {
				frappe.call({
					method: 'instacertify.api.invoice.create_credit_note',
					args: { name: frm.doc.name },
					callback(r) {
						if (r.message) frappe.set_route('Form', 'IC Invoice', r.message);
					}
				});
			}, __('Actions'));
		}
	},
	customer(frm) {
		if (!frm.doc.customer) return;
		frappe.call({
			method: 'instacertify.api.invoice.apply_customer_tax_defaults',
			args: { customer: frm.doc.customer, company_state: frm.doc.company_state },
			callback(r) {
				if (!r.message) return;
				Object.entries(r.message).forEach(([k, v]) => frm.set_value(k, v));
			}
		});
	},
	customer_gstin(frm) {
		if (frm.doc.billing_country === 'India' && frm.doc.customer_gstin && frm.doc.customer_gstin.length === 15) {
			frappe.db.get_single_value('IC Settings', 'auto_fetch_gstin_on_invoice').then((enabled) => {
				if (enabled && typeof instacertify !== 'undefined' && instacertify.gst) {
					instacertify.gst.fetch_and_apply(frm, 'customer_gstin');
				}
			});
		}
	}
});

frappe.ui.form.on('IC Invoice Item', {
	qty(frm, cdt, cdn) { recalc_row(frm, cdt, cdn); },
	rate(frm, cdt, cdn) { recalc_row(frm, cdt, cdn); },
	tax_rate(frm, cdt, cdn) { recalc_row(frm, cdt, cdn); }
});

function recalc_row(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	const amount = (row.qty || 0) * (row.rate || 0);
	frappe.model.set_value(cdt, cdn, 'amount', amount);
	frappe.model.set_value(cdt, cdn, 'tax_amount', amount * ((row.tax_rate || 0) / 100));
}
