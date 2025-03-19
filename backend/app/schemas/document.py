from pydantic import BaseModel, Field, UUID4
from typing import Optional, List
from datetime import date, datetime
from enum import Enum

class DocumentStatus(str, Enum):
    ACTIVE = "Active"
    PENDING_APPROVAL = "Pending Approval"
    EXPIRED = "Expired"

class DocumentCategory(str, Enum):
    CONTRIBUTION_AGREEMENT = "Contribution Agreement"
    KYC = "KYC"
    NOTIFICATION = "Notification"
    REPORT = "Report"
    OTHER = "Other"

class DocumentBase(BaseModel):
    name: str
    category: DocumentCategory
    status: Optional[DocumentStatus] = DocumentStatus.ACTIVE
    expiry_date: Optional[date] = None
    process_id: Optional[str] = None

class DocumentCreate(DocumentBase):
    pass

class DocumentUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[DocumentCategory] = None
    status: Optional[DocumentStatus] = None
    expiry_date: Optional[date] = None
    process_id: Optional[str] = None

class DocumentInDB(DocumentBase):
    document_id: UUID4
    file_path: str
    date_uploaded: datetime
    drive_file_id: Optional[str] = None
    drive_link: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Legacy fields - will be removed in the future
    uploader_drive_link: Optional[str] = None
    assignee_drive_link: Optional[str] = None
    reviewer_drive_link: Optional[str] = None
    fund_manager_drive_link: Optional[str] = None
    approver_drive_link: Optional[str] = None
    
    class Config:
        from_attributes = True

class Document(BaseModel):
    """Clean document response without legacy drive link fields"""
    document_id: UUID4
    name: str
    category: DocumentCategory
    status: Optional[DocumentStatus] = None
    expiry_date: Optional[date] = None
    process_id: Optional[str] = None
    file_path: str
    date_uploaded: datetime
    drive_file_id: Optional[str] = None
    drive_link: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class DocumentUploadResponse(Document):
    """Schema for document upload response"""
    pass

class TaskDocumentCreate(BaseModel):
    compliance_task_id: UUID4
    document_id: UUID4

class TaskDocumentInDB(TaskDocumentCreate):
    task_document_id: UUID4
    created_at: datetime

    class Config:
        from_attributes = True

class TaskDocument(TaskDocumentInDB):
    pass

class DocumentWithTasks(Document):
    tasks: List[TaskDocumentInDB] = []

class DocumentList(BaseModel):
    """Response model for paginated document list"""
    documents: List[Document]
    total: int
    
    class Config:
        from_attributes = True
