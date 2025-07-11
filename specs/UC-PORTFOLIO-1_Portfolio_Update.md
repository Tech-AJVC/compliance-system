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

- Upload SHA populate fields
- Take Email, PAN, ISIN, Date of Signing Termsheet, Date of Signing SHA, Date of Funding Company, Date of Signing EC, Latest Valuation, Date of Valuation from UI
- Update Portfolio DB

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

##### Required Fields

- **Startup Name** (required): Text input field
- **Registered Name** (required): Text input field
- **Correspondence Email** (required): Email input field
- **PAN** (required): Text input field with PAN format validation
- **ISIN** (required): Text input field with ISIN format validation
- **Funding** (required): Currency input field with ₹ symbol
- **Date of Funding** (required): Date picker field
- **Date of Signing Term Sheet** (required): Date picker field
- **Date of Signing EC** (required): Date picker field
- **Latest Valuation** (required): Currency input field with ₹ symbol
- **Date of Valuation** (required): Date picker field

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

1. **Onboard Company** via form.
2. **Bulk Ingest** via CSV.
3. **Edit & Historical Valuation tracking**.
4. **Search & Filter**.

## 3. Technical Requirements

- Table `portfolio_company` + `company_valuation` history.
- FastAPI routes `/portfolio-companies`.
- Ingestor cron job parses CSV from S3.

DB Schema

───────────────────────────── PORTFOLIO_INVESTMENTS  
 ─────────────────────────────
• investment_id: BIGINT PRIMARY KEY
• company_id: INT FK→PORTFOLIO_COMPANIES
• fund_id: INT FK→FUND_DETAILS -- enables joins to fund
• amount_invested: DECIMAL(18,2) -- 15000000.00 (₹1.5 Cr)
• termsheet_sign_date: DATE -- 25 Sep 2024
• sha_shared_date: DATE -- 3 Oct 2024
• sha_sign_date: DATE -- 21 Nov 2024
• funding_date: DATE -- 28 Nov 2024
• funding_tat_days: INT -- 64
• sha_status: VARCHAR(20) -- Signed / Pending
• funding_status: VARCHAR(20) -- Done / Pending
• latest_valuation: DECIMAL(18,2) NULL -- 15000000.00
• valuation_date: DATE NULL -- 28 Nov 2024
• ec_date: DATE NULL -- 3 Oct 2024
• ec_sign_date: DATE NULL -- 21 Nov 2024
• ec_documentation_status: VARCHAR(20) NULL -- Signed / Pending
• created_at: TIMESTAMPTZ DEFAULT now()
• updated_at: TIMESTAMPTZ DEFAULT now()

─────────────────────────────
PORTFOLIO_COMPANIES
─────────────────────────────
• company_id: INT PRIMARY KEY
• startup_brand: VARCHAR(255) -- "Yinara"
• legal_entity_name: VARCHAR(255) -- "NuYug Retail Private Limited"
• sector: VARCHAR(100) -- Consumer
• product_description: TEXT -- jewellery tagline
• registered_address: TEXT
• pan: VARCHAR(20) NULL
• isin: VARCHAR(20) NULL
• correspondence_email: VARCHAR(255)
• created_at: TIMESTAMPTZ DEFAULT now()
• updated_at: TIMESTAMPTZ DEFAULT now()

───────────────────────────── 19. PORTFOLIO_INVESTMENTS  
 ─────────────────────────────
• investment_id: BIGINT PRIMARY KEY
• company_id: INT FK→PORTFOLIO_COMPANIES
• fund_id: INT FK→FUND_DETAILS -- enables joins to fund
• amount_invested: DECIMAL(18,2) -- 15000000.00 (₹1.5 Cr)
• termsheet_sign_date: DATE -- 25 Sep 2024
• sha_shared_date: DATE -- 3 Oct 2024
• sha_sign_date: DATE -- 21 Nov 2024
• funding_date: DATE -- 28 Nov 2024
• funding_tat_days: INT -- 64
• sha_status: VARCHAR(20) -- Signed / Pending
• funding_status: VARCHAR(20) -- Done / Pending
• latest_valuation: DECIMAL(18,2) NULL -- 15000000.00
• valuation_date: DATE NULL -- 28 Nov 2024
• ec_date: DATE NULL -- 3 Oct 2024
• ec_sign_date: DATE NULL -- 21 Nov 2024
• ec_documentation_status: VARCHAR(20) NULL -- Signed / Pending
• created_at: TIMESTAMPTZ DEFAULT now()
• updated_at: TIMESTAMPTZ DEFAULT now()

Indexes
• (company_id, fund_id)
• (funding_date)

─────────────────────────────
Foreign-key / JOIN relationships
─────────────────────────────
• FUND_DETAILS.fund_id ←→ PORTFOLIO_INVESTMENTS.fund_id
• PORTFOLIO_COMPANIES.company_id ←→ PORTFOLIO_INVESTMENTS.company_id
• PORTFOLIO_COMPANIES.company_id ←→ PORTFOLIO_FOUNDERS.company_id

API's

9. PORTFOLIO

9.1 Companies
Resource: /portfolio-companies
POST /portfolio-companies
JSON
{
"startup_brand": "Yinara",
"legal_entity_name": "NuYug Retail Pvt Ltd",
"sector": "Consumer",
"email": "team@yinara.com",
"address": "B1/123 Saket, Delhi",
"pan": "AAACY1234D",
"isin": "INE000123456"
}

Returns 201
JSON
{
"company_id": 55
}

GET /portfolio-companies?sector=Consumer
GET /portfolio-companies/{company_id}
PUT /portfolio-companies/{company_id}
DELETE /portfolio-companies/{company_id}
GET /portfolio-companies/search?query=yinara
Returns
JSON
[{
"company_id": 55,
"startup_brand": "Yinara"
}]

POST /portfolio-companies/{company_id}/upload-sha (File Upload)
Request: multipart/form-data { file:<sha.pdf> }
Returns 204 No Content.
Company Object
JSON
{
"company_id": 55,
"startup_brand": "Yinara",
"legal_entity_name": "NuYug Retail Pvt Ltd",
"sector": "Consumer",
"product_description": null,
"registered_address": "B1/123 Saket, Delhi",
"pan": "AAACY1234D",
"isin": "INE000123456",
"created_at": "2025-05-07T08:15:22Z",
"updated_at": "2025-05-07T08:15:22Z"
}

9.2 Founders
Resource: /portfolio-founders
Standard CRUD operations (company_id, name, email). No file uploads.
9.3 Investments
Resource: /portfolio-investments
POST /portfolio-investments
JSON
{
"company_id": 55,
"fund_id": 12,
"amount_invested": 15000000.00,
"termsheet_sign_date": "2024-09-25",
"sha_sign_date": "2024-11-21",
"funding_date": "2024-11-28",
"latest_valuation": 18000000.00,
"valuation_date": "2025-03-31",
"ec_date": "2024-10-03",
"sha_status": "Signed",
"funding_status": "Done"
}

Returns 201
JSON
{
"investment_id": 901
}

GET /portfolio-investments?fund_id=12&funding_status=Done
GET /portfolio-investments/{investment_id}
PUT /portfolio-investments/{investment_id}
DELETE /portfolio-investments/{investment_id}
Investment Object
JSON
{
"investment_id": 901,
"company_id": 55,
"fund_id": 12,
"amount_invested": 15000000.00,
"termsheet_sign_date": "2024-09-25",
"sha_shared_date": "2024-10-03",
"sha_sign_date": "2024-11-21",
"funding_date": "2024-11-28",
"funding_tat_days": 64,
"sha_status": "Signed",
"funding_status": "Done",
"latest_valuation": 18000000.00,
"valuation_date": "2025-03-31",
"ec_date": "2024-10-03",
"ec_sign_date": "2024-11-21",
"ec_documentation_status": "Signed",
"created_at": "2025-05-07T10:02:11Z",
"updated_at": "2025-05-07T10:02:11Z"
}

Indexes
• (startup_brand) UNIQUE
• (legal_entity_name) UNIQUE

### PORTFOLIO_COMPANIES Updates

```sql
ALTER TABLE PORTFOLIO_COMPANIES ADD COLUMN correspondence_email VARCHAR(255);
```

### PORTFOLIO_DOCUMENTS (Missing Table)

```sql
CREATE TABLE PORTFOLIO_DOCUMENTS (
    portfolio_document_id INT PRIMARY KEY,
    company_id INT REFERENCES PORTFOLIO_COMPANIES(company_id),
    document_id INT REFERENCES DOCUMENTS(document_id),
    document_type VARCHAR(50), -- SHA, Term_Sheet, EC, Valuation_Report, etc.
    created_at TIMESTAMPTZ DEFAULT now()
);
```

## PROCESS SECTION - PORTFOLIO DATABASE CREATION

This process handles the registration and onboarding of portfolio companies by extracting information from various documents and combining it with UI inputs.

### Subprocess: Company Information (from SHA)

- **Output**: Company, Founder 1, Founder 2, Founder 3, Founder 4, Address, Date of Signing SHA (Excel)
- **Input Source**: SHA
- **Input Format**: PDF
- **Transformation**: Direct
- **Input Field**: Company, Founder 1, Founder 2, Founder 3, Founder 4, Address, Date of Signing
- **Formula**: N/A
- **DB vs PDF Analysis**: ⚠️ After initial extraction, these fields should be stored in PORTFOLIO_COMPANIES and PORTFOLIO_FOUNDERS tables

### Subprocess: Company Basic Information (UI Input)

- **Output**: Email, Sector, PAN, ISIN (Excel)
- **Input Source**: UI for Portfolio
- **Input Format**: Form Field
- **Transformation**: Direct
- **Input Field**: Form Field inputs
- **Formula**: N/A
- **DB vs PDF Analysis**: ✅ Direct UI input stored in PORTFOLIO_COMPANIES table

### Subprocess: Investment Information (from UI)

- **Output**: Funding (Excel)
- **Input Source**: UI for Portfolio
- **Input Format**: PDF
- **Transformation**: Direct
- **Input Field**: Funding Amount
- **Formula**: N/A
- **DB vs PDF Analysis**: ✅ Store in PORTFOLIO_INVESTMENTS table

### Subprocess: Term Sheet Information (from UI)

- **Output**: Date of Signing Termsheet (Excel)
- **Input Source**: UI for Portfolio
- **Input Format**: PDF
- **Transformation**: Direct
- **Input Field**: Date of Signing
- **Formula**: N/A
- **DB vs PDF Analysis**: ✅ Store in PORTFOLIO_INVESTMENTS table

### Subprocess: Funding Transaction Information (UI)

- **Output**: Date of Funding Company (Excel)
- **Input Source**: UI for Portfolio
- **Input Format**: PDF
- **Transformation**: Direct
- **Input Field**: Transaction Date
- **Formula**: N/A
- **DB vs PDF Analysis**: ✅ Use UI

### Subprocess: Employment Contract Information (from UI)

- **Output**: Date of Signing EC (Excel)
- **Input Source**: UI for Portfolio
- **Input Format**: PDF
- **Transformation**: Direct
- **Input Field**: Date of Signing
- **Formula**: N/A
- **DB vs PDF Analysis**: ✅ Store in PORTFOLIO_INVESTMENTS table

### Subprocess: Valuation Information (from UI)

- **Output**: Latest Valuation, Date of Valuation (Excel)
- **Input Source**: UI for Portfolio
- **Input Format**: PDF
- **Transformation**: Direct
- **Input Field**: Valuation Amount, Valuation Date
- **Formula**: N/A
- **DB vs PDF Analysis**: ✅ Store in PORTFOLIO_INVESTMENTS table

### Missing Upstream Fields Analysis:

- ✅ No upstream dependencies - Portfolio registration is independent
- ✅ All required fields can be captured through document extraction + UI inputs

### Downstream Usage:

- Portfolio Details are used by:
  - SEBI Activity Report (portfolio investment information, valuations)
  - Investment tracking and reporting
  - Fund performance calculations

### DB vs PDF Optimization:

- ✅ **Company basic info**: Store in PORTFOLIO_COMPANIES table for reuse
- ✅ **Founder information**: Store in PORTFOLIO_FOUNDERS table
- ✅ **Investment details**: Store in PORTFOLIO_INVESTMENTS table
- ⚠️ **Document-based dates**: Extract once and store in DB tables
- ⚠️ **Account statement processing**: Similar to payment reconciliation, extract and store

### Document Processing Priority:

1. **SHA (Shareholders Agreement)**: Company details, founders, address

### Portfolio Database Structure:

- **PORTFOLIO_COMPANIES**: Core company information
- **PORTFOLIO_FOUNDERS**: Founder details linked to companies
- **PORTFOLIO_INVESTMENTS**: Investment transactions and valuations
- **PORTFOLIO_DOCUMENTS**: Document management for each company

## 4. Contradictions

| # | Valuation Currency | PRD fixed to INR | UX dropdown multi-currency | Decide support multi-currency? |

## 5. Tasks

### Human

- [ ] Confirm currency design.

### AI

- [ ] DB migrations.
- [ ] Implement ingest cron.
- [ ] FE table & form.
- [ ] Tests.

---

_Status: draft._

## MISSING API ENDPOINTS

### PORTFOLIO DOCUMENT MANAGEMENT (Critical Missing)

Resource: /portfolio-companies/{company_id}/documents
GET /portfolio-companies/{company_id}/documents
Returns array of portfolio company documents
JSON
[{
"portfolio_document_id": 350,
"document_id": 250,
"document_type": "SHA",
"document_name": "Yinara_SHA_2024.pdf",
"file_path": "https://drive.google.com/file/d/xyz",
"uploaded_at": "2025-05-08T09:14:11Z"
}]

DELETE /portfolio-companies/{company_id}/documents/{portfolio_document_id}

### PORTFOLIO COMPANY SEARCH AND FILTERING (Missing) (VERIFY WHAT ALL SEARCH FIELDS NEEDED)

Resource: /portfolio-companies/search
GET /portfolio-companies/search?query=yinara&sector=Consumer&funding_status=Done
Returns filtered portfolio results
JSON
[{
"company_id": 55,
"startup_brand": "Yinara",
"legal_entity_name": "NuYug Retail Pvt Ltd",
"correspondence_email": "team@yinara.com",
"sector": "Consumer",
"latest_investment": {
"amount_invested": 1500000.00,
"funding_date": "2024-08-19",
"latest_valuation": 1500000.00
}
}]

# WORKPLAN - PORTFOLIO UPDATE IMPLEMENTATION

## Overview

This workplan details the implementation of Portfolio Update functionality to manage portfolio companies, investments, and related documents for fund management and regulatory reporting.

## Phase 1: Database Schema Implementation

### 1.1 Create Portfolio Companies Model (HIGH PRIORITY)

**File**: `backend/app/models/portfolio_company.py` (new file)
**Dependencies**: None
**Estimated Time**: 2 days

**Tasks**:

- [ ] Create `PortfolioCompany` SQLAlchemy model
- [ ] Add fields: company_id, startup_brand, legal_entity_name, correspondence_email, sector, pan, isin, address, date_of_incorporation, status
- [ ] Create proper field validations and constraints
- [ ] Add unique constraints for startup_brand and legal_entity_name
- [ ] Create Pydantic schemas in `backend/app/schemas/portfolio.py`

### 1.2 Create Portfolio Founders Model (HIGH PRIORITY)

**File**: `backend/app/models/portfolio_founder.py` (new file)
**Dependencies**: Portfolio Company model
**Estimated Time**: 1 day

**Tasks**:

- [ ] Create `PortfolioFounder` SQLAlchemy model
- [ ] Add fields: founder_id, company_id, founder_name, founder_email, founder_phone, designation, equity_percentage
- [ ] Create relationships to PortfolioCompany model
- [ ] Add proper field validations
- [ ] Create Pydantic schemas

### 1.3 Create Portfolio Investments Model (HIGH PRIORITY)

**File**: `backend/app/models/portfolio_investment.py` (new file)
**Dependencies**: Portfolio Company, Fund models
**Estimated Time**: 2 days

**Tasks**:

- [ ] Create `PortfolioInvestment` SQLAlchemy model
- [ ] Add fields: investment_id, company_id, fund_id, investment_type, amount_invested, investment_date, valuation, valuation_date, security_type, shares_acquired, share_price
- [ ] Create relationships to PortfolioCompany and Fund models
- [ ] Add investment status tracking
- [ ] Create Pydantic schemas

### 1.4 Create Portfolio Documents Model (HIGH PRIORITY)

**File**: `backend/app/models/portfolio_document.py` (new file)
**Dependencies**: Portfolio Company, Document models
**Estimated Time**: 1 day

**Tasks**:

- [ ] Create `PortfolioDocument` SQLAlchemy model
- [ ] Add fields: portfolio_document_id, company_id, document_id, document_type, created_at
- [ ] Create relationships to PortfolioCompany and Document models
- [ ] Add document type enum (SHA, Term_Sheet, SSA, EC, Valuation_Report, etc.)
- [ ] Create Pydantic schemas

### 1.5 Database Migrations (HIGH PRIORITY)

**File**: `backend/alembic/versions/xxx_create_portfolio_tables.py`
**Dependencies**: All portfolio models
**Estimated Time**: 1 day

**Tasks**:

- [ ] Create migration for PORTFOLIO_COMPANIES table
- [ ] Create migration for PORTFOLIO_FOUNDERS table
- [ ] Create migration for PORTFOLIO_INVESTMENTS table
- [ ] Create migration for PORTFOLIO_DOCUMENTS table
- [ ] Add proper indexes and constraints
- [ ] Test migration up/down operations

## Phase 2: Document Processing Services

### 2.1 Portfolio Document Parser Service (HIGH PRIORITY)

**File**: `backend/app/services/portfolio_document_parser.py` (new file)
**Dependencies**: PDF extractor, Portfolio models
**Estimated Time**: 4 days

**Tasks**:

- [ ] Implement SHA (Shareholders Agreement) parser
- [ ] Add data extraction validation and error handling
- [ ] Store extracted data with confidence scores

### 2.2 Portfolio Data Extraction Service (HIGH PRIORITY)

**File**: `backend/app/services/portfolio_data_extractor.py` (new file)
**Dependencies**: Document parser, Portfolio models
**Estimated Time**: 3 days

**Tasks**:

- [ ] Extract company information from SHA documents
- [ ] Parse founder details from legal documents
- [ ] Implement data validation and normalization

## Phase 3: API Implementation

### 3.1 Portfolio Companies API (HIGH PRIORITY)

**File**: `backend/app/api/portfolio_companies.py` (new file)
**Dependencies**: Portfolio models and services
**Estimated Time**: 3 days

**Endpoints to Implement**:

- [ ] `POST /portfolio-companies` - Create new portfolio company
- [ ] `GET /portfolio-companies` - List portfolio companies with filtering
- [ ] `GET /portfolio-companies/{company_id}` - Get specific company details
- [ ] `PUT /portfolio-companies/{company_id}` - Update company details
- [ ] `DELETE /portfolio-companies/{company_id}` - Delete company
- [ ] `GET /portfolio-companies/search` - Search companies by multiple criteria

**Business Logic**:

- [ ] Validate unique constraints (startup_brand, legal_entity_name)
- [ ] Handle company status transitions
- [ ] Implement proper error handling and status codes
- [ ] Add audit logging for company operations

### 3.2 Portfolio Investments API (HIGH PRIORITY)

**File**: `backend/app/api/portfolio_investments.py` (new file)
**Dependencies**: Investment models and services
**Estimated Time**: 2 days

**Endpoints to Implement**:

- [ ] `POST /portfolio-companies/{company_id}/investments` - Create new investment
- [ ] `GET /portfolio-companies/{company_id}/investments` - List company investments
- [ ] `PUT /investments/{investment_id}` - Update investment details
- [ ] `GET /investments/{investment_id}/valuation-history` - Get valuation history

### 3.3 Portfolio Documents API (HIGH PRIORITY)

**File**: `backend/app/api/portfolio_documents.py` (new file)
**Dependencies**: Document processing services
**Estimated Time**: 2 days

**Endpoints to Implement**:

- [ ] `POST /portfolio-companies/{company_id}/documents` - Link document to company
- [ ] `GET /portfolio-companies/{company_id}/documents` - Get company documents
- [ ] `DELETE /portfolio-companies/{company_id}/documents/{portfolio_document_id}` - Unlink document
- [ ] `POST /portfolio-documents/process` - Process document for data extraction

## Phase 4: Integration and Workflow

### 4.1 Portfolio Data Integration Service (HIGH PRIORITY)

**File**: `backend/app/services/portfolio_integration.py` (new file)
**Dependencies**: All portfolio services, SEBI reporting
**Estimated Time**: 2 days

**Tasks**:

- [ ] Integrate portfolio data with SEBI reporting
- [ ] Connect to fund performance calculations
- [ ] Link with compliance tracking systems
- [ ] Provide data for regulatory filings
- [ ] Create portfolio summary dashboards
- [ ] Handle data synchronization across systems

### 4.2 Portfolio Workflow Service (MEDIUM PRIORITY)

**File**: `backend/app/services/portfolio_workflow.py` (new file)
**Dependencies**: Portfolio models, task management
**Estimated Time**: 2 days

**Tasks**:

- [ ] Create portfolio company onboarding workflow
- [ ] Add document processing workflow
- [ ] Implement notification system for workflow events
- [ ] Add compliance checking and alerts

## Phase 5: Advanced Features

### 5.3 Portfolio Compliance Service (MEDIUM PRIORITY)

**File**: `backend/app/services/portfolio_compliance.py` (new file)
**Dependencies**: Portfolio models, compliance rules
**Estimated Time**: 2 days

**Tasks**:

- [ ] Implement regulatory compliance checking
- [ ] Add investment limit validations
- [ ] Create sector exposure monitoring
- [ ] Implement conflict of interest checking
- [ ] Add compliance reporting automation
- [ ] Create compliance alerts and notifications

## Phase 6: Testing and Integration

### 6.1 Update Main Application (HIGH PRIORITY)

**File**: `backend/main.py`
**Dependencies**: All API routers
**Estimated Time**: 0.5 days

**Tasks**:

- [ ] Add all portfolio-related routers to main FastAPI app
- [ ] Update API documentation
- [ ] Add proper error handling middleware
- [ ] Configure background task scheduling

### 6.2 Unit Tests (HIGH PRIORITY)

**Files**: Multiple test files for each component
**Dependencies**: Complete implementation
**Estimated Time**: 4 days

**Test Coverage**:

- [ ] Portfolio model tests
- [ ] Document parsing accuracy tests
- [ ] Investment calculation tests
- [ ] API endpoint tests
- [ ] Service layer tests
- [ ] Integration workflow tests

### 6.3 Integration Tests (HIGH PRIORITY)

**File**: `backend/tests/test_portfolio_integration.py`
**Dependencies**: Complete implementation
**Estimated Time**: 2 days

**Test Scenarios**:

- [ ] End-to-end portfolio company onboarding
- [ ] Document processing and data extraction
- [ ] Investment tracking and valuation updates
- [ ] Integration with SEBI reporting
- [ ] Error handling and recovery scenarios

## Dependencies and Blockers

### Upstream Dependencies

- **HIGH**: Fund Registration implementation (fund context required)
- **MEDIUM**: Document management system (already implemented)
- **MEDIUM**: PDF extraction utility (already implemented)

### Downstream Impact

- **CRITICAL**: SEBI reporting depends on portfolio investment data
- **HIGH**: Fund performance calculations use portfolio data
- **MEDIUM**: Regulatory compliance reporting uses portfolio information

### External Dependencies

- Document templates and formats standardization
- Valuation methodology approval
- Regulatory compliance requirements clarification

## Implementation Priority

### Phase 1 (Week 1): Database Foundation

1. Portfolio Companies Model - **CRITICAL**
2. Portfolio Investments Model - **CRITICAL**
3. Portfolio Founders Model - **CRITICAL**
4. Portfolio Documents Model - **CRITICAL**
5. Database Migrations - **CRITICAL**

### Phase 2 (Week 2): Document Processing

1. Portfolio Document Parser Service - **CRITICAL**
2. Portfolio Data Extraction Service - **CRITICAL**
3. Portfolio Companies API - **CRITICAL**

### Phase 3 (Week 3): Core APIs

1. Portfolio Investments API - **CRITICAL**
2. Portfolio Documents API - **CRITICAL**
3. Portfolio Data Integration Service - **HIGH**

### Phase 4 (Week 4): Integration and Workflow

1. Portfolio Workflow Service - **HIGH**
2. Account Statement Integration - **MEDIUM**
3. Portfolio Reporting Service - **MEDIUM**

### Phase 5 (Week 5): Advanced Features

1. Portfolio Analytics Service - **MEDIUM**
2. Portfolio Dashboard API - **MEDIUM**
3. Portfolio Compliance Service - **MEDIUM**

### Phase 6 (Week 6): Testing and Optimization

1. Unit Tests - **CRITICAL**
2. Integration Tests - **CRITICAL**
3. Performance Optimization - **MEDIUM**

## Success Criteria

- [ ] Portfolio companies can be created and managed via API
- [ ] Documents can be processed and linked to companies
- [ ] Investment tracking and valuation updates working
- [ ] Integration with SEBI reporting functional
- [ ] Portfolio analytics and reporting available
- [ ] Document processing accuracy >90%
- [ ] 90%+ test coverage on new functionality
- [ ] Performance acceptable for 100+ portfolio companies

## Risk Mitigation

### Technical Risks

- **Document parsing complexity**: Multiple validation layers and manual review options
- **Data integration challenges**: Comprehensive testing and fallback mechanisms
- **Performance with large datasets**: Async processing and optimization

### Business Risks

- **Valuation accuracy**: Multiple validation sources and approval workflows
- **Regulatory compliance**: Legal review and compliance monitoring
- **Data consistency**: Comprehensive audit trails and validation

### Operational Risks

- **Document format changes**: Flexible parsing with configuration options
- **Integration failures**: Fallback mechanisms and error handling
- **Data migration issues**: Comprehensive testing and validation procedures
