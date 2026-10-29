from datetime import datetime
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field

from app.schemas.knowledge import SourceCitation


class ProposedBudgetChange(BaseModel):
    action_type: Literal["propose_budget_reduction", "propose_budget_reallocation", "propose_preference_update"]
    summary: str
    current_total_budget: int
    proposed_total_budget: int
    proposed_categories: list[dict[str, Any]] = Field(default_factory=list)
    proposed_preferences: dict[str, Any] = Field(default_factory=dict)
    requires_user_approval: bool = True
    warning: str = (
        "EventWise AI never changes your approved budget silently. "
        "Review and click 'Approve & Apply Proposal' to persist these changes."
    )


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=2000)
    event_id: Optional[int] = None
    session_id: Optional[int] = None


class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    event_id: Optional[int] = None
    role: Literal["user", "assistant"]
    content: str
    citations: list[SourceCitation] = Field(default_factory=list)
    proposed_changes: Optional[ProposedBudgetChange] = None
    created_at: datetime


class ChatResponse(BaseModel):
    session_id: int
    event_id: Optional[int] = None
    reply: str
    suggestions: list[str] = Field(default_factory=list)
    citations: list[SourceCitation] = Field(default_factory=list)
    proposed_changes: Optional[ProposedBudgetChange] = None
    missing_evidence_note: Optional[str] = None
    generation_mode: str = "ollama"
    history: list[ChatMessageResponse] = Field(default_factory=list)


class ChatSessionSummary(BaseModel):
    id: int
    event_id: Optional[int] = None
    title: str
    message_count: int
    updated_at: datetime
