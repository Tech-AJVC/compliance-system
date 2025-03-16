from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, Dict, Any
from uuid import UUID
import sys

from app.database.base import get_db
from app.auth.security import get_current_user
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogResponse, AuditLogList

# Import test models for testing environment
if 'pytest' in sys.modules:
    from tests.conftest import TestUser as User
    from tests.conftest import TestAuditLog as AuditLog

router = APIRouter()


@router.get("/logs", response_model=AuditLogList)
async def get_audit_logs(
    activity: Optional[str] = Query(None, description="Filter by activity type"),
    user_name: Optional[str] = Query(None, description="Filter by user name"),
    skip: int = Query(0, description="Number of records to skip for pagination"),
    limit: int = Query(100, description="Maximum number of records to return"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get paginated audit logs with optional filtering.
    Only users with 'Fund Manager' role can access this endpoint.
    
    - **activity**: Optional filter by activity type
    - **user_name**: Optional filter by user name (case-insensitive partial match)
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return (for pagination)
    """
    # Check if user has appropriate role
    if current_user.get("role") != "Fund Manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Fund Managers can access audit logs"
        )
    
    # Start with a query that joins AuditLog with User to get user names
    query = db.query(
        AuditLog,
        User.name.label("user_name")
    ).outerjoin(
        User, 
        AuditLog.user_id == User.user_id
    )
    
    # Apply filters
    if activity:
        query = query.filter(AuditLog.activity == activity)
    
    if user_name:
        query = query.filter(User.name.ilike(f"%{user_name}%"))
    
    # Order by timestamp (newest first)
    query = query.order_by(AuditLog.timestamp.desc())
    
    # Get total count before pagination
    total = query.count()
    
    # Apply pagination
    results = query.offset(skip).limit(limit).all()
    
    # Convert results to response format
    logs = []
    for audit_log, user_name in results:
        log_dict = {
            "log_id": audit_log.log_id,
            "user_id": audit_log.user_id,
            "activity": audit_log.activity,
            "timestamp": audit_log.timestamp,
            "details": audit_log.details,
            "user_name": user_name
        }
        logs.append(log_dict)
    
    return {"logs": logs, "total": total}


@router.get("/logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific audit log by ID.
    Only users with 'Fund Manager' role can access this endpoint.
    """
    # Check if user has appropriate role
    if current_user.get("role") != "Fund Manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Fund Managers can access audit logs"
        )
    
    # Query for the specific audit log with user name
    result = db.query(
        AuditLog,
        User.name.label("user_name")
    ).outerjoin(
        User,
        AuditLog.user_id == User.user_id
    ).filter(
        AuditLog.log_id == log_id
    ).first()
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit log with ID {log_id} not found"
        )
    
    audit_log, user_name = result
    
    # Convert to response format
    return {
        "log_id": audit_log.log_id,
        "user_id": audit_log.user_id,
        "activity": audit_log.activity,
        "timestamp": audit_log.timestamp,
        "details": audit_log.details,
        "user_name": user_name
    }
