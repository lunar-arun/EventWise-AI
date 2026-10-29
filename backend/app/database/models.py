from datetime import datetime, timezone
from typing import Any
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class EventModel(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    event_type = Column(String(50), nullable=False, index=True)  # wedding | birthday | community
    location = Column(String(200), nullable=False)
    total_budget = Column(Integer, nullable=False)  # Integer INR
    guest_count = Column(Integer, nullable=False)
    event_date = Column(String(20), nullable=False)  # YYYY-MM-DD
    preferred_theme = Column(String(200), nullable=True, default="")
    dietary_requirements = Column(String(300), nullable=True, default="")
    additional_preferences = Column(Text, nullable=True, default="")

    summary = Column(Text, nullable=True, default="")
    theme_recommendations = Column(JSON, nullable=False, default=list)
    ai_suggestions = Column(JSON, nullable=False, default=list)
    citations = Column(JSON, nullable=False, default=list)
    missing_evidence_note = Column(Text, nullable=True, default="")
    generation_mode = Column(String(50), nullable=False, default="pending")

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    budget_categories = relationship(
        "BudgetCategoryModel",
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="BudgetCategoryModel.id",
    )
    expenses = relationship(
        "ExpenseModel",
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="ExpenseModel.id.desc()",
    )
    tasks = relationship(
        "TaskModel",
        back_populates="event",
        cascade="all, delete-orphan",
        order_by="TaskModel.due_date.asc(), TaskModel.id.asc()",
    )
    chat_sessions = relationship(
        "ChatSessionModel",
        back_populates="event",
        cascade="all, delete-orphan",
    )


class BudgetCategoryModel(Base):
    __tablename__ = "budget_categories"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(120), nullable=False)
    planned_amount = Column(Integer, nullable=False)  # Integer INR
    is_emergency_reserve = Column(Boolean, default=False, nullable=False)
    notes = Column(String(500), nullable=True, default="")

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    event = relationship("EventModel", back_populates="budget_categories")


class ExpenseModel(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    category_name = Column(String(120), nullable=False)
    title = Column(String(200), nullable=False)
    amount = Column(Integer, nullable=False)  # Integer INR
    incurred_date = Column(String(20), nullable=False)  # YYYY-MM-DD
    notes = Column(String(500), nullable=True, default="")

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    event = relationship("EventModel", back_populates="expenses")


class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(250), nullable=False)
    description = Column(Text, nullable=True, default="")
    milestone_label = Column(String(120), nullable=False)
    due_date = Column(String(20), nullable=False)  # YYYY-MM-DD
    status = Column(String(30), nullable=False, default="pending")  # pending | in_progress | completed
    priority = Column(String(30), nullable=False, default="medium")  # low | medium | high
    category = Column(String(100), nullable=False, default="General")
    is_clamped = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    event = relationship("EventModel", back_populates="tasks")


class ChatSessionModel(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String(200), nullable=False, default="Event Planning Session")
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    event = relationship("EventModel", back_populates="chat_sessions")
    messages = relationship(
        "ChatMessageModel",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessageModel.id.asc()",
    )


class ChatMessageModel(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(Integer, nullable=True, index=True)
    role = Column(String(30), nullable=False)  # user | assistant
    content = Column(Text, nullable=False)
    citations = Column(JSON, nullable=False, default=list)
    proposed_changes = Column(JSON, nullable=True, default=None)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    session = relationship("ChatSessionModel", back_populates="messages")


class KnowledgeDocumentModel(Base):
    __tablename__ = "knowledge_documents"

    id = Column(String(64), primary_key=True, index=True)
    title = Column(String(250), nullable=False)
    filename = Column(String(250), nullable=False)
    file_type = Column(String(30), nullable=False)  # pdf | txt | csv | json | entry
    file_path = Column(String(500), nullable=True)
    raw_content = Column(Text, nullable=True)
    event_type = Column(String(50), nullable=False, default="general")
    category = Column(String(100), nullable=False, default="general")
    location = Column(String(150), nullable=False, default="general")
    source_label = Column(String(250), nullable=False, default="Curated EventWise Guide")
    is_illustrative = Column(Boolean, default=True, nullable=False)
    status = Column(String(30), nullable=False, default="indexed")  # indexed | processing | failed
    chunk_count = Column(Integer, nullable=False, default=0)
    error_message = Column(Text, nullable=True, default=None)

    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
