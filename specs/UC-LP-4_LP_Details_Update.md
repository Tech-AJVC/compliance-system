# UC-LP-4 — LP Details Update

> **Category:** Limited Partner Workflows  
> **Primary actor:** Compliance Officer  
> **Secondary actor:** Limited Partner (read-only)

---

## 1. References

| Doc | Section                       |
| --- | ----------------------------- |
| PRD | §4 – "LP Profile Management"  |
| TRD | §15 – LP Details API          |
| UX  | LP Detail Drawer (side-panel) |

### PRD Extract

> _"System shall maintain a comprehensive profile for each LP including contact info, tax jurisdiction, commitment amount, depository details, etc. Fields editable by Compliance role."_

### TRD Extract

> _Endpoint `PUT /lps/{id}` with JSON schema v2 …_

### UX Extract

> Side-panel with tabs: General, Contribution, Documents.

---

### Use Case

#### Trigger

- UI update LP screen add input fields for invested_fund_id, email_for_drawdowns

#### Behaviour

- Read LP details from KYC, CA, CML uploaded
- Store all the KYC, CA, CML in doc repository against the LP Id
- Populate DB with all statutory fields (ISIN, DP-ID, etc.) from the documents.
- Save the DB to LP Details
- Email the LP and Fund Manager that units have been allotted
- Record one audit-log entry for the LP Update

### Figma UI Screen Inputs

#### Limited Partners List View

- **Onboard Limited Partner Button**: Primary action button
- **Search Field**: "Search tasks..." placeholder text
- **LP Table Columns**:
  - Name (with status indicators: blue circle for verified, orange warning for issues)
  - Email
  - Drawdown Status (with status badges)
  - Commitment Amount (₹ format)
  - Remaining Drawdown (₹ format)
- **Status Indicators**:
  - Waiting for KYC (above name)
  - Under Review (above name)
  - Various drawdown statuses: Pending, Wire Pending, Allotment Pending, Allotment Done

#### LP Profile Detail Modal (Warren Buffet example)

- **Modal Header**: LP name with close button and verification status
- **Contact Information**: warren@berkshire.com displayed prominently
- **Attachments Section**:
  - Contribution Agreement.pdf (clickable link)
  - CML-Warren.pdf (clickable link)

##### General Tab

- **Name**: Warren Buffet
- **Gender**: Male
- **Date Of Birth**: 29-02-2025
- **Mobile Number**: 9999999999
- **Email**: warren@berkshire.com
- **PAN Number**: ARETG29202
- **Address**: Example Address
- **Nominee**: Wilen

##### Contribution Tab

- **Date of Agreement**: 29-02-2025
- **Commitment Amount**: ₹10,000,000
- **Remaining Drawdown**: ₹9,000,000
- **Acknowledgement of PPM**: Yes
- **Depository**: NSDL
- **DPID**: 12321213
- **Client ID**: 432432
- **Class of Shares**: Class A
- **ISIN**: INF1C8N22014
- **Type**: Individual
- **Tax Jurisdiction**: Resident
- **Geography**: India
- **Email for drawdowns**: warren@berkshire.com

#### Status Badge Variations

- **Drawdown Pending**: Blue badge with pending icon
- **Demat Pending**: Orange badge with warning icon
- **Acceptance Pending**: Orange badge
- **Allotment Pending**: Orange badge
- **Allotment Done**: Green badge with checkmark
- **Wire Pending**: Orange badge with wire icon

## 2. Functional Requirements

1. Inline edit on LP table.
2. Validation rules (PAN format, email regex…).
3. Audit log of every field change.
4. Attachment upload (CML, Contribution Agreement) stored in Drive.

## 3. Technical Requirements

- Backend: FastAPI router `/lp` (already partially implemented).
- Use Google Drive util for doc upload.
- AuthZ: only Compliance & Admin.

DB Schema 7. LP_DETAILS (+ delta)
─────────────────────────────
• invested_fund_id: INT
• email_for_drawdowns: VARCHAR(255) NULL
• kyc_status: VARCHAR(50) NULL # Two values "Done" or "Pending"
(Index added on pan, email_for_drawdowns)

## MISSING DATABASE SCHEMA

### LP_DOCUMENTS (Critical Missing Table)

```sql
CREATE TABLE LP_DOCUMENTS (
    lp_document_id INT PRIMARY KEY,
    lp_id INT REFERENCES LP_DETAILS(lp_id),
    document_id INT REFERENCES DOCUMENTS(document_id),
    document_type VARCHAR(50), -- KYC, CA, CML, Drawdown_Notice, etc.
    created_at TIMESTAMPTZ DEFAULT now()
);
```

### LP_DETAILS Updates for Status Management

```sql
 Existing status column DEFAULT 'Waiting for KYC';
-- Possible values: 'Waiting for KYC', 'Contribution Agreement/CML Pending','Active'
```

API's

2. LIMITED PARTNERS

Resource: /lps
POST /lps
JSON

Returns 201
JSON // Access all LP details from ID
{
"lp_id": 101,
"created_at": "2025-05-03T11:50:10Z"
}

GET /lps?invested_fund_id=12&drawdown_status=Drawdown%20Pending GET /lps/{lp_id}
PUT /lps/{lp_id}
DELETE /lps/{lp_id}
GET /lps/search?query=street
Returns
JSON
[{
"lp_id": 101,
"lp_name": "Main Street Capital"
}]

LP Object (Every Column)
JSON
{
"lp_id": 101,
"lp_name": "Main Street Capital",
"email_for_drawdowns": "investor@msc.com",
"invested_fund_id": 12,
"total_drawdown": 1500000.00,
"remaining_drawdown": 3500000.00,
"last_drawdown_status": "Drawdown Pending",
"kyc_status": "Done",
"created_at": "2025-05-03T11:50:10Z",
"updated_at": "2025-05-03T11:50:10Z"
}

## MISSING API ENDPOINTS

### LP STATUS MANAGEMENT (Critical Missing)

Resource: /lps/{lp_id}/status
PATCH /lps/{lp_id}/status
JSON
{
"status": "Active",
"kyc_status": "Done"
}

Returns 200
JSON
{
"lp_id": 101,
"status_updated": true,
"updated_at": "2025-05-08T09:14:11Z"
}

### LP DOCUMENT MANAGEMENT (Critical Missing)

Resource: /lps/{lp_id}/documents
GET /lps/{lp_id}/documents
Returns array of LP documents
JSON
[{
"lp_document_id": 250,
"document_id": 150,
"document_type": "CA",
"document_name": "Contribution Agreement.pdf",
"file_path": "https://drive.google.com/file/d/xyz",
"uploaded_at": "2025-05-08T09:14:11Z"
}]

POST /lps/{lp_id}/documents
JSON
{
"document_id": 150,
"document_type": "KYC"
}

DELETE /lps/{lp_id}/documents/{lp_document_id}

## PROCESS SECTION - LP DETAILS

This process handles the registration and onboarding of Limited Partners (LPs) by extracting information from various documents and storing it in the LP_DETAILS table.

### Subprocess: Client Master List (CML) Extraction

- **Output**: Citizenship, Client ID, Depository, DOB, DOI, DPID, Geography, PAN, Type (Excel)
- **Input Source**: Client Master List
- **Input Format**: PDF
- **Transformation**: Direct
- **Input Field**: Sub Type, Client ID, Depository Name, Sole/First Holder DOB, DP (last 8 digits), Country, PAN, Client Type
- **Formula**: N/A
- **DB vs PDF Analysis**: ⚠️ After initial extraction, these fields should be stored in LP_DETAILS table and referenced from DB for downstream processes

### Subprocess: Contribution Agreement (CA) Extraction

- **Output**: Address, Class of Shares, Commit, Commitment Amount, Date of Agreement, Email, Email for Drawdowns, Gender, ISIN, LP Name, Mobile No., Nominee (Excel)
- **Input Source**: Contribution Agreement
- **Input Format**: PDF
- **Transformation**: Direct + Computation
- **Input Field**: Name and Address of the Contributor, Class/Subclass of Units, Amount of Capital Commitment, Date of Agreement, Email id, Mobile/Tel. No., Details of Nominee
- **Formula**:
  - Gender: Extract from Name using AI
  - ISIN: If Class A, ISIN = Value 1, If Class B, ISIN = Value 2
- **DB vs PDF Analysis**: ⚠️ After initial extraction, these fields should be stored in LP_DETAILS table

### Subprocess: Drawdown Notice Extraction

- **Output**: Total Drawdown (Excel)
- **Input Source**: Drawdown Notice
- **Input Format**: PDF
- **Transformation**: Direct
- **Input Field**: Amount Due (aggregated across all drawdowns)
- **Formula**: N/A
- **DB vs PDF Analysis**: ✅ This should be computed from LP_DRAWDOWNS table, not stored in LP_DETAILS

### Subprocess: KYC Status Extraction

- **Output**: KYC Status (Excel)
- **Input Source**: KYC
- **Input Format**: PDF
- **Transformation**: Direct
- **Input Field**: Status
- **Formula**: N/A
- **DB vs PDF Analysis**: ✅ Store in LP_DETAILS.kyc_status field

### Missing Upstream Fields Analysis:

- ⚠️ **Geography/Country field**: Required for downstream SEBI Activity Report and InVi Filing (foreign investor filtering)
- ⚠️ **DPID and Client ID**: Required for Unit Allotment process
- ⚠️ **Depository Name**: Required for Unit Allotment process
- ✅ All other LP fields are captured in this process

### Downstream Usage:

- LP Details are used by:
  - Capital Call/Drawdown Notice (commitment amounts, contact info)
  - Unit Allotment (depository details, PAN, names)
  - Payment Reconciliation (name matching)
  - SEBI Activity Report (investor categorization by geography/type)
  - InVi Filing (foreign investor filtering)

### Critical Missing Fields for Downstream Processes:

1. **Geography/Country**: Essential for SEBI reporting and InVi filing
2. **DPID**: Required for Unit Allotment sheet
3. **Client ID**: Required for Unit Allotment sheet
4. **Depository Name**: Required for Unit Allotment sheet

## 4. Contradictions

| #   | Field                       | PRD default | UX default     | Resolution          |
| --- | --------------------------- | ----------- | -------------- | ------------------- |
| 1   | Tax Jurisdiction mandatory? | Yes         | Field optional | Await clarification |

## 5. Tasks

### Human

- [ ] Clarify mandatory fields vs optional.

### AI

- [ ] Complete LP schema migration.
- [ ] Implement `PUT /lps/{id}` validations.
- [ ] FE: LP Detail Drawer editable mode.
- [ ] Write audit log util.

---

_Status: draft._

# WORKPLAN - LP DETAILS UPDATE IMPLEMENTATION

## Overview

This workplan details the implementation of LP Details Update functionality to enhance the existing LP management system with document parsing, bulk updates, and improved data management capabilities.

## Phase 1: Document Processing Enhancement

### 1.1 Document Parser Service Enhancement (HIGH PRIORITY)

**File**: `backend/app/services/document_parser.py` (new file)
**Dependencies**: Existing PDF extractor, LP models
**Estimated Time**: 3 days

**Tasks**:

- [ ] Enhance existing PDF extraction for LP-specific documents
- [ ] Implement Contribution Agreement parser
- [ ] Add KYC document parser
- [ ] Create Bank Statement parser for LP account details
- [ ] Implement Certificate parsing (incorporation, identity, etc.)
- [ ] Add data validation and error handling
- [ ] Store extracted data with confidence scores

### 1.2 Document-to-LP Mapping Service (HIGH PRIORITY)

**File**: `backend/app/services/lp_document_mapper.py` (new file)
**Dependencies**: Document parser, LP models
**Estimated Time**: 2 days

**Tasks**:

- [ ] Map extracted document data to LP model fields
- [ ] Implement field conflict resolution
- [ ] Handle multiple documents per LP
- [ ] Create data validation rules
- [ ] Implement change tracking and audit
- [ ] Add manual review and approval workflow

### 1.3 Bulk Update Processing Service (MEDIUM PRIORITY)

**File**: `backend/app/services/lp_bulk_processor.py` (enhance existing)
**Dependencies**: Enhanced LP models, document parsing
**Estimated Time**: 2 days

**Tasks**:

- [ ] Enhance existing bulk upload functionality
- [ ] Add document-based bulk updates
- [ ] Implement batch processing for large datasets
- [ ] Add validation and error reporting
- [ ] Create progress tracking for bulk operations
- [ ] Handle partial failures and rollback

## Phase 2: API Enhancement

### 2.1 Enhanced LP Management API (HIGH PRIORITY)

**File**: `backend/app/api/lp.py` (enhance existing)
**Dependencies**: Enhanced LP services
**Estimated Time**: 2 days

**Endpoints to Enhance/Add**:

- [ ] `POST /lp/parse-document` - Parse and extract LP data from documents
- [ ] `POST /lp/bulk-update-from-documents` - Bulk update from document batch
- [ ] `PUT /lp/{lp_id}/merge-document-data` - Merge document data with existing LP
- [ ] `GET /lp/{lp_id}/document-history` - Get document processing history
- [ ] `POST /lp/validate-bulk-data` - Validate bulk data before processing

**Business Logic Enhancements**:

- [ ] Add document-based data validation
- [ ] Implement field-level change tracking
- [ ] Add approval workflow for document-based updates
- [ ] Enhanced error handling and reporting

### 2.2 Document Management API Enhancement (MEDIUM PRIORITY)

**File**: `backend/app/api/documents.py` (enhance existing)
**Dependencies**: Document processing services
**Estimated Time**: 1 day

**Endpoints to Add**:

- [ ] `POST /documents/process-for-lp` - Process document for LP data extraction
- [ ] `GET /documents/processing-status/{document_id}` - Get processing status
- [ ] `POST /documents/reprocess/{document_id}` - Reprocess document

## Phase 3: Data Quality and Validation

### 3.1 LP Data Validation Service (HIGH PRIORITY)

**File**: `backend/app/services/lp_validator.py` (new file)
**Dependencies**: LP models, external validation APIs
**Estimated Time**: 2 days

**Tasks**:

- [ ] Implement PAN number validation
- [ ] Add email address validation and verification
- [ ] Implement phone number validation
- [ ] Add address validation and standardization
- [ ] Create bank account validation
- [ ] Implement duplicate detection algorithms
- [ ] Add data completeness scoring

### 3.2 Data Quality Dashboard Service (MEDIUM PRIORITY)

**File**: `backend/app/services/lp_data_quality.py` (new file)
**Dependencies**: LP models, validation service
**Estimated Time**: 2 days

**Tasks**:

- [ ] Create data quality metrics and scoring
- [ ] Implement data completeness tracking
- [ ] Add data accuracy monitoring
- [ ] Create data quality reports
- [ ] Implement data quality alerts
- [ ] Add trending and historical analysis

### 3.3 Data Quality API (MEDIUM PRIORITY)

**File**: `backend/app/api/lp_data_quality.py` (new file)
**Dependencies**: Data quality services
**Estimated Time**: 1 day

**Endpoints to Implement**:

- [ ] `GET /lp/data-quality/summary` - Overall data quality summary
- [ ] `GET /lp/data-quality/issues` - List data quality issues
- [ ] `POST /lp/data-quality/validate` - Validate specific LP data
- [ ] `GET /lp/data-quality/completeness` - Data completeness report

## Phase 4: Enhanced UI Integration

### 4.1 Document Upload and Processing Integration (HIGH PRIORITY)

**File**: `backend/app/services/lp_ui_integration.py` (new file)
**Dependencies**: Document processing, LP APIs
**Estimated Time**: 2 days

**Tasks**:

- [ ] Create document upload workflow for LP updates
- [ ] Implement real-time processing status updates
- [ ] Add document preview and validation
- [ ] Create field-by-field update confirmation
- [ ] Implement batch operation monitoring
- [ ] Add error handling and user feedback

### 4.2 LP Search and Filter Enhancement (MEDIUM PRIORITY)

**File**: `backend/app/api/lp.py` (enhance existing search)
**Dependencies**: Enhanced LP models
**Estimated Time**: 1 day

**Search Enhancements**:

- [ ] Add advanced filtering by multiple criteria
- [ ] Implement full-text search across LP data
- [ ] Add search by document type and status
- [ ] Create saved search functionality
- [ ] Add export capabilities for search results

## Phase 5: Integration and Workflow

### 5.1 LP Lifecycle Workflow Service (MEDIUM PRIORITY)

**File**: `backend/app/services/lp_lifecycle.py` (new file)
**Dependencies**: LP models, task management
**Estimated Time**: 2 days

**Tasks**:

- [ ] Create LP onboarding workflow
- [ ] Implement status transition management
- [ ] Add automated task creation for LP processes
- [ ] Create approval workflows for LP changes
- [ ] Implement notification system for status changes
- [ ] Add compliance checking and alerts

### 5.2 LP Integration with Other Systems (HIGH PRIORITY)

**File**: `backend/app/services/lp_integrations.py` (new file)
**Dependencies**: LP models, other system APIs
**Estimated Time**: 2 days

**Tasks**:

- [ ] Integration with drawdown system
- [ ] Connection to payment reconciliation
- [ ] Link with unit allotment system
- [ ] Integration with compliance tracking
- [ ] Connection to document management
- [ ] API for external system integration

## Phase 6: Testing and Performance

### 6.1 Enhanced Unit Tests (HIGH PRIORITY)

**Files**: Enhance existing and create new test files
**Dependencies**: All enhanced functionality
**Estimated Time**: 3 days

**Test Coverage**:

- [ ] Document parsing accuracy tests
- [ ] Data validation tests
- [ ] Bulk processing tests
- [ ] API enhancement tests
- [ ] Integration workflow tests
- [ ] Performance tests for large datasets

### 6.2 Integration Tests (HIGH PRIORITY)

**File**: `backend/tests/test_lp_details_integration.py`
**Dependencies**: Complete implementation
**Estimated Time**: 2 days

**Test Scenarios**:

- [ ] End-to-end document processing to LP update
- [ ] Bulk update workflows
- [ ] Data quality monitoring
- [ ] Integration with other systems
- [ ] Error handling and recovery

### 6.3 Performance Optimization (MEDIUM PRIORITY)

**Files**: Various service files
**Dependencies**: Complete implementation
**Estimated Time**: 2 days

**Optimization Tasks**:

- [ ] Optimize document processing performance
- [ ] Implement caching for frequently accessed data
- [ ] Add database query optimization
- [ ] Implement async processing for bulk operations
- [ ] Add monitoring and performance metrics

## Dependencies and Blockers

### Upstream Dependencies

- **HIGH**: Existing LP management system (already implemented)
- **MEDIUM**: Document management system (already implemented)
- **MEDIUM**: PDF extraction utility (already implemented)

### Downstream Impact

- **CRITICAL**: All LP-dependent systems benefit from improved data quality
- **HIGH**: Drawdown generation accuracy improves
- **HIGH**: Payment reconciliation matching improves
- **MEDIUM**: SEBI reporting data quality improves

### External Dependencies

- Document templates and formats standardization
- Data validation service APIs (PAN, email, address)
- UI/UX design for enhanced LP management interface

## Implementation Priority

### Phase 1 (Week 1): Document Processing

1. Document Parser Service Enhancement - **CRITICAL**
2. Document-to-LP Mapping Service - **CRITICAL**
3. Enhanced LP Management API - **HIGH**

### Phase 2 (Week 2): Data Quality

1. LP Data Validation Service - **CRITICAL**
2. Bulk Update Processing Service - **HIGH**
3. Data Quality Dashboard Service - **MEDIUM**

### Phase 3 (Week 3): Integration and APIs

1. LP Integration with Other Systems - **HIGH**
2. Document Management API Enhancement - **HIGH**
3. Data Quality API - **MEDIUM**

### Phase 4 (Week 4): UI and Workflow

1. Document Upload and Processing Integration - **HIGH**
2. LP Lifecycle Workflow Service - **MEDIUM**
3. LP Search and Filter Enhancement - **MEDIUM**

### Phase 5 (Week 5): Testing and Optimization

1. Enhanced Unit Tests - **CRITICAL**
2. Integration Tests - **CRITICAL**
3. Performance Optimization - **MEDIUM**

## Success Criteria

- [ ] Documents can be parsed and mapped to LP data automatically
- [ ] Bulk updates work efficiently for 100+ LPs
- [ ] Data quality monitoring and reporting functional
- [ ] Enhanced search and filtering capabilities working
- [ ] Integration with other systems seamless
- [ ] Document processing accuracy >95%
- [ ] 90%+ test coverage on enhanced functionality
- [ ] Performance acceptable for 1000+ LPs

## Risk Mitigation

### Technical Risks

- **Document parsing accuracy**: Multiple validation layers and manual review options
- **Performance with large datasets**: Async processing and optimization
- **Data corruption**: Comprehensive backup and rollback capabilities

### Business Risks

- **Data quality issues**: Validation at multiple points and quality monitoring
- **Integration failures**: Fallback mechanisms and error handling
- **User adoption**: Gradual rollout and training

### Operational Risks

- **Document format changes**: Flexible parsing with configuration options
- **Data migration issues**: Comprehensive testing and validation
- **System downtime**: Graceful degradation and maintenance windows
