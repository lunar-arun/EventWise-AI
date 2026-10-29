from datetime import date, timedelta
from app.schemas.event import EventCreate
from app.schemas.task import TaskUpdate
from app.services.event_service import EventService
from app.services.timeline_service import TimelineService


def test_default_birthday_milestones_relative_dates(test_env):
    """Verify the 6 required birthday milestones relative to an upcoming event date."""
    db = test_env["db"]
    ref_today = date(2026, 10, 1)
    ev_date = ref_today + timedelta(days=30)

    created = EventService.create_event(
        db,
        EventCreate(
            name="Milestone Check Birthday",
            event_type="birthday",
            location="Chennai",
            total_budget=25000,
            guest_count=50,
            event_date=ev_date.isoformat(),
            generate_initial_plan=False,
        ),
    )
    from app.database.repository import EventRepository

    event = EventRepository.get_event(db, created.id)
    assert event is not None

    tasks = TimelineService.generate_and_persist_timeline(
        db, event, reference_date=ref_today, preserve_completed=False
    )
    assert len(tasks) == 6
    labels = [t.milestone_label for t in tasks]
    assert labels == [
        "Three weeks before",
        "Two weeks before",
        "One week before",
        "Three days before",
        "One day before",
        "Event day",
    ]
    expected_offsets = [21, 14, 7, 3, 1, 0]
    for task, offset in zip(tasks, expected_offsets):
        assert task.due_date == (ev_date - timedelta(days=offset)).isoformat()
        assert task.is_clamped is False


def test_past_and_close_event_dates_clamp_safely(test_env):
    """Verify deadlines are never scheduled in the past when an event is near or past."""
    db = test_env["db"]
    ref_today = date(2026, 10, 28)
    near_date = ref_today + timedelta(days=4)

    created = EventService.create_event(
        db,
        EventCreate(
            name="Short Notice Event",
            event_type="birthday",
            location="Bengaluru",
            total_budget=25000,
            guest_count=40,
            event_date=near_date.isoformat(),
            generate_initial_plan=False,
        ),
    )
    from app.database.repository import EventRepository

    event = EventRepository.get_event(db, created.id)
    assert event is not None

    tasks = TimelineService.generate_and_persist_timeline(
        db, event, reference_date=ref_today, preserve_completed=False
    )
    for t in tasks:
        assert date.fromisoformat(t.due_date) >= ref_today
    # Milestones 21, 14, and 7 days before should be clamped to ref_today
    clamped_tasks = [t for t in tasks if t.is_clamped]
    assert len(clamped_tasks) == 3

    summary = TimelineService.compute_timeline_summary(event, reference_date=ref_today)
    assert summary.schedule_notice is not None


def test_large_scale_guest_count_adds_crowd_milestone_and_task_status_transitions(test_env):
    db = test_env["db"]
    future_date = (date.today() + timedelta(days=90)).isoformat()
    created = EventService.create_event(
        db,
        EventCreate(
            name="Grand Wedding 250 Guests",
            event_type="wedding",
            location="Madurai",
            total_budget=600000,
            guest_count=250,
            event_date=future_date,
            generate_initial_plan=False,
        ),
    )
    # 6 standard wedding tasks + 1 large-scale crowd task = 7 tasks
    assert len(created.tasks) == 7
    assert any("250 guests" in t.title for t in created.tasks)

    first_task_id = created.tasks[0].id
    updated_in_prog = TimelineService.update_task(
        db, first_task_id, TaskUpdate(status="in_progress")
    )
    assert updated_in_prog.status == "in_progress"

    updated_done = TimelineService.update_task(
        db, first_task_id, TaskUpdate(status="completed")
    )
    assert updated_done.status == "completed"
