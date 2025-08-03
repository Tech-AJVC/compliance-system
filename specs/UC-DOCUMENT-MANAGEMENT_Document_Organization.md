# UC-DOCUMENT-MANAGEMENT — Document Organization

> **Use-case category:** Document Management  
> **Primary actor:** Fund Manager, Compliance Officer  
> **Secondary actors:** All Users

---

## 1. Source References

| Document                      | Section(s)                                                |
| ----------------------------- | --------------------------------------------------------- |
| **PRD Phase-2**               | §8 – "Document Repository Management"                    |
| **TRD Phase-2**               | §18 – Document Folder & Organization APIs               |
| **UX Requirements – Phase-2** | Screen flows: "Document Repository", "Folder Management" |

### 1.1 PRD Extract

> _"The system shall provide a hierarchical document organization system allowing users to categorize documents by quarters, entity types, and business functions for efficient retrieval and compliance tracking..."_

### 1.2 TRD Extract

> _API: `POST /document-folders` → creates hierarchical folder structure_  
> _Data model: `DOCUMENT_FOLDERS` table with parent-child relationships_

### 1.3 UX Extract

> _Document repository with sorting options, hierarchical folder structure, and integrated search functionality_

### 1.4 Enhanced Document Organization (from Figma)

#### Document Repository Main View

- **Page Title**: "Documents"
- **Sort Options**: 
  - "Sort By - Portfolio Companies" 
  - "Sort By - Quarters"
  - "Sort By - Limited Partners"
- **Search Field**: "Search documents..." placeholder with filter icon
- **Folder Structure**: Hierarchical display with folder icons

#### Folder Organization Types

##### Quarter-Based Organization
- **Root Folders**: Q1'25, Q4'24, Q3'24, Q2'24, Q1'24
- **Subfolder Structure**: 
  - SEBI (regulatory documents)
  - RBI (banking documents)
  - IT/GST (tax documents)
  - MCA (corporate affairs)

##### Entity-Based Organization
- **Limited Partner Folders**: 
  - Warren Buffet, Peter Lynch, Benjamin Graham
  - Charlie Munger, George Soros, Ray Dalio
  - Mark Cuban, Peter Thiel, Bill Gates, Cathie Wood
- **Portfolio Company Folders**:
  - Yinara, Scuba, Thread Factory
  - Chop Finance, Trufides

##### Document List View
- **Document Items**: Show file name, type, and linked tasks
- **Document Actions**: Three-dot menu with options
- **Linked Task Display**: "LinkedTask" associations
- **Date Information**: "Date Uploaded" column
- **File Types**: Support for PDF, XML, Excel, and other formats

#### Search and Filter Capabilities
- **Global Search**: Search across all documents and folders
- **Filter Options**: By document type, date range, entity
- **Advanced Search**: Search within document content (future enhancement)

---

## 2. Database Schema

### DOCUMENT_FOLDERS

```sql
CREATE TABLE DOCUMENT_FOLDERS (
    folder_id INT PRIMARY KEY,
    folder_name VARCHAR(255) NOT NULL, -- Q1'25, SEBI, Warren Buffet, Yinara, etc.
    parent_folder_id INT REFERENCES DOCUMENT_FOLDERS(folder_id),
    folder_type VARCHAR(50) NOT NULL, -- Quarter, Category, LP, Portfolio, Root
    entity_reference_id INT, -- LP ID or Portfolio Company ID if applicable
    fund_id INT REFERENCES FUND_DETAILS(fund_id),
    folder_path VARCHAR(500), -- computed path like /Q1'25/SEBI/
    sort_order INT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(parent_folder_id, folder_name)
);
```

### DOCUMENTS (Enhanced)

```sql
ALTER TABLE DOCUMENTS ADD COLUMN folder_id INT REFERENCES DOCUMENT_FOLDERS(folder_id);
ALTER TABLE DOCUMENTS ADD COLUMN linked_entity_type VARCHAR(50); -- LP, Portfolio, Fund, Task
ALTER TABLE DOCUMENTS ADD COLUMN linked_entity_id INT; -- Reference to LP, Portfolio, etc.
ALTER TABLE DOCUMENTS ADD COLUMN tags VARCHAR(500); -- Comma-separated tags for categorization
ALTER TABLE DOCUMENTS ADD COLUMN file_size_bytes BIGINT;
ALTER TABLE DOCUMENTS ADD COLUMN mime_type VARCHAR(100);
```

### DOCUMENT_LINKS

```sql
CREATE TABLE DOCUMENT_LINKS (
    link_id SERIAL PRIMARY KEY,
    document_id INT REFERENCES DOCUMENTS(document_id),
    linked_entity_type VARCHAR(50) NOT NULL, -- Task, LP, Portfolio, Fund
    linked_entity_id INT NOT NULL,
    link_type VARCHAR(50), -- supporting, output, reference
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## 3. API Endpoints

### Document Folder Management

Resource: /document-folders

```
GET /document-folders?fund_id=12&folder_type=Quarter
```

Returns hierarchical folder structure:
```json
[
  {
    "folder_id": 100,
    "folder_name": "Q1'25",
    "folder_type": "Quarter",
    "parent_folder_id": null,
    "folder_path": "/Q1'25/",
    "children": [
      {
        "folder_id": 101,
        "folder_name": "SEBI",
        "folder_type": "Category",
        "parent_folder_id": 100,
        "folder_path": "/Q1'25/SEBI/",
        "document_count": 5
      },
      {
        "folder_id": 102,
        "folder_name": "RBI",
        "folder_type": "Category",
        "parent_folder_id": 100,
        "folder_path": "/Q1'25/RBI/",
        "document_count": 3
      }
    ],
    "document_count": 15,
    "sort_order": 1
  }
]
```

```
POST /document-folders
JSON
{
  "folder_name": "Q2'25",
  "folder_type": "Quarter",
  "parent_folder_id": null,
  "fund_id": 12,
  "sort_order": 2
}
```

### Document Organization

Resource: /documents/organized

```
GET /documents/organized?folder_id=101&fund_id=12
```

Returns documents in specific folder:
```json
{
  "folder_info": {
    "folder_id": 101,
    "folder_name": "SEBI",
    "folder_path": "/Q1'25/SEBI/",
    "folder_type": "Category"
  },
  "documents": [
    {
      "document_id": 150,
      "name": "SEBI-Report-Q1-2025.xml",
      "category": "SEBI Report",
      "uploaded_date": "2025-05-08T09:14:11Z",
      "file_path": "https://drive.google.com/file/d/xyz",
      "file_size_bytes": 2048576,
      "mime_type": "application/xml",
      "linked_tasks": [
        {
          "task_id": 450,
          "task_title": "Quarterly SEBI Filing",
          "link_type": "output"
        }
      ],
      "linked_entities": [
        {
          "entity_type": "Fund",
          "entity_id": 12,
          "entity_name": "AJVC Fund"
        }
      ]
    }
  ],
  "subfolders": []
}
```

### Bulk Document Operations

Resource: /documents/bulk

```
POST /documents/bulk/move
JSON
{
  "document_ids": [150, 151, 152],
  "target_folder_id": 102,
  "move_reason": "Quarterly reorganization"
}
```

```
POST /documents/bulk/link-to-entity
JSON
{
  "document_ids": [150, 151],
  "entity_type": "LP",
  "entity_id": 101,
  "link_type": "supporting"
}
```

### Document Search

Resource: /documents/search

```
GET /documents/search?q=SEBI&folder_type=Quarter&date_from=2025-01-01
```

Returns:
```json
{
  "results": [
    {
      "document_id": 150,
      "name": "SEBI-Report-Q1-2025.xml",
      "folder_path": "/Q1'25/SEBI/",
      "match_score": 0.95,
      "highlighted_content": "...SEBI Activity Report...",
      "uploaded_date": "2025-05-08T09:14:11Z"
    }
  ],
  "total_results": 1,
  "search_query": "SEBI",
  "filters_applied": {
    "folder_type": "Quarter",
    "date_from": "2025-01-01"
  }
}
```

---

## 4. Functional Requirements

### 4.1 Folder Management
- **Hierarchical Structure**: Support multi-level folder nesting
- **Auto-Organization**: Automatically categorize documents based on entity types
- **Flexible Sorting**: Support multiple organization schemes (by quarter, entity, category)
- **Bulk Operations**: Move multiple documents between folders efficiently

### 4.2 Document Linking
- **Entity Associations**: Link documents to LPs, portfolio companies, tasks, and funds
- **Link Types**: Distinguish between supporting documents, outputs, and references
- **Automatic Linking**: Auto-link documents based on upload context
- **Relationship Tracking**: Maintain audit trail of document relationships

### 4.3 Search and Discovery
- **Global Search**: Search across all document names and metadata
- **Filtered Search**: Search within specific folders or entity types
- **Content Search**: Search within document content (PDF text extraction)
- **Advanced Filters**: Filter by date range, file type, entity associations

### 4.4 Access Control
- **Folder Permissions**: Control access to folders based on user roles
- **Document Security**: Ensure sensitive documents are properly protected
- **Audit Logging**: Track all document access and modifications

---

## 5. Use Case Flows

### 5.1 Document Upload and Organization
1. User uploads document via drag-and-drop or file selector
2. System analyzes document metadata and content
3. System suggests appropriate folder based on content and context
4. User confirms or modifies folder placement
5. System automatically links document to relevant entities
6. System updates folder statistics and search index

### 5.2 Folder Structure Creation
1. User navigates to document repository
2. User selects organization type (Quarter, LP, Portfolio)
3. System generates appropriate folder structure
4. User can create custom subfolders as needed
5. System maintains folder hierarchy and path information

### 5.3 Document Search and Retrieval
1. User enters search query in global search field
2. System searches document names, content, and metadata
3. System returns ranked results with highlighting
4. User can apply additional filters to narrow results
5. User selects document to view or download
6. System logs access for audit purposes

---

## 6. Folder Organization Examples

### By Quarters (Regulatory/Compliance Focus)
```
📁 Q1'25
  📁 SEBI
    📄 SEBI-Activity-Report-Q1-2025.xml
    📄 Fund-Portfolio-Summary.pdf
  📁 RBI
    📄 Bank-Statement-Q1.pdf
  📁 IT/GST
    📄 GST-Returns-Q1.pdf
  📁 MCA
    📄 Annual-Filing-Form11.pdf

📁 Q4'24
  📁 SEBI
  📁 RBI
  📁 IT/GST
  📁 MCA
```

### By Limited Partners (Investor Focus)
```
📁 Warren Buffet
  📄 KYC-Document.pdf
  📄 Contribution-Agreement.pdf
  📄 CML-Warren.pdf
  📄 Drawdown-Notice-Q1.pdf

📁 Peter Lynch
  📄 KYC-Document.pdf
  📄 Contribution-Agreement.pdf

📁 Benjamin Graham
  📄 KYC-Document.pdf
  📄 Contribution-Agreement.pdf
```

### By Portfolio Companies (Investment Focus)
```
📁 Yinara
  📄 SHA-Agreement.pdf
  📄 Investment-Summary.pdf
  📄 Valuation-Report.pdf

📁 Scuba
  📄 SHA-Agreement.pdf
  📄 Due-Diligence-Report.pdf

📁 Thread Factory
  📄 SHA-Agreement.pdf
  📄 Financial-Statements.pdf
```

---

## 7. Permission Matrix

| Role                | Create Folders | Upload Docs | Move Docs | Delete Docs | View All |
|---------------------|----------------|-------------|-----------|-------------|----------|
| Fund Manager        | ✓              | ✓           | ✓         | ✓           | ✓        |
| Compliance Officer  | ✓              | ✓           | ✓         | ✓           | ✓        |
| Limited Partner     | ✗              | ✗           | ✗         | ✗           | Own Only |
| Portfolio Company   | ✗              | ✗           | ✗         | ✗           | Own Only |
| Auditor            | ✗              | ✓           | ✗         | ✗           | ✓        |
| Legal              | ✗              | ✓           | ✗         | ✗           | ✓        | 