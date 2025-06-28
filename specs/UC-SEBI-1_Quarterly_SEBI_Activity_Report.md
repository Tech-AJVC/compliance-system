# UC-SEBI-1 — Produce Quarterly SEBI Activity Report

> **Category:** Regulatory Reporting  
> **Primary actor:** Compliance Officer  
> **Regulator:** Securities & Exchange Board of India (SEBI)

---

## 1. References

| Doc | Section                     |
| --- | --------------------------- |
| PRD | §5 – "SEBI Activity Report" |
| TRD | §20 – XML Generator Service |
| UX  | SEBI Report Form & table    |

### PRD Extract

> _"System should generate a SEBI Activity Report in prescribed XML schema and allow Compliance Officer to download or submit digitally."_

### TRD Extract

> _Script `sebi_xml_generator.py` maps DB fields to XSD `sebiFormV1` …_

### UX Extract

> Simple form asking 3 monetary figures + **Generate** button; list page shows generated XML with download link.

---

### Use Case

#### Trigger

- Send an email 15 days before end of quarter for SEBI Activity Report Reminder
- User inputs Temporary investments made as at the end of quarter (Rs. Cr), Estimated Expenses for the tenure (Rs. Cr)and Investable Funds (Rs. Cr).This is 15 days before the end of the quarter on UI and clicks 'Generate Activity Report'

#### Behaviour

- Pull data from LP, Draw-down, Portfolio tables, Fund Details per field mapping.
- Calculate the Total Commitment received as on Initial Close, the Investable Amount, Cumulative Portfolio Investments made as at the end of quarter, Total Commitment received as at the end of quarter (Corpus), Gross Cumulative Funds raised as at the end of quarter (Rs. Cr) based on Funding in Portfolio DB and Commitment Amount LP Details
- Group investors by name geography type with their amount based on LP Details fields
- Generate XML, name it according to quarter, and store in Doc Repository.
- Send an email to Fund Manager with the activity report update
- Record one audit-log entry for the Activity Report Update

### Figma UI Screen Inputs

#### SEBI Report Generation Form

- **Form Title**: "SEBI Report"
- **Subtitle**: "Generate a report for the current quarter"

##### Input Fields

- **Temporary Investments** (required): Currency input field with ₹ symbol
- **Cash in Hand** (required): Currency input field with ₹ symbol
- **Estimated Expenses** (required): Currency input field with ₹ symbol

##### Action Buttons

- **Generate Button**: Primary action button (dark background)
- **Cancel Button**: Secondary action button

#### SEBI Reports List View

- **Generate SEBI Report Button**: Primary action button
- **Search Field**: General search functionality
- **Reports Table Columns**:
  - Quarter (Q1'25 format)
  - Generated On (19th August 2024 format)
  - Document (SEBI-Report.xml as downloadable link)
- **Three-dot Menu**: Action menu for each report (View/Download/Delete options)

#### Fund Details Integration

- **Scheme Details Section**:

  - Scheme Name: Ajvc Fund Scheme of Ajvc Trust
  - Status: Active (green badge)
  - Registration: AWEOER123
  - Extension: Extension Permitted

- **AIF Details Section**:

  - Fund Name: AJVC Fund
  - AIF Registration: AAKTA6772D
  - Registration Number: IN/AIF2/24-25/1578
  - Structure: Trust
  - Category: Category II AIF

- **Financial Information**:

  - Corpus as on Initial Close: ₹80,000,00,000
  - Target Fund Size: ₹100,000,00,000
  - Greenshoe Option: ₹80,000,000

- **Bank Details**:
  - Bank: HDFC Bank AJVC
  - Account Numbers: 123245983274893​2, HDFC090000
  - Bank Contact: Aviral Bhatnagar (+91 9999999999)

#### Important Dates Timeline

- **PPM Final Draft Sent**: 12th August 2024
- **PPM Taken on Record**: 7th February 2025
- **Scheme Launch**: 15th March 2025
- **Initial Close**: 20th March 2025
- **Final Close**: 20th June 2025
- **End Date of Scheme**: 20th July 2025
- **End Date of Extended Term**: 30th august 2025

#### Report Document Preview

- **XML Format**: Generated reports in SEBI-compliant XML format
- **Download Functionality**: Direct download links for generated reports
- **Date Tracking**: Clear indication of when each report was generated

## PROCESS SECTION - SEBI ACTIVITY REPORT

This process handles the generation of quarterly SEBI activity reports by aggregating data from multiple upstream processes and combining it with user inputs for regulatory compliance.

### Subprocess: Fund Basic Information (from Fund Details)

- **Output**: AIF SI Portal Login, Scheme Name, Scheme Type, Name of the AIF, PAN of the AIF, Registration Number of the AIF, Legal Structure of the AIF, Category and Sub-category of the AIF (XML)
- **Input Source**: Fund Details
- **Input Format**: Form Field
- **Transformation**: Direct
- **Input Field**: SI Portal User ID, Scheme Name, Scheme Type, Name of the AIF, PAN of the AIF, Registration Number of the AIF, Legal Structure of the AIF, Category and Sub-category of the AIF
- **Formula**: N/A
- **DB vs PDF Analysis**: ✅ Read from FUND_DETAILS table

### Subprocess: Fund Entity Information (from Fund Details)

- **Output**: Entity Type, Entity Name, Entity PAN, Entity Email, Entity Address, Scheme Name, Name of Custodian, Name of RTA (XML)
- **Input Source**: Fund Details
- **Input Format**: Excel
- **Transformation**: Direct
- **Input Field**: Entity Type, Entity Name, Entity PAN, Entity Email, Entity Address, Scheme Name, Name of Custodian, Name of RTA
- **Formula**: Entity Type = "Manager" for fund manager
- **DB vs PDF Analysis**: ✅ Read from FUND_DETAILS and linked ENTITIES tables

### Subprocess: Compliance Officer Information (from Fund Details)

- **Output**: Name of Compliance Officer, Email of Compliance Officer, Contact No. of Compliance Officer (XML)
- **Input Source**: Fund Details
- **Input Format**: Form Field
- **Transformation**: Direct
- **Input Field**: Name of Compliance Officer, Email of Compliance Officer, Contact No. of Compliance Officer
- **Formula**: N/A
- **DB vs PDF Analysis**: ✅ Read from FUND_DETAILS table

### Subprocess: Investment Officer Information (from Entity Details)

- **Output**: Investment Officer Name, Designation, PAN, DIN/DPIN if any, Date of Appointment (XML)
- **Input Source**: Entity Details (Manager)
- **Input Format**: Excel
- **Transformation**: Direct
- **Input Field**: Investment Officer Name, Designation, PAN, DIN/DPIN if any, Date of Appointment
- **Formula**: N/A
- **DB vs PDF Analysis**: ✅ Read from FUND_DETAILS table (investment officer fields)

### Subprocess: Fund Timeline Information (from Fund Details)

- **Output**: Date of filing final draft PPM with SEBI, Date of SEBI Communication for taking the PPM on record, Date of launch of scheme, Date of Initial Close, Date of final close, End date of terms of Scheme, Any Extension of Term permitted, End date of Extended term (XML)
- **Input Source**: Fund Details
- **Input Format**: Form Field
- **Transformation**: Direct
- **Input Field**: All date fields as specified
- **Formula**: N/A
- **DB vs PDF Analysis**: ✅ Read from FUND_DETAILS table

### Subprocess: Portfolio Investment Information (from Portfolio Details)

- **Output**: Name of Investee Company, PAN of Investee Company, Type of Investee Company, Type of Security, Security details, Whether offshore investment, ISIN, SEBI Registration Number, Whether Associate, Whether managed by AIF's manager, Sector, Amount invested, Latest Value of Investment, Date of valuation (XML)
- **Input Source**: Portfolio Details
- **Input Format**: Excel
- **Transformation**: Direct
- **Input Field**: Company, PAN, Type, Security, Geography, ISIN, SEBI Registration, Conflict, Sector, Amount, Valuation, Valuation Date
- **Formula**: N/A
- **DB vs PDF Analysis**: ✅ Read from PORTFOLIO_DETAILS table

### Subprocess: Financial Calculations (from Multiple Sources)

- **Output**: Total Commitment received as on Initial Close, Total Commitment received as at end of quarter, Gross Cumulative Funds raised, Cumulative Portfolio Investments, Investable Funds (XML)
- **Input Source**: Contribution Agreement/LP Details + Portfolio Details + UI Financial Details
- **Input Format**: PDF + Excel + Form Field
- **Transformation**: Computation
- **Input Field**: Amount of Capital Commitment, Portfolio investments, Drawdown amounts, Fees
- **Formula**:
  - Total Commitment Initial Close = SUM(Capital_Commitment) till initial close
  - Total Commitment Quarter End = SUM(Capital_Commitment) till this quarter
  - Gross Cumulative Funds = SUMIF(Capital_Commitment, Q#)
  - Cumulative Portfolio Investments = COUNTIF(Portfolio investments)
  - Investable Funds = SUM(Amount Due from drawdown) - SUM(Fees)
- **DB vs PDF Analysis**: ✅ Calculate from LP_DETAILS, LP_DRAWDOWNS, and PORTFOLIO_DETAILS tables

### Subprocess: Temporary Investments and Cash (from UI Financial Details)

- **Output**: Temporary investments, Cash in hand, Estimated Expenses, Name of Investee Company (Temporary), Cost of Investment, Type of Security (XML)
- **Input Source**: UI for Financial Details + Portfolio Details
- **Input Format**: Excel
- **Transformation**: Direct
- **Input Field**: Liquid Fund Investment, Total Fees, Liquid Fund Name, Liquid Fund Type
- **Formula**: N/A
- **DB vs PDF Analysis**: ✅ Store in dedicated financial details table for reuse

### Subprocess: Investor Categorization (from LP Details)

- **Output**: Details of Investors (in Nos.) by Category, Details of Investors (in Crs) by Category (XML)
- **Input Source**: Contribution Agreement + Client Master List/LP Details
- **Input Format**: PDF
- **Transformation**: Computation
- **Input Field**: Name, Geography, Type, Commitment Amount
- **Formula**:
  - Investor Numbers = COUNTIFS(Name, Geography, Type)
  - Investor Amounts = SUMIFS(Name, Geography, Type)
- **DB vs PDF Analysis**: ✅ Calculate from LP_DETAILS table with geography and type fields

### Missing Upstream Fields Analysis:

- ⚠️ **Geography/Country**: Required for investor categorization but may not be in LP_DETAILS
- ⚠️ **Client Type**: Required for investor categorization but may not be in LP_DETAILS
- ✅ **Fund details**: Available from Fund Registration process
- ✅ **Portfolio details**: Available from Portfolio Registration process
- ✅ **Commitment amounts**: Available from LP Details Registration process

### Downstream Usage:

- SEBI Activity Report is the final regulatory output and doesn't feed into other processes

### DB vs PDF Optimization:

- ✅ **Fund information**: Read from FUND_DETAILS table
- ✅ **Entity information**: Read from ENTITIES and FUND_ENTITIES tables
- ✅ **Portfolio information**: Read from PORTFOLIO_DETAILS table
- ✅ **LP commitment amounts**: Read from LP_DETAILS table
- ✅ **Drawdown amounts**: Read from LP_DRAWDOWNS table
- ⚠️ **Geography and Type for investor categorization**: Must be captured in LP registration

### Critical Missing Fields for This Process:

1. **Geography/Country**: Essential for investor categorization by jurisdiction
2. **Client Type**: Essential for investor categorization (Individual, Corporate, etc.)
3. **Standardized LP categorization**: Based on trustee/Orbis jurisdiction requirements

## 2. Functional Requirements

1. **Input form** (fields: Temporary Investments, Cash in Hand, Estimated Expenses).
2. **Validation** – numeric, non-negative.
3. **XML Generation** conforming to XSD (attach spec).
4. **Storage & Versioning** in `sebi_reports` table.
5. **Download** link & audit trail entry.

## 3. Technical Requirements

- Use lxml to build XML.
- XSD stored in repo under `/schemas/sebi/`.
- Endpoint `POST /sebi-reports` returns presigned URL.

DB Schema's

───────────────────────────── SEBI_ACTIVITY_REPORTS
─────────────────────────────
• sebi_report_id: BIGINT PK
• fund_id: INT FK→FUND_DETAILS
• reporting_quarter: VARCHAR(20) -- FY25Q1
• document_id: INT FK→DOCUMENTS
• version: INT DEFAULT 1
• generated_by: UUID FK→USERS.user_id
• generated_at: TIMESTAMP
• status: VARCHAR(30) DEFAULT 'Draft' -- Draft/Reviewed/Filed
• gross_cumulative_funds_raised DECIMAL(18,2) DEFAULT 0.00, -- Gross Cumulative Funds raised as at the end of quarter (Rs. Cr)

• temporary_investments DECIMAL(18,2) DEFAULT 0.00, -- Temporary investments made as at the end of quarter (Rs. Cr)

• cash_in_hand DECIMAL(18,2) DEFAULT 0.00, -- Cash in hand as at the end of quarter (Rs. Cr)

• estimated_expenses DECIMAL(18,2) DEFAULT 0.00, -- Estimated Expenses for the tenure (Rs. Cr)

• investable_funds DECIMAL(18,2) DEFAULT 0.00, -- Investable Funds (Rs. Cr)
• total_commitment_received DECIMAL(18,2) DEFAULT 0.00, -- Total Commitment received (Corpus) as on Initial Close (Rs. Cr)

• investors_details_numbers BIGINT -- Details of Investors (in Nos.) (By Category)
• investors_details_amounts DECIMAL(18,2) DEFAULT 0.00, -- Details of Investors (in Crs) (By Category)

API's

7. SEBI ACTIVITY REPORTS

Resource: /sebi-activity-reports
POST /sebi-activity-reports/generate
JSON
{
"fund_id": 12,
"reporting_quarter": "FY25Q1",
"temporary_investments": 12.5,
"estimated_expenses": 3.8,
"cash_in_hand_quarter_end": 200,
"investable_funds": 550.0, // Optional if frontend calculates
}

Returns 201
XML with including the following fields:
{
"sebi_report_id": 6001,
"fund_id": 12,
"reporting_quarter": "FY25Q1",
"scheme_name": "AJVC FUND SCHEME OF AJVC TRUST",
"scheme_pan": "AAKTA6772D",
"scheme_type": "Closed Ended",
"legal_structure": "Trust",
"category_subcategory": "Category II AIF",
"gross_cumulative_funds_raised": 530.0,
"total_commitment_received": 560.0,
"temporary_investments": 12.5,
"cash_in_hand": 25.0,
"estimated_expenses": 3.8,
"investable_funds": 550.0,
"investors_details_numbers": 42,
"investors_details_amounts": 560.0,
"officers": {
"compliance_officer_name": "Sachin Rao",
"compliance_officer_email": "sachin@ajvc.com",
"investment_officer_name": "Aviral Bhatnagar",
"designation": "Fund Manager",
"din_dpin": null,
"date_of_appointment": "2025-02-01"
},
"custodian_name": null,
"rta_name": null,
"investee_details": [
{
"company_name": "Yinara",
"pan": "AAACY1234D",
"type": "Equity",
"security": "CCPS",
"geography": "India",
"isin": "INE000123456",
"amount_invested": 150.00,
"latest_valuation": 180.00,
"valuation_date": "2025-03-31",
"conflict_flag": "No"
}
],
"document_id": 89011,
"version": 1,
"status": "Draft",
"generated_by": "1d4e3a07-bfb1-4f8b-9c3a-e320c7f2f111",
"generated_at": "2025-07-05T09:31:00Z"
}
GET /sebi-activity-reports?fund_id=12&status=Draft
GET /sebi-activity-reports/{id}
PUT /sebi-activity-reports/{id}/mark-reviewed
Returns 204 No Content. PUT /sebi-activity-reports/{id}/mark-filed
Returns 204 No Content.

## MISSING API ENDPOINTS

### SEBI REPORTS LISTING (Critical Missing)

Resource: /sebi-activity-reports
GET /sebi-activity-reports?fund_id=12&status=Draft
Returns list of generated reports
JSON
[{
"sebi_report_id": 6001,
"fund_id": 12,
"reporting_quarter": "Q1'25",
"generated_on": "2024-08-19",
"document_name": "SEBI-Report-Q1-2025.xml",
"document_id": 150,
"download_url": "https://drive.google.com/file/d/xyz",
"status": "Filed",
"generated_by_name": "Sachin Rao",
"generated_at": "2025-05-08T09:14:11Z"
}]

GET /sebi-activity-reports/{sebi_report_id}/download
Returns presigned download URL
JSON
{
"download_url": "https://secure-download-url.com/sebi-report.xml",
"expires_at": "2025-05-08T10:14:11Z"
}

DELETE /sebi-activity-reports/{sebi_report_id}
Returns 204 No Content

## 4. Contradictions

| #   | Issue                                                         | PRD | UX     | Action           |
| --- | ------------------------------------------------------------- | --- | ------ | ---------------- |
| 1   | PRD mentions **auto-submit** to SEBI portal; UX only download | §5  | Screen | Decide MVP scope |

## 5. Tasks

### Human

- [ ] Confirm whether auto-submit is in scope.

### AI

- [ ] Implement XML generator util.
- [ ] FastAPI route & DB model.
- [ ] FE form and list page.
- [ ] Unit tests + XSD validation.

---

_Status: draft._

# WORKPLAN - SEBI ACTIVITY REPORT IMPLEMENTATION

## Overview

This workplan details the implementation of Quarterly SEBI Activity Report generation functionality, integrating data from multiple sources to create regulatory-compliant XML reports.

## Phase 1: Database Schema Implementation

### 1.1 Create SEBI Reports Model (HIGH PRIORITY)

**File**: `backend/app/models/sebi_report.py` (new file)
**Dependencies**: Fund models
**Estimated Time**: 1 day

**Tasks**:

- [ ] Create `SEBIReport` SQLAlchemy model
- [ ] Add fields: report_id, fund_id, quarter, report_date, temporary_investments, cash_in_hand, estimated_expenses, xml_file_path, status, generated_by, approved_by
- [ ] Create relationships to Fund model
- [ ] Add report status enum (Draft, Generated, Approved, Submitted)
- [ ] Create Pydantic schemas in `backend/app/schemas/sebi.py`

### 1.2 Create SEBI Report Data Model (HIGH PRIORITY)

**File**: `backend/app/models/sebi_report_data.py` (new file)
**Dependencies**: SEBI Report model
**Estimated Time**: 1 day

**Tasks**:

- [ ] Create `SEBIReportData` SQLAlchemy model for storing calculated report data
- [ ] Add fields: data_id, report_id, data_type, data_value, calculation_source, created_at
- [ ] Create relationships to SEBIReport model
- [ ] Add data type enum for different report sections
- [ ] Store intermediate calculations for audit purposes

### 1.3 Database Migrations (HIGH PRIORITY)

**File**: `backend/alembic/versions/xxx_create_sebi_tables.py`
**Dependencies**: SEBI models
**Estimated Time**: 0.5 days

**Tasks**:

- [ ] Create migration for SEBI_REPORTS table
- [ ] Create migration for SEBI_REPORT_DATA table
- [ ] Add proper indexes for performance
- [ ] Test migration up/down operations

## Phase 2: Data Aggregation Services

### 2.1 SEBI Data Aggregator Service (HIGH PRIORITY)

**File**: `backend/app/services/sebi_data_aggregator.py` (new file)
**Dependencies**: Fund, LP, Portfolio, Drawdown models
**Estimated Time**: 4 days

**Tasks**:

- [ ] Implement fund basic information aggregation from Fund Details
- [ ] Aggregate entity information from Fund-Entity relationships
- [ ] Collect compliance officer information
- [ ] Gather investment officer details
- [ ] Extract fund timeline information
- [ ] Aggregate portfolio investment data
- [ ] Calculate financial metrics from multiple sources
- [ ] Implement data validation and consistency checks

### 2.2 Financial Calculations Service (HIGH PRIORITY)

**File**: `backend/app/services/sebi_financial_calculator.py` (new file)
**Dependencies**: LP, Drawdown, Portfolio models
**Estimated Time**: 3 days

**Tasks**:

- [ ] Calculate total commitment received as on initial close
- [ ] Calculate total commitment received as at end of quarter
- [ ] Compute gross cumulative funds raised
- [ ] Calculate cumulative portfolio investments
- [ ] Compute investable funds
- [ ] Implement investor geography and type grouping
- [ ] Add validation for calculation accuracy
- [ ] Store calculation audit trails

### 2.3 Investor Classification Service (MEDIUM PRIORITY)

**File**: `backend/app/services/investor_classifier.py` (new file)
**Dependencies**: LP models
**Estimated Time**: 2 days

**Tasks**:

- [ ] Group investors by name, geography, and type
- [ ] Calculate investment amounts by category
- [ ] Implement investor type classification
- [ ] Handle geography-based grouping
- [ ] Create investor summary statistics
- [ ] Add validation for classification accuracy

## Phase 3: XML Generation Engine

### 3.1 SEBI XML Generator Service (HIGH PRIORITY)

**File**: `backend/app/services/sebi_xml_generator.py` (new file)
**Dependencies**: Data aggregation services, XML schema
**Estimated Time**: 4 days

**Tasks**:

- [ ] Implement XML schema mapping for SEBI format
- [ ] Create XML template structure
- [ ] Map database fields to XML elements
- [ ] Implement data transformation and formatting
- [ ] Add XML validation against SEBI XSD schema
- [ ] Handle XML generation errors and validation
- [ ] Store generated XML files with proper naming

### 3.2 XML Schema Validation Service (HIGH PRIORITY)

**File**: `backend/app/services/xml_validator.py` (new file)
**Dependencies**: XML generator
**Estimated Time**: 2 days

**Tasks**:

- [ ] Implement SEBI XSD schema validation
- [ ] Add XML structure validation
- [ ] Validate data types and formats
- [ ] Check required field completeness
- [ ] Generate validation reports
- [ ] Handle validation errors and warnings

### 3.3 Report Template Service (MEDIUM PRIORITY)

**File**: `backend/app/services/sebi_template_service.py` (new file)
**Dependencies**: XML generator
**Estimated Time**: 2 days

**Tasks**:

- [ ] Create configurable XML templates
- [ ] Implement template versioning
- [ ] Handle template customization
- [ ] Add template validation
- [ ] Support multiple SEBI form versions
- [ ] Implement template update mechanisms

## Phase 4: API Implementation

### 4.1 SEBI Reports API (HIGH PRIORITY)

**File**: `backend/app/api/sebi_reports.py` (new file)
**Dependencies**: SEBI services
**Estimated Time**: 3 days

**Endpoints to Implement**:

- [ ] `POST /sebi-reports/generate` - Generate new SEBI report
- [ ] `GET /sebi-reports` - List SEBI reports with filtering
- [ ] `GET /sebi-reports/{report_id}` - Get specific report details
- [ ] `GET /sebi-reports/{report_id}/download` - Download XML report
- [ ] `POST /sebi-reports/{report_id}/approve` - Approve report
- [ ] `GET /sebi-reports/preview` - Preview report data before generation

**Business Logic**:

- [ ] Validate input data for report generation
- [ ] Handle report approval workflow
- [ ] Implement report status transitions
- [ ] Add proper error handling and status codes
- [ ] Generate unique report filenames

### 4.2 SEBI Data API (MEDIUM PRIORITY)

**File**: `backend/app/api/sebi_data.py` (new file)
**Dependencies**: Data aggregation services
**Estimated Time**: 2 days

**Endpoints to Implement**:

- [ ] `GET /sebi-data/fund-info` - Get fund information for reporting
- [ ] `GET /sebi-data/financial-summary` - Get financial calculations
- [ ] `GET /sebi-data/investor-classification` - Get investor groupings
- [ ] `POST /sebi-data/validate` - Validate report data before generation

## Phase 5: Automation and Scheduling

### 5.1 SEBI Report Reminder Service (HIGH PRIORITY)

**File**: `backend/app/services/sebi_reminder_service.py` (new file)
**Dependencies**: Email service, Task management
**Estimated Time**: 2 days

**Tasks**:

- [ ] Create scheduled job for quarterly reminders
- [ ] Send email 15 days before quarter end
- [ ] Create compliance tasks for report generation
- [ ] Track reminder status and responses
- [ ] Implement escalation for overdue reports
- [ ] Integrate with existing task management system

### 5.2 Report Generation Workflow (MEDIUM PRIORITY)

**File**: `backend/app/services/sebi_workflow.py` (new file)
**Dependencies**: SEBI services, task management
**Estimated Time**: 2 days

**Tasks**:

- [ ] Create automated report generation workflow
- [ ] Implement approval workflow for reports
- [ ] Add data validation checkpoints
- [ ] Handle workflow status tracking
- [ ] Implement rollback capabilities
- [ ] Add notification system for workflow events

### 5.3 SEBI Submission Service (LOW PRIORITY)

**File**: `backend/app/services/sebi_submission.py` (new file)
**Dependencies**: SEBI API integration
**Estimated Time**: 3 days

**Tasks**:

- [ ] Implement SEBI portal integration (future)
- [ ] Add automated submission capability
- [ ] Handle submission status tracking
- [ ] Implement submission error handling
- [ ] Add submission confirmation and receipts
- [ ] Create submission audit trails

## Phase 6: Integration and Testing

### 6.1 Update Main Application (HIGH PRIORITY)

**File**: `backend/main.py`
**Dependencies**: All API routers
**Estimated Time**: 0.5 days

**Tasks**:

- [ ] Add SEBI reports router to main FastAPI app
- [ ] Add SEBI data router
- [ ] Update API documentation
- [ ] Configure background task scheduling

### 6.2 Unit Tests (HIGH PRIORITY)

**Files**: Multiple test files for each component
**Dependencies**: Complete implementation
**Estimated Time**: 4 days

**Test Coverage**:

- [ ] Data aggregation accuracy tests
- [ ] Financial calculation tests
- [ ] XML generation and validation tests
- [ ] API endpoint tests
- [ ] Service layer tests
- [ ] Integration workflow tests

### 6.3 Integration Tests (HIGH PRIORITY)

**File**: `backend/tests/test_sebi_integration.py`
**Dependencies**: Complete implementation
**Estimated Time**: 2 days

**Test Scenarios**:

- [ ] End-to-end report generation flow
- [ ] Data accuracy across all sources
- [ ] XML validation and compliance
- [ ] Reminder and workflow automation
- [ ] Error handling and recovery scenarios

## Dependencies and Blockers

### Upstream Dependencies

- **CRITICAL**: Fund Registration implementation (fund details required)
- **CRITICAL**: LP Details and Drawdowns (financial calculations)
- **CRITICAL**: Portfolio management (investment data)
- **HIGH**: Payment reconciliation (actual fund flows)

### Downstream Impact

- **CRITICAL**: Regulatory compliance depends on accurate reporting
- **HIGH**: Fund operations depend on timely report submission
- **MEDIUM**: Investor communications reference report data

### External Dependencies

- SEBI XML schema and validation requirements
- SEBI portal integration specifications (future)
- Regulatory compliance review and approval

## Implementation Priority

### Phase 1 (Week 1): Database and Data Aggregation

1. SEBI Reports Model - **CRITICAL**
2. SEBI Report Data Model - **CRITICAL**
3. SEBI Data Aggregator Service - **CRITICAL**
4. Database Migrations - **CRITICAL**

### Phase 2 (Week 2): Calculations and XML Generation

1. Financial Calculations Service - **CRITICAL**
2. SEBI XML Generator Service - **CRITICAL**
3. XML Schema Validation Service - **CRITICAL**

### Phase 3 (Week 3): APIs and Integration

1. SEBI Reports API - **CRITICAL**
2. Investor Classification Service - **HIGH**
3. SEBI Data API - **HIGH**

### Phase 4 (Week 4): Automation and Workflow

1. SEBI Report Reminder Service - **HIGH**
2. Report Generation Workflow - **HIGH**
3. Report Template Service - **MEDIUM**

### Phase 5 (Week 5): Testing and Optimization

1. Unit Tests - **CRITICAL**
2. Integration Tests - **CRITICAL**
3. Performance Optimization - **MEDIUM**

### Phase 6 (Week 6): Advanced Features

1. SEBI Submission Service - **LOW**
2. Documentation - **MEDIUM**
3. Performance Monitoring - **MEDIUM**

## Success Criteria

- [ ] SEBI reports generated automatically with accurate data
- [ ] XML files comply with SEBI schema requirements
- [ ] Quarterly reminders sent automatically
- [ ] Report approval workflow functioning
- [ ] All financial calculations accurate and auditable
- [ ] Data aggregation from all required sources working
- [ ] 90%+ test coverage on new functionality
- [ ] Report generation time <5 minutes for typical fund

## Risk Mitigation

### Technical Risks

- **Data accuracy**: Multiple validation layers and audit trails
- **XML compliance**: Comprehensive schema validation and testing
- **Performance issues**: Optimize data aggregation and caching

### Business Risks

- **Regulatory non-compliance**: Legal review and compliance validation
- **Calculation errors**: Multiple validation sources and approval process
- **Missing deadlines**: Automated reminders and escalation procedures

### Operational Risks

- **Data source failures**: Fallback mechanisms and manual override options
- **Schema changes**: Flexible XML generation with configuration
- **System downtime**: Backup generation capabilities and manual processes
