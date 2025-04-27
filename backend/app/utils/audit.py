from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from typing import Optional, Dict, Any
import uuid

def log_activity(
    db: Session,
    activity: str,
    user_id: Optional[uuid.UUID] = None,
    details: Optional[str] = None
) -> AuditLog:
    """
    Create an audit log entry for user activity.
    
    Args:
        db: Database session
        activity: Description of the activity (e.g., "document_upload", "login")
        user_id: UUID of the user performing the action (None for system actions)
        details: Additional details about the activity (JSON or text)
    
    Returns:
        The created AuditLog instance
    """
    try:
        # Ensure user_id is either None or a proper UUID object
        parsed_user_id = None
        if user_id is not None:
            if isinstance(user_id, str):
                try:
                    parsed_user_id = uuid.UUID(user_id)
                except ValueError:
                    print(f"Warning: Invalid UUID string: {user_id}")
            else:
                parsed_user_id = user_id
                
        audit_log = AuditLog(
            user_id=parsed_user_id,
            activity=activity,
            details=details
        )
        
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        return audit_log
    except Exception as e:
        db.rollback()
        print(f"Error logging activity: {str(e)}")
        # Return None instead of raising an exception to prevent disrupting main functions
        return None
