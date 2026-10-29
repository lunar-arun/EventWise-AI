from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.repository import EventRepository
from app.database.session import get_db
from app.schemas.event import EventDetailResponse
from app.services.event_service import EventService
from app.services.planner_service import PlannerService

router = APIRouter(prefix="/api", tags=["AI Event Planner"])


@router.post("/events/{event_id}/generate-plan", response_model=EventDetailResponse)
def generate_event_plan(
    event_id: int,
    reset_budget: bool = Query(default=False, description="Reset category allocations to default template"),
    reset_timeline: bool = Query(default=False, description="Regenerate timeline milestones"),
    db: Session = Depends(get_db),
) -> EventDetailResponse:
    event = EventRepository.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event {event_id} not found.")

    updated_event = PlannerService.generate_plan_for_event(
        db=db,
        event=event,
        reset_budget_allocations=reset_budget,
        reset_timeline=reset_timeline,
    )
    return EventService.to_detail_response(updated_event)
