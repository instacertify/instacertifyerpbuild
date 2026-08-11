frappe.ui.form.on('IC Quotation', {
	refresh(frm) {
		frm.set_query('quotation_template', () => ({
			filters: { is_active: 1 }
		}));
		if (frm.doc.docstatus === 1 && ['Finalised', 'Shared', 'Changes Requested'].includes(frm.doc.status)) {
			frm.add_custom_button(__('Share with Customer'), () => {
				frappe.call({
					method: 'instacertify.api.quotation.share_quote',
					args: { quotation: frm.doc.name },
					freeze: true,
					callback(r) {
						if (r.message) {
							frappe.msgprint({
								title: __('Quote Link'),
								message: __('Share this link with the customer:<br><a href="{0}" target="_blank">{0}</a>', [r.message]),
								indicator: 'blue'
							});
							frm.reload_doc();
						}
					}
				});
			}, __('Actions'));
		}
		if (frm.doc.docstatus === 1 && frm.doc.status === 'Accepted') {
			frm.add_custom_button(__('Start Project'), () => {
				frappe.call({
					method: 'instacertify.api.quotation.start_project',
					args: { quotation: frm.doc.name },
					freeze: true,
					callback(r) {
						if (r.message) frappe.set_route('Form', 'IC Project', r.message);
					}
				});
			}, __('Actions'));
			frm.add_custom_button(__('Save as Template'), () => {
				frappe.prompt({
					label: 'Template Name',
					fieldname: 'template_name',
					fieldtype: 'Data',
					reqd: 1
				}, (values) => {
					frappe.call({
						method: 'instacertify.api.quotation.save_as_template',
						args: { quotation: frm.doc.name, template_name: values.template_name },
						freeze: true,
						callback(r) {
							if (r.message) frappe.set_route('Form', 'IC Quotation Template', r.message);
						}
					});
				}, __('Create Quotation Template'));
			}, __('Actions'));
		}
	},
	quotation_template(frm) {
		if (!frm.doc.quotation_template) return;
		frappe.call({
			method: 'instacertify.api.quotation.apply_template',
			args: { template: frm.doc.quotation_template, quotation: frm.doc.name || null },
			callback(r) {
				if (!r.message) return;
				const d = r.message;
				['service', 'category', 'scope_of_work', 'certification_timeline', 'force_majeure', 'terms_and_conditions', 'currency']
					.forEach((k) => { if (d[k] !== undefined) frm.set_value(k, d[k]); });
				frm.clear_table('cost_lines');
				(d.cost_lines || []).forEach((row) => {
					frm.add_child('cost_lines', row);
				});
				frm.clear_table('testing_lines');
				(d.testing_lines || []).forEach((row) => {
					frm.add_child('testing_lines', row);
				});
				frm.refresh_fields();
			}
		});
	},
	service(frm) {
		if (frm.doc.service) {
			frappe.db.get_doc('IC Service', frm.doc.service).then((svc) => {
				if (svc.certification_timeline_notes && !frm.doc.certification_timeline) {
					frm.set_value('certification_timeline', svc.certification_timeline_notes);
				}
				if (svc.category) frm.set_value('category', svc.category);
			});
		}
	}
});

frappe.ui.form.on('IC Quotation Cost Line', {
	qty(frm, cdt, cdn) { recalc(frm, cdt, cdn); },
	rate(frm, cdt, cdn) { recalc(frm, cdt, cdn); },
	cost_type(frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (['Consulting', 'Lab / Testing'].includes(row.cost_type)) {
			frappe.model.set_value(cdt, cdn, 'counts_as_revenue', 1);
			frappe.model.set_value(cdt, cdn, 'payable_to', 'InstaCertify');
		} else if (row.cost_type === 'Government Fees') {
			frappe.model.set_value(cdt, cdn, 'counts_as_revenue', 0);
			frappe.model.set_value(cdt, cdn, 'payable_to', 'Government Portal');
		}
		recalc(frm, cdt, cdn);
	}
});

function recalc(frm, cdt, cdn) {
	const row = locals[cdt][cdn];
	frappe.model.set_value(cdt, cdn, 'amount', (row.qty || 0) * (row.rate || 0));
	frm.trigger('calculate_totals');
}
