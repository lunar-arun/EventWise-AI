from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.repository import BudgetRepository, EventRepository
from app.database.session import get_db
from app.schemas.budget import (
    BudgetSummaryResponse,
    BudgetUpdateRequest,
    ExpenseCreate,
)
from app.services.budget_service import BudgetService, BudgetValidationError

router = APIRouter(prefix="/api", tags=["Budget Planner"])


@router.get("/events/{event_id}/budget", response_model=BudgetSummaryResponse)
def get_event_budget(
    event_id: int,
    db: Session = Depends(get_db),
) -> BudgetSummaryResponse:
    event = EventRepository.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event {event_id} not found.")
    return BudgetService.compute_budget_summary(event)


@router.put("/events/{event_id}/budget", response_model=BudgetSummaryResponse)
def update_event_budget(
    event_id: int,
    payload: BudgetUpdateRequest,
    db: Session = Depends(get_db),
) -> BudgetSummaryResponse:
    event = EventRepository.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event {event_id} not found.")
    try:
        return BudgetService.update_budget_allocations(db, event, payload)
    except BudgetValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/events/{event_id}/expenses",
    response_model=BudgetSummaryResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_event_expense(
    event_id: int,
    payload: ExpenseCreate,
    db: Session = Depends(get_db),
) -> BudgetSummaryResponse:
    event = EventRepository.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event {event_id} not found.")
    try:
        return BudgetService.add_expense(db, event, payload)
    except BudgetValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/events/{event_id}/expenses/{expense_id}", response_model=BudgetSummaryResponse)
def delete_event_expense(
    event_id: int,
    expense_id: int,
    db: Session = Depends(get_db),
) -> BudgetSummaryResponse:
    event = EventRepository.get_event(db, event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Event {event_id} not found.")
    expense = BudgetRepository.get_expense(db, expense_id=expense_id, event_id=event_id)
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Expense {expense_id} not found.")
    BudgetRepository.delete_expense(db, expense)
    db.refresh(event)
    return BudgetService.compute_budget_summary(event)
