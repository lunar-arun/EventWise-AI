from datetime import date
from sqlalchemy.orm import Session

from app.database.models import (
    ChatMessageModel,
    EventModel,
    ExpenseModel,
    KnowledgeDocumentModel,
    TaskModel,
)
from app.database.repository import EventRepository
from app.schemas.event import (
    ActivityItem,
    DashboardResponse,
    EventCreate,
    EventDetailResponse,
    EventSummaryCard,
    EventUpdate,
    ThemeRecommendation,
)
from app.schemas.knowledge import SourceCitation
from app.schemas.task import TaskResponse
from app.services.budget_service import BudgetService, BudgetValidationError
from app.services.planner_service import PlannerService
from app.services.timeline_service import TimelineService


class EventService:
    @staticmethod
    def _to_summary_card(event: EventModel, index: int = 1) -> EventSummaryCard:
        tasks = list(event.tasks or [])
        total_tasks = len(tasks)
        completed_tasks = sum(1 for t in tasks if t.status == "completed")
        pct = round((completed_tasks / total_tasks) * 100.0, 1) if total_tasks > 0 else 0.0

        planned_spending = sum(int(c.planned_amount) for c in (event.budget_categories or []))
        actual_spending = sum(int(e.amount) for e in (event.expenses or []))
        effective_used = actual_spending if actual_spending > 0 else planned_spending
        remaining = int(event.total_budget) - effective_used

        world_map = {"birthday": "1", "wedding": "2", "community": "3"}
        w = world_map.get(event.event_type, "1")
        level_badge = f"WORLD {w}-{index}"

        return EventSummaryCard(
            id=event.id,
            name=event.name,
            event_type=event.event_type,  # type: ignore[arg-type]
            location=event.location,
            total_budget=int(event.total_budget),
            guest_count=int(event.guest_count),
            event_date=event.event_date,
            preferred_theme=event.preferred_theme or "",
            dietary_requirements=event.dietary_requirements or "",
            summary=event.summary or "",
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            completion_percentage=pct,
            planned_spending=planned_spending,
            actual_spending=actual_spending,
            remaining_budget=remaining,
            level_badge=level_badge,
            created_at=event.created_at,
            updated_at=event.updated_at,
        )

    @staticmethod
    def to_detail_response(event: EventModel) -> EventDetailResponse:
        budget_summary = BudgetService.compute_budget_summary(event)
        tasks_sorted = sorted(list(event.tasks or []), key=lambda t: (t.due_date, t.id or 0))
        themes = [ThemeRecommendation.model_validate(t) for t in (event.theme_recommendations or [])]
        citations = [SourceCitation.model_validate(c) for c in (event.citations or [])]

        return EventDetailResponse(
            id=event.id,
            name=event.name,
            event_type=event.event_type,  # type: ignore[arg-type]
            location=event.location,
            total_budget=int(event.total_budget),
            guest_count=int(event.guest_count),
            event_date=event.event_date,
            preferred_theme=event.preferred_theme or "",
            dietary_requirements=event.dietary_requirements or "",
            additional_preferences=event.additional_preferences or "",
            summary=event.summary or "",
            theme_recommendations=themes,
            ai_suggestions=list(event.ai_suggestions or []),
            citations=citations,
            missing_evidence_note=event.missing_evidence_note or "",
            generation_mode=event.generation_mode or "deterministic_fallback",
            budget=budget_summary,
            tasks=[TaskResponse.model_validate(t) for t in tasks_sorted],
            created_at=event.created_at,
            updated_at=event.updated_at,
        )

    @staticmethod
    def list_event_summaries(db: Session, skip: int = 0, limit: int = 50) -> list[EventSummaryCard]:
        events = EventRepository.list_events(db, skip=skip, limit=limit)
        return [EventService._to_summary_card(ev, idx) for idx, ev in enumerate(events, start=1)]

    @staticmethod
    def create_event(db: Session, payload: EventCreate) -> EventDetailResponse:
        BudgetService.validate_positive_budget(payload.total_budget)
        event_obj = EventModel(
            name=payload.name.strip(),
            event_type=payload.event_type,
            location=payload.location.strip(),
            total_budget=int(payload.total_budget),
            guest_count=int(payload.guest_count),
            event_date=payload.event_date,
            preferred_theme=(payload.preferred_theme or "").strip(),
            dietary_requirements=(payload.dietary_requirements or "").strip(),
            additional_preferences=(payload.additional_preferences or "").strip(),
            summary=f"Initialized {payload.event_type} plan for {payload.name.strip()}.",
        )
        EventRepository.create_event(db, event_obj)
        BudgetService.initialize_event_budget(db, event_obj)
        TimelineService.generate_and_persist_timeline(db, event_obj, preserve_completed=False)
        db.commit()
        db.refresh(event_obj)

        if payload.generate_initial_plan:
            event_obj = PlannerService.generate_plan_for_event(db, event_obj)

        return EventService.to_detail_response(event_obj)

    @staticmethod
    def update_event(
        db: Session,
        event: EventModel,
        update_in: EventUpdate,
    ) -> EventDetailResponse:
        date_changed = False
        scale_or_type_changed = False
        budget_changed = False

        if update_in.name is not None:
            event.name = update_in.name.strip()
        if update_in.event_type is not None and update_in.event_type != event.event_type:
            event.event_type = update_in.event_type
            scale_or_type_changed = True
        if update_in.location is not None:
            event.location = update_in.location.strip()
        if update_in.total_budget is not None and update_in.total_budget != event.total_budget:
            if not update_in.user_approved_budget_change:
                raise BudgetValidationError(
                    "Never silently change the user's total budget. "
                    "Pass user_approved_budget_change=True to confirm updating total_budget."
                )
            BudgetService.validate_positive_budget(update_in.total_budget)
            event.total_budget = int(update_in.total_budget)
            budget_changed = True
        if update_in.guest_count is not None and update_in.guest_count != event.guest_count:
            event.guest_count = int(update_in.guest_count)
            scale_or_type_changed = True
        if update_in.event_date is not None and update_in.event_date != event.event_date:
            event.event_date = update_in.event_date
            date_changed = True
        if update_in.preferred_theme is not None:
            event.preferred_theme = update_in.preferred_theme.strip()
        if update_in.dietary_requirements is not None:
            event.dietary_requirements = update_in.dietary_requirements.strip()
        if update_in.additional_preferences is not None:
            event.additional_preferences = update_in.additional_preferences.strip()

        if budget_changed:
            BudgetService.initialize_event_budget(db, event)
        if date_changed or scale_or_type_changed:
            TimelineService.generate_and_persist_timeline(db, event, preserve_completed=True)

        db.commit()
        db.refresh(event)

        if update_in.regenerate_plan:
            event = PlannerService.generate_plan_for_event(
                db,
                event,
                reset_budget_allocations=budget_changed,
                reset_timeline=(date_changed or scale_or_type_changed),
            )

        return EventService.to_detail_response(event)

    @staticmethod
    def get_dashboard_summary(db: Session) -> DashboardResponse:
        events = EventRepository.list_events(db, skip=0, limit=100)
        today_str = date.today().isoformat()

        cards = [EventService._to_summary_card(ev, idx) for idx, ev in enumerate(events, start=1)]
        upcoming_cards = [c for c in cards if c.event_date >= today_str]
        if not upcoming_cards:
            upcoming_cards = cards[:6]

        all_tasks: list[TaskModel] = []
        for ev in events:
            all_tasks.extend(ev.tasks or [])

        total_tasks = len(all_tasks)
        completed_tasks = sum(1 for t in all_tasks if t.status == "completed")
        in_progress_tasks = sum(1 for t in all_tasks if t.status == "in_progress")
        overall_pct = round((completed_tasks / total_tasks) * 100.0, 1) if total_tasks > 0 else 0.0

        total_budget_all = sum(c.total_budget for c in cards)
        total_planned_all = sum(c.planned_spending for c in cards)
        total_actual_all = sum(c.actual_spending for c in cards)
        remaining_all = sum(c.remaining_budget for c in cards)

        active_quests = sorted(
            [t for t in all_tasks if t.status != "completed"],
            key=lambda t: (t.due_date, 0 if t.priority == "high" else 1),
        )[:6]

        docs_count = db.query(KnowledgeDocumentModel).filter(KnowledgeDocumentModel.status == "indexed").count()

        # Compile recent activity from persisted records
        activities: list[ActivityItem] = []
        for ev in events[:4]:
            activities.append(
                ActivityItem(
                    id=f"ev_{ev.id}",
                    category="event",
                    title=f"Event Plan: {ev.name}",
                    detail=f"{ev.event_type.capitalize()} in {ev.location} • Budget ₹{ev.total_budget:,}",
                    timestamp=ev.updated_at,
                    event_id=ev.id,
                )
            )

        recent_expenses = (
            db.query(ExpenseModel).order_by(ExpenseModel.created_at.desc()).limit(3).all()
        )
        for exp in recent_expenses:
            activities.append(
                ActivityItem(
                    id=f"exp_{exp.id}",
                    category="expense",
                    title=f"Expense Recorded: {exp.title}",
                    detail=f"₹{exp.amount:,} in {exp.category_name}",
                    timestamp=exp.created_at,
                    event_id=exp.event_id,
                )
            )

        recent_docs = (
            db.query(KnowledgeDocumentModel)
            .order_by(KnowledgeDocumentModel.updated_at.desc())
            .limit(3)
            .all()
        )
        for doc in recent_docs:
            activities.append(
                ActivityItem(
                    id=f"doc_{doc.id}",
                    category="knowledge",
                    title=f"Knowledge Indexed: {doc.title}",
                    detail=f"{doc.chunk_count} chunks • {doc.category}",
                    timestamp=doc.updated_at,
                    event_id=None,
                )
            )

        recent_msgs = (
            db.query(ChatMessageModel)
            .filter(ChatMessageModel.role == "user")
            .order_by(ChatMessageModel.created_at.desc())
            .limit(2)
            .all()
        )
        for msg in recent_msgs:
            activities.append(
                ActivityItem(
                    id=f"chat_{msg.id}",
                    category="chat",
                    title="AI Assistant Follow-up",
                    detail=msg.content[:80],
                    timestamp=msg.created_at,
                    event_id=msg.event_id,
                )
            )

        activities.sort(key=lambda a: a.timestamp, reverse=True)

        return DashboardResponse(
            total_events=len(events),
            upcoming_events_count=sum(1 for c in cards if c.event_date >= today_str),
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            in_progress_tasks=in_progress_tasks,
            overall_completion_percentage=overall_pct,
            total_budget_across_events=total_budget_all,
            total_planned_across_events=total_planned_all,
            total_actual_across_events=total_actual_all,
            remaining_budget_across_events=remaining_all,
            indexed_documents_count=docs_count,
            upcoming_events=upcoming_cards[:6],
            upcoming_quests=[TaskResponse.model_validate(t) for t in active_quests],
            recent_activity=activities[:8],
        )
