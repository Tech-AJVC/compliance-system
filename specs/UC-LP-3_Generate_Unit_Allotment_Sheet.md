# UC-LP-3 — Generate Unit-Allotment Sheet

> **Category:** Limited Partner Workflows  
> **Primary actor:** Compliance Officer  
> **Secondary actors:** Fund Manager, RTA

---

## 1. References

| Doc | Section                                                  |
| --- | -------------------------------------------------------- |
| PRD | §3.3 – "Unit Allotment"                                  |
| TRD | §14 – Allotment Generator Service                        |
| UX  | _Generate Unit Allotment_ modal, Allotment status badges |

### PRD Extract

> _"Upon confirmation of drawdown payments the system shall generate an allotment sheet allocating units proportionally to payments received …"_

### TRD Extract

> _Service `allotment_generator` subscribes to event `DRAW_DOWN_COMPLETED`, creates Excel using openpyxl …_

### UX Extract

> Modal requiring DP details (DPID, Client ID) + preview of share counts.

---

## Use Case

#### Trigger

- Payment status for all LP's becomes "Paid". Date to do this is 20 days post to drawdown Contribution Due Date

#### Behaviour

- Search over all Drawdown Notices, CML, CA and Fund Details DB for all LP's extract the required values for Unit Allotment
- Compute units = Drawdown Amount ÷ NAV.
- Populate Excel allotment template with all statutory fields (ISIN, DP-ID, etc.).
- Save the sheet to the Repository
- Email the LP and Fund Manager that units have been allotted
- Record one audit-log entry for the Unit Allotment

### Figma UI Screen Inputs

#### Unit Allotment Status Interface

- **Allotment Status Badge**: Visual indicator
  - Allotment Done (green with checkmark)
- **Progress Timeline**: Step 3 in the 4-step process
  - Shows "100% units allotted" when complete
  - Shows "No units allotted yet" when pending

#### Unit Allotment Processing

- **Automated Trigger**: System automatically processes when all payments are "Paid"
- **Calculation Display**: Shows unit computation (Drawdown Amount ÷ NAV)
- **Excel Template Population**: Backend process with statutory fields
- **Confirmation Notifications**: Success indicators for LP and Fund Manager emails

#### Document Repository Integration

- **Allotment Sheet Storage**: Automatic saving to repository
- **Document Linking**: Connection to LP profiles and drawdown records
- **Audit Trail Display**: Visual confirmation of allotment completion

## PROCESS SECTION - LP UNIT ALLOTMENT

This process handles the generation of unit allotment sheets for Limited Partners after payment reconciliation is complete, by combining data from multiple sources to calculate and allocate units.

### Subprocess: LP Depository Information (from Client Master List)

- **Output**: CLID, Depository, DPID, FIRST-HOLDER-PAN (Excel)
- **Input Source**: Client Master List
- **Input Format**: PDF
- **Transformation**: Direct
- **Input Field**: Client ID, Depository Name, DP (last 8 digits), PAN
- **Formula**: N/A
- **DB vs PDF Analysis**: ✅ These fields should be stored in LP_DETAILS table during LP registration and read from DB

### Subprocess: LP Name Information (from Contribution Agreement)

- **Output**: FIRST-HOLDER-NAME, MGMT FEES, COMMITTED AMT (Excel)
- **Input Source**: Contribution Agreement
- **Input Format**: PDF
- **Transformation**: Direct + Computation
- **Input Field**: Name and Address of Contributor, Commitment Amount
- **Formula**: MGMT FEES = If the quarter since start is even, 1% of commitment amount + GST
- **DB vs PDF Analysis**: ✅ Name and Commitment Amount should be read from LP_DETAILS table, MGMT FEES calculated based on quarter

### Subprocess: Drawdown Information (from Drawdown Notice)

- **Output**: AMT ACCEPTED, DRAWDOWN AMOUNT, DRAWDOWN DATE, DRAWDOWN QUARTER (Excel)
- **Input Source**: Drawdown Notice
- **Input Format**: PDF
- **Transformation**: Direct + Computation
- **Input Field**: Amount Due, Drawdown Date
- **Formula**: DRAWDOWN QUARTER = Quarter of Drawdown Date
- **DB vs PDF Analysis**: ✅ Read from LP_DRAWDOWNS table instead of re-parsing PDFs

### Subprocess: Fund NAV Information (from Fund Details)

- **Output**: NAV/F. VALUE (Excel)
- **Input Source**: Fund Details
- **Input Format**: PDF
- **Transformation**: Direct
- **Input Field**: NAV is 100
- **Formula**: N/A
- **DB vs PDF Analysis**: ✅ Read from FUND_DETAILS.nav field

### Subprocess: Unit Calculation and Fees

- **Output**: ALLOTED UNIT, STAMP DUTY (Excel)
- **Input Source**: Drawdown Notice
- **Input Format**: PDF
- **Transformation**: Computation
- **Input Field**: Amount Due, NAV
- **Formula**:
  - ALLOTED UNIT = Amount Due / NAV
  - STAMP DUTY = Amount Due \* 0.005%
- **DB vs PDF Analysis**: ✅ Calculate using data from LP_DRAWDOWNS and FUND_DETAILS tables

### Subprocess: Empty Fields (Placeholders)

- **Output**: THIRD-HOLDER-NAME, THIRD-HOLDER-PAN, BANK ACCOUNT NO, BANK NAME, DATE OF ALLOTMENT, IFSC CODE, MICR CODE, SECOND-HOLDER-NAME, SECOND-HOLDER-PAN, STATUS (Excel)
- **Input Source**: NA
- **Input Format**: PDF
- **Transformation**: Direct
- **Input Field**: NA
- **Formula**: N/A
- **DB vs PDF Analysis**: ✅ These are empty columns or system-generated fields

### Missing Upstream Fields Analysis:

- ⚠️ **DPID, Client ID, Depository**: Required from Client Master List but may not be captured in LP Details Registration
- ✅ **LP names and commitment amounts**: Available from LP Details Registration
- ✅ **Drawdown amounts and dates**: Available from Drawdown Notice process
- ✅ **NAV**: Available from Fund Registration process

### Downstream Usage:

- Unit Allotment data is used by:
  - InVi Filing (unit quantities for foreign investors)
  - SEBI Activity Report (units allotted information)
  - LP status tracking (allotment completion)

### DB vs PDF Optimization:

- ✅ **LP names**: Read from LP_DETAILS table
- ✅ **Commitment amounts**: Read from LP_DETAILS table
- ✅ **Drawdown amounts**: Read from LP_DRAWDOWNS table
- ✅ **Fund NAV**: Read from FUND_DETAILS table
- ⚠️ **Depository details**: Should be captured during LP registration for reuse

### Critical Missing Fields for This Process:

1. **DPID**: Required for unit allotment but may not be in LP_DETAILS table
2. **Client ID**: Required for unit allotment but may not be in LP_DETAILS table
3. **Depository Name**: Required for unit allotment but may not be in LP_DETAILS table

## 2. Functional Requirements

1. **Trigger** – When all LPs for a drawdown are `Acceptance Pending` or `Wire Pending`? (ambiguity – see below).
2. **Computation** – Units = Payment / Unit Price (configurable).
3. **Output** – Excel & PDF (format per SEBI spec).
4. **Distribution** – Email to RTA & LP.

## 3. Technical Requirements

- Use openpyxl for XLSX, ReportLab for PDF.
- Store documents in S3 bucket `allotments/` + DB link.
- Event-driven via pub/sub.

DB Schema

───────────────────────────── 14. UNIT_ALLOTMENTS ─────────────────────────────
• allotment_id INT PK
• drawdown_id INT FK → LP_DRAWDOWNS
• lp_id INT FK → LP_DETAILS
• clid VARCHAR(60)
• depository VARCHAR(60)
• dpid VARCHAR(20)
• first_holder_name VARCHAR(255)
• first_holder_pan VARCHAR(20)
• second_holder_name VARCHAR(255) NULL
• second_holder_pan VARCHAR(20) NULL
• mgmt_fees DECIMAL(18,2)
• committed_amt DECIMAL(18,2)
• amt_accepted DECIMAL(18,2)
• drawdown_amount DECIMAL(18,2)
• drawdown_date DATE
• drawdown_quarter VARCHAR(20)
• nav_value DECIMAL(10,2) -- "NAV/F VALUE"
• allotted_units INT
• stamp_duty DECIMAL(10,2)
• third_holder_name VARCHAR(255)
• third_holder_pan VARCHAR(20)
• status VARCHAR(40) DEFAULT 'Generated'
• created_at TIMESTAMPTZ DEFAULT now()
• bank_ifsc: VARCHAR(15)
• bank_account_name: VARCHAR(255)
• bank_account_no: VARCHAR(50)
• micr_code: VARCHAR(50)

API's

6. UNIT ALLOTMENTS

Resource: /unit-allotments
POST /unit-allotments/generate
JSON
{
"fund_id": 12,
"drawdown_quarter": "FY25Q1",
"date_of_allotment": "2025-07-20"
}

Returns list
JSON
{
"allotment_id": 23001,
"lp_id": 101,
"clid": "1234567",
"depository": "CDSL",
"dpid": "12345678",
"first_holder_name": "Main Street Capital",
"first_holder_pan": "AAACM5588P",
"second_holder_name": null,
"second_holder_pan": null,
"third_holder_name": null,
"third_holder_pan": null,
"mgmt_fees": 118000.00,
"committed_amt": 5000000.00,
"amt_accepted": 1000000.00,
"drawdown_amount": 1000000.00,
"drawdown_date": "2025-05-04",
"drawdown_quarter": "FY25Q1",
"nav_value": 100.00,
"allotted_units": 10000,
"stamp_duty": 75.00,
"bank_account_no": "0031182000344",
"bank_name": "ICICI Bank",
"ifsc_code": "ICIC0003311",
"micr_code": "110002331",
"date_of_allotment": "2025-07-20",
"status": "Generated"
}
GET /unit-allotments?fund_id=12&status=Generated GET /unit-allotments/{allotment_id}
PUT /unit-allotments/{allotment_id}/upload-cdsl-pdf (File Upload)
Request: multipart/form-data { file: <cdsl_consolidated.pdf> }
Returns 204 No Content.

## 4. Contradictions

| #   | Description                                                                              | PRD  | TRD | Resolution                       |
| --- | ---------------------------------------------------------------------------------------- | ---- | --- | -------------------------------- |
| 1   | Trigger condition wording differs (PRD: after _all_ payments, TRD: after _each_ payment) | §3.3 | §14 | Align on "all payments received" |

## 5. Tasks

### Human

- [ ] Confirm trigger condition.
- [ ] Approve template.

### AI

- [ ] Implement `allotment_generator` worker.
- [ ] Unit tests on calculation logic.
- [ ] FE: Unit Allotment Preview screen.

---

_Status: draft._

# WORKPLAN - UNIT ALLOTMENT SHEET IMPLEMENTATION

## Overview

This workplan details the implementation of Unit Allotment Sheet generation functionality, building on the Payment Reconciliation system to calculate and allocate units to LPs after successful payments.

## Phase 1: Database Schema Enhancements

### 1.1 Enhance LP Drawdowns Model for Unit Allocation (HIGH PRIORITY)

**File**: `backend/app/models/lp_drawdowns.py`
**Dependencies**: Existing LPDrawdown model, Payment Reconciliation
**Estimated Time**: 1 day

**Tasks**:

- [ ] Add unit allocation fields to existing LPDrawdown model:
  - `units_allocated`, `unit_price`, `allocation_date`, `allocation_status`
- [ ] Add unit allocation status enum (Pending, Calculated, Allocated, Completed)
- [ ] Update relationships and constraints
- [ ] Create enhanced Pydantic schemas for unit allocation

### 1.2 Create Unit Allotment Model (HIGH PRIORITY)

**File**: `backend/app/models/unit_allotment.py` (new file)
**Dependencies**: LPDrawdown, Fund models
**Estimated Time**: 1 day

**Tasks**:

- [ ] Create `UnitAllotment` SQLAlchemy model
- [ ] Add fields: allotment_id, fund_id, drawdown_quarter, total_amount_received, total_units_allocated, nav_per_unit, allotment_date, status
- [ ] Create relationships to Fund and LPDrawdown models
- [ ] Add allotment status enum (Draft, Calculated, Approved, Completed)
- [ ] Create Pydantic schemas in `backend/app/schemas/allotment.py`

### 1.3 Database Migrations (HIGH PRIORITY)

**File**: `backend/alembic/versions/xxx_add_unit_allotment_tables.py`
**Dependencies**: Enhanced models
**Estimated Time**: 0.5 days

**Tasks**:

- [ ] Create migration to add unit allocation fields to LP_DRAWDOWNS
- [ ] Create migration for UNIT_ALLOTMENT table
- [ ] Add proper indexes for performance
- [ ] Test migration up/down operations

## Phase 2: Unit Calculation Engine

### 2.1 Unit Calculation Service (HIGH PRIORITY)

**File**: `backend/app/services/unit_calculator.py` (new file)
**Dependencies**: Payment Reconciliation, Fund models
**Estimated Time**: 3 days

**Tasks**:

- [ ] Implement unit calculation algorithms based on NAV
- [ ] Calculate pro-rata unit allocation based on payment amounts
- [ ] Handle partial payments and adjustments
- [ ] Validate calculation results against fund rules
- [ ] Implement rounding and precision handling
- [ ] Add comprehensive unit tests for calculations

### 2.2 NAV Management Service (MEDIUM PRIORITY)

**File**: `backend/app/services/nav_service.py` (new file)
**Dependencies**: Fund models, Portfolio valuations
**Estimated Time**: 2 days

**Tasks**:

- [ ] Implement NAV calculation based on fund performance
- [ ] Handle NAV updates and versioning
- [ ] Validate NAV against market conditions
- [ ] Store NAV history for audit purposes
- [ ] Create NAV approval workflow
- [ ] Integration with portfolio valuation data

### 2.3 Unit Allocation Engine (HIGH PRIORITY)

**File**: `backend/app/services/unit_allocator.py` (new file)
**Dependencies**: Unit Calculator, Payment status
**Estimated Time**: 2 days

**Tasks**:

- [ ] Process all paid LPs for unit allocation
- [ ] Handle allocation rules and constraints
- [ ] Validate allocation against available units
- [ ] Implement allocation approval workflow
- [ ] Track allocation history and changes
- [ ] Generate allocation summary reports

## Phase 3: API Implementation

### 3.1 Unit Allotment API (HIGH PRIORITY)

**File**: `backend/app/api/unit_allotment.py` (new file)
**Dependencies**: Unit allocation services
**Estimated Time**: 3 days

**Endpoints to Implement**:

- [ ] `POST /unit-allotments/calculate` - Calculate units for paid LPs
- [ ] `GET /unit-allotments` - List allotment sessions
- [ ] `GET /unit-allotments/{allotment_id}` - Get allotment details
- [ ] `POST /unit-allotments/{allotment_id}/approve` - Approve allotment
- [ ] `GET /unit-allotments/{allotment_id}/sheet` - Generate allotment sheet

**Business Logic**:

- [ ] Validate all LPs have completed payments
- [ ] Calculate units based on current NAV
- [ ] Handle allocation approval workflow
- [ ] Generate Excel allotment sheets
- [ ] Track allotment status changes

### 3.2 NAV Management API (MEDIUM PRIORITY)

**File**: `backend/app/api/nav.py` (new file)
**Dependencies**: NAV service
**Estimated Time**: 2 days

**Endpoints to Implement**:

- [ ] `POST /nav` - Set/update NAV for fund
- [ ] `GET /nav/current` - Get current NAV
- [ ] `GET /nav/history` - Get NAV history
- [ ] `POST /nav/approve` - Approve NAV changes

## Phase 4: Document Generation

### 4.1 Allotment Sheet Generator (HIGH PRIORITY)

**File**: `backend/app/services/allotment_sheet_generator.py` (new file)
**Dependencies**: Unit Allotment models, Excel generation
**Estimated Time**: 3 days

**Tasks**:

- [ ] Create Excel template for unit allotment sheet
- [ ] Generate allotment sheet with all LP details
- [ ] Include calculation formulas and validations
- [ ] Format sheet according to regulatory requirements
- [ ] Store generated sheets in document repository
- [ ] Create PDF version for distribution

### 4.2 Allotment Certificate Generator (MEDIUM PRIORITY)

**File**: `backend/app/services/certificate_generator.py` (new file)
**Dependencies**: Unit Allotment models
**Estimated Time**: 2 days

**Tasks**:

- [ ] Generate individual unit certificates for LPs
- [ ] Create certificate templates with fund branding
- [ ] Include all required legal and regulatory information
- [ ] Digital signature integration
- [ ] Batch certificate generation
- [ ] Certificate delivery via email

## Phase 5: Integration and Workflow

### 5.1 Payment-to-Allotment Workflow (HIGH PRIORITY)

**File**: `backend/app/services/payment_allotment_workflow.py` (new file)
**Dependencies**: Payment Reconciliation, Unit Allocation
**Estimated Time**: 2 days

**Tasks**:

- [ ] Create automated workflow from payment completion to unit allocation
- [ ] Implement business rules for allocation triggers
- [ ] Handle workflow status tracking
- [ ] Add approval gates and notifications
- [ ] Implement rollback capabilities
- [ ] Integration with existing task management

### 5.2 Notification and Communication (MEDIUM PRIORITY)

**File**: `backend/app/services/allotment_notifications.py` (new file)
**Dependencies**: Email service, Unit Allotment models
**Estimated Time**: 1 day

**Tasks**:

- [ ] Send allotment completion notifications to LPs
- [ ] Send allotment sheets and certificates via email
- [ ] Notify fund managers of allotment status
- [ ] Create allotment summary reports
- [ ] Handle notification preferences and delivery tracking

## Phase 6: Testing and Integration

### 6.1 Update Main Application (HIGH PRIORITY)

**File**: `backend/main.py`
**Dependencies**: All API routers
**Estimated Time**: 0.5 days

**Tasks**:

- [ ] Add unit allotment routers to main FastAPI app
- [ ] Add NAV management router
- [ ] Update API documentation
- [ ] Configure background task scheduling

### 6.2 Unit Tests (HIGH PRIORITY)

**Files**: Multiple test files for each component
**Dependencies**: Complete implementation
**Estimated Time**: 3 days

**Test Coverage**:

- [ ] Unit calculation algorithm tests
- [ ] NAV management tests
- [ ] Allotment workflow tests
- [ ] API endpoint tests
- [ ] Document generation tests
- [ ] Integration workflow tests

### 6.3 Integration Tests (HIGH PRIORITY)

**File**: `backend/tests/test_unit_allotment_integration.py`
**Dependencies**: Complete implementation
**Estimated Time**: 2 days

**Test Scenarios**:

- [ ] End-to-end payment to allotment flow
- [ ] Unit calculation accuracy tests
- [ ] Document generation and delivery
- [ ] Workflow state management
- [ ] Error handling and rollback scenarios

## Dependencies and Blockers

### Upstream Dependencies

- **CRITICAL**: Payment Reconciliation completion (payment confirmation required)
- **CRITICAL**: Fund Registration with NAV information
- **HIGH**: Capital Call Notice for drawdown context

### Downstream Impact

- **HIGH**: SEBI reporting uses unit allocation data
- **MEDIUM**: LP portfolio tracking depends on unit allocation
- **MEDIUM**: Fund performance calculations use unit data

### External Dependencies

- Fund NAV calculation methodology approval
- Unit certificate template design and legal approval
- Regulatory compliance for unit allocation process

## Implementation Priority

### Phase 1 (Week 1): Database and Calculations

1. Enhance LP Drawdowns Model - **CRITICAL**
2. Create Unit Allotment Model - **CRITICAL**
3. Unit Calculation Service - **CRITICAL**
4. Database Migrations - **CRITICAL**

### Phase 2 (Week 2): Core APIs and Engine

1. Unit Allocation Engine - **CRITICAL**
2. Unit Allotment API - **CRITICAL**
3. NAV Management Service - **HIGH**

### Phase 3 (Week 3): Document Generation

1. Allotment Sheet Generator - **CRITICAL**
2. NAV Management API - **HIGH**
3. Allotment Certificate Generator - **MEDIUM**

### Phase 4 (Week 4): Workflow and Integration

1. Payment-to-Allotment Workflow - **CRITICAL**
2. Notification and Communication - **HIGH**
3. Unit Tests - **CRITICAL**

### Phase 5 (Week 5): Testing and Optimization

1. Integration Tests - **CRITICAL**
2. Performance Optimization - **MEDIUM**
3. Documentation - **MEDIUM**

## Success Criteria

- [ ] Units calculated accurately based on payments and NAV
- [ ] Allotment sheets generated automatically after payment completion
- [ ] Unit certificates created and delivered to LPs
- [ ] NAV management system working properly
- [ ] Workflow automation from payment to allotment functioning
- [ ] All calculations auditable and traceable
- [ ] 90%+ test coverage on new functionality
- [ ] Performance acceptable for 100+ LPs per allotment

## Risk Mitigation

### Technical Risks

- **Calculation accuracy**: Multiple validation layers and audit trails
- **NAV data integrity**: Version control and approval workflows
- **Document generation performance**: Async processing for large batches

### Business Risks

- **Incorrect unit allocation**: Comprehensive validation and approval process
- **Regulatory compliance**: Legal review of allocation process and documents
- **NAV disputes**: Clear NAV calculation methodology and audit trail

### Operational Risks

- **Manual intervention needs**: Automated workflow with manual override capabilities
- **Document delivery failures**: Multiple delivery channels and confirmation tracking
- **Approval bottlenecks**: Clear approval workflows with escalation procedures
