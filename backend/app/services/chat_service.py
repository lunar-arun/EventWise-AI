import re
from typing import Optional
from sqlalchemy.orm import Session

from app.database.models import ChatMessageModel, EventModel
from app.database.repository import ChatRepository, EventRepository
from app.rag.generation import get_generation_service
from app.rag.retrieval import get_retrieval_service
from app.schemas.chat import (
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    ProposedBudgetChange,
)
from app.schemas.knowledge import SourceCitation
from app.services.budget_service import BudgetService


def _parse_rupee_amount_from_text(text: str) -> Optional[int]:
    """Extract an integer INR amount from phrases like 'by ₹5,000', 'by 5000', or 'to 20,000'."""
    match = re.search(r"(?:₹|rs\.?|inr)?\s*(\d{1,3}(?:,\d{2,3})+|\d{3,9})", text, flags=re.IGNORECASE)
    if not match:
        return None
    digits = match.group(1).replace(",", "")
    try:
        val = int(digits)
        return val if val > 0 else None
    except ValueError:
        return None


class ChatService:
    @staticmethod
    def _build_deterministic_event_context(
        event: Optional[EventModel],
        user_message: str,
    ) -> tuple[str, Optional[ProposedBudgetChange]]:
        if not event:
            return (
                "No specific event is currently selected. Provide general event planning guidance with illustrative INR estimates.",
                None,
            )

        budget_summary = BudgetService.compute_budget_summary(event)
        tasks = list(event.tasks or [])
        pending_tasks = [t for t in tasks if t.status != "completed"]
        completed_tasks = [t for t in tasks if t.status == "completed"]

        cat_lines = [
            f"  * {c.name}: Planned ₹{c.planned_amount:,} | Actual ₹{c.actual_spent:,} "
            f"{'(Emergency Reserve)' if c.is_emergency_reserve else ''}"
            for c in budget_summary.categories
        ]
        task_lines = [
            f"  * [{t.status.upper()}] {t.title} (Due: {t.due_date}, Milestone: {t.milestone_label})"
            for t in pending_tasks[:8]
        ]

        proposed_change: Optional[ProposedBudgetChange] = None
        msg_lower = user_message.lower()

        # Detect if user asks to reduce or change the budget
        if any(w in msg_lower for w in ("reduce", "cut", "lower", "decrease", "shrink")) and "budget" in msg_lower:
            amount = _parse_rupee_amount_from_text(user_message) or int(round(event.total_budget * 0.15))
            proposal_dict = BudgetService.build_proposed_budget_reduction(event, amount)
            proposed_change = ProposedBudgetChange(
                action_type="propose_budget_reduction",
                summary=(
                    f"Proposed reducing total budget by ₹{event.total_budget - proposal_dict['proposed_total_budget']:,} "
                    f"(from ₹{event.total_budget:,} to ₹{proposal_dict['proposed_total_budget']:,}) while keeping "
                    "your Emergency Reserve protected."
                ),
                current_total_budget=proposal_dict["current_total_budget"],
                proposed_total_budget=proposal_dict["proposed_total_budget"],
                proposed_categories=proposal_dict["proposed_categories"],
                requires_user_approval=True,
            )
        elif any(w in msg_lower for w in ("vegetarian", "vegan", "jain", "halal", "gluten", "menu", "dietary")):
            if "vegetarian" in msg_lower:
                new_diet = "100% Pure Vegetarian Menu (with live regional counters)"
            elif "jain" in msg_lower:
                new_diet = "Jain & Pure Vegetarian Menu (no root vegetables)"
            elif "vegan" in msg_lower:
                new_diet = "Plant-Based / Vegan Menu"
            else:
                new_diet = "Custom Dietary Menu (Updated via Chat)"

            proposed_change = ProposedBudgetChange(
                action_type="propose_preference_update",
                summary=f"Proposed updating dietary requirements to '{new_diet}' and refreshing catering notes.",
                current_total_budget=event.total_budget,
                proposed_total_budget=event.total_budget,
                proposed_categories=[
                    {
                        "name": c.name,
                        "planned_amount": c.planned_amount,
                        "is_emergency_reserve": c.is_emergency_reserve,
                        "notes": c.notes,
                    }
                    for c in budget_summary.categories
                ],
                proposed_preferences={"dietary_requirements": new_diet},
                requires_user_approval=True,
            )

        context_lines = [
            f"Event ID: {event.id}",
            f"Event Name: {event.name}",
            f"Event Type: {event.event_type}",
            f"Location: {event.location}",
            f"Event Date: {event.event_date}",
            f"Guest Count: {event.guest_count}",
            f"Preferred Theme: {event.preferred_theme or 'Flexible'}",
            f"Dietary Requirements: {event.dietary_requirements or 'Standard'}",
            f"Approved Total Budget (Authoritative Python): ₹{budget_summary.total_budget:,} INR",
            f"Planned Spending: ₹{budget_summary.planned_spending:,} INR",
            f"Actual Expenses Recorded: ₹{budget_summary.actual_spending:,} INR",
            f"Emergency Reserve: ₹{budget_summary.emergency_reserve:,} INR",
            f"Remaining Budget (vs Planned): ₹{budget_summary.remaining_planned_budget:,} INR",
            "Category Allocations:",
            *cat_lines,
            f"Tasks Summary: {len(completed_tasks)} completed, {len(pending_tasks)} remaining out of {len(tasks)} total tasks.",
            "Remaining Tasks:",
            *(task_lines if task_lines else ["  * All tasks are currently marked completed!"]),
        ]
        if proposed_change:
            context_lines.append(
                f"DETERMINISTIC PROPOSAL READY (Awaiting User Approval): {proposed_change.summary}"
            )

        return "\n".join(context_lines), proposed_change

    @staticmethod
    def handle_chat(db: Session, req: ChatRequest) -> ChatResponse:
        event: Optional[EventModel] = None
        if req.event_id is not None:
            event = EventRepository.get_event(db, req.event_id)
            if not event:
                raise LookupError(f"Event with id {req.event_id} not found.")

        session_title = f"Chat: {event.name}" if event else f"Planning Chat: {req.message[:40]}"
        session = ChatRepository.get_or_create_session(
            db,
            session_id=req.session_id,
            event_id=req.event_id,
            title=session_title,
        )

        # Persist user message
        user_msg_model = ChatMessageModel(
            session_id=session.id,
            event_id=req.event_id,
            role="user",
            content=req.message.strip(),
            citations=[],
            proposed_changes=None,
        )
        ChatRepository.add_message(db, user_msg_model)

        # Build conversation history string from recent messages
        prior_msgs = list(session.messages or [])[-8:]
        history_str = "\n".join(
            f"{m.role.upper()}: {m.content}" for m in prior_msgs if m.id != user_msg_model.id
        )

        # Deterministic Python calculations & optional non-destructive proposal
        event_context_str, proposed_change = ChatService._build_deterministic_event_context(
            event, req.message
        )

        # Retrieve relevant knowledge chunks
        retrieval_query = req.message
        if event:
            retrieval_query = f"{event.event_type} {event.location} {req.message}"
        retrieved_chunks, _, fallback_reason = get_retrieval_service().retrieve(
            query=retrieval_query,
            event_type=event.event_type if event else None,
            location=event.location if event else None,
        )

        # Generate grounded response
        gen_payload, verified_citations, mode = get_generation_service().generate_chat_reply(
            user_message=req.message,
            event_context=event_context_str,
            conversation_history=history_str,
            retrieved_chunks=retrieved_chunks,
            fallback_reason=fallback_reason,
        )

        # Append deterministic task or budget summary when explicitly asked
        reply_text = gen_payload.reply
        msg_lower = req.message.lower()
        if event and ("task" in msg_lower or "remain" in msg_lower or "checklist" in msg_lower):
            remaining = [t for t in (event.tasks or []) if t.status != "completed"]
            if remaining:
                bullet_tasks = "\n".join(
                    f"- **{t.title}** ({t.milestone_label}, Due: `{t.due_date}`, Status: `{t.status}`)"
                    for t in remaining[:6]
                )
                if bullet_tasks not in reply_text:
                    reply_text = f"{reply_text}\n\n**Remaining Event Tasks ({len(remaining)}):**\n{bullet_tasks}"

        if proposed_change and "approve" not in reply_text.lower():
            reply_text = (
                f"{reply_text}\n\n💡 **Proposed Adjustment Ready:** {proposed_change.summary} "
                "Your persisted budget/plan has **not** been changed automatically—use the approval card below to apply it."
            )

        assistant_msg_model = ChatMessageModel(
            session_id=session.id,
            event_id=req.event_id,
            role="assistant",
            content=reply_text,
            citations=[c.model_dump() for c in verified_citations],
            proposed_changes=proposed_change.model_dump() if proposed_change else None,
        )
        ChatRepository.add_message(db, assistant_msg_model)
        db.commit()
        db.refresh(session)

        history_out = [
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

        return ChatResponse(
            session_id=session.id,
            event_id=req.event_id,
            reply=reply_text,
            suggestions=list(gen_payload.suggestions),
            citations=verified_citations,
            proposed_changes=proposed_change,
            missing_evidence_note=gen_payload.missing_evidence_note or fallback_reason,
            generation_mode=mode,
            history=history_out,
        )
