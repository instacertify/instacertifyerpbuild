# InstaCertify ERP (ERPNext v16)

Custom Frappe app for **InstaCertify** — a consulting & certification firm. Built for ERPNext **v16** with blue/orange branded dashboards, quotation templates, customer share links, project tracking, lab/sample workflows, asset register, and role-based CRM.

## What you get

- **Lead CRM** — person, company, service/testing request, company size, India state dropdown, lead source (Google, Direct Call, Lead Generated, Referral, IndiaMART, Consultant library), expected timeline, GST, remarks
- **Quotation templates** — save finalised quotes as templates; sales picks from dropdown and reuses costing
- **Costing** — consulting, lab/testing, government fees, other; payable to InstaCertify / Govt portal / Lab direct; **consulting + lab always count as revenue**
- **Certification timeline**, force majeure, T&C, **unique barcode + QR** on every quote
- **Share quote link** — customer accepts (notifies sales + admin) or requests changes with remarks
- **Start project** from accepted quote, mapped to customer
- **Customer / project records** — PDF/image deliverables, progress remarks, login credentials, commitments/incidents, quotes & invoices
- **Document library** per service — shareable checklist / TRF; customer uploads; staff download
- **Lab library** for sales — accreditation, prices, location, scope sheet, accreditation certificate
- **Sample tracking** — Received → Dispatched to Lab → Testing → Report Available → Uploaded → Share link; QR for physical sample
- **Assets** — anyone can register; auto asset code; custodian + value
- **My Profile** — salary slips, joining letter with QR, attendance / holiday calendar (via ERPNext HRMS)
- **Roles** — IC Admin, IC All Ops Manager, IC Sales Person, IC Operations Manager, IC HR
- **Dashboard** — personal greeting, pending tasks, colourful KPI cards, process diagram
- **Currency** — INR primary, multi-currency selectable

## Install on latest ERPNext v16

Use the latest ERPNext from GitHub:

```bash
# on your bench
cd frappe-bench
bench get-app --branch version-16 https://github.com/frappe/erpnext.git
bench get-app --branch version-16 https://github.com/frappe/hrms.git   # optional but recommended
bench get-app https://github.com/instacertify/instacertifyerpbuild.git
bench --site <your-site> install-app erpnext
bench --site <your-site> install-app hrms
bench --site <your-site> install-app instacertify
bench --site <your-site> migrate
bench build --app instacertify
bench --site <your-site> clear-cache
```

### Load demo data (ABC Electronics portal + invoices)

From **InstaCertify Dashboard → Load Demo Data**, or:

```bash
bench --site <site> execute instacertify.ic_setup.seed.seed_demo_data
```

Python deps (auto if listed in app requirements):

```bash
bench pip install qrcode Pillow
```

## First-time setup

1. Open **IC Settings** — confirm INR, brand colours (`#0B5FFF` / `#FF7A00`), default T&C / force majeure
2. Assign roles to users: `IC Admin`, `IC All Ops Manager`, `IC Sales Person`, `IC Operations Manager`, `IC HR`
3. Open workspace **InstaCertify** or page **ic-dashboard**
4. Seeded sample services: ISO 9001, Product Testing, Certificate Renewal

## Key user flows

### Sales quotation
1. Create **IC Lead** → convert to Customer  
2. New **IC Quotation** → pick **Quotation Template** (optional) → select **Service**  
3. Add cost lines + testing lines (lab, standard, samples, accreditation, timeline)  
4. Submit → **Share with Customer** → copy link  
5. On Accept → **Start Project** and/or **Save as Template**

### Operations / testing
1. Create **IC Test Request** from project/quote  
2. Update sample status; on **Sample Received** generate sample QR for dispatch  
3. Upload report → **Share Report with Customer**  
4. Maintain **IC Lab** library (prices, scope sheet, certificates)

### Admin
- Excel download buttons on Lead / Quotation / Project / Test Request lists  
- Full visibility across modules  

## Public portals (no login)

| URL | Use |
|-----|-----|
| `/quote/<token>` | Customer quote accept / change request |
| `/docs-upload/<token>` | Checklist file upload |
| `/trf/<token>` | Test Request Form view |
| `/report/<token>` | Shared lab report |
| `/sample/<code>` | Sample tracking |
| `/customer-project/<token>` | Customer project card (progress, docs, reports, messages, credentials) |
| `/customer-credentials/<token>` | Shareable customer login credentials |
| `/pay-invoice/<token>` | Zoho-style payment link (partial payments) |
| `/invoice-portal/<token>` | Customer invoice portal |

## Docs

- [Architecture & flow diagram](docs/ARCHITECTURE.md)
- [Roles & permissions](docs/ROLES_AND_PERMISSIONS.md)
- [Customer portal & Zoho-style invoicing](docs/CUSTOMER_PORTAL_AND_INVOICING.md)

## Brand

Desk CSS uses InstaCertify **blue** and **orange** hues with a light atmospheric gradient — operational, not bland.

## License

MIT — InstaCertify
