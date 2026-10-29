from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.repository import EventRepository
from app.database.session import get_db
from app.schemas.event import (
    DashboardResponse,
    EventCreate,
    EventDetailResponse,
    EventSummaryCard,
    EventUpdate,
)
from app.services.budget_service import BudgetValidationError
from app.services.event_service import EventService

router = APIRouter(prefix="/api", tags=["Events & Dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
def get_dashboard(db: Session = Depends(get_db)) -> DashboardResponse:
    return EventService.get_dashboard_summary(db)


@router.get("/events", response_model=list[EventSummaryCard])
def list_events(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[EventSummaryCard]:
    return EventService.list_event_summaries(db, skip=skip, limit=limit)


@router.post("/events", response_model=EventDetailResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    payload: EventCreate,
    db: Session = Depends(get_db),
) -> EventDetailResponse:
    try:
        return EventService.create_event(db, payload)
    except BudgetValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/events/{event_id}", response_model=EventDetailResponse)
def get_event(
    event_id: int,
    db: Session = Depends(get_db),
) -> EventDetailResponse:
    event = EventRepository.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event {event_id} not found.")
    return EventService.to_detail_response(event)


@router.patch("/events/{event_id}", response_model=EventDetailResponse)
def update_event(
    event_id: int,
    payload: EventUpdate,
    db: Session = Depends(get_db),
) -> EventDetailResponse:
    event = EventRepository.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event {event_id} not found.")
    try:
        return EventService.update_event(db, event, payload)
    except BudgetValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/events/{event_id}", status_code=status.HTTP_200_OK)
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    event = EventRepository.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event {event_id} not found.")
    EventRepository.delete_event(db, event)
    return {"status": "deleted", "message": f"Event {event_id} deleted."}
