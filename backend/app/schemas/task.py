from datetime import date, datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator

TaskStatusType = Literal["pending", "in_progress", "completed"]
TaskPriorityType = Literal["low", "medium", "high"]


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=250)
    description: Optional[str] = Field(default="", max_length=1000)
    milestone_label: str = Field(default="Custom Quest", min_length=2, max_length=120)
    due_date: str = Field(..., description="YYYY-MM-DD")
    status: TaskStatusType = "pending"
    priority: TaskPriorityType = "medium"
    category: str = Field(default="General", min_length=2, max_length=100)

    @field_validator("due_date")
    @classmethod
    def validate_due_date(cls, v: str) -> str:
        date.fromisoformat(v)
        return v


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=250)
    description: Optional[str] = Field(default=None, max_length=1000)
    milestone_label: Optional[str] = Field(default=None, min_length=2, max_length=120)
    due_date: Optional[str] = None
    status: Optional[TaskStatusType] = None
    priority: Optional[TaskPriorityType] = None
    category: Optional[str] = Field(default=None, min_length=2, max_length=100)

    @field_validator("due_date")
    @classmethod
    def validate_optional_due_date(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            date.fromisoformat(v)
        return v


class TaskResponse(BaseModel):
    id: int
    event_id: int
    title: str
    description: str
    milestone_label: str
    due_date: str
    status: TaskStatusType
    priority: TaskPriorityType
    category: str
    is_clamped: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TimelineSummaryResponse(BaseModel):
    event_id: int
    event_name: str
    event_type: str
    event_date: str
    days_until_event: int
    schedule_notice: Optional[str] = None
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    pending_tasks: int
    completion_percentage: float
    tasks: list[TaskResponse]
