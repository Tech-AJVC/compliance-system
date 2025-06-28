# UC-SEBI-2 — Generate inVi Filing Pack

> **Category:** Regulatory Reporting  
> **Primary actor:** Compliance Officer

---

## 1. References

| Doc | Section                          |
| --- | -------------------------------- |
| PRD | §6 – "inVi Filing Pack"          |
| TRD | §21 – Filing Pack Generator      |
| UX  | inVi Filing Form + Preview modal |

### PRD Extract

> _"System must compile requisite docs (Allotment sheet, Capital Call notice, Bank statements) into a single PDF/A portfolio for submission to inVi portal."_

### TRD Extract

> _Service concatenates PDFs, applies digital signature, outputs `filing_<qtr>.pdf`\_

### UX Extract

> Form pre-filled list of docs with checkboxes; button **Generate & Download**.

---

### Use Case

#### Trigger

- "Prepare Filing" action in UI/immediately after all Lps drawdown and post unit allotment 30 days do inVi Filling

#### Behaviour

- Pre-fill XML / PDF forms with CA, CML and LP Unit Allotment
- Filter foreign investors by geography, units get total investors count
- Check DP ID from top of CML and DP from header
- Calculate Amount being reported in the current form (in Rs) by grouping LP on country and calculating sum in this quarter
- Total amount as received so far (in Rs) calculate bl Foreign Client Type LPs sum drawdown Amount Due based on notice date of drawdown in this quarter
- Fill a template for Invi with calculated details
- Record one audit-log entry for the inVi Filling Update

### Figma UI Screen Inputs

#### inVi Filing Form Interface

- **Form Title**: Pre-filled document selection interface
- **Document Checklist**: Checkboxes for required documents
  - Allotment Sheet
  - Capital Call Notice
  - Bank Statements
  - Other regulatory documents
- **Generate & Download Button**: Primary action button
- **Quarter Selection**: Dropdown for selecting filing quarter
- **Status Indicators**: Visual indicators for document completion status

#### Document Repository Integration

- **Quarterly Folders**: Document organization by quarters (Q1'25, Q2'25, etc.)
- **Category Subfolders**:
  - SEBI folder
  - RBI folder
  - IT/GST folder
  - MCA folder
- **LP-specific Folders**: Individual folders for each Limited Partner
  - Warren Buffet folder
  - Peter Lynch folder
  - Benjamin Graham folder
  - Charlie Munger folder
  - George Soros folder
- **Portfolio Company Folders**: Dedicated folders for portfolio companies
  - Yinara folder
  - Scuba folder
  - Thread Factory folder
  - Chop Finance folder
  - Trufides folder

#### Document Management Features

- **Search Functionality**: "Search documents..." placeholder text
- **Sort Options**:
  - Sort By - Limited Partners
  - Sort By - Portfolio Companies
  - Sort By - Quarters
- **Document Types**: Support for various document formats (PDF, Excel, etc.)
- **Linked Tasks**: Documents can be linked to specific compliance tasks
- **Date Tracking**: Upload date and last modified tracking for all documents

#### Document Preview and Download

- **Document Viewer**: Modal interface for document preview
  - Tax Collection at Source (TCS) Data Collection (example document)
  - Download button for document access
  - Close button for modal dismissal
- **File Format Support**: PDF, Excel, XML, and other compliance document formats

## PROCESS SECTION - INVI FILING

This process handles the generation of inVi filing documents for foreign investors by filtering and aggregating unit allotment and payment data for regulatory submission.

### Subprocess: Foreign Investor Filtering (from Unit Allotment + Client Master List)

- **Output**: Investor Name, Qty, Booking Date, Client Type Depository, DPID, Client ID, DP, Name of the country (PDF)
- **Input Source**: Unit Allotment + Client Master List
- **Input Format**: PDF
- **Transformation**: Computation
- **Input Field**: Allotted Unit, Name, Geography, Type, Depository, DP, Client ID
- **Formula**: FILTER(Name, Foreign, Investor) - Filter all data where Geography indicates foreign investor
- **DB vs PDF Analysis**: ✅ Filter from LP_DETAILS table using geography field + read unit allotment data from UNIT_ALLOTMENTS table

### Subprocess: Foreign Investment Amount Calculation (Current Quarter)

- **Output**: Amount being reported in the current form (in Rs) (PDF)
- **Input Source**: Unit Allotment + Drawdown Notice
- **Input Format**: PDF
- **Transformation**: Computation
- **Input Field**: Allotted Unit, Amount, Geography, Type
- **Formula**: FILTER(Name, Foreign, Investor) + SUM amounts for current quarter
- **DB vs PDF Analysis**: ✅ Calculate from LP_DRAWDOWNS table filtered by geography and quarter

### Subprocess: Total Foreign Investment Amount Calculation (Cumulative)

- **Output**: Total amount as received so far (in Rs) (PDF)
- **Input Source**: Unit Allotment + Drawdown Notice
- **Input Format**: PDF
- **Transformation**: Computation
- **Input Field**: Allotted Unit, Amount, Geography, Type
- **Formula**: All Foreign Client Type LPs sum drawdown Amount Due based on notice date of drawdown in this quarter
- **DB vs PDF Analysis**: ✅ Calculate cumulative sum from LP_DRAWDOWNS table for all foreign LPs

### Subprocess: Foreign Investor Count Calculation

- **Output**: Number of Foreign Investors (PDF)
- **Input Source**: Unit Allotment + Client Master List
- **Input Format**: PDF
- **Transformation**: Computation
- **Input Field**: Allotted Unit, Geography, Type
- **Formula**: FILTER(Name, Foreign, Investor) + COUNT unique investors
- **DB vs PDF Analysis**: ✅ Count distinct foreign LPs from LP_DETAILS table

### Subprocess: Depository Participant Information

- **Output**: DPID verification (PDF)
- **Input Source**: Client Master List
- **Input Format**: PDF
- **Transformation**: Computation
- **Input Field**: DPID, Geography, Type
- **Formula**: Check IN304158 number for DP value on the top
- **DB vs PDF Analysis**: ✅ Read from LP_DETAILS table depository information

### Missing Upstream Fields Analysis:

- ⚠️ **Geography/Country**: Critical for foreign investor filtering - must be captured in LP Details Registration
- ⚠️ **Client Type**: Required to identify foreign investors vs domestic
- ✅ **Unit allotment data**: Available from Unit Allotment process
- ✅ **Drawdown amounts**: Available from Drawdown Notice process
- ✅ **Depository details**: Should be available from LP Details Registration

### Downstream Usage:

- InVi Filing is a regulatory submission and doesn't feed into other processes

### DB vs PDF Optimization:

- ✅ **LP geography and type**: Read from LP_DETAILS table for filtering
- ✅ **Unit allotment quantities**: Read from UNIT_ALLOTMENTS table
- ✅ **Drawdown amounts**: Read from LP_DRAWDOWNS table
- ✅ **Depository details**: Read from LP_DETAILS table
- ⚠️ **Foreign investor identification**: Requires geography field in LP_DETAILS

### Critical Missing Fields for This Process:

1. **Geography/Country field in LP_DETAILS**: Essential for identifying foreign investors
2. **Client Type field in LP_DETAILS**: Required for investor categorization
3. **Standardized country codes**: For consistent foreign investor identification

### Foreign Investor Identification Logic:

- **Domestic Investors**: Geography = "India" or similar domestic indicators
- **Foreign Investors**: Geography = any country other than India
- **Investment Amount Aggregation**: Sum by country for current quarter and cumulative totals
- **Regulatory Compliance**: Ensure all foreign investments are properly reported

## 2. Functional Requirements

1. Select quarter → auto-select relevant documents.
2. Allow manual inclusion/exclusion.
3. Generate combined PDF/A, digitally sign (PFX provided).
4. Store & provide download.

## 3. Technical Requirements

- Use Marker conversion.
- Sign using `signxml` + DSC token.
- Endpoint `POST /invi-filing`.

DB Schema

───────────────────────────── 16. INVI_FILINGS
─────────────────────────────
• invi_id: BIGINT PK
• lp_id: INT FK→FUND_DETAILS
• filing_quarter: VARCHAR(20)
• status: VARCHAR(30) -- Prefilled/In Review/Submitted
• qty DECIMAL(18,2) DEFAULT 0, -- Qty (quantity);
• booking_date DATE, -- Booking Date
• client_type_depository VARCHAR(100), -- Client Type Depository;
• dpid VARCHAR(100), -- DPID; storing as text (can be numeric or alphanumeric)
• client_id VARCHAR(100), -- Client ID; storing as text for flexibility
• dp VARCHAR(100), -- DP; a shorthand identifier for the depository participant (CDSL, NSDL)
• name_of_country VARCHAR(100), -- Name of the country associated with the investor or filing
• current_reported_amount DECIMAL(18,2) DEFAULT 0.00, -- Amount being reported in the current form (in Rs)
• total_received_amount DECIMAL(18,2) DEFAULT 0.00, -- Total amount as received so far from LP (in Rs)
• submitted_at TIMESTAMP NULL, -- Submitted timestamp; can be NULL if not yet submitted

API Contracts

8. INVI FILINGS

Resource: /invi-filings
POST /invi-filings/generate
JSON
{
"fund_id": 12,
"filing_quarter": "FY25Q1"
}

Returns
JSON
[
{
"invi_id": 30001,
"lp_id": 109,
"filing_quarter": "FY25Q1",
"investor_name": "Blue Delta Capital",
"qty": 10000,
"booking_date": "2025-08-25",
"client_type_depository": "Foreign Portfolio Investor",
"dpid": "12345678",
"client_id": "789456123",
"dp": "NSDL",
"name_of_country": "Singapore",
"current_reported_amount": 1000000.00,
"total_received_amount": 3000000.00,
"status": "Prefilled",
"submitted_at": null
}
]

GET /invi-filings?fund_id=12&status=Prefilled
GET /invi-filings/{invi_id}
PUT /invi-filings/{invi_id}/submit
Returns 204 No Content (sets status to Submitted + timestamp).

## 4. Contradictions

| #   | Doc Inclusion            | PRD           | UX               | Action            |
| --- | ------------------------ | ------------- | ---------------- | ----------------- |
| 1   | Include Fund NAV report? | Not mentioned | Checkbox present | Confirm necessity |

## 5. Tasks

### Human

- [ ] Provide digital signature PFX file & password.

### AI

- [ ] Implement filing generator util.
- [ ] FE form & status column in drawdowns page.
- [ ] Tests on PDF/A validation.

---

_Status: draft._
