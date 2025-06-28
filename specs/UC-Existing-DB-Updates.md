1. USERS (no change)
   Roles Uodated:

["Manager", "Compliance Officer", "Limited Partner", "Portfolio Company", "Auditor", "Legal"]
Sponsor
Trustee
Tax
Accountant
Custodian
Valuer
Investment Officer
Compliance Officer

───────────────────────────── 2. COMPLIANCE*TASKS (+ Phase-2 delta)
─────────────────────────────
• trigger_type: VARCHAR(30) NULL -- periodic,special, manual
(Cron for drawdown sebi activity report, manual for others)
• process_name: VARCHAR(30) NULL
• trigger_value: VARCHAR(100) NULL -- “0 0 4 */3 \_” etc.
• output_document_id: INT NULL FK→DOCUMENTS -- primary artefact

### COMPLIANCE_TASKS Updates

```sql
ALTER TABLE COMPLIANCE_TASKS ADD COLUMN title VARCHAR(255) NOT NULL;
ALTER TABLE COMPLIANCE_TASKS ADD COLUMN process VARCHAR(100);
ALTER TABLE COMPLIANCE_TASKS ADD COLUMN completion_criteria VARCHAR(100);
```

## MISSING DATABASE SCHEMA

### DOCUMENT_FOLDERS (Critical Missing Table)

```sql
CREATE TABLE DOCUMENT_FOLDERS (
    folder_id INT PRIMARY KEY,
    folder_name VARCHAR(255), -- Q1'25, SEBI, Warren Buffet, Yinara, etc.
    parent_folder_id INT REFERENCES DOCUMENT_FOLDERS(folder_id),
    folder_type VARCHAR(50), -- Quarter, Category, LP, Portfolio, Root
    entity_reference_id INT, -- LP ID or Portfolio Company ID if applicable
    fund_id INT REFERENCES FUND_DETAILS(fund_id),
    folder_path VARCHAR(500), -- computed path like /Q1'25/SEBI/
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

### DOCUMENTS Table Updates

```sql
ALTER TABLE DOCUMENTS ADD COLUMN folder_id INT REFERENCES DOCUMENT_FOLDERS(folder_id);
ALTER TABLE DOCUMENTS ADD COLUMN linked_entity_type VARCHAR(50); -- LP, Portfolio, Fund, Task
ALTER TABLE DOCUMENTS ADD COLUMN linked_entity_id INT; -- Reference to LP, Portfolio, etc.
```

## MISSING API ENDPOINTS

### DOCUMENT FOLDER MANAGEMENT (Critical Missing)

Resource: /document-folders
GET /document-folders?fund_id=12&folder_type=Quarter
Returns hierarchical folder structure
JSON
[{
"folder_id": 100,
"folder_name": "Q1'25",
"folder_type": "Quarter",
"parent_folder_id": null,
"folder_path": "/Q1'25/",
"children": [{
"folder_id": 101,
"folder_name": "SEBI",
"folder_type": "Category",
"parent_folder_id": 100,
"folder_path": "/Q1'25/SEBI/"
}],
"document_count": 15
}]

POST /document-folders
JSON
{
"folder_name": "Q2'25",
"folder_type": "Quarter",
"parent_folder_id": null,
"fund_id": 12
}

### DOCUMENT ORGANIZATION (Critical Missing)

Resource: /documents/organized
GET /documents/organized?folder_id=101&fund_id=12
Returns documents in specific folder
JSON
{
"folder_info": {
"folder_id": 101,
"folder_name": "SEBI",
"folder_path": "/Q1'25/SEBI/"
},
"documents": [{
"document_id": 150,
"name": "SEBI-Report-Q1-2025.xml",
"category": "SEBI Report",
"uploaded_date": "2025-05-08T09:14:11Z",
"file_path": "https://drive.google.com/file/d/xyz",
"linked_tasks": ["Quarterly SEBI Filing"]
}],
"subfolders": []
}

### BULK DOCUMENT OPERATIONS (Missing)

Resource: /documents/bulk
POST /documents/bulk/move
JSON
{
"document_ids": [150, 151, 152],
"target_folder_id": 102,
"move_reason": "Quarterly reorganization"
}

POST /documents/bulk/link-to-entity
JSON
{
"document_ids": [150, 151],
"entity_type": "LP",
"entity_id": 101
}

3. TASK_DOCUMENTS (no change)
   ─────────────────────────────
4. DOCUMENTS (delta)
   ─────────────────────────────
   • version: INT DEFAULT 1
   • generated_by_service: VARCHAR(50) NULL -- e.g. “sebi_report_service”

#### Task Management Integration

- **Create Task Form**: Interface for creating compliance tasks
  - Title (required)
  - Description (multi-line text area)
  - Supporting Documents (drag and drop upload)
  - Category (dropdown selection)
  - Process (dropdown selection)
  - Completion Criteria (dropdown selection)
  - Due Date (date picker)
  - Repeat Task (checkbox option)
  - Predecessor Task (dropdown selection)
  - Assign to (dropdown selection)
  - Reviewer (dropdown selection)
  - Final Approver (dropdown selection)

### 12. TASK MANAGEMENT (Enhanced)

Resource: /tasks
POST /tasks
JSON
{
"title": "Quarterly SEBI Filing",
"description": "Complete SEBI activity report for Q1 FY25",
"category": "SEBI",
"process": "Regulatory Filing",
"completion_criteria": "Report Submitted",
"deadline": "2025-06-30T23:59:59Z",
"assignee_id": 5,
"reviewer_id": 3,
"approver_id": 1,
"recurrence": "Quarterly",
"dependent_task_id": null
}

Returns 201
JSON
{
"compliance_task_id": 450,
"created_at": "2025-05-08T09:14:11Z"
}

GET /tasks?category=SEBI&state=Open&assignee_id=5
GET /tasks/{task_id}
PATCH /tasks/{task_id}
DELETE /tasks/{task_id}

### 13. DASHBOARD ANALYTICS (Critical Missing)

Resource: /dashboard
GET /dashboard/stats?fund_id=12
Returns
JSON
{
"total_tasks": 45,
"completed_tasks": 32,
"overdue_tasks": 3,
"pending_tasks": 10,
"compliance_percentage": 71.1,
"upcoming_deadlines": [
{
"task_id": 450,
"title": "Quarterly SEBI Filing",
"deadline": "2025-06-30T23:59:59Z",
"days_remaining": 15
}
],
"recent_activities": [
{
"activity": "Task completed",
"task_title": "LP Drawdown Notice",
"timestamp": "2025-05-08T09:14:11Z"
}
]
}
