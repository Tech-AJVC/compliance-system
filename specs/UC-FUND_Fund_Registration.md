DB Schema:

9. FUND_DETAILS
   ─────────────────────────────
   • fund_id: INT PRIMARY KEY
   • scheme_name: VARCHAR(255) -- "AJVC FUND SCHEME OF AJVC TRUST"
   • scheme_status: VARCHAR(40) -- Active Scheme / Closed Ended etc.
   • aif_name: VARCHAR(255) -- "AJVC Fund"
   • aif_pan: VARCHAR(20) -- "AAKTA6772D"
   • aif_registration_no: VARCHAR(50) -- "IN/AIF2/24-25/1578"
   • legal_structure: VARCHAR(50) -- Trust / LLP / Company
   • category_subcategory: VARCHAR(100) -- "Category II AIF, Category I AIF, Category III AIF"
   • entity_type: VARCHAR(50) -- MANAGER / SPONSOR etc.
   • entity_name: VARCHAR(255)
   • entity_pan: VARCHAR(20)
   • entity_email: VARCHAR(255)
   • entity_address: TEXT
   • custodian_name: VARCHAR(255)
   • rta_name: VARCHAR(255)
   • compliance_officer_name: VARCHAR(255)
   • compliance_officer_email: VARCHAR(255)
   • compliance_officer_phone: VARCHAR(20)
   • investment_officer_name: VARCHAR(255)
   • investment_officer_designation: VARCHAR(100) -- "Fund Manager"
   • investment_officer_pan: VARCHAR(20)
   • investment_officer_din: VARCHAR(20) NULL
   • date_of_appointment: DATE
   • scheme_pan: VARCHAR(20) -- duplicate of aif_pan but kept for template parity
   • scheme_structure_type: VARCHAR(40) -- Closed Ended / Open Ended
   • date_final_draft_ppm: DATE
   • date_sebi_ppm_comm: DATE
   • date_launch_of_scheme: DATE
   • date_initial_close: DATE
   • date_final_close: DATE NULL
   • commitment_initial_close_cr: DECIMAL(18,2) NULL -- 8 510 Cr ⇒ store 8510.00
   • terms_end_date: DATE
   • extension_permitted: BOOLEAN -- TRUE / FALSE
   • extended_end_date: DATE NULL
   • bank_name: VARCHAR(255)
   • bank_ifsc: VARCHAR(15)
   • bank_account_name: VARCHAR(255)
   • bank_account_no: VARCHAR(50)
   • bank_contact_person: VARCHAR(255)
   • bank_contact_phone: VARCHAR(20)
   • created_at: TIMESTAMPTZ DEFAULT now()
   • updated_at: TIMESTAMPTZ DEFAULT now()
   • nav: INT
   • target_fund_size:
   • greenshoe option:

Manager, Trust, Fund

Indexes
• (scheme_name) UNIQUE
• (aif_pan) UNIQUE
• (bank_account_no) UNIQUE

## MISSING DATABASE SCHEMA

### FUND_ENTITIES (Critical Missing Table)

```sql
CREATE TABLE FUND_ENTITIES (
    fund_entity_id INT PRIMARY KEY,
    fund_id INT REFERENCES FUND_DETAILS(fund_id),
    entity_id INT REFERENCES ENTITIES(entity_id),
    entity_role VARCHAR(50), -- Manager, Trust, Custodian, RTA, Trustee, Auditor, Merchant Banker
    is_primary BOOLEAN DEFAULT false, -- for primary Manager, Trust, etc.
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

API's

1. FUNDS

Resource: /funds
POST /funds
JSON
{
"scheme_name": "AJVC FUND SCHEME OF AJVC TRUST",
"scheme_type": "Closed Ended",
"scheme_status": "Active Scheme",
"category_subcategory": "Category II AIF",
"legal_structure": "Trust",
"aif_name": "AJVC Fund",
"aif_pan": "AAKTA6772D",
"aif_registration_no": "IN/AIF2/24-25/1578",
"date_initial_close": "2025-02-20",
"target_fund_size_cr": 600.00,
"bank_name": "HDFC Bank",
"bank_ifsc": "HDFC0000001",
"bank_account_name": "AJVC Fund",
"bank_account_no": "012345678901",
"bank_contact_person": "Mahesh Iyer",
"bank_contact_phone": "+91-9876543210",
"compliance_officer_name": "Sachin Rao",
"compliance_officer_email": "sachin@ajvc.com",
"investment_officer_name": "Aviral Bhatnagar",
"Investment_office r_pan": "AAAPA1234A"
}

Returns 201
JSON
{
"fund_id": 12,
"created_at": "2025-05-03T11:40:22Z"
}
GET /funds?scheme_status=Active&category_subcategory=Category%20II%20AIF
GET /funds/{fund_id}
PUT /funds/{fund_id}
DELETE /funds/{fund_id}
GET /funds/search?query=ajvc
Returns
JSON
{
"fund_id": 12,
"scheme_name": "AJVC FUND SCHEME OF AJVC TRUST"
}
Fund Object – Complete Column Set
JSON
{
"fund_id": 12,
"scheme_name": "AJVC FUND SCHEME OF AJVC TRUST",
"scheme_status": "Active Scheme",
"aif_name": "AJVC Fund",
"aif_pan": "AAKTA6772D",
"aif_registration_no": "IN/AIF2/24-25/1578",
"legal_structure": "Trust",
"category_subcategory": "Category II AIF",
"scheme_structure_type": "Closed Ended",
"entity_type": null,
"entity_name": null,
"entity_pan": null,
"entity_email": null,
"entity_address": null,
"custodian_name": null,
"rta_name": null,
"compliance_officer_name": "Sachin Rao",
"compliance_officer_email": "sachin@ajvc.com",
"compliance_officer_phone": null,
"investment_officer_name": "Aviral Bhatnagar",
"investment_officer_designation": "Fund Manager",
"investment_officer_pan": "AAAPA1234A",
"investment_officer_din": null,
"date_of_appointment": "2025-02-01",
"scheme_pan": "AAKTA6772D",
"date_final_draft_ppm": null,
"date_sebi_ppm_comm": null,
"date_launch_of_scheme": "2025-03-15",
"date_initial_close": "2025-02-20",
"date_final_close": null,
"terms_end_date": null,
"extension_permitted": false,
"extended_end_date": null,
"commitment_initial_close_cr": 560.00,
"bank_name": "HDFC Bank",
"bank_ifsc": "HDFC0000001",
"bank_account_name": "AJVC Fund",
"bank_account_no": "012345678901",
"bank_contact_person": "Mahesh Iyer",
"bank_contact_phone": "+91-9876543210",
"nav": 100,
"target_fund_size": 600.00,
"greenshoe_option": null,
"created_at": "2025-05-03T11:40:22Z",
"updated_at": "2025-05-03T11:40:22Z"
}

10. ENTITIES

Resource: /entities
POST /entities (UI / Form-field inputs ONLY)
JSON
{
"entity_type": "Auditor", // dropdown
"entity_pan": "AAACA1234F", // Form Field
"entity_registration_number": "FRN01234", // Form Field
"entity_tan": "MUMA12345B", // Form Field
"entity_date_of_incorp": "2015-07-21", // Form Field
"entity_gst_number": "27AAACA1234F1Z6", // Form Field
"entity_poc": "Ravi Kumar", // Form Field
"entity_poc_din": "07456321", // Form Field
"entity_poc_pan": "AAAPR9876C" // Form Field
}

Returns 201 Created
JSON
{
"entity_id": 41,
"created_at": "2025-05-08T09:14:11Z"
}
PUT /entities/{entity_id}
Same body structure as POST; partial update is allowed.
DELETE /entities/{entity_id}
GET /entities?entity_type=Auditor&gst_number=27AAACA1234F1Z6
GET /entities/{entity_id}
GET /entities/search?query=ravi
Returns
JSON
[{
"entity_id": 41,
"entity_name": "—",
"entity_type": "Auditor"
}]

Entity Object – All Columns
JSON
{
"entity_id": 41,
"entity_type": "Auditor",
"entity_name": null, // populated later via document OCR
"entity_pan": "AAACA1234F",
"entity_address": null,
"entity_telephone": null,
"entity_email": null,
"entity_poc": "Ravi Kumar",
"entity_registration_number": "FRN01234",
"entity_tan": "MUMA12345B",
"entity_date_of_incorporation": "2015-07-21",
"entity_gst_number": "27AAACA1234F1Z6",
"entity_poc_din": "07456321",
"entity_poc_pan": "AAAPR9876C",
"created_at": "2025-05-08T09:14:11Z",
"updated_at": "2025-05-08T09:14:11Z"
}

## MISSING API ENDPOINTS

### 11. FUND-ENTITY RELATIONSHIPS

Resource: /fund-entities
POST /fund-entities
JSON
{
"fund_id": 12,
"entity_id": 41,
"entity_role": "Manager",
"is_primary": true
}

Returns 201
JSON
{
"fund_entity_id": 150,
"created_at": "2025-05-08T09:14:11Z"
}

GET /fund-entities?fund_id=12
Returns array of fund-entity relationships
JSON
[{
"fund_entity_id": 150,
"fund_id": 12,
"entity_id": 41,
"entity_role": "Manager",
"is_primary": true,
"entity_details": {
"entity_name": "AJVC Management",
"entity_pan": "AAACA1234F",
"entity_email": "manager@ajvc.com"
}
}]

DELETE /fund-entities/{fund_entity_id}
Returns 204 No Content

### FUND DETAILS AGGREGATION (Missing) (BEING USED IN SEBI ACTIVITY REPORT AS A SCREEN TO AGG INFORMATION)

Resource: /funds/{fund_id}/details-summary
GET /funds/{fund_id}/details-summary
Returns comprehensive fund information for reporting
JSON
{
"fund_id": 12,
"scheme_details": {
"scheme_name": "Ajvc Fund Scheme of Ajvc Trust",
"status": "Active",
"registration": "AWEOER123",
"extension_permitted": true
},
"aif_details": {
"fund_name": "AJVC Fund",
"aif_registration": "AAKTA6772D",
"registration_number": "IN/AIF2/24-25/1578",
"structure": "Trust",
"category": "Category II AIF"
},
"financial_info": {
"corpus_initial_close": 8000000000.00,
"target_fund_size": 10000000000.00,
"greenshoe_option": 80000000.00
},
"important_dates": {
"ppm_final_draft_sent": "2024-08-12",
"ppm_taken_on_record": "2025-02-07",
"scheme_launch": "2025-03-15",
"initial_close": "2025-03-20",
"final_close": "2025-06-20",
"end_date_scheme": "2025-07-20",
"end_date_extended": "2025-08-30"
},
"bank_details": {
"bank_name": "HDFC Bank AJVC",
"account_numbers": ["123245983274893​2", "HDFC090000"],
"bank_contact": "Aviral Bhatnagar (+91 9999999999)"
}
}

### Use Case

#### Trigger

- Fund Manager creates a new fund in the system

#### Behaviour

- Capture comprehensive fund details across multiple categories
- Store fund information in structured database schema
- Enable entity management for all fund-related stakeholders
- Validate regulatory compliance fields
- Generate fund documentation templates

---

### Figma UI Screen Inputs

#### Add New Fund Form

##### Scheme Details Section

- **Scheme Name** (required): Text input field
- **Scheme Status** (required): Dropdown (Active, Inactive options)
- **Scheme Structure** (required): Dropdown (Close Ended, Open Ended options)
- **Scheme PAN** (required): Text input field with PAN format validation
- **Date of filing final draft PPM with SEBI** (required): Date picker
- **Date of SEBI Communication for taking the PPM on record** (required): Date picker
- **Date of launch of scheme** (required): Date picker
- **Date of Initial Close** (required): Date picker
- **Date of final close** (required): Date picker
- **Total Commitment received (Corpus) as on Initial Close (Rs. Cr)** (required): Currency input field
- **Target Fund Size** (required): Currency input field
- **Greenshoe option** (required): Currency input field
- **End date of terms of Scheme** (required): Date picker
- **Any Extension of Term permitted as per fund documents** (required): Dropdown (Yes/No)
- **End date of Extended term** (required): Date picker (conditional)

##### Bank Details Section

- **Bank Name** (required): Text input field
- **IFSC** (required): Text input field with IFSC format validation
- **Bank Account Name** (required): Text input field
- **Bank Account Number** (required): Text input field
- **Bank Contact** (required): Text input field
- **Contact Phone** (required): Phone number input field

##### AIF Details Section

- **Name of the AIF** (required): Text input field (e.g., AJVC Fund)
- **PAN Number of the AIF** (required): Text input field (e.g., AAKTA6772D)
- **Registration Number of the AIF** (required): Text input field (e.g., IN/AIF2/24-25/1578)
- **Legal Structure of the AIF** (required): Dropdown (Trust, Company, LLP options)
- **Category and Sub-category of the AIF** (required): Dropdown (Category II AIF options)

##### Add Entities Section

- **Manager** (required): Dropdown selection
- **Trust** (required): Dropdown selection
- **Custodian** (required): Dropdown selection
- **RTA** (required): Dropdown selection
- **Other Entities**: Dynamic entity addition
  - **Add Entity Button**: Secondary button to add more entities
  - **Entity Type Dropdown**: Manager, Sponsor, Trust, Custodian, RTA, Trustee, Auditor, Merchant Banker
  - **Remove Button**: Option to remove added entities

#### Entity Profile Forms (Role-specific)

##### Update Profile - Common Fields

- **Role** (required): Dropdown with options:
  - Manager, Sponsor, Trust, Merchant Banker, RTA, Trustee, Auditor
- **Name** (required): Text input field
- **Email** (required): Email input field with validation
- **Phone No.** (required): Phone number input field
- **Address** (required): Textarea field with placeholder "Enter the full postal address"
- **PAN Number** (required): Text input field with PAN validation

##### Other Details Section (Role-specific fields)

- **Registration Number**: Text input field
- **TAN Number**: Text input field (for Trust role)
- **Date of Incorporation**: Date picker field (for Trust role)
- **GST Number**: Text input field (for Manager role)
- **POC DIN Number**: Text input field (for Manager role)
- **POC PAN Number**: Text input field (for Manager role)

#### Entity Profile Update Forms

##### Manager Profile Update

- **Role Dropdown**: Manager (pre-selected)
- **Name**: Text input field
- **Email**: Email input field
- **Phone No.**: Phone number input field
- **Address**: Multi-line text area
- **PAN Number**: Text input with PAN format validation
- **Other Details Section**:
  - Registration Number: Text input
  - TAN Number: Text input
  - Date of Incorporation: Date picker
  - GST Number: Text input
  - POC DIN Number: Text input
  - POC PAN Number: Text input

##### Sponsor Profile Update

- **Role Dropdown**: Sponsor (pre-selected)
- **Name**: Text input field
- **Email**: Email input field
- **Phone No.**: Phone number input field
- **Address**: Multi-line text area
- **PAN Number**: Text input with PAN format validation
- **Other Details Section**:
  - Registration Number: Text input
  - TAN Number: Text input
  - Date of Incorporation: Date picker
  - GST Number: Text input

##### Trust Profile Update

- **Role Dropdown**: Trust (pre-selected)
- **Name**: Text input field
- **Email**: Email input field
- **Phone No.**: Phone number input field
- **Address**: Multi-line text area
- **PAN Number**: Text input with PAN format validation
- **Other Details Section**:
  - TAN Number: Text input
  - Date of Incorporation: Date picker

##### Auditor Profile Update

- **Role Dropdown**: Auditor (pre-selected)
- **Name**: Text input field
- **Email**: Email input field
- **Phone No.**: Phone number input field
- **Address**: Multi-line text area
- **PAN Number**: Text input with PAN format validation
- **Other Details Section**:
  - Registration Number: Text input

##### RTA Profile Update

- **Role Dropdown**: RTA (pre-selected)
- **Name**: Text input field
- **Email**: Email input field
- **Phone No.**: Phone number input field
- **Address**: Multi-line text area
- **PAN Number**: Text input with PAN format validation
- **Other Details Section**:
  - Registration Number: Text input

##### Trustee Profile Update

- **Role Dropdown**: Trustee (pre-selected)
- **Name**: Text input field
- **Email**: Email input field
- **Phone No.**: Phone number input field
- **Address**: Multi-line text area
- **PAN Number**: Text input with PAN format validation
- **Other Details Section**:
  - Registration Number: Text input

##### Merchant Banker Profile Update

- **Role Dropdown**: Merchant Banker (pre-selected)
- **Name**: Text input field
- **Email**: Email input field
- **Phone No.**: Phone number input field
- **Address**: Multi-line text area
- **PAN Number**: Text input with PAN format validation
- **Other Details Section**:
  - Registration Number: Text input

#### Entity Field Mapping (From Figma Comments)

- **Registration Number**: Required for Sponsor, Manager, Merchant Banker, Auditor, RTA, Trustee
- **TAN Number**: Required for Sponsor, Manager, Trust
- **Date of Incorporation**: Required for Sponsor, Manager, Trust
- **GST Number**: Required for Sponsor, Manager
- **POC DIN Number**: Required for Manager only
- **POC PAN Number**: Required for Manager only

#### Fund Details View (Read-only)

- **Scheme Details**: Left column displaying all scheme information
- **AIF Details**: Right column displaying AIF information
- **Bank Details**: Dedicated section for banking information
- **Entities List**: Display of all associated entities with their roles
- **Edit/Delete Actions**: Available for fund modification

## PROCESS SECTION - ENTITY ONBOARDING

This process handles the registration and onboarding of various entities (Manager, Sponsor, Trust, Custodian, RTA, Trustee, Auditor, Merchant Banker) that are linked to the fund.

### Subprocess: Entity Type Selection

- **Output**: Entity Type (Dropdown)
- **Input Source**: Stored List
- **Input Format**: Dropdown
- **Transformation**: Direct
- **Input Field**: "RTA, Accountant, Tax, Auditor, Merchant Banker, Trustee, Sponsor, Manager, Legal Advisor, Trust, Compliance Officer"
- **Formula**: N/A
- **DB vs PDF Analysis**: ✅ This is UI-driven, no PDF extraction needed

### Subprocess: Entity Basic Information (from PPM)

- **Output**: Entity Name, Entity Address, Entity Telephone, Entity Email (Form Fields)
- **Input Source**: PPM
- **Input Format**: PDF
- **Transformation**: Direct
- **Input Field**: Name of Entity, Address of Entity, Telephone of Entity, Email of Entity
- **Formula**: N/A
- **DB vs PDF Analysis**: ⚠️ After initial extraction and storage in ENTITIES table, subsequent processes can read from DB

### Subprocess: Entity Regulatory Information (UI Input)

- **Output**: Entity PAN, Entity POC, Entity Registration Number, Entity TAN, Entity Date of Incorporation, Entity GST Number, Entity POC DIN Number, Entity POC PAN (Form Fields)
- **Input Source**: UI for Onboarding
- **Input Format**: Form Field
- **Transformation**: Direct
- **Input Field**: PAN of Entity, POC of Entity, Registration Number of Entity, TAN of Entity, Date of Incorporation of Entity, GST Number of Entity, POC DIN Number of Entity, POC PAN of Entity
- **Formula**: N/A
- **DB vs PDF Analysis**: ✅ This is UI-driven, stored directly in ENTITIES table

### Entity-Specific Field Requirements:

- **Registration Number Required**: Sponsor, Manager, Merchant Banker, Auditor, RTA, Trustee, Trust
- **TAN Required**: Sponsor, Manager, Trust
- **Date of Incorporation Required**: Sponsor, Manager, Trust
- **GST Number Required**: Sponsor, Manager
- **POC DIN/PAN Required**: Manager only

## PROCESS SECTION - FUND REGISTRATION

This process handles the registration of fund details and linking with various entities.

### Subprocess: Entity Linkage to Fund

- **Output**: RTA Linkage, Accountant Linkage, Tax Linkage, Auditor Linkage, Merchant Banker Linkage, Trustee Linkage, Sponsor Linkage, Manager Linkage, Legal Advisor Linkage, Trust Linkage, Compliance Officer Linkage (UI Toggle)
- **Input Source**: Entity Onboarding
- **Input Format**: UI Toggle
- **Transformation**: Direct
- **Input Field**: Entity Name, PAN, Address, Telephone, Email, POC, Registration Number (for applicable entities)
- **Formula**: N/A
- **DB vs PDF Analysis**: ✅ References existing ENTITIES table data, creates FUND_ENTITIES relationships

### Missing Upstream Fields Analysis:

- ✅ All entity information is captured in the Entity Onboarding process
- ✅ Fund registration can reference entity data from ENTITIES table
- ✅ No missing upstream dependencies identified

### Downstream Usage:

- Fund details and linked entities are used by:
  - LP Details Registration (fund bank details, compliance officer info)
  - SEBI Activity Report (entity information, fund structure details)
  - Drawdown Notice (fund bank account information)

## NOT REQUIRED

10. FUND_BANK_TRANSACTIONS
    ─────────────────────────────
    • txn_id: BIGINT PK
    • fund_id: INT FK→FUND_DETAILS
    • txn_date: DATE
    • value_date: DATE
    • narration: TEXT
    • amount: DECIMAL(18,2) -- positive = credit
    • currency: CHAR(3) DEFAULT 'INR'
    • balance: DECIMAL(18,2)
    • bank_reference: VARCHAR(100)
    • raw_payload: JSONB -- full API response for audit
    • imported_at: TIMESTAMP
    • created_at: TIMESTAMPTZ DEFAULT now()

11. FUND BANK TRANSACTIONS

Resource: /fund-bank-transactions
GET /fund-bank-transactions?fund_id=12&unreconciled_only=true
Returns list
JSON
{
"txn_id": 998877665,
"fund_id": 12,
"txn_date": "2025-05-05",
"value_date": "2025-05-05",
"narration": "NEFT / MAIN STREET CAPITAL",
"amount": 1000000.00,
"currency": "INR",
"balance": 123456789.22,
"bank_reference": "NEFT202505051234",
"raw_payload": { ... },
"imported_at": "2025-05-05T02:15:00Z",
"reconciled": true,
"matched_drawdown": 4501
}
POST /fund-bank-transactions/manual-import (File Upload)
Request: multipart/form-data { file: <statement.pdf> }
Returns: { "imported_rows": 87 }

# WORKPLAN - FUND REGISTRATION IMPLEMENTATION

## Overview

This workplan details the step-by-step implementation of Fund Registration functionality including database schema, API endpoints, and integration requirements based on the specifications above.

## Phase 1: Database Schema Implementation

### 1.1 Create Fund Details Model (HIGH PRIORITY)

**File**: `backend/app/models/fund_details.py`
**Dependencies**: None
**Estimated Time**: 2 days

**Tasks**:

- [ ] Create `FundDetails` SQLAlchemy model with all 40+ fields specified in schema
- [ ] Add proper field types, constraints, and indexes
- [ ] Include relationships to other models
- [ ] Add model validation methods
- [ ] Create Pydantic schemas in `backend/app/schemas/fund.py`

**Schema Fields to Implement**:

```python
# Key fields from specification
fund_id, scheme_name, scheme_status, aif_name, aif_pan, aif_registration_no,
legal_structure, category_subcategory, entity_type, entity_name, entity_pan,
entity_email, entity_address, custodian_name, rta_name, compliance_officer_name,
compliance_officer_email, compliance_officer_phone, investment_officer_name,
investment_officer_designation, investment_officer_pan, investment_officer_din,
date_of_appointment, scheme_pan, scheme_structure_type, date_final_draft_ppm,
date_sebi_ppm_comm, date_launch_of_scheme, date_initial_close, date_final_close,
commitment_initial_close_cr, terms_end_date, extension_permitted, extended_end_date,
bank_name, bank_ifsc, bank_account_name, bank_account_no, bank_contact_person,
bank_contact_phone, nav, target_fund_size, greenshoe_option
```

### 1.2 Create Entities Model (HIGH PRIORITY)

**File**: `backend/app/models/entity.py`
**Dependencies**: None
**Estimated Time**: 1 day

**Tasks**:

- [ ] Create `Entity` SQLAlchemy model for auditors, custodians, RTAs, etc.
- [ ] Add fields: entity_type, entity_pan, entity_registration_number, entity_tan, entity_date_of_incorp, entity_gst_number, entity_poc, entity_poc_din, entity_poc_pan
- [ ] Create Pydantic schemas in `backend/app/schemas/entity.py`
- [ ] Add validation for PAN, GST, TAN formats

### 1.3 Create Fund-Entity Relationship Model (HIGH PRIORITY)

**File**: `backend/app/models/fund_entity.py`
**Dependencies**: FundDetails, Entity models
**Estimated Time**: 0.5 days

**Tasks**:

- [ ] Create `FundEntity` junction table model
- [ ] Link funds to multiple entities (Manager, Trust, Custodian, RTA, Trustee, Auditor, Merchant Banker)
- [ ] Add `is_primary` flag for primary relationships
- [ ] Create appropriate foreign key relationships

### 1.4 Database Migrations (HIGH PRIORITY)

**File**: `backend/alembic/versions/xxx_create_fund_tables.py`
**Dependencies**: All models above
**Estimated Time**: 1 day

**Tasks**:

- [ ] Create Alembic migration for FUND_DETAILS table
- [ ] Create Alembic migration for ENTITIES table
- [ ] Create Alembic migration for FUND_ENTITIES junction table
- [ ] Add proper indexes and constraints
- [ ] Test migration up/down operations

## Phase 2: API Implementation

### 2.1 Fund Management API (HIGH PRIORITY)

**File**: `backend/app/api/funds.py`
**Dependencies**: Fund models, schemas
**Estimated Time**: 3 days

**Endpoints to Implement**:

- [ ] `POST /funds` - Create new fund
- [ ] `GET /funds` - List funds with filtering (scheme_status, category_subcategory)
- [ ] `GET /funds/{fund_id}` - Get specific fund details
- [ ] `PUT /funds/{fund_id}` - Update fund details
- [ ] `DELETE /funds/{fund_id}` - Delete fund
- [ ] `GET /funds/search?query=` - Search funds by name

**Business Logic**:

- [ ] Validate unique constraints (scheme_name, aif_pan, bank_account_no)
- [ ] Handle date field validation
- [ ] Implement proper error handling and status codes
- [ ] Add audit logging for fund operations

### 2.2 Entity Management API (MEDIUM PRIORITY)

**File**: `backend/app/api/entities.py`
**Dependencies**: Entity models, schemas
**Estimated Time**: 2 days

**Endpoints to Implement**:

- [ ] `POST /entities` - Create new entity
- [ ] `GET /entities` - List entities with filtering (entity_type, gst_number)
- [ ] `GET /entities/{entity_id}` - Get specific entity
- [ ] `PUT /entities/{entity_id}` - Update entity details
- [ ] `DELETE /entities/{entity_id}` - Delete entity
- [ ] `GET /entities/search?query=` - Search entities

**Business Logic**:

- [ ] Validate PAN, GST, TAN number formats
- [ ] Handle entity type validation
- [ ] Implement proper error handling

### 2.3 Fund-Entity Relationship API (MEDIUM PRIORITY)

**File**: `backend/app/api/fund_entities.py`
**Dependencies**: Fund and Entity APIs
**Estimated Time**: 1 day

**Endpoints to Implement**:

- [ ] `POST /funds/{fund_id}/entities` - Link entity to fund
- [ ] `GET /funds/{fund_id}/entities` - Get fund's linked entities
- [ ] `DELETE /funds/{fund_id}/entities/{entity_id}` - Unlink entity from fund
- [ ] `PUT /funds/{fund_id}/entities/{entity_id}` - Update entity role/primary status

## Phase 3: Integration and Testing

### 3.1 Update Main Application (HIGH PRIORITY)

**File**: `backend/main.py`
**Dependencies**: All API routers
**Estimated Time**: 0.5 days

**Tasks**:

- [ ] Add fund router to main FastAPI app
- [ ] Add entity router to main FastAPI app
- [ ] Add fund-entity router to main FastAPI app
- [ ] Update API documentation

### 3.2 Unit Tests (HIGH PRIORITY)

**Files**: `backend/tests/test_funds.py`, `backend/tests/test_entities.py`
**Dependencies**: All models and APIs
**Estimated Time**: 2 days

**Test Coverage**:

- [ ] Model validation tests
- [ ] API endpoint tests (CRUD operations)
- [ ] Business logic tests (validation, constraints)
- [ ] Error handling tests
- [ ] Database relationship tests

### 3.3 Integration Tests (MEDIUM PRIORITY)

**File**: `backend/tests/test_fund_integration.py`
**Dependencies**: Complete implementation
**Estimated Time**: 1 day

**Test Scenarios**:

- [ ] End-to-end fund creation with entities
- [ ] Fund-entity relationship management
- [ ] Search and filtering functionality
- [ ] Data consistency tests

## Phase 4: Documentation

### 4.2 API Documentation (MEDIUM PRIORITY)

**Dependencies**: Complete API implementation
**Estimated Time**: 0.5 days

**Tasks**:

- [ ] Update OpenAPI/Swagger documentation
- [ ] Add example requests/responses
- [ ] Document error codes and messages

## Dependencies and Blockers

### Upstream Dependencies

- None (this is a foundational use case)

### Downstream Impact

- **CRITICAL**: LP workflows depend on fund_id from this implementation
- **CRITICAL**: SEBI reporting requires fund details
- **CRITICAL**: Portfolio management needs fund context

### External Dependencies

- Database server setup and configuration
- Authentication/authorization system (already implemented)

## Implementation Priority

### Phase 1 (Week 1): Core Database

1. Fund Details Model - **CRITICAL**
2. Entities Model - **CRITICAL**
3. Fund-Entity Relationship - **CRITICAL**
4. Database Migrations - **CRITICAL**

### Phase 2 (Week 2): Core APIs

1. Fund Management API - **CRITICAL**
2. Entity Management API - **HIGH**
3. Fund-Entity Relationship API - **HIGH**

### Phase 3 (Week 3): Testing and Integration

1. Unit Tests - **CRITICAL**
2. Integration Tests - **HIGH**
3. Main App Integration - **CRITICAL**

### Phase 4 (Week 4): Documentation

1. API Documentation - **MEDIUM**

## Success Criteria

- [ ] All fund CRUD operations working via API
- [ ] All entity CRUD operations working via API
- [ ] Fund-entity relationships properly managed
- [ ] All database constraints and validations working
- [ ] 90%+ test coverage on new code
- [ ] API documentation complete and accurate
- [ ] No breaking changes to existing LP functionality

## Risk Mitigation

### Technical Risks

- **Database migration failures**: Test migrations thoroughly in staging environment
- **Performance issues with large datasets**: Add proper indexing and pagination
- **API response time**: Implement caching for frequently accessed fund data

### Business Risks

- **Data validation failures**: Implement comprehensive validation at model and API levels
- **Regulatory compliance**: Ensure all required fields are captured and validated
- **User experience**: Provide clear error messages and validation feedback
