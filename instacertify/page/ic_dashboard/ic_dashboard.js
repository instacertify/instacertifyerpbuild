frappe.pages["ic-dashboard"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("InstaCertify Dashboard"),
		single_column: true,
	});

	$(wrapper).find(".layout-main-section").html(`
		<div class="ic-dash-wrap">
			<div class="ic-dash-hero">
				<h1 id="ic-greeting">InstaCertify</h1>
				<p>Your consulting, certification and testing command centre</p>
			</div>
			<div class="ic-card-grid" id="ic-cards"></div>
			<div class="ic-task-panel">
				<h3>${__("Pending tasks & progress")}</h3>
				<div id="ic-tasks"></div>
			</div>
			<div class="ic-flow-diagram">
				<h3 style="margin:0 0 10px;">${__("End-to-end flow")}</h3>
				<svg viewBox="0 0 960 160" xmlns="http://www.w3.org/2000/svg" aria-label="InstaCertify process flow">
					<defs>
						<linearGradient id="icg" x1="0" x2="1">
							<stop offset="0%" stop-color="#0B5FFF"/>
							<stop offset="100%" stop-color="#FF7A00"/>
						</linearGradient>
					</defs>
					${["Lead CRM", "Quote + Template", "Customer Accept", "Project", "Docs / TRF", "Lab & Sample", "Report / Invoice"]
						.map((label, i) => {
							const x = 20 + i * 135;
							return `
							<rect x="${x}" y="40" width="120" height="56" rx="12" fill="url(#icg)" opacity="${0.85 - i * 0.05}"/>
							<text x="${x + 60}" y="74" text-anchor="middle" fill="#fff" font-size="12" font-family="Segoe UI, sans-serif" font-weight="700">${label}</text>
							${i < 6 ? `<path d="M${x + 122} 68 H${x + 133}" stroke="#FF7A00" stroke-width="3" marker-end="url(#arrow)"/>` : ""}
						`;
						})
						.join("")}
					<defs>
						<marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
							<path d="M0,0 L6,3 L0,6 Z" fill="#FF7A00"/>
						</marker>
					</defs>
					<text x="480" y="140" text-anchor="middle" fill="#5b677a" font-size="12" font-family="Segoe UI, sans-serif">
						Revenue counted from Consulting + Lab charges · Govt fees tracked separately
					</text>
				</svg>
			</div>
		</div>
	`);

	frappe.call({
		method: "instacertify.api.dashboard.get_home_dashboard",
		callback(r) {
			if (!r.message) return;
			const data = r.message;
			$("#ic-greeting").text(data.greeting);
			const $cards = $("#ic-cards").empty();
			(data.cards || []).forEach((c) => {
				const $card = $(`
					<div class="ic-stat-card" style="border-top-color:${c.color}">
						<div class="label">${frappe.utils.escape_html(c.label)}</div>
						<div class="value">${c.value}</div>
					</div>
				`);
				$card.on("click", () => {
					const parts = c.route.replace("/app/", "").split("/").filter(Boolean);
					frappe.set_route(...parts);
				});
				$cards.append($card);
			});
			const $tasks = $("#ic-tasks").empty();
			if (!(data.tasks || []).length) {
				$tasks.append(`<div style="color:#5b677a">${__("You're all caught up.")}</div>`);
			}
			(data.tasks || []).forEach((t) => {
				const $row = $(`
					<div class="ic-task-row">
						<div>
							<span class="ic-task-type" style="background:${t.color}22;color:${t.color}">${frappe.utils.escape_html(t.type)}</span>
							<div style="font-weight:700">${frappe.utils.escape_html(t.title)}</div>
							<div style="color:#5b677a;font-size:12px">${frappe.utils.escape_html(t.subtitle || "")}</div>
						</div>
						<div style="font-weight:600;color:${t.color}">${frappe.utils.escape_html(t.status)}</div>
					</div>
				`);
				$row.on("click", () => {
					const parts = t.route.replace("/app/", "").split("/").filter(Boolean);
					frappe.set_route(...parts);
				});
				$tasks.append($row);
			});
		},
	});
};
