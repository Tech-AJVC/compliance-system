from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database.base import get_db
from app.models.compliance_task import ComplianceTask, TaskState
from app.auth.security import get_current_user, check_role
from app.schemas.report import TaskStats
from datetime import datetime
from typing import Dict, Any

router = APIRouter()


@router.get("/tasks-stats", response_model=TaskStats)
async def get_task_stats(
        current_user: Dict[str, Any] = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """
    Get statistics on compliance tasks:
    - Total number of tasks
    - Number of completed tasks
    - Number of overdue tasks
    - Number of open tasks
    - Number of pending tasks
    - Number of review required tasks
    """
    # Total tasks
    total_tasks = db.query(func.count(ComplianceTask.compliance_task_id)).scalar()

    # Completed tasks
    completed_tasks = db.query(func.count(ComplianceTask.compliance_task_id)) \
        .filter(ComplianceTask.state == TaskState.COMPLETED.value) \
        .scalar()

    # Overdue tasks
    now = datetime.utcnow()
    overdue_tasks = db.query(func.count(ComplianceTask.compliance_task_id)) \
        .filter(
        ComplianceTask.state == TaskState.OVERDUE.value,
    ) \
        .scalar()

    # Open tasks
    open_tasks = db.query(func.count(ComplianceTask.compliance_task_id)) \
        .filter(ComplianceTask.state == TaskState.OPEN.value) \
        .scalar()

    # Pending tasks
    pending_tasks = db.query(func.count(ComplianceTask.compliance_task_id)) \
        .filter(ComplianceTask.state == TaskState.PENDING.value) \
        .scalar()

    # Review required tasks
    review_required_tasks = db.query(func.count(ComplianceTask.compliance_task_id)) \
        .filter(ComplianceTask.state == TaskState.REVIEW_REQUIRED.value) \
        .scalar()

    return TaskStats(
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        overdue_tasks=overdue_tasks,
        open_tasks=open_tasks,
        pending_tasks=pending_tasks,
        review_required_tasks=review_required_tasks
    )
