from pydantic import BaseModel, UUID4
from typing import Optional, List
from datetime import datetime


class AuditLogBase(BaseModel):
    """Base schema for audit log data"""
    activity: str
    details: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    """Schema for creating audit logs"""
    user_id: Optional[UUID4] = None


class AuditLogResponse(AuditLogBase):
    """Schema for returning audit log data"""
    log_id: UUID4
    user_id: Optional[UUID4] = None
    timestamp: datetime
    user_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class AuditLogList(BaseModel):
    """Response model for paginated audit log list"""
    logs: List[AuditLogResponse]
    total: int
    
    class Config:
        from_attributes = True
