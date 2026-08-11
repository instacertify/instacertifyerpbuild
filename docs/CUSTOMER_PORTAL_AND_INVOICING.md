# Customer Project Portal & Zoho-style Invoicing

Built for **ERPNext version-16** (`https://github.com/frappe/erpnext.git` branch `version-16`).

## Quotation currency rule

- **India** customers → quote currency is always **INR**
- **Outside India** customers → quote currency is always **USD**

Set via `Customer Country` on **IC Quotation** (auto from Lead / Customer address). Currency field is read-only.

## Customer project portal

Shareable link from **IC Project → Customer → Share Customer Portal**:

`/customer-project/<token>`

Shows:
- Brand **INSTACERTIFY**
- Customer + certification name (e.g. ABC Electronics / BIS CRS)
- Progress % bar
- Documents checklist with UPLOAD for pending items
- Reports (View / Download)
- Messages from operations/sales
- **Login credentials** — revealed only when project status is **Completed**

### Shareable customer login credentials

DocType: **IC Customer Portal Account**

Can be created/shared by:
- IC Admin
- IC All Ops Manager
- IC Operations Manager
- IC Sales Person
- IC Customer Manager

Link: `/customer-credentials/<token>`

## Zoho Books–style invoicing (`IC Invoice`)

Automatic determination:
- Outside India customer → **USD** + Export zero-rated GST
- India same state → **CGST + SGST**
- India other state → **IGST**
- Exempt / SEZ / Reverse charge flags
- Place of supply
- Default HSN/SAC `9983` for consulting
- GSTIN format + checksum validation

Also includes:
- Invoice approval workflow (`Draft → Pending Approval → Approved`)
- Payment links (`/pay-invoice/<token>`)
- Partial payments + balance tracking
- Automatic reminders (daily scheduler)
- Recurring invoices
- Credit notes
- Customer invoice portal (`/invoice-portal/<token>`)
- Multi-currency (INR default, USD for exports)

## Demo / evaluation data

On desk dashboard click **Load Demo Data**, or:

```bash
bench --site <site> execute instacertify.ic_setup.seed.seed_demo_data
```

Creates ABC Electronics BIS CRS project at 65% with the document checklist from the product mock, plus INR and USD sample invoices.
