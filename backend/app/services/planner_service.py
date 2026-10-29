from sqlalchemy.orm import Session

from app.database.models import EventModel
from app.rag.generation import get_generation_service
from app.rag.retrieval import get_retrieval_service
from app.services.budget_service import BudgetService
from app.services.timeline_service import TimelineService


class PlannerService:
    @staticmethod
    def generate_plan_for_event(
        db: Session,
        event: EventModel,
        reset_budget_allocations: bool = False,
        reset_timeline: bool = False,
    ) -> EventModel:
        # 1. Ensure deterministic budget categories exist (preserve user-approved categories unless empty or requested)
        if not event.budget_categories or reset_budget_allocations:
            BudgetService.initialize_event_budget(db, event)

        # 2. Ensure deterministic timeline tasks exist (preserve completed/in_progress status)
        if not event.tasks or reset_timeline:
            TimelineService.generate_and_persist_timeline(db, event, preserve_completed=True)

        # 3. Build semantic retrieval query
        query_parts = [
            f"{event.event_type} event planning guide",
            f"location {event.location}",
            f"budget {event.total_budget} INR for {event.guest_count} guests",
        ]
        if event.preferred_theme:
            query_parts.append(f"theme {event.preferred_theme} decoration ideas")
        if event.dietary_requirements:
            query_parts.append(f"catering menu {event.dietary_requirements}")
        if event.additional_preferences:
            query_parts.append(str(event.additional_preferences))

        retrieval_query = " | ".join(query_parts)
        retrieval_service = get_retrieval_service()
        retrieved_chunks, _, fallback_reason = retrieval_service.retrieve(
            query=retrieval_query,
            event_type=event.event_type,
            location=event.location,
        )

        # 4. Prepare structured event details for grounded generation
        event_details = {
            "name": event.name,
            "event_type": event.event_type,
            "location": event.location,
            "total_budget": event.total_budget,
            "guest_count": event.guest_count,
            "event_date": event.event_date,
            "preferred_theme": event.preferred_theme or "Flexible / Open",
            "dietary_requirements": event.dietary_requirements or "Standard",
            "additional_preferences": event.additional_preferences or "None specified",
        }

        generation_service = get_generation_service()
        plan_payload, verified_citations, mode = generation_service.generate_event_plan(
            event_details=event_details,
            retrieved_chunks=retrieved_chunks,
            fallback_reason=fallback_reason,
        )

        event.summary = plan_payload.summary
        event.theme_recommendations = [t.model_dump() for t in plan_payload.theme_recommendations]
        event.ai_suggestions = list(plan_payload.ai_suggestions)
        event.citations = [c.model_dump() for c in verified_citations]
        event.missing_evidence_note = plan_payload.missing_evidence_note or (fallback_reason or "")
        event.generation_mode = mode

        db.commit()
        db.refresh(event)
        return event
