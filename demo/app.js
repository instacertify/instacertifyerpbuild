const titles = {
  dashboard: "InstaCertify Dashboard",
  leads: "Leads CRM",
  quotes: "Quotations & Templates",
  projects: "Projects & Customer Records",
  testing: "Labs & Sample Tracking",
  portal: "Customer Share Portals",
  projectcard: "Customer Project Card",
  invoices: "Zoho-style Invoicing",
  flow: "End-to-End Process Flow",
};

document.querySelectorAll(".nav").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".nav").forEach((b) => b.classList.remove("active"));
    document.querySelectorAll(".view").forEach((v) => v.classList.remove("active"));
    btn.classList.add("active");
    const view = btn.dataset.view;
    document.getElementById(`view-${view}`).classList.add("active");
    document.getElementById("page-title").textContent = titles[view] || "InstaCertify";
  });
});

// Auto-tour for video walkthrough when ?tour=1
const params = new URLSearchParams(location.search);
if (params.get("tour") === "1") {
  const order = ["dashboard", "leads", "quotes", "projects", "projectcard", "invoices", "testing", "portal", "flow"];
  let i = 0;
  const tick = () => {
    const btn = document.querySelector(`.nav[data-view="${order[i]}"]`);
    if (btn) btn.click();
    i = (i + 1) % order.length;
  };
  setInterval(tick, 2800);
}
