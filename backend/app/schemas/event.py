from datetime import date, datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator

from app.schemas.budget import BudgetSummaryResponse
from app.schemas.knowledge import SourceCitation
from app.schemas.task import TaskResponse

EventTypeLiteral = Literal["wedding", "birthday", "community"]


class ThemeRecommendation(BaseModel):
    title: str
    tagline: str
    description: str
    decor_highlights: list[str]
    catering_notes: str
    estimated_tier: str = "Illustrative Estimate"
    source_Backed: bool = False


class EventCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=200)
    event_type: EventTypeLiteral
    location: str = Field(..., min_length=2, max_length=200)
    total_budget: int = Field(..., gt=0, le=1_000_000_000, description="Total budget in integer INR")
    guest_count: int = Field(..., gt=0, le=100_000)
    event_date: str = Field(..., description="YYYY-MM-DD")
    preferred_theme: Optional[str] = Field(default="", max_length=200)
    dietary_requirements: Optional[str] = Field(default="", max_length=300)
    additional_preferences: Optional[str] = Field(default="", max_length=2000)
    generate_initial_plan: bool = True

    @field_validator("name", "location")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty.")
        return cleaned

    @field_validator("event_date")
    @classmethod
    def validate_iso_date(cls, v: str) -> str:
        date.fromisoformat(v)
        return v


class EventUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=200)
    event_type: Optional[EventTypeLiteral] = None
    location: Optional[str] = Field(default=None, min_length=2, max_length=200)
    total_budget: Optional[int] = Field(default=None, gt=0, le=1_000_000_000)
    user_approved_budget_change: bool = False
    guest_count: Optional[int] = Field(default=None, gt=0, le=100_000)
    event_date: Optional[str] = None
    preferred_theme: Optional[str] = Field(default=None, max_length=200)
    dietary_requirements: Optional[str] = Field(default=None, max_length=300)
    additional_preferences: Optional[str] = Field(default=None, max_length=2000)
    regenerate_plan: bool = False

    @field_validator("event_date")
    @classmethod
    def validate_optional_iso_date(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            date.fromisoformat(v)
        return v


class EventSummaryCard(BaseModel):
    id: int
    name: str
    event_type: EventTypeLiteral
    location: str
    total_budget: int
    guest_count: int
    event_date: str
    preferred_theme: str
    dietary_requirements: str
    summary: str
    total_tasks: int
    completed_tasks: int
    completion_percentage: float
    planned_spending: int
    actual_spending: int
    remaining_budget: int
    level_badge: str
    created_at: datetime
    updated_at: datetime


class EventDetailResponse(BaseModel):
    id: int
    name: str
    event_type: EventTypeLiteral
    location: str
    total_budget: int
    guest_count: int
    event_date: str
    preferred_theme: str
    dietary_requirements: str
    additional_preferences: str
    summary: str
    theme_recommendations: list[ThemeRecommendation]
    ai_suggestions: list[str]
    citations: list[SourceCitation]
    missing_evidence_note: str
    generation_mode: str
    illustrative_price_notice: str = (
        "Sample costs and budget allocations are illustrative estimates in INR, "
        "not verified live vendor prices, ratings, or booking confirmations."
    )
    budget: BudgetSummaryResponse
    tasks: list[TaskResponse]
    created_at: datetime
    updated_at: datetime


class ActivityItem(BaseModel):
    id: str
    category: Literal["event", "task", "expense", "knowledge", "chat"]
    title: str
    detail: str
    timestamp: datetime
    event_id: Optional[int] = None


class DashboardResponse(BaseModel):
    total_events: int
    upcoming_events_count: int
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    overall_completion_percentage: float
    total_budget_across_events: int
    total_planned_across_events: int
    total_actual_across_events: int
    remaining_budget_across_events: int
    indexed_documents_count: int
    upcoming_events: list[EventSummaryCard]
    upcoming_quests: list[TaskResponse]
    recent_activity: list[ActivityItem]
