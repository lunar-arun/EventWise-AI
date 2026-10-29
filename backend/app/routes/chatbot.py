from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.repository import ChatRepository
from app.database.session import get_db
from app.schemas.chat import (
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    ChatSessionSummary,
    ProposedBudgetChange,
)
from app.schemas.knowledge import SourceCitation
from app.services.chat_service import ChatService

router = APIRouter(prefix="/api", tags=["AI Planning Chatbot"])


@router.post("/chat", response_model=ChatResponse)
def post_chat_message(
    payload: ChatRequest,
    db: Session = Depends(get_db),
) -> ChatResponse:
    try:
        return ChatService.handle_chat(db, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/chat/sessions", response_model=list[ChatSessionSummary])
def list_chat_sessions(
    event_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
) -> list[ChatSessionSummary]:
    sessions = ChatRepository.list_sessions(db, event_id=event_id)
    return [
        ChatSessionSummary(
            id=s.id,
            event_id=s.event_id,
            title=s.title,
            message_count=len(s.messages or []),
            updated_at=s.updated_at,
        )
        for s in sessions
    ]


@router.get("/chat/sessions/{session_id}", response_model=list[ChatMessageResponse])
def get_chat_session_messages(
    session_id: int,
    db: Session = Depends(get_db),
) -> list[ChatMessageResponse]:
    session = ChatRepository.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chat session {session_id} not found.")
    return [
        ChatMessageResponse(
            id=m.id,
            session_id=m.session_id,
            event_id=m.event_id,
            role=m.role,  # type: ignore[arg-type]
            content=m.content,
            citations=[SourceCitation.model_validate(c) for c in (m.citations or [])],
            proposed_changes=(
                ProposedBudgetChange.model_validate(m.proposed_changes)
                if m.proposed_changes
                else None
            ),
            created_at=m.created_at,
        )
        for m in session.messages
    ]
