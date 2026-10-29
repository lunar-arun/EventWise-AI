from datetime import date, timedelta
from typing import Optional
from sqlalchemy.orm import Session

from app.database.models import EventModel, TaskModel
from app.database.repository import TaskRepository
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate, TimelineSummaryResponse

# Milestone templates: (days_before_event, milestone_label, title, description, priority, category)
BIRTHDAY_MILESTONES: list[tuple[int, str, str, str, str, str]] = [
    (
        21,
        "Three weeks before",
        "Finalize budget and guest list",
        "Approve the integer INR category budget, lock emergency reserve, and compile the guest invite list.",
        "high",
        "Planning",
    ),
    (
        14,
        "Two weeks before",
        "Investigate venue and catering options",
        "Shortlist 3 venues and caterers, compare illustrative estimates, and confirm dietary requirements.",
        "high",
        "Venue & Catering",
    ),
    (
        7,
        "One week before",
        "Confirm invitations and decorations",
        "Send digital/printed invitations, track RSVPs, and finalize theme backdrop and cake order.",
        "medium",
        "Decor & Invites",
    ),
    (
        3,
        "Three days before",
        "Verify supplies and arrangements",
        "Reconfirm delivery times with cake, catering, and decor vendors; purchase return gifts and tableware.",
        "medium",
        "Logistics",
    ),
    (
        1,
        "One day before",
        "Complete preparation",
        "Prepare music playlist, charge cameras, pack emergency kit, and confirm venue setup access.",
        "high",
        "Preparation",
    ),
    (
        0,
        "Event day",
        "Follow the event checklist",
        "Oversee decoration setup, welcome guests, coordinate cake cutting and catering service, and settle balances.",
        "high",
        "Execution",
    ),
]

WEDDING_MILESTONES: list[tuple[int, str, str, str, str, str]] = [
    (
        60,
        "Two months before",
        "Finalize wedding budget, guest count, and marriage hall",
        "Lock total wedding budget in INR, confirm auspice dates, and book the primary venue and catering lead.",
        "high",
        "Venue & Budget",
    ),
    (
        30,
        "One month before",
        "Confirm wedding catering menu, photography, and ritual supplies",
        "Conduct food tasting, finalize vegetarian/specialty counters, and book photography and music teams.",
        "high",
        "Catering & Media",
    ),
    (
        14,
        "Two weeks before",
        "Dispatch invitations and finalize mandap & floral decoration plan",
        "Complete guest RSVP tracking, confirm stage/mandap floral design, and arrange guest accommodation.",
        "high",
        "Decor & Guests",
    ),
    (
        7,
        "One week before",
        "Reconfirm vendor schedules, transport, and power backup",
        "Walk through the venue timeline with decorators, caterers, and electrical backup staff.",
        "medium",
        "Logistics",
    ),
    (
        1,
        "One day before",
        "Complete pre-wedding venue inspection and hospitality desk setup",
        "Verify welcome kits, seating signage, dressing rooms, and emergency reserve cash/UPI readiness.",
        "high",
        "Preparation",
    ),
    (
        0,
        "Event day",
        "Execute wedding day master checklist",
        "Coordinate muhurtham/ceremony flow, buffet replenishment, guest hospitality, and vendor sign-offs.",
        "high",
        "Execution",
    ),
]

COMMUNITY_MILESTONES: list[tuple[int, str, str, str, str, str]] = [
    (
        30,
        "Four weeks before",
        "Finalize community event budget, committee roles, and venue permissions",
        "Set budget allocations, assign volunteer leads, and obtain community hall or municipal ground permissions.",
        "high",
        "Governance & Permits",
    ),
    (
        14,
        "Two weeks before",
        "Arrange sound/AV equipment, refreshments, and stage setup",
        "Book PA system, microphones, seating chairs, water stations, and community meal caterers.",
        "high",
        "Venue & AV",
    ),
    (
        7,
        "One week before",
        "Publish community announcements and confirm volunteer roster",
        "Distribute neighborhood flyers/messages, confirm guest speakers, and brief crowd-flow volunteers.",
        "medium",
        "Outreach",
    ),
    (
        3,
        "Three days before",
        "Verify sanitation, first-aid, and waste management supplies",
        "Confirm dustbins, drinking water cans, first-aid box, and backup lighting.",
        "medium",
        "Safety & Logistics",
    ),
    (
        1,
        "One day before",
        "Complete stage signage and sound check preparation",
        "Test microphones, verify registration desk materials, and confirm food delivery schedule.",
        "high",
        "Preparation",
    ),
    (
        0,
        "Event day",
        "Follow the community event day checklist",
        "Manage registration, program schedule, refreshment distribution, and post-event venue cleanup.",
        "high",
        "Execution",
    ),
]


class TimelineService:
    @staticmethod
    def build_tasks_for_event(
        event: EventModel,
        reference_date: Optional[date] = None,
    ) -> list[TaskModel]:
        today = reference_date or date.today()
        ev_date = date.fromisoformat(event.event_date)
        etype = event.event_type.strip().lower()

        if etype == "wedding":
            base_template = list(WEDDING_MILESTONES)
        elif etype == "community":
            base_template = list(COMMUNITY_MILESTONES)
        else:
            base_template = list(BIRTHDAY_MILESTONES)

        # Scale adjustment: add dedicated large-crowd coordination task for >150 guests
        if event.guest_count >= 150:
            base_template.insert(
                2,
                (
                    10,
                    "Ten days before (Large Scale)",
                    f"Coordinate crowd flow, extra buffet counters & parking for {event.guest_count} guests",
                    f"Add parallel food serving lines and dedicated ushering for {event.guest_count} attendees.",
                    "high",
                    "Scale & Crowd",
                ),
            )

        tasks: list[TaskModel] = []
        for days_before, label, title, desc, priority, category in base_template:
            ideal_due = ev_date - timedelta(days=days_before)
            is_clamped = False
            note_suffix = ""

            if ev_date < today:
                # Event date is already in the past: clamp to today so no impossible past deadline is silently scheduled
                actual_due = today
                is_clamped = True
                note_suffix = (
                    f" [Note: Event date ({ev_date.isoformat()}) is in the past; "
                    f"deadline clamped to {today.isoformat()} for immediate review.]"
                )
            elif ideal_due < today:
                # Event is upcoming soon, but this milestone window has passed: compress safely between today and event_date
                actual_due = today
                is_clamped = True
                note_suffix = (
                    f" [Compressed schedule: ideal milestone was {ideal_due.isoformat()}, "
                    f"clamped to {today.isoformat()} because the event is only {(ev_date - today).days} day(s) away.]"
                )
            else:
                actual_due = ideal_due

            tasks.append(
                TaskModel(
                    event_id=event.id,
                    title=title,
                    description=f"{desc}{note_suffix}".strip(),
                    milestone_label=label,
                    due_date=actual_due.isoformat(),
                    status="pending",
                    priority=priority,
                    category=category,
                    is_clamped=is_clamped,
                )
            )
        return tasks

    @staticmethod
    def generate_and_persist_timeline(
        db: Session,
        event: EventModel,
        reference_date: Optional[date] = None,
        preserve_completed: bool = True,
    ) -> list[TaskModel]:
        new_tasks = TimelineService.build_tasks_for_event(event, reference_date=reference_date)
        return TaskRepository.replace_tasks_for_event(
            db,
            event_id=event.id,
            tasks=new_tasks,
            preserve_completed=preserve_completed,
        )

    @staticmethod
    def update_task(
        db: Session,
        task_id: int,
        update_in: TaskUpdate,
    ) -> TaskModel:
        task = TaskRepository.get_task(db, task_id)
        if not task:
            raise LookupError(f"Task with id {task_id} not found.")

        if update_in.title is not None:
            task.title = update_in.title.strip()
        if update_in.description is not None:
            task.description = update_in.description.strip()
        if update_in.milestone_label is not None:
            task.milestone_label = update_in.milestone_label.strip()
        if update_in.due_date is not None:
            task.due_date = update_in.due_date
        if update_in.status is not None:
            task.status = update_in.status
        if update_in.priority is not None:
            task.priority = update_in.priority
        if update_in.category is not None:
            task.category = update_in.category.strip()

        db.commit()
        db.refresh(task)
        return task

    @staticmethod
    def add_custom_task(
        db: Session,
        event_id: int,
        task_in: TaskCreate,
    ) -> TaskModel:
        today = date.today()
        target_due = date.fromisoformat(task_in.due_date)
        is_clamped = target_due < today
        task = TaskModel(
            event_id=event_id,
            title=task_in.title.strip(),
            description=(task_in.description or "").strip(),
            milestone_label=task_in.milestone_label.strip(),
            due_date=task_in.due_date,
            status=task_in.status,
            priority=task_in.priority,
            category=task_in.category.strip(),
            is_clamped=is_clamped,
        )
        return TaskRepository.create_task(db, task)

    @staticmethod
    def compute_timeline_summary(
        event: EventModel,
        reference_date: Optional[date] = None,
    ) -> TimelineSummaryResponse:
        today = reference_date or date.today()
        ev_date = date.fromisoformat(event.event_date)
        days_until = (ev_date - today).days

        tasks_orm = sorted(
            list(event.tasks or []),
            key=lambda t: (t.due_date, t.id or 0),
        )
        total = len(tasks_orm)
        completed = sum(1 for t in tasks_orm if t.status == "completed")
        in_progress = sum(1 for t in tasks_orm if t.status == "in_progress")
        pending = sum(1 for t in tasks_orm if t.status == "pending")
        pct = round((completed / total) * 100.0, 1) if total > 0 else 0.0

        any_clamped = any(bool(t.is_clamped) for t in tasks_orm)
        schedule_notice: Optional[str] = None
        if days_until < 0:
            schedule_notice = (
                f"This event's date ({event.event_date}) is in the past ({abs(days_until)} day(s) ago). "
                "Task deadlines were clamped to prevent scheduling impossible past dates."
            )
        elif any_clamped:
            schedule_notice = (
                f"This event is coming up in {days_until} day(s). Earlier milestone deadlines were "
                "compressed to today so you can focus on immediate action items."
            )

        return TimelineSummaryResponse(
            event_id=event.id,
            event_name=event.name,
            event_type=event.event_type,
            event_date=event.event_date,
            days_until_event=days_until,
            schedule_notice=schedule_notice,
            total_tasks=total,
            completed_tasks=completed,
            in_progress_tasks=in_progress,
            pending_tasks=pending,
            completion_percentage=pct,
            tasks=[TaskResponse.model_validate(t) for t in tasks_orm],
        )
