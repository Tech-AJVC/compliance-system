from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class TaskStats(BaseModel):
    """Schema for task statistics report"""
    total_tasks: int
    completed_tasks: int
    overdue_tasks: int
    open_tasks: int
    pending_tasks: int
    review_required_tasks: int

    class Config:
        from_attributes = True
