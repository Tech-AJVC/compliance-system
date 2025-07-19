# UC-PORTFOLIO-1 — Portfolio Update

> **Category:** Portfolio Companies  
> **Primary actor:** Investment Analyst  
> **Secondary actors:** Fund Manager

---

## 1. References

| Doc | Section                                          |
| --- | ------------------------------------------------ |
| PRD | §7 – "Portfolio Database"                        |
| TRD | §25 – Portfolio Ingestor Service                 |
| UX  | Portfolio Companies table, Onboard Company modal |

### PRD Extract

> "_System shall store current valuation, funding rounds, key dates and documents per portfolio company…_"

### TRD Extract

> _Service consumes CSV / Xero export to update valuations nightly …_

### UX Extract

> Onboard Company form fields: Startup Name, Registered Name, PAN, ISIN, Funding, Date of Funding, Latest Valuation.

---

### Use Case

#### Trigger

- UI update Portfolio screen

#### Behaviour

- Upload SHA document via multipart form data for automatic extraction
- Extract company information from SHA: Company Name, Founder Names (1-4), Address, Date of Signing SHA, Funding TAT
- Accept structured UI input for three categories:
  - Company data: Startup Name, Sector, PAN, ISIN, Product Description
  - Founders data: Founder Emails (1-4), Founder Roles (1-4) 
  - Investment data: Fund ID, Funding Amount, Term Sheet Date, Funding Date, EC Date, Latest Valuation, Valuation Date
- Create company, founders, and investment records atomically in single transaction
- Return created entity IDs and extracted data for confirmation

### Figma UI Screen Inputs

#### Portfolio Companies List View

- **Onboard Company Button**: Primary action button
- **Search Field**: General search functionality
- **Portfolio Table Columns**:
  - Name (company name)
  - Funding (₹ format, e.g., 1,50,000)
  - Date of Funding (date format)
  - Latest Valuation (₹ format)
- **Three-dot Menu**: Action menu for each portfolio company (Edit/Delete options)

#### Onboard Company Form

- **Form Title**: "Onboard Company"
- **Subtitle**: "Add all relevant company details below"
- **SHA Upload**: File upload component for SHA document (automatic extraction)

##### Required Fields (UI Input)

**Company Information:**
- **Startup Name** (required): Text input field
- **Sector** (required): Text input field
- **PAN** (required): Text input field with PAN format validation
- **ISIN** (required): Text input field with ISIN format validation
- **Product Description** (optional): Text area field

**Investment Information:**
- **Funding** (required): Currency input field with ₹ symbol
- **Date of Funding** (required): Date picker field
- **Date of Signing Term Sheet** (required): Date picker field
- **Date of Signing EC** (required): Date picker field
- **Latest Valuation** (required): Currency input field with ₹ symbol
- **Date of Valuation** (required): Date picker field

**Founder Information (up to 4 founders):**
- **Founder Email** (required): Email input field
- **Founder Role** (required): Text input field

##### Auto-Extracted Fields (from SHA Document)
- **Company Name**: Extracted automatically from SHA
- **Founder Names (1-4)**: Extracted automatically from SHA
- **Address**: Extracted automatically from SHA
- **Date of Signing SHA**: Extracted automatically from SHA
- **Funding TAT**: Extracted automatically from SHA

##### Action Buttons

- **Onboard Button**: Primary action button (dark background)
- **Cancel Button**: Secondary action button

#### Portfolio Document Organization

- **Document Repository Integration**: Portfolio companies organized in dedicated folders
- **Company-specific Folders**: Each portfolio company (Yinara, Scuba, Thread Factory, Chop Finance, Trufides) has dedicated document storage
- **Document Categories**: SHA, Term Sheets, EC documents, Valuation reports

#### Portfolio Companies Data Display

- **Sample Company**: Yinara
  - Funding: 1,50,000
  - Date of Funding: 19th August 2024
  - Latest Valuation: 1,50,000
- **Consistent Currency Format**: All monetary values displayed in ₹ format without decimals

## 2. Functional Requirements

1. **Combined Portfolio Onboard** via SHA upload + structured UI form data.
2. **Individual Entity Management** via separate CRUD APIs.
3. **SHA Document Processing** with automatic field extraction.
4. **Atomic Transaction** handling for company, founders, and investment creation.
5. **Search & Filter** for existing portfolio companies.

## 3. Technical Requirements

- Tables `portfolio_companies`, `portfolio_founders`, `portfolio_investments` + document tracking.
- FastAPI route `/portfolio-companies/onboard` for combined operations.
- Individual management routes `/portfolio-companies`, `/portfolio-founders`, `/portfolio-investments`.
- SHA document processing service for field extraction.
- Multipart form data handling for file upload + JSON data.
- Transaction management for atomic operations.

## 4. Database Schema

───────────────────────────── 
PORTFOLIO_INVESTMENTS  
 ─────────────────────────────
• investment_id: BIGINT PRIMARY KEY
• company_id: INT FK→PORTFOLIO_COMPANIES
• fund_id: INT FK→FUND_DETAILS -- enables joins to fund
• amount_invested: DECIMAL(18,2) -- 15000000.00 (₹1.5 Cr)
• termsheet_sign_date: DATE -- 25 Sep 2024
• sha_sign_date: DATE -- 21 Nov 2024
• funding_date: DATE -- 28 Nov 2024
• funding_tat_days: INT -- 64
• latest_valuation: DECIMAL(18,2) NULL -- 15000000.00
• valuation_date: DATE NULL -- 28 Nov 2024
• ec_sign_date: DATE NULL -- 21 Nov 2024
• created_at: TIMESTAMPTZ DEFAULT now()
• updated_at: TIMESTAMPTZ DEFAULT now()

─────────────────────────────
PORTFOLIO_COMPANIES
─────────────────────────────
• company_id: INT PRIMARY KEY
• startup_brand: VARCHAR(255) -- "Yinara"
• company_name: VARCHAR(255) -- "NuYug Retail Private Limited"
• sector: VARCHAR(100) -- Consumer
• product_description: TEXT -- jewellery tagline
• registered_address: TEXT
• pan: VARCHAR(20) NULL
• isin: VARCHAR(20) NULL
• created_at: TIMESTAMPTZ DEFAULT now()
• updated_at: TIMESTAMPTZ DEFAULT now()
• fund_id: INT FK→FUND_DETAILS -- enables joins to fund



─────────────────────────────
PORTFOLIO_FOUNDERS
 ─────────────────────────────
• founder_id: INT PRIMARY KEY
• company_id: INT FK→PORTFOLIO_COMPANIES
• founder_name: VARCHAR(255) -- "Founder 1", "Founder 2", etc.
• founder_email: VARCHAR(255) -- Email 1, Email 2, etc.
• founder_role: VARCHAR(255) -- Founder 1,2,3,4 Roles
• created_at: TIMESTAMPTZ DEFAULT now()
• updated_at: TIMESTAMPTZ DEFAULT now()

─────────────────────────────
PORTFOLIO_DOCUMENTS
─────────────────────────────
• portfolio_document_id: INT PRIMARY KEY
• company_id: INT FK→PORTFOLIO_COMPANIES
• document_id: INT FK→DOCUMENTS
• document_type: VARCHAR(50) -- SHA, Term_Sheet, EC, Valuation_Report, etc.
• doc_link: VARCHAR(255) -- Document link/URL
• created_at: TIMESTAMPTZ DEFAULT now()

### Indexes
• PORTFOLIO_INVESTMENTS: (company_id, fund_id), (funding_date)
• PORTFOLIO_FOUNDERS: (company_id), (founder_email) UNIQUE
• PORTFOLIO_COMPANIES: (startup_brand) UNIQUE, (company_name) UNIQUE

### Foreign-key / JOIN relationships
• FUND_DETAILS.fund_id ←→ PORTFOLIO_INVESTMENTS.fund_id
• PORTFOLIO_COMPANIES.company_id ←→ PORTFOLIO_INVESTMENTS.company_id
• PORTFOLIO_COMPANIES.company_id ←→ PORTFOLIO_FOUNDERS.company_id

## 5. API Contracts

### 5.1 Portfolio Onboard (Combined)
Resource: /portfolio-companies/onboard
POST /portfolio-companies/onboard
Content-Type: multipart/form-data

Form Data:
- sha_document: (file) SHA PDF document for extraction
- company_data: (JSON string) Company information from UI
- founders_data: (JSON string) Founder information from UI  
- investment_data: (JSON string) Investment information from UI

company_data JSON:
{
"startup_brand": "Yinara",
"sector": "Consumer",
"pan": "AAACY1234D",
  "isin": "INE000123456",
  "product_description": "Luxury jewellery brand"
}

founders_data JSON:
{
  "founders": [
    {
      "founder_email": "john@yinara.com",
      "founder_role": "CEO"
    },
    {
      "founder_email": "jane@yinara.com", 
      "founder_role": "CTO"
    }
  ]
}

investment_data JSON:
{
  "fund_id": 12,
  "amount_invested": 15000000.00,
  "termsheet_sign_date": "2024-09-25",
  "funding_date": "2024-11-28", 
  "ec_sign_date": "2024-10-03",
  "latest_valuation": 18000000.00,
  "valuation_date": "2025-03-31"
}

SHA Document Extraction (Automatic):
- company_name: Extracted from SHA document
- founder_name: Extracted founder names (1-4) from SHA document
- registered_address: Extracted from SHA document  
- sha_sign_date: Extracted from SHA document
- funding_tat_days: Extracted from SHA document

Returns 201
{
  "company_id": 55,
  "investment_id": 901,
  "founder_ids": [101, 102],
  "extracted_data": {
    "company_name": "NuYug Retail Private Limited",
    "founders_extracted": ["John Doe", "Jane Smith"],
    "registered_address": "B1/123 Saket, Delhi",
    "sha_sign_date": "2024-11-21",
    "funding_tat_days": 64
  }
}

### 5.2 Portfolio Companies (Individual Management)
Resource: /portfolio-companies
GET /portfolio-companies?sector=Consumer
GET /portfolio-companies/{company_id}
PUT /portfolio-companies/{company_id}
DELETE /portfolio-companies/{company_id}
GET /portfolio-companies/search?query=yinara

Company Object:
{
"company_id": 55,
"startup_brand": "Yinara",
  "company_name": "NuYug Retail Pvt Ltd",
"sector": "Consumer",
  "product_description": "Luxury jewellery brand",
"registered_address": "B1/123 Saket, Delhi",
"pan": "AAACY1234D",
"isin": "INE000123456",
"created_at": "2025-05-07T08:15:22Z",
"updated_at": "2025-05-07T08:15:22Z"
}

### 5.3 Portfolio Founders (Individual Management)
Resource: /portfolio-founders
GET /portfolio-companies/{company_id}/founders
PUT /founders/{founder_id}
DELETE /founders/{founder_id}

Founder Object:
{
  "founder_id": 101,
"company_id": 55,
  "founder_name": "John Doe",
  "founder_email": "john@yinara.com",
  "founder_role": "CEO",
  "created_at": "2025-05-07T08:20:15Z",
  "updated_at": "2025-05-07T08:20:15Z"
}

### 5.4 Portfolio Investments (Individual Management)
Resource: /portfolio-investments
GET /portfolio-investments?fund_id=12
GET /portfolio-investments/{investment_id}
PUT /portfolio-investments/{investment_id}
DELETE /portfolio-investments/{investment_id}

Investment Object:
{
"investment_id": 901,
"company_id": 55,
"fund_id": 12,
"amount_invested": 15000000.00,
"termsheet_sign_date": "2024-09-25",
"sha_sign_date": "2024-11-21",
"funding_date": "2024-11-28",
"funding_tat_days": 64,
"latest_valuation": 18000000.00,
"valuation_date": "2025-03-31",
  "ec_sign_date": "2024-10-03",
"created_at": "2025-05-07T10:02:11Z",
"updated_at": "2025-05-07T10:02:11Z"
  "fund_id": "12345"
}

### 5.5 Portfolio Document Management

Resource: /portfolio-companies/{company_id}/documents

POST /portfolio-companies/{company_id}/documents
JSON
{
"document_id": 250,
"document_type": "SHA",
}

Returns 201
JSON
{
"portfolio_document_id": 350
}

GET /portfolio-companies/{company_id}/documents
Returns array of portfolio company documents
JSON
[{
"portfolio_document_id": 350,
"document_id": 250,
"document_type": "SHA",
"document_name": "Yinara_SHA_2024.pdf",
"file_path": "https://drive.google.com/file/d/xyz",
"uploaded_at": "2025-05-08T09:14:11Z",
"doc_link": ""
}]

DELETE /portfolio-companies/{company_id}/documents/{portfolio_document_id}

## 6. Process Flow - Portfolio Onboard Combined

### Input Sources & Field Mapping

**SHA Document Extraction (Automatic)**:
- **Company Name**: Legal entity name from SHA document
- **Founder Names (1-4)**: Individual founder names from SHA document
- **Registered Address**: Company address from SHA document
- **Date of Signing SHA**: SHA execution date from document
- **Funding TAT**: Turnaround time calculation from SHA document

**UI Input Categories**:

**Company Information**:
- **Startup Brand**: Brand/startup name
- **Sector**: Business sector classification
- **PAN**: Permanent Account Number
- **ISIN**: International Securities Identification Number
- **Product Description**: Business description

**Founders Information**:
- **Founder Emails (1-4)**: Contact emails for each founder
- **Founder Roles (1-4)**: Position/role for each founder

**Investment Information**:
- **Fund ID**: Reference to funding source
- **Amount Invested**: Investment amount in ₹
- **Term Sheet Sign Date**: Date of term sheet execution
- **Funding Date**: Date of actual funding
- **EC Sign Date**: Employment contract signing date
- **Latest Valuation**: Current company valuation
- **Valuation Date**: Date of valuation assessment

### Output
- Created company record with extracted and UI data
- Created founder records (matching extracted names with UI emails/roles)
- Created investment record with all investment details
- Atomic transaction ensuring data consistency

## 7. Implementation Notes

### Data Validation
- SHA extraction results should be validated before database insertion
- UI data and extracted data should be cross-validated for consistency
- Founder count from SHA should match founder emails/roles provided in UI

### Error Handling
- If SHA extraction fails, return clear error message with file format requirements
- If any database operation fails, rollback entire transaction
- Provide detailed field-level validation errors for UI inputs

### Performance Considerations
- SHA processing should be asynchronous for large documents
- Consider caching extracted data for retry scenarios
- Database operations should be optimized for batch inserts

---

_Status: Updated for combined onboard API approach._