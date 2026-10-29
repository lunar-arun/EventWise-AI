from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator

AllowedEventTypeFilter = Literal["wedding", "birthday", "community", "general"]


class SourceCitation(BaseModel):
    document_id: str
    chunk_id: str
    title: str
    filename: str
    category: str = "general"
    event_type: str = "general"
    location: str = "general"
    source_label: str = "Curated EventWise Guide"
    is_illustrative: bool = True
    excerpt: str
    distance: float = Field(..., description="Raw vector L2/cosine distance from ChromaDB (lower is closer)")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Normalized similarity score (not a probability of truth)")


class KnowledgeEntryCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=250)
    content: str = Field(..., min_length=20, max_length=100000)
    event_type: AllowedEventTypeFilter = "general"
    category: str = Field(default="general", min_length=2, max_length=100)
    location: str = Field(default="general", min_length=2, max_length=150)
    source_label: str = Field(default="User Structured Entry (Illustrative)", min_length=2, max_length=250)
    is_illustrative: bool = True

    @field_validator("title", "content", "category", "location", "source_label")
    @classmethod
    def strip_text(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Field cannot be empty or whitespace only.")
        return cleaned


class KnowledgeEntryUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=250)
    content: Optional[str] = Field(default=None, min_length=20, max_length=100000)
    event_type: Optional[AllowedEventTypeFilter] = None
    category: Optional[str] = Field(default=None, min_length=2, max_length=100)
    location: Optional[str] = Field(default=None, min_length=2, max_length=150)
    source_label: Optional[str] = Field(default=None, min_length=2, max_length=250)
    is_illustrative: Optional[bool] = None


class KnowledgeDocumentResponse(BaseModel):
    id: str
    title: str
    filename: str
    file_type: str
    event_type: str
    category: str
    location: str
    source_label: str
    is_illustrative: bool
    status: str
    chunk_count: int
    error_message: Optional[str] = None
    raw_content: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000)
    event_type: Optional[str] = None
    category: Optional[str] = None
    location: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=20)


class KnowledgeSearchResponse(BaseModel):
    query: str
    results: list[SourceCitation]
    fallback_applied: bool = False
    fallback_reason: Optional[str] = None
    total_found: int
