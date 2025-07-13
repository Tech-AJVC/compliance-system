# UC-LP-1 — Generate & Send Capital-Call Notice

> **Use-case category:** Limited Partner Workflows  
> **Primary actor:** Fund Manager  
> **Secondary actors:** Compliance Officer, Limited Partner (recipient)

---

## 1. Source References

| Document                      | Section(s)                                                |
| ----------------------------- | --------------------------------------------------------- |
| **PRD Phase-2**               | §3.1 – "Capital Call" (pg 4–6)                            |
| **TRD Phase-2**               | §9 – §12 _(APIs & data model)_                            |
| **UX Requirements – Phase-2** | Screen flows: "Initiate Drawdown", "Drawdown Status Card" |

_(Please refer to the PDFs in `/docs` for verbatim text; extracts copied below remain unchanged)._

### Use Case

#### Trigger

- Email goes to the Fund Manager on the 7th of every quarter to make a capital call
- Fund Manager inputs Amount Due, Contribution Due Date, Forecast Next Quarter, Notice Date on the UI
- Fund Manager clicks "Issue Capital Call" for a draw-down round.

#### Behaviour

- Calculate each LP's pro-rata Amount Due and Remaining Commitment from Fund Details, Contribution Agreement, details of UI
- Create a Drawdown Notice in Excel with calculated and static fields
- Store the Drawdown Notice fields in the DB
- Display a preview to the user of the Drawdown Notice for each LP in a paginated format (X sheets)
- Send individual e-mails to every LP for a capital call and store a copy of the Drawdown Notice in the Document Repository against LP ID
- Record one audit-log entry for the Capital Call

### 1.1 PRD Extract

> _"The system shall allow a Fund Manager to initiate a Capital-Call for a given quarter, automatically generating drawdown amounts for each onboarded LP based on their commitments, and dispatch a formal notice via email…"_  
> … _(full paragraph retained)_

### 1.2 TRD Extract

> _API: `POST /drawdowns` → persists `drawdown` record, auto-creates `drawdown_lps` children, triggers event `DRAW_DOWN_INITIATED`_  
> _Data model changes: table `drawdown_lp_status` …_  
> …
> DB Schema
> ───────────────────────────── 8. LP_DRAWDOWNS
> ─────────────────────────────
> • drawdown_id: INT PRIMARY KEY
> • lp_id: INT                     --FK to LP_DETAILS.lp_id
> • total_drawdown: DECIMAL(15,2)         -- e.g. 2000000.00
> • total_units_allotted: INT           – e.g. 20000
> • allotted_units: INT              – e.g. 15000 (if different from total)
> • nav_value: DECIMAL(10,2)             – e.g. 100.00
> • date_of_allotment: DATE             – e.g. 01/01/2025
> • committed_amt: DECIMAL(15,2)          – e.g. 10000000.00
> • remaining_commitment: DECIMAL(15,2)
> • drawdown_amount: DECIMAL(15,2)         – e.g. 1500000.00
> • mgmt_fees: DECIMAL(15,2)            – e.g. 118000.00
> • amt_accepted: DECIMAL(15,2)           – e.g. 1500000.00
> • fund_account_no: VARCHAR(50)
> • micr_code: VARCHAR(20)
> • stamp_duty: DECIMAL(10,2)           – e.g. 75.00
> • status: VARCHAR(50)               -- e.g. "5 - Allotment Done"
> • drawdown_due_date: DATE               – e.g. 05/11/2024
> • bank_contact: VARCHAR(50) 
> • drawdown_quarter: VARCHAR(20)        – e.g. FY25Q3
> • forecast_next_quarter: DECIMAL(15,2)  
> • fund_id: INT

───────────────────────────── 13. DRAWDOWN_NOTICES
─────────────────────────────
• drawdown_id: INT FK→LP_DRAWDOWNS
• lp_id: INT FK→LP_DETAILS
• document_id: INT FK→DOCUMENTS
• notice_date: DATE
• amount_due: DECIMAL(18,2)
• due_date: DATE
• status: VARCHAR(30) DEFAULT 'Sent' -- Sent/Failed/Viewed
• sent_at: TIMESTAMP
• delivery_channel: VARCHAR(30) -- email

API's: 3. DRAWDOWNS

Resource: /drawdowns
POST /drawdowns/generate_drawdowns
JSON
{
"fund_id": 12,
"total_drawdown_amount": 65000000.00,
"forecast_next_quarter": 5000000.00,
"drawdown_due_date": "2025-06-30"
}

Returns 200 (list – one per LP, all 16 columns)
JSON
[
{
"drawdown_id": 4501,
"bank_name": "HDFC Bank",
"ifsc": "HDFC0000001",
"acct_name": "AJVC Fund",
"acct_number": "012345678901",
"bank_contact": "Mahesh Iyer",
"phone": "+91-9876543210",
"amount_due": 1000000.00,
"total_commitment": 5000000.00,
"amount_called_up": 1500000.00,
"remaining_commitment": 3500000.00,
"contribution_due_date": "2025-06-30",
"forecast_next_quarter": 5000000.00,
"notice_date": "2025-05-04",
"investor": "Main Street Capital",
"status": "Sent"
}]
Other End-points
GET /drawdowns?fund_id=12&status=Sent
GET /drawdowns/{drawdown_id}
Returns 200
{
"drawdown_id": 4501,
"bank_name": "HDFC Bank",
"ifsc": "HDFC0000001",
"acct_name": "AJVC Fund",
"acct_number": "012345678901",
"lp_ids":['123', '456', '789'] ,
"bank_contact": "Mahesh Iyer",
"phone": "+91-9876543210",
"amount_due": 1000000.00,
"total_commitment": 5000000.00,
"amount_called_up": 1500000.00,
"remaining_commitment": 3500000.00,
"contribution_due_date": "2025-06-30",
"forecast_next_quarter": 5000000.00,
"notice_date": "2025-05-04",
"investor": "Main Street Capital",
"status": "Sent"
}
GET /drawdowns/{drawdown_id}/status
Returns
JSON
{
"status": "Allotment Done"
}
PUT /drawdowns/{drawdown_id}/cancel
Returns 204 No Content.

GET /drawdowns/due_date
filter on Drawdown Notices Table to get list of LP IDs given quarter range

## MISSING API ENDPOINTS

### DRAWDOWN PREVIEW (Critical Missing) (CHECK NEED IF DRAWDOWN GIVES ALL INFO ALREADY)

Resource: /drawdowns/preview
POST /drawdowns/preview
JSON
{
"fund_id": 12,
"percentage_drawdown": 15.0,
"notice_date": "2025-05-04",
"due_date": "2025-06-30",
"forecast_next_quarter": 12.0
}

Returns 200 - Preview without persisting
JSON
{
"preview_id": "temp_4501",
"total_drawdown_amount": 65000000.00,
"lp_previews": [
{
"lp_id": 101,
"lp_name": "Warren Buffet",
"commitment_amount": 10000000.00,
"drawdown_amount": 1500000.00,
"drawdown_so_far": 1000000.00,
"remaining_commitment": 8500000.00
}
],
"summary": {
"total_lps": 16,
"total_amount": 65000000.00,
"average_drawdown": 4062500.00
}
}

### DRAWDOWN STATUS TRANSITIONS (Critical Missing)

Resource: /drawdowns/{drawdown_id}/status-transition
PATCH /drawdowns/{drawdown_id}/status-transition
JSON
{
"new_status": "Wire Pending",
"notes": "Payment instruction sent to LP"
}

Returns 200
JSON
{
"drawdown_id": 4501,
"previous_status": "Demat Pending",
"new_status": "Wire Pending",
"transition_timestamp": "2025-05-08T09:14:11Z",
"valid_next_statuses": ["Acceptance Pending", "Cancelled"]
}

GET /drawdowns/{drawdown_id}/status-history
Returns status transition history
JSON
[{
"status": "Sent",
"timestamp": "2025-05-04T10:00:00Z",
"notes": "Drawdown notice sent to LP"
}, {
"status": "Demat Pending",
"timestamp": "2025-05-05T14:30:00Z",
"notes": "LP acknowledged receipt"
}]

### BATCH DRAWDOWN OPERATIONS (Missing)

Resource: /drawdowns/batch
POST /drawdowns/batch/status-update
JSON
{
"drawdown_ids": [4501, 4502, 4503],
"new_status": "Allotment Pending",
"notes": "Bulk status update after payment verification"
}

Returns 200
JSON
{
"updated_count": 3,
"failed_updates": [],
"timestamp": "2025-05-08T09:14:11Z"
}

### Drawdown LP SEARCH AND FILTERING (Missing)

Resource: /lps/search
GET /lps/search?query=warren&status=Verified&drawdown_status=Pending
Returns filtered LP results
JSON
[{
"lp_id": 101,
"lp_name": "Warren Buffet",
"email": "warren@berkshire.com",
"overall_status": "Verified",
"last_drawdown_status": "Pending",
"commitment_amount": 10000000.00,
"remaining_drawdown": 9000000.00
}]

### 1.3 UX Extract

> _Figma Frame — Initiate Drawdown Modal_  
> Fields: Notice Date, Due Date, % Drawdown, Expected Amount, Forecast %, LP table (Name, Drawdown, Drawdown so far).  
> Primary CTA **Send** (enabled when required fields valid).

---

## 2. Functional Requirements (PRD-driven)

1. **Initiate Drawdown**  
   a. Manager selects quarter (e.g., _Q1'25_).  
   b. Inputs Notice Date, Due Date, % drawdown, etc.  
   c. System calculates per-LP drawdown amounts.  
   d. On **Send**, persistence + email notice.

2. **Email Notice Generation**  
   • Templated PDF with fund letterhead (see PRD Appendix A).  
   • One email per LP, BCC Compliance.

3. **Audit Trail**  
   • Write audit log entry `CAPITAL_CALL_SENT` with payload.

4. **Permission**  
   • Only roles _Fund Manager_ / _Compliance Officer_ may invoke.

## 3. UX Requirements

- Modal form validation, progress indicator on send.
- Drawdown Status card states: _Pending_, _Wire Pending_, _Unit Allotment Generated_, _Allotment Done_.
- Colour tokens from design system (#007AFF blue, #F5A623 yellow, #00B386 green).

## 4. Technical Requirements (TRD-driven)

- Backend service `drawdown_service` responsible for:  
  – Generating DB rows in `drawdowns`, `drawdown_lp`.  
  – Publishing message on `drawdown.notice` queue.
- Worker picks message, renders PDF via ReportLab, sends via SendGrid.
- New cron job `drawdown_status_sync` to refresh statuses from banking API (see UC-LP-2).

## 5. Contradictions / Ambiguities

| #   | Description                                                                        | PRD ref   | UX ref              | Resolution                                 |
| --- | ---------------------------------------------------------------------------------- | --------- | ------------------- | ------------------------------------------ |
| 1   | PRD states default drawdown % = **10 %**, UX modal shows field pre-filled **12 %** | PRD §3.1  | UX modal screenshot | Pending stakeholder clarification          |
| 2   | TRD requires PDF **and** XML output; PRD mentions PDF only                         | TRD §11.4 | PRD §3.1            | Default to PDF; XML flagged 'nice-to-have' |

## 6. Task Breakdown

### Human Tasks

- [ ] Product owner to resolve contradictions listed above.
- [ ] Legal to approve Capital-Call PDF template (due **14-Jun-25**).
- [ ] DevOps to provision `drawdown_service` container + queue.

### AI-Executable Tasks

- [ ] Implement `drawdown_service` REST endpoint & SQLAlchemy models.
- [ ] Generate migration for new tables.
- [ ] Implement PDF generation using ReportLab.
- [ ] Write unit + integration tests (pytest).
- [ ] FE: build Initiate Drawdown modal (React, MUI).
- [ ] FE: build Drawdown Status Card component.
- [ ] Update CI pipeline to include new service.

---

_Status: initial draft generated (see Git SHA)._

### Figma UI Screen Inputs

#### Initiate Drawdown Form

- **Notice Date** (required): Date picker field
- **Due Date** (required): Date picker field
- **Percentage drawdown** (required): Percentage input field with % symbol
- **Expected drawdown amount for this quarter**: Currency input field (₹ format)
- **Forecasted drawdown for next quarter** (required): Percentage input field with % symbol
- **Limited Partners Preview Table**:
  - Name column
  - Drawdown Amount column (₹ format)
  - Drawdown so far column (₹ format)
- **Send Button**: Primary action button (dark background)
- **Cancel Button**: Secondary action button

#### Drawdown Status Screens

- **Quarter Selector**: Dropdown (Q1'25, Q4'24, Q3'24, Q2'24, Q1'24)
- **Status Badge**: Dynamic status indicator
  - Drawdown Pending (blue)
  - Wire Pending (orange)
  - Unit Allotment Generated (orange)
  - Allotment Done (green)

#### Progress Timeline (4-step process)

1. **Notice**:

   - Sent on 7th January 2025 (completed - checkmark)
   - Yet to be sent (pending - number badge)

2. **Money Transfer**:

   - 20% - (20/100) transfers done (in progress)
   - 100% - (100/100) transfers done (completed)
   - No transfers done (pending)
   - Upload statement link (blue link)

3. **Unit Allotment**:

   - No units allotted yet (pending)
   - 100% units allotted (completed)

4. **inVi filing**:
   - Not yet done (pending)
   - Done (completed)

#### Drawdown Details Modal

- **Modal Title**: "Initiate Drawdown"
- **Subtitle**: "Send capital call to all onboarded Limited Partners"
- **Header Information**:
  - Notice Date, Due Date, Percentage Drawdown
  - Expected Drawdown, Forecasted Drawdown, Next Drawdown Date
  - Total Drawdown Till Date, Total Drawdown (%)
- **LP-specific Calculations Table**:
  - Limited Partners column
  - Drawdown Amount column (₹10,00,000 format)
  - Remaining Drawdown column (₹70,00,000 format)
  - Drawdown Status column (badges)

#### Drawdowns List View

- **Initiate Drawdown Button**: Primary action button
- **Search Field**: "Search Drawdowns..." placeholder
- **Table Columns**:
  - Quarter (Q1'25, Q4'24, etc.)
  - Notice Date (7/1/2025 format)
  - Drawdown Status (badge indicators)
  - InVi Filing (badge indicators)
  - Drawdown (₹1,00,00,000 format)
  - Remaining Drawdown (₹50,00,000 format)
- **Status Options**:
  - Pending (blue badge)
  - Allotment Done (green badge)
  - Done (green badge)

#### Status Badge System

- **Not Applicable**: Green badge with checkmark
- **Pending**: Blue badge with clock icon
- **Document Generated**: Orange badge with document icon
- **Done**: Green badge with checkmark

## PROCESS SECTION - DRAWDOWN NOTICE

This process handles the generation of capital call notices (drawdown notices) for Limited Partners by combining fund details with LP-specific information.

### Subprocess: Fund Bank Details Extraction

- **Output**: Bank Name, IFSC, Acct Name, Acct Number, Bank Contact, Phone (Excel)
- **Input Source**: Fund Details
- **Input Format**: Form Field
- **Transformation**: Direct
- **Input Field**: Bank Name, IFSC, Acct Name, Acct Number, Bank Contact, Contact Phone
- **Formula**: N/A
- **DB vs PDF Analysis**: ✅ Read from FUND_DETAILS table (bank_name, bank_ifsc, bank_account_name, bank_account_no, bank_contact_person, bank_contact_phone)

### Subprocess: LP Drawdown Amount Calculation

- **Output**: Amount Due, Total Commitment, Amount Called Up, Remaining Commitment (Excel)
- **Input Source**: UI for Drawdown + Contribution Agreement + LP Details
- **Input Format**: Form Field + PDF
- **Transformation**: Computation
- **Input Field**: % Drawdown (UI), Commitment Amount (CA)
- **Formula**:
  - Amount Due = % Drawdown \* Total Commitment
  - Amount Called Up = SUMIF(AmountDue, Contributor) (sum over all previous notices)
  - Remaining Commitment = Commitment Amount - Amount Called Up
- **DB vs PDF Analysis**: ✅ Read Commitment Amount from LP_DETAILS table, calculate amounts using UI inputs

### Subprocess: Drawdown Schedule Information

- **Output**: Contribution Due Date, Forecast Next Quarter, Notice Date, Investor (Excel)
- **Input Source**: UI for Drawdown + Contribution Agreement
- **Input Format**: Form Field + PDF
- **Transformation**: Direct
- **Input Field**: Due Date, Next Quarter Forecast, Notice Date, Name and Address of Contributor
- **Formula**: N/A
- **DB vs PDF Analysis**: ✅ Read Investor name from LP_DETAILS table, other fields from UI inputs

### Missing Upstream Fields Analysis:

- ✅ **Fund bank details**: Available from Fund Registration process
- ✅ **LP commitment amounts**: Available from LP Details Registration process
- ✅ **LP names and contact info**: Available from LP Details Registration process
- ✅ No missing upstream dependencies identified

### Downstream Usage:

- Drawdown Notice data is used by:
  - Payment Reconciliation (amount matching, contributor matching)
  - Unit Allotment (drawdown amounts, dates)
  - SEBI Activity Report (cumulative funds raised calculations)
  - InVi Filing (foreign investor amount reporting)

### DB vs PDF Optimization:

- ✅ **Fund bank details**: Read from FUND_DETAILS table instead of re-extracting from PDFs
- ✅ **LP commitment amounts**: Read from LP_DETAILS table instead of re-parsing Contribution Agreements
- ✅ **LP names**: Read from LP_DETAILS table instead of re-parsing Contribution Agreements
- ⚠️ **Historical drawdown amounts**: Should be calculated from LP_DRAWDOWNS table for accuracy

## 2. Functional Requirements

# WORKPLAN - CAPITAL CALL NOTICE IMPLEMENTATION

## Overview

This workplan details the implementation of Capital Call Notice generation and management functionality, building on existing LP infrastructure to add drawdown capabilities.

## Phase 1: Database Schema Enhancements

### 1.1 Enhance LP Drawdowns Model (HIGH PRIORITY)

**File**: `backend/app/models/lp_drawdowns.py`
**Dependencies**: Existing LPDrawdown model, Fund Details model
**Estimated Time**: 1 day

**Current Status**: Basic LPDrawdown model exists but needs enhancement
**Tasks**:

- [ ] Add missing fields to match specification:
  - `total_units_allotted`, `allotted_units`, `nav_value`, `date_of_allotment`
  - `committed_amt`, `remaining_commitment`, `mgmt_fees`, `amt_accepted`
  - `fund_account_no`, `micr_code`, `stamp_duty`, `bank_contact`
  - `drawdown_quarter`, `forecast_next_quarter`, `fund_id`
- [ ] Update existing model relationships
- [ ] Add proper field validations and constraints
- [ ] Create enhanced Pydantic schemas in `backend/app/schemas/lp.py`

### 1.2 Create Drawdown Notices Model (HIGH PRIORITY)

**File**: `backend/app/models/drawdown_notice.py`
**Dependencies**: LPDrawdown, LPDetails, Document models
**Estimated Time**: 1 day

**Tasks**:
#Check need for doc_id

- [ ] Create `DrawdownNotice` SQLAlchemy model
- [ ] Add fields: drawdown_id, lp_id, document_id, notice_date, amount_due, due_date, status, sent_at, delivery_channel
- [ ] Create relationships to LPDrawdown, LPDetails, and Document models
- [ ] Add status enum (Sent, Failed, Viewed)
- [ ] Create Pydantic schemas in `backend/app/schemas/drawdown.py`

### 1.3 Database Migrations (HIGH PRIORITY)

**File**: `backend/alembic/versions/xxx_enhance_drawdown_tables.py`
**Dependencies**: Enhanced models
**Estimated Time**: 0.5 days

**Tasks**:

- [ ] Create migration to add missing fields to LP_DRAWDOWNS table
- [ ] Create migration for DRAWDOWN_NOTICES table
- [ ] Add proper indexes for performance
- [ ] Test migration up/down operations

## Phase 2: Core API Implementation

### 2.1 Drawdown Generation API (HIGH PRIORITY)

**File**: `backend/app/api/drawdowns.py` (new file)
**Dependencies**: Enhanced drawdown models, Fund API
**Estimated Time**: 3 days

**Endpoints to Implement**:

- [ ] `POST /drawdowns/generate_drawdowns` - Generate drawdowns for all LPs
- [ ] `GET /drawdowns` - List drawdowns with filtering (fund_id, status)
- [ ] `GET /drawdowns/{drawdown_id}` - Get specific drawdown details
- [ ] `GET /drawdowns/{drawdown_id}/status` - Get drawdown status
- [ ] `PUT /drawdowns/{drawdown_id}/cancel` - Cancel drawdown

**Business Logic**:

- [ ] Calculate pro-rata amounts based on LP commitments
- [ ] Generate drawdown records for all LPs in a fund
- [ ] Validate fund exists and has LPs
- [ ] Handle date validations and business rules
- [ ] Add proper error handling and status codes

### 2.2 Drawdown Preview API (HIGH PRIORITY)

**File**: `backend/app/api/drawdowns.py`
**Dependencies**: Fund and LP models
**Estimated Time**: 2 days

**Endpoints to Implement**:

- [ ] `POST /drawdowns/preview` - Generate preview without persisting

**Business Logic**:

- [ ] Calculate drawdown amounts based on percentage or total amount
- [ ] Generate preview data for all LPs
- [ ] Calculate summary statistics (total LPs, total amount, average)
- [ ] Return temporary preview ID for tracking
- [ ] No database persistence for preview

### 2.3 Drawdown Status Management API (MEDIUM PRIORITY)

**File**: `backend/app/api/drawdowns.py`
**Dependencies**: Drawdown models
**Estimated Time**: 1 day

**Endpoints to Implement**:

- [ ] `PATCH /drawdowns/{drawdown_id}/status-transition` - Update drawdown status
- [ ] `GET /drawdowns/due_date` - Get drawdowns by quarter range

**Business Logic**:

- [ ] Implement status transition validation
- [ ] Track status change history
- [ ] Send notifications on status changes
- [ ] Add audit logging for status changes

## Phase 3: Document Generation and Email Integration

### 3.1 Excel Generation Service (HIGH PRIORITY)

**File**: `backend/app/services/excel_generator.py` (new file)
**Dependencies**: Drawdown models, template files
**Estimated Time**: 2 days

**Tasks**:

- [ ] Create Excel template for drawdown notices
- [ ] Implement Excel generation using openpyxl or xlsxwriter
- [ ] Generate individual Excel files per LP
- [ ] Include all required fields from specification
- [ ] Store generated files in document repository
- [ ] Link generated documents to drawdown notices

### 3.2 Email Integration Service (HIGH PRIORITY)

**File**: `backend/app/services/email_service.py` (enhance existing)
**Dependencies**: Google Gmail API integration (already exists)
**Estimated Time**: 2 days

**Tasks**:

- [ ] Enhance existing Gmail service for drawdown emails
- [ ] Create email templates for capital call notices
- [ ] Implement bulk email sending for all LPs
- [ ] Track email delivery status
- [ ] Handle email failures and retries
- [ ] Store email logs in audit system

### 3.3 Document Storage Integration (MEDIUM PRIORITY)

**File**: `backend/app/services/document_service.py` (enhance existing)
**Dependencies**: Google Drive integration, Document model
**Estimated Time**: 1 day

**Tasks**:

- [ ] Store generated Excel files in Google Drive
- [ ] Create document records in database
- [ ] Link documents to drawdown notices and LPs
- [ ] Implement document retrieval and download

## Phase 4: Integration and Testing

### 4.1 Update Main Application (HIGH PRIORITY)

**File**: `backend/main.py`
**Dependencies**: Drawdown API router
**Estimated Time**: 0.5 days

**Tasks**:

- [ ] Add drawdown router to main FastAPI app
- [ ] Update API documentation
- [ ] Add proper error handling middleware

### 4.2 Unit Tests (HIGH PRIORITY)

**Files**: `backend/tests/test_drawdowns.py`, `backend/tests/test_drawdown_services.py`
**Dependencies**: Complete implementation
**Estimated Time**: 3 days

**Test Coverage**:

- [ ] Drawdown model tests
- [ ] Drawdown API endpoint tests
- [ ] Drawdown calculation logic tests
- [ ] Excel generation tests
- [ ] Email service tests
- [ ] Status transition tests
- [ ] Error handling tests

### 4.3 Integration Tests (MEDIUM PRIORITY)

**File**: `backend/tests/test_drawdown_integration.py`
**Dependencies**: Complete implementation
**Estimated Time**: 2 days

**Test Scenarios**:

- [ ] End-to-end drawdown generation flow
- [ ] Email sending and document generation
- [ ] Status transition workflows
- [ ] Error handling and rollback scenarios

## Phase 5: Business Logic and Calculations

### 5.1 Drawdown Calculation Engine (HIGH PRIORITY)

**File**: `backend/app/services/drawdown_calculator.py` (new file)
**Dependencies**: LP and Fund models
**Estimated Time**: 2 days

**Tasks**:

- [ ] Implement pro-rata calculation logic
- [ ] Calculate remaining commitments
- [ ] Handle management fees calculations
- [ ] Implement stamp duty calculations
- [ ] Add validation for calculation results
- [ ] Create comprehensive unit tests for calculations

### 5.2 Quarterly Reminder System (MEDIUM PRIORITY)

**File**: `backend/app/services/reminder_service.py` (new file)
**Dependencies**: Email service, Compliance Task model
**Estimated Time**: 1 day

**Tasks**:

- [ ] Create scheduled job for quarterly reminders
- [ ] Send email to Fund Manager on 7th of every quarter
- [ ] Create compliance tasks for capital call reminders
- [ ] Integrate with existing task management system

## Dependencies and Blockers

### Upstream Dependencies

- **CRITICAL**: Fund Registration implementation (fund_id required)
- **HIGH**: Enhanced LP Details (commitment amounts, fund relationships)

### Downstream Impact

- **CRITICAL**: Payment Reconciliation depends on drawdown data
- **HIGH**: Unit Allotment depends on drawdown completion
- **MEDIUM**: SEBI reporting uses drawdown information

### External Dependencies

- Google Gmail API (already configured)
- Google Drive API (already configured)
- Excel template design and approval

## Implementation Priority

### Phase 1 (Week 1): Database Foundation

1. Enhance LP Drawdowns Model - **CRITICAL**
2. Create Drawdown Notices Model - **CRITICAL**
3. Database Migrations - **CRITICAL**

### Phase 2 (Week 2): Core APIs

1. Drawdown Generation API - **CRITICAL**
2. Drawdown Preview API - **CRITICAL**
3. Status Management API - **HIGH**

### Phase 3 (Week 3): Document and Email

1. Excel Generation Service - **CRITICAL**
2. Email Integration Service - **CRITICAL**
3. Document Storage Integration - **HIGH**

### Phase 4 (Week 4): Testing and Calculations

1. Drawdown Calculation Engine - **CRITICAL**
2. Unit Tests - **CRITICAL**
3. Integration Tests - **HIGH**

### Phase 5 (Week 5): Advanced Features

1. Quarterly Reminder System - **MEDIUM**
2. Performance Optimization - **MEDIUM**
3. Documentation - **MEDIUM**

## Success Criteria

- [ ] Fund Manager can generate capital call for entire fund
- [ ] Individual drawdown notices generated for each LP
- [ ] Excel files automatically created and stored
- [ ] Emails sent to all LPs with attachments
- [ ] Drawdown status tracking working
- [ ] Preview functionality working without persistence
- [ ] All calculations accurate and validated
- [ ] 90%+ test coverage on new functionality
- [ ] Performance acceptable for 100+ LPs

## Risk Mitigation

### Technical Risks

- **Excel generation performance**: Implement async processing for large LP lists
- **Email delivery failures**: Implement retry mechanism and failure tracking
- **Calculation errors**: Extensive unit testing and validation

### Business Risks

- **Incorrect calculations**: Multiple validation layers and audit trails
- **Email compliance**: Ensure proper email headers and delivery tracking
- **Data consistency**: Implement proper transaction management

### Operational Risks

- **Template changes**: Version control for Excel templates
- **Email limits**: Monitor and handle Gmail API rate limits
- **Storage limits**: Monitor Google Drive storage usage
