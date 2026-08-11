// Copyright (c) 2026, InstaCertify and contributors
// For license information, please see license.txt

frappe.ui.form.on('IC Settings', {
	refresh(frm) {
		frm.add_custom_button(__('Open GST Settings'), () => {
			if (frappe.boot.user.can_read.includes('GST Settings') || frappe.model.can_read('GST Settings')) {
				frappe.set_route('Form', 'GST Settings');
			} else {
				frappe.msgprint(__(
					'GST Settings not available. Install India Compliance and follow {0}',
					[`<a href="https://docs.indiacompliance.app/docs/configuration/gst_setup" target="_blank">GST Setup docs</a>`]
				));
			}
		}, __('India Compliance'));

		frm.add_custom_button(__('Check Compliance Status'), () => {
			frappe.call({
				method: 'instacertify.api.gst_compliance.get_india_compliance_status',
				freeze: true,
				callback(r) {
					const d = r.message || {};
					const lines = [
						`<b>Installed:</b> ${d.installed ? 'Yes' : 'No'}`,
						`<b>GST Settings:</b> ${d.gst_settings_exists ? 'Found' : 'Missing'}`,
						`<b>API enabled (detected):</b> ${d.api_enabled ? 'Yes' : 'No / Unknown'}`,
						`<b>Sandbox:</b> ${d.sandbox_mode ? 'Yes' : 'No'}`,
						`<b>Validate GSTIN status:</b> ${d.validate_gstin_status ? 'Yes' : 'No'}`,
						`<b>IC fetch toggle:</b> ${d.fetch_enabled_in_ic_settings ? 'Enabled' : 'Disabled'}`,
						`<p>${frappe.utils.escape_html(d.message || '')}</p>`,
						`<p><a href="${d.docs_url}" target="_blank">GST Setup docs</a> ·
						 <a href="${d.api_docs_url}" target="_blank">API / GSP credentials</a></p>`,
					];
					frappe.msgprint({
						title: __('India Compliance Status'),
						indicator: d.installed ? 'green' : 'orange',
						message: lines.join('<br>'),
					});
				}
			});
		}, __('India Compliance'));

		frm.add_custom_button(__('Test GSTIN Fetch'), () => {
			frappe.prompt(
				{
					label: 'GSTIN',
					fieldname: 'gstin',
					fieldtype: 'Data',
					reqd: 1,
				},
				(values) => {
					frappe.call({
						method: 'instacertify.api.gst_compliance.fetch_gstin_details',
						args: { gstin: values.gstin, force_update: 1 },
						freeze: true,
						callback(r) {
							const d = r.message || {};
							frappe.msgprint({
								title: __('GSTIN Fetch Result'),
								indicator: d.valid || d.source === 'india_compliance' ? 'green' : 'orange',
								message: `
									<b>Source:</b> ${frappe.utils.escape_html(d.source || '')}<br>
									<b>GSTIN:</b> ${frappe.utils.escape_html(d.gstin || '')}<br>
									<b>Status:</b> ${frappe.utils.escape_html(d.status || '—')}<br>
									<b>Legal Name:</b> ${frappe.utils.escape_html(d.legal_name || '—')}<br>
									<b>Trade Name:</b> ${frappe.utils.escape_html(d.trade_name || '—')}<br>
									<b>State:</b> ${frappe.utils.escape_html(d.state || '—')}<br>
									<p>${frappe.utils.escape_html(d.message || '')}</p>
								`,
							});
						}
					});
				},
				__('Fetch GSTIN via India Compliance')
			);
		}, __('India Compliance'));
	}
});
