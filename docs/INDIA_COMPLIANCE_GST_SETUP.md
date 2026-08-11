# India Compliance — GST Setup & Data Fetching

InstaCertify integrates with **[India Compliance](https://github.com/resilient-tech/india-compliance)** for live GSTIN validation and GST data fetching.

Official guide: [Configuring GST in ERPNext](https://docs.indiacompliance.app/docs/configuration/gst_setup)  
API / GSP credentials: [Setting Up API](https://docs.indiacompliance.app/docs/ewaybill-and-einvoice/gst_settings)

## Install

```bash
bench get-app --branch version-16 https://github.com/resilient-tech/india-compliance.git
bench --site <site> install-app india_compliance
bench --site <site> migrate
```

## Configure (once)

1. Open **IC Settings → India Compliance · GST Setup**
2. Enable **Enable India Compliance GST Data Fetching**
3. Click **Open GST Settings** (or search Desk → GST Settings)
4. In GST Settings:
   - Enable API features
   - Add **GSP credentials** (Credentials tab)
   - Configure **GST Accounts** (Input / Output / Reverse Charge) per company — CGST / SGST / IGST / Cess
   - Turn on **Validate GSTIN Status** if you want live checks
5. Set Company GSTIN and ensure Customers / Addresses have GSTIN + GST State
6. Use **Check Compliance Status** and **Test GSTIN Fetch** buttons on IC Settings

## Where InstaCertify fetches GSTIN

| Form | Action |
|------|--------|
| **IC Lead** | GST → Fetch GSTIN Details (auto if toggle on) |
| **IC Quotation** | GST → Fetch GSTIN Details for Customer GSTIN |
| **IC Invoice** | GST → Fetch GSTIN Details for Customer GSTIN |
| **IC Settings** | Test GSTIN Fetch |

Fetched fields (when API returns data): status, legal/trade name, state, registration category — applied to state / billing state / company name where available.

## Notes

- India Compliance is **optional** but required for live API fetch. Without it, InstaCertify still runs local GSTIN format/checksum validation.
- Sandbox vs production is controlled in **GST Settings**, not only IC Settings.
- Sign up for an India Compliance Account if your GSP/API plan requires it (see India Compliance docs).
