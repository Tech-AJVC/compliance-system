from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional, List
from enum import Enum


class TaskState(str, Enum):
    OPEN = "Open"
    PENDING = "Pending"
    REVIEW_REQUIRED = "Review Required"
    COMPLETED = "Completed"
    OVERDUE = "Overdue"


class TaskCategory(str, Enum):
    SEBI = "SEBI"
    RBI = "RBI"
    IT_GST = "IT/GST"
    LP = "LP"
    OTHER = "Other"

class DocumentInfo(BaseModel):
    document_id: UUID4
    name: str
    category: str
    drive_link: Optional[str] = None

    class Config:
        from_attributes = True


class ComplianceTaskBase(BaseModel):
    description: str
    deadline: datetime
    category: TaskCategory
    assignee_id: UUID4
    reviewer_id: Optional[UUID4] = None
    approver_id: Optional[UUID4] = None
    recurrence: Optional[str] = None
    dependent_task_id: Optional[UUID4] = None


class ComplianceTaskCreate(ComplianceTaskBase):
    pass


class ComplianceTaskUpdate(BaseModel):
    state: Optional[TaskState] = None
    description: Optional[str] = None
    deadline: Optional[datetime] = None
    category: Optional[TaskCategory] = None
    assignee_id: Optional[UUID4] = None
    reviewer_id: Optional[UUID4] = None
    approver_id: Optional[UUID4] = None
    recurrence: Optional[str] = None
    dependent_task_id: Optional[UUID4] = None


class ComplianceTaskResponse(ComplianceTaskBase):
    compliance_task_id: UUID4
    state: TaskState
    created_at: datetime
    updated_at: datetime
    assignee_name: Optional[str] = None  # Added assignee name field
    reviewer_name: Optional[str] = None  # Added reviewer name field
    approver_name: Optional[str] = None  # Added approver name field
    documents: List[DocumentInfo] = []  # List of associated document info

    class Config:
        from_attributes = True


class ComplianceTaskList(BaseModel):
    """Response model for paginated task list"""
    tasks: List[ComplianceTaskResponse]
    total: int

    class Config:
        from_attributes = True
