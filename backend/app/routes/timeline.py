from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.repository import EventRepository, TaskRepository
from app.database.session import get_db
from app.schemas.task import (
    TaskCreate,
    TaskResponse,
    TaskUpdate,
    TimelineSummaryResponse,
)
from app.services.timeline_service import TimelineService

router = APIRouter(prefix="/api", tags=["Timeline & Tasks"])


@router.get("/events/{event_id}/tasks", response_model=TimelineSummaryResponse)
def get_event_tasks(
    event_id: int,
    db: Session = Depends(get_db),
) -> TimelineSummaryResponse:
    event = EventRepository.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event {event_id} not found.")
    return TimelineService.compute_timeline_summary(event)


@router.post("/events/{event_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_event_task(
    event_id: int,
    payload: TaskCreate,
    db: Session = Depends(get_db),
) -> TaskResponse:
    event = EventRepository.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event {event_id} not found.")
    created = TimelineService.add_custom_task(db, event_id=event.id, task_in=payload)
    return TaskResponse.model_validate(created)


@router.patch("/tasks/{task_id}", response_model=TaskResponse)
def update_task_status(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
) -> TaskResponse:
    try:
        updated = TimelineService.update_task(db, task_id=task_id, update_in=payload)
        return TaskResponse.model_validate(updated)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/tasks/{task_id}", status_code=status.HTTP_200_OK)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
) -> dict[str, str]:
    task = TaskRepository.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found.")
    TaskRepository.delete_task(db, task)
    return {"status": "deleted", "message": f"Task {task_id} deleted."}
