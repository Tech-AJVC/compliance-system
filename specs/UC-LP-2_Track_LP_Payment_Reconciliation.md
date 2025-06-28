# UC-LP-2 — Track LP Payment & Reconciliation

> **Use-case category:** Limited Partner Workflows  
> **Primary actor:** Compliance Officer  
> **Secondary actors:** Fund Manager, Finance Team

---

## 1. Source References

| Document            | Section(s)                                                            |
| ------------------- | --------------------------------------------------------------------- |
| **PRD Phase-2**     | §3.2 – "LP Payment Tracking"                                          |
| **TRD Phase-2**     | §13 – Bank API integration                                            |
| **UX Requirements** | Screens: "LP list (drawdown status column)", "Drawdown Details Modal" |

### 1.1 PRD Extract

> _"The system shall ingest bank statement data and automatically mark LP payments against drawdown invoices, updating **Remaining Drawdown** in real time..."_  
> ...

### 1.2 TRD Extract

DB Schema

11. LP_PAYMENTS (link individual credits to drawdowns)
    ─────────────────────────────
    • lp_payment_id: BIGINT PK
    • lp_id: INT FK→LP_DETAILS
    • drawdown_id: INT FK→LP_DRAWDOWNS
    • txn_id: BIGINT FK→FUND_BANK_TRANSACTIONS
    • paid_amount: DECIMAL(18,2)
    • matched_by_rule: VARCHAR(50) -- "ref-contains-pan" etc.
    • matched_at: TIMESTAMP
    • status: VARCHAR(20) DEFAULT 'Paid' -- Paid / Shortfall / Over-payment

───────────────────────────── 12. PAYMENT_RECONCILIATION
─────────────────────────────
• recon_id: BIGINT PK
• drawdown_quarter: VARCHAR(20)
• total_expected: DECIMAL(18,2)
• total_received: DECIMAL(18,2)
• run_timestamp: TIMESTAMP
• report_document_id: INT FK→DOCUMENTS

APIs

Resource: /reconciliations
POST /reconciliations/run
JSON
{
"fund_id": 12,
"drawdown_quarter": "FY25Q1"
}

Returns
JSON
{
"recon_id": 9002,
"fund_id": 12,
"drawdown_quarter": "FY25Q1",
"total_expected": 65000000.00,
"total_received": 61000000.00,
"overall_status": "In-Progress",
"created_at": "2025-05-06T02:10:11Z",
"per_lp": [
{
"lp_id": 101,
"expected": 1000000.00,
"received": 1000000.00,
"contributor_check": true,
"amount_check": true,
"status": "Paid"
},
{
"lp_id": 102,
"expected": 1500000.00,
"received": 0.00,
"contributor_check": false,
"amount_check": false,
"status": "Pending"
}
]
}
GET /reconciliations?fund_id=12&overall_status=In-Progress
GET /reconciliations/{recon_id}

### 1.3 UX Extract

> Status badges: _Wire Pending_ → _Acceptance Pending_ → _Allotment Pending_ → _Allotment Done_.

---

### Use Case

#### Trigger

- Drawdown notice generated till payment received. Maximum reminder can go till 14 days later, ie, expiry date of drawdown, remind two times in this 14 days
- Add a button to send a payment reminder given LP details

#### Behaviour

- Match credits to drawdown notices using Investor Name + amount.
- Update payment status to Paid / Shortfall / Over-payment.
- Surface real-time dashboard of Paid vs Pending for Fund team.
- Emit Payment status via email to Fund manager

---

### Figma UI Screen Inputs

#### Payment Status Tracking Interface

- **Status Badges**: Visual indicators for payment progression
  - Wire Pending (orange)
  - Acceptance Pending (orange)
  - Allotment Pending (orange)
  - Allotment Done (green)

#### Payment Reconciliation Dashboard

- **LP Payment Table**: Table showing payment status for each LP
  - LP Name
  - Expected Amount
  - Received Amount
  - Payment Status
  - Days Remaining (until deadline)
- **Payment Reminder Button**: Action to send payment reminders
- **Bulk Status Update**: Interface for updating multiple payment statuses

#### Payment Status Workflow

- **Progress Timeline**: Visual representation of payment stages
  1. Notice Sent
  2. Payment Due
  3. Payment Received
  4. Amount Reconciled
- **Status Update Form**: Interface for manual status updates
- **Payment Confirmation**: Success/failure indicators

## PROCESS SECTION - PAYMENT RECONCILIATION

This process handles the reconciliation of LP payments against drawdown notices by extracting payment information from bank account statements and matching them with expected amounts.

### Subprocess: Payment Information Extraction (from Account Statement)

- **Output**: Contributor, Value (Excel)
- **Input Source**: Account Statement
- **Input Format**: PDF
- **Transformation**: Computation
- **Input Field**: Description, Credit
- **Formula**:
  - Contributor = EXTRACTNAME(Description)
  - Value = EXTRACTVALUE(Credit)
- **DB vs PDF Analysis**: ⚠️ Account statements need to be processed for each reconciliation run, but extracted data should be stored in FUND_BANK_TRANSACTIONS table

### Subprocess: Contributor Name Matching

- **Output**: Contributor Check (Excel)
- **Input Source**: Drawdown Notice + Payment Reconciliation
- **Input Format**: Excel
- **Transformation**: Computation
- **Input Field**: Investor (from Drawdown), Contributor (from Payment)
- **Formula**: Check IF(Investor = Contributor)
- **DB vs PDF Analysis**: ✅ Read Investor names from LP_DETAILS table and compare with extracted payment contributor names

### Subprocess: Amount Matching

- **Output**: Amount Check (Excel)
- **Input Source**: Drawdown Notice + Payment Reconciliation
- **Input Format**: Excel
- **Transformation**: Computation
- **Input Field**: Amount Due (from Drawdown), Value (from Payment)
- **Formula**: Check IF(Amount Due = Value)
- **DB vs PDF Analysis**: ✅ Read Amount Due from LP_DRAWDOWNS table and compare with extracted payment amounts

### Subprocess: Final Payment Reconciliation

- **Output**: Payment Reconciliation (Excel)
- **Input Source**: Payment Reconciliation
- **Input Format**: Excel
- **Transformation**: Computation
- **Input Field**: Contributor Check, Amount Check
- **Formula**: Check IF(Contributor Check AND Amount Check = TRUE)
- **DB vs PDF Analysis**: ✅ Final reconciliation status stored in LP_PAYMENTS table

### Missing Upstream Fields Analysis:

- ✅ **Drawdown amounts**: Available from Drawdown Notice process
- ✅ **LP names**: Available from LP Details Registration process
- ✅ **Expected payment amounts**: Available from Drawdown Notice process
- ✅ No missing upstream dependencies identified

### Downstream Usage:

- Payment Reconciliation data is used by:
  - Unit Allotment (payment confirmation before unit allocation)
  - SEBI Activity Report (actual funds received calculations)
  - InVi Filing (actual foreign investment amounts)

### DB vs PDF Optimization:

- ✅ **LP names for matching**: Read from LP_DETAILS table instead of re-parsing Contribution Agreements
- ✅ **Expected amounts**: Read from LP_DRAWDOWNS table instead of re-parsing Drawdown Notices
- ⚠️ **Bank statement processing**: Must be done for each reconciliation run, but results should be stored in FUND_BANK_TRANSACTIONS table
- ✅ **Reconciliation results**: Store in LP_PAYMENTS table for future reference

### Payment Reconciliation Window:

- **Process runs daily for 14 days** after drawdown due date
- **Automatic expiry** after 14 days if payment not received
- **Manual reconciliation** possible for late payments

## 2. Functional Requirements

1. **Bank Transaction Ingestion** (auto & manual CSV upload fallback).
2. **Matching Algorithm** – match credit line item to LP by `UTR` or `Expected Amount ± tolerance`.
3. **Status Transitions** – update `drawdown_lp.status` accordingly.
4. **Reconciliation Report** – downloadable CSV.

## 3. Technical Requirements

- Integrate HDFC Corporate API (OAuth2 flow).
- Store raw transactions in `bank_txn` table (idempotent).
- Cron + webhook hybrid.

## 4. Contradictions

| #   | Issue                                           | PRD  | UX  | Action                  |
| --- | ----------------------------------------------- | ---- | --- | ----------------------- |
| 1   | PRD allows ±₹100 tolerance; TRD hard-codes ±₹50 | §3.2 | N/A | Confirm tolerance value |

## 5. Task Breakdown

### Human

- [ ] Finalise bank API credentials.
- [ ] Decide tolerance value.

### AI

- [ ] Build `bank_sync` service + unit tests.
- [ ] Matching algorithm implementation.
- [ ] Reconciliation report endpoint + FE table.

---

_Status: draft._

# WORKPLAN - PAYMENT RECONCILIATION IMPLEMENTATION

## Overview

This workplan details the implementation of LP Payment Reconciliation functionality to track and match payments against drawdown notices, building on the Capital Call Notice system.

## Phase 1: Database Schema Implementation

### 1.1 Create Bank Transactions Model (HIGH PRIORITY)

**File**: `backend/app/models/bank_transaction.py` (new file)
**Dependencies**: Fund Details model
**Estimated Time**: 1 day

**Tasks**:

- [ ] Create `BankTransaction` SQLAlchemy model
- [ ] Add fields: txn_id, fund_id, txn_date, value_date, narration, amount, currency, balance, bank_reference, raw_payload, imported_at
- [ ] Create relationships to Fund model
- [ ] Add proper field validations and constraints
- [ ] Create Pydantic schemas in `backend/app/schemas/bank.py`

### 1.2 Create Payment Reconciliation Model (HIGH PRIORITY)

**File**: `backend/app/models/payment_reconciliation.py` (new file)
**Dependencies**: LPDrawdown, BankTransaction models
**Estimated Time**: 1 day

**Tasks**:

- [ ] Create `PaymentReconciliation` SQLAlchemy model
- [ ] Add fields: recon_id, fund_id, drawdown_quarter, total_expected, total_received, overall_status, per_lp data
- [ ] Create relationships to Fund and LPDrawdown models
- [ ] Add status enum (In-Progress, Completed, Failed)
- [ ] Create Pydantic schemas in `backend/app/schemas/reconciliation.py`

### 1.3 Create LP Payments Model (HIGH PRIORITY)

**File**: `backend/app/models/lp_payment.py` (new file)
**Dependencies**: LPDetails, LPDrawdown, BankTransaction models
**Estimated Time**: 1 day

**Tasks**:

- [ ] Create `LPPayment` SQLAlchemy model
- [ ] Add fields: payment_id, lp_id, drawdown_id, bank_txn_id, expected_amount, received_amount, contributor_check, amount_check, status
- [ ] Create relationships to LP and transaction models
- [ ] Add payment status enum (Pending, Paid, Shortfall, Over-payment)
- [ ] Create Pydantic schemas in `backend/app/schemas/payment.py`

### 1.4 Database Migrations (HIGH PRIORITY)

**File**: `backend/alembic/versions/xxx_create_payment_tables.py`
**Dependencies**: All payment models
**Estimated Time**: 0.5 days

**Tasks**:

- [ ] Create migration for BANK_TRANSACTIONS table
- [ ] Create migration for PAYMENT_RECONCILIATION table
- [ ] Create migration for LP_PAYMENTS table
- [ ] Add proper indexes for performance (txn_date, fund_id, lp_id)
- [ ] Test migration up/down operations

## Phase 2: Bank Integration and Transaction Processing

### 2.1 Bank Statement Processing Service (HIGH PRIORITY)

**File**: `backend/app/services/bank_processor.py` (new file)
**Dependencies**: PDF extraction utility, Bank Transaction model
**Estimated Time**: 3 days

**Tasks**:

- [ ] Implement PDF bank statement parser using existing pdf_extractor.py
- [ ] Extract transaction data (date, amount, description, reference)
- [ ] Parse contributor names from transaction descriptions
- [ ] Handle multiple bank statement formats
- [ ] Implement data validation and error handling
- [ ] Store raw transactions in database with idempotency

### 2.2 Bank API Integration Service (MEDIUM PRIORITY)

**File**: `backend/app/services/bank_api.py` (new file)
**Dependencies**: Bank Transaction model, external bank APIs
**Estimated Time**: 4 days

**Tasks**:

- [ ] Implement HDFC Corporate API integration (OAuth2 flow)
- [ ] Create automated transaction fetching
- [ ] Handle API rate limits and error responses
- [ ] Implement webhook handling for real-time updates
- [ ] Add retry mechanisms and failure handling
- [ ] Store API responses with audit trail

### 2.3 Transaction Import API (HIGH PRIORITY)

**File**: `backend/app/api/bank_transactions.py` (new file)
**Dependencies**: Bank processing services
**Estimated Time**: 2 days

**Endpoints to Implement**:

- [ ] `POST /bank-transactions/manual-import` - Upload bank statement PDF
- [ ] `GET /bank-transactions` - List transactions with filtering
- [ ] `POST /bank-transactions/sync` - Trigger API sync
- [ ] `GET /bank-transactions/{txn_id}` - Get specific transaction

**Business Logic**:

- [ ] Validate uploaded files (PDF format, size limits)
- [ ] Process statements asynchronously
- [ ] Handle duplicate transaction detection
- [ ] Provide import status and progress updates

## Phase 3: Payment Matching and Reconciliation

### 3.1 Payment Matching Engine (HIGH PRIORITY)

**File**: `backend/app/services/payment_matcher.py` (new file)
**Dependencies**: Bank Transaction, LP Payment models
**Estimated Time**: 3 days

**Tasks**:

- [ ] Implement name matching algorithm (fuzzy matching for LP names)
- [ ] Implement amount matching with tolerance (±₹50 or ±₹100)
- [ ] Handle UTR-based matching when available
- [ ] Create confidence scoring for matches
- [ ] Implement manual matching override capability
- [ ] Add comprehensive logging for match decisions

### 3.2 Reconciliation Engine (HIGH PRIORITY)

**File**: `backend/app/services/reconciliation_engine.py` (new file)
**Dependencies**: Payment Matcher, Reconciliation models
**Estimated Time**: 2 days

**Tasks**:

- [ ] Create reconciliation sessions for drawdown quarters
- [ ] Process all LP payments against expected amounts
- [ ] Update payment statuses (Paid, Shortfall, Over-payment)
- [ ] Calculate reconciliation summary statistics
- [ ] Generate reconciliation reports
- [ ] Handle partial payments and multiple payments per LP

### 3.3 Reconciliation API (HIGH PRIORITY)

**File**: `backend/app/api/reconciliation.py` (new file)
**Dependencies**: Reconciliation services
**Estimated Time**: 2 days

**Endpoints to Implement**:

- [ ] `POST /reconciliations` - Start new reconciliation session
- [ ] `GET /reconciliations` - List reconciliation sessions
- [ ] `GET /reconciliations/{recon_id}` - Get reconciliation details
- [ ] `POST /reconciliations/{recon_id}/process` - Process reconciliation
- [ ] `GET /reconciliations/{recon_id}/report` - Download reconciliation report

**Business Logic**:

- [ ] Validate reconciliation prerequisites (drawdowns exist)
- [ ] Handle concurrent reconciliation sessions
- [ ] Provide real-time reconciliation status updates
- [ ] Generate downloadable CSV reports

## Phase 4: Payment Reminder and Notification System

### 4.1 Payment Reminder Service (MEDIUM PRIORITY)

**File**: `backend/app/services/payment_reminder.py` (new file)
**Dependencies**: Email service, LP Payment models
**Estimated Time**: 2 days

**Tasks**:

- [ ] Create scheduled job for payment reminders
- [ ] Send reminders 2 times within 14 days of due date
- [ ] Track reminder sending status
- [ ] Customize reminder content based on LP details
- [ ] Handle reminder frequency and limits
- [ ] Integrate with existing email service

### 4.2 Payment Status Notification Service (MEDIUM PRIORITY)

**File**: `backend/app/services/payment_notifications.py` (new file)
**Dependencies**: Email service, Reconciliation models
**Estimated Time**: 1 day

**Tasks**:

- [ ] Send payment status updates to Fund Manager
- [ ] Create real-time dashboard notifications
- [ ] Send reconciliation completion notifications
- [ ] Handle notification preferences and subscriptions
- [ ] Integrate with existing notification system

### 4.3 Payment Reminder API (MEDIUM PRIORITY)

**File**: `backend/app/api/payment_reminders.py` (new file)
**Dependencies**: Reminder services
**Estimated Time**: 1 day

**Endpoints to Implement**:

- [ ] `POST /payment-reminders/send` - Send manual reminder to LP
- [ ] `GET /payment-reminders/status` - Get reminder status for drawdown
- [ ] `POST /payment-reminders/schedule` - Schedule reminder campaign

## Phase 5: Dashboard and Reporting

### 5.1 Payment Dashboard Service (MEDIUM PRIORITY)

**File**: `backend/app/services/payment_dashboard.py` (new file)
**Dependencies**: Payment and Reconciliation models
**Estimated Time**: 2 days

**Tasks**:

- [ ] Create real-time payment status aggregations
- [ ] Calculate paid vs pending statistics
- [ ] Generate payment timeline data
- [ ] Create LP-wise payment summaries
- [ ] Implement dashboard caching for performance

### 5.2 Payment Dashboard API (MEDIUM PRIORITY)

**File**: `backend/app/api/payment_dashboard.py` (new file)
**Dependencies**: Dashboard service
**Estimated Time**: 1 day

**Endpoints to Implement**:

- [ ] `GET /payment-dashboard/summary` - Overall payment summary
- [ ] `GET /payment-dashboard/lp-status` - LP-wise payment status
- [ ] `GET /payment-dashboard/timeline` - Payment timeline data
- [ ] `GET /payment-dashboard/overdue` - Overdue payments list

## Phase 6: Integration and Testing

### 6.1 Update Main Application (HIGH PRIORITY)

**File**: `backend/main.py`
**Dependencies**: All API routers
**Estimated Time**: 0.5 days

**Tasks**:

- [ ] Add all payment-related routers to main FastAPI app
- [ ] Update API documentation
- [ ] Add proper error handling middleware
- [ ] Configure background task scheduling

### 6.2 Unit Tests (HIGH PRIORITY)

**Files**: Multiple test files for each component
**Dependencies**: Complete implementation
**Estimated Time**: 4 days

**Test Coverage**:

- [ ] Bank transaction model and processing tests
- [ ] Payment matching algorithm tests
- [ ] Reconciliation engine tests
- [ ] API endpoint tests
- [ ] Service layer tests
- [ ] Error handling and edge case tests

### 6.3 Integration Tests (HIGH PRIORITY)

**File**: `backend/tests/test_payment_integration.py`
**Dependencies**: Complete implementation
**Estimated Time**: 2 days

**Test Scenarios**:

- [ ] End-to-end payment reconciliation flow
- [ ] Bank statement processing and matching
- [ ] Reminder system functionality
- [ ] Dashboard data accuracy
- [ ] Error handling and recovery scenarios

## Dependencies and Blockers

### Upstream Dependencies

- **CRITICAL**: Capital Call Notice implementation (drawdown data required)
- **CRITICAL**: Fund Registration implementation (fund context required)
- **HIGH**: LP Details with accurate commitment amounts

### Downstream Impact

- **CRITICAL**: Unit Allotment depends on payment confirmation
- **HIGH**: SEBI reporting uses actual payment data
- **MEDIUM**: Portfolio investment tracking needs payment validation

### External Dependencies

- Bank API credentials and integration approval
- PDF processing capabilities (already available)
- Email service configuration (already available)

## Implementation Priority

### Phase 1 (Week 1): Database Foundation

1. Bank Transactions Model - **CRITICAL**
2. Payment Reconciliation Model - **CRITICAL**
3. LP Payments Model - **CRITICAL**
4. Database Migrations - **CRITICAL**

### Phase 2 (Week 2): Core Processing

1. Bank Statement Processing Service - **CRITICAL**
2. Transaction Import API - **CRITICAL**
3. Payment Matching Engine - **CRITICAL**

### Phase 3 (Week 3): Reconciliation

1. Reconciliation Engine - **CRITICAL**
2. Reconciliation API - **CRITICAL**
3. Bank API Integration Service - **HIGH**

### Phase 4 (Week 4): Notifications and Reminders

1. Payment Reminder Service - **HIGH**
2. Payment Status Notification Service - **HIGH**
3. Payment Reminder API - **MEDIUM**

### Phase 5 (Week 5): Dashboard and Testing

1. Payment Dashboard Service - **MEDIUM**
2. Payment Dashboard API - **MEDIUM**
3. Unit Tests - **CRITICAL**

### Phase 6 (Week 6): Integration and Optimization

1. Integration Tests - **CRITICAL**
2. Performance Optimization - **MEDIUM**
3. Documentation - **MEDIUM**

## Success Criteria

- [ ] Bank statements can be processed automatically and manually
- [ ] Payment matching achieves >95% accuracy for exact matches
- [ ] Reconciliation reports generate correctly
- [ ] Payment reminders sent automatically
- [ ] Real-time payment dashboard working
- [ ] All payment statuses tracked accurately
- [ ] 90%+ test coverage on new functionality
- [ ] Performance acceptable for 1000+ transactions per month

## Risk Mitigation

### Technical Risks

- **Bank API integration complexity**: Start with manual upload, add API later
- **Payment matching accuracy**: Implement confidence scoring and manual override
- **Performance with large datasets**: Implement pagination and caching

### Business Risks

- **Incorrect payment matching**: Multiple validation layers and manual review process
- **Missing payments**: Implement comprehensive audit trails and reporting
- **Reconciliation errors**: Add rollback capabilities and version control

### Operational Risks

- **Bank API downtime**: Fallback to manual processing
- **Statement format changes**: Flexible parsing with configuration options
- **Reminder spam**: Implement frequency limits and opt-out mechanisms
