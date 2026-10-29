import pytest
from app.schemas.budget import BudgetCategoryAllocationInput, BudgetUpdateRequest, ExpenseCreate
from app.schemas.event import EventCreate
from app.services.budget_service import BudgetService, BudgetValidationError
from app.services.event_service import EventService


def test_illustrative_birthday_25000_exact_allocations():
    """Verify the exact ₹25,000 birthday budget breakdown specified in Section 5.D."""
    allocs = BudgetService.calculate_default_allocations("birthday", 25000)
    by_name = {a.name: a.planned_amount for a in allocs}

    assert by_name["Venue"] == 5000
    assert by_name["Food and beverages"] == 8000
    assert by_name["Decoration"] == 3000
    assert by_name["Cake"] == 2000
    assert by_name["Entertainment"] == 2000
    assert by_name["Miscellaneous"] == 2000
    assert by_name["Emergency reserve"] == 3000
    assert sum(by_name.values()) == 25000


def test_budget_rounding_always_sums_to_total():
    """Verify non-round integer INR budgets always sum exactly to total_budget."""
    for event_type in ("birthday", "wedding", "community"):
        for total in (10001, 25003, 99999, 123456):
            allocs = BudgetService.calculate_default_allocations(event_type, total)
            assert sum(a.planned_amount for a in allocs) == total
            assert any(a.is_emergency_reserve for a in allocs)


def test_reject_invalid_or_negative_budgets():
    with pytest.raises(BudgetValidationError):
        BudgetService.validate_positive_budget(0)
    with pytest.raises(BudgetValidationError):
        BudgetService.validate_positive_budget(-5000)
    with pytest.raises(BudgetValidationError):
        BudgetService.validate_positive_budget(500)


def test_budget_overrun_detection_and_expense_tracking(test_env):
    db = test_env["db"]
    created = EventService.create_event(
        db,
        EventCreate(
            name="Test Overrun Birthday",
            event_type="birthday",
            location="Chennai",
            total_budget=25000,
            guest_count=50,
            event_date="2027-05-15",
            generate_initial_plan=False,
        ),
    )
    from app.database.repository import EventRepository

    event = EventRepository.get_event(db, created.id)
    assert event is not None

    # Add an expense that exceeds the ₹5,000 Venue category allocation
    summary = BudgetService.add_expense(
        db,
        event,
        ExpenseCreate(
            category_name="Venue",
            title="Premium Banquet Hall",
            amount=6500,
            incurred_date="2026-10-28",
        ),
    )
    venue_cat = next(c for c in summary.categories if c.name == "Venue")
    assert venue_cat.actual_spent == 6500
    assert venue_cat.is_over_category_budget is True
    assert summary.actual_spending == 6500
    assert summary.remaining_actual_budget == 18500
    assert any("Venue" in w for w in summary.warnings)

    # Add another expense pushing total actual spending above ₹25,000
    summary2 = BudgetService.add_expense(
        db,
        event,
        ExpenseCreate(
            category_name="Food and beverages",
            title="Luxury Catering Full Payment",
            amount=20000,
            incurred_date="2026-10-28",
        ),
    )
    assert summary2.actual_spending == 26500
    assert summary2.is_actual_over_budget is True
    assert summary2.overrun_amount == 1500


def test_never_silently_change_total_budget(test_env):
    db = test_env["db"]
    created = EventService.create_event(
        db,
        EventCreate(
            name="Protected Budget Event",
            event_type="birthday",
            location="Chennai",
            total_budget=25000,
            guest_count=40,
            event_date="2027-06-01",
            generate_initial_plan=False,
        ),
    )
    from app.database.repository import EventRepository

    event = EventRepository.get_event(db, created.id)
    assert event is not None

    # Attempting to change total_budget without user_approved_total_change=True must fail
    with pytest.raises(BudgetValidationError):
        BudgetService.update_budget_allocations(
            db,
            event,
            BudgetUpdateRequest(
                total_budget=20000,
                user_approved_total_change=False,
                categories=[
                    BudgetCategoryAllocationInput(name="Venue", planned_amount=17000),
                    BudgetCategoryAllocationInput(
                        name="Emergency reserve", planned_amount=3000, is_emergency_reserve=True
                    ),
                ],
            ),
        )

    # With explicit user approval, total_budget updates cleanly
    approved = BudgetService.update_budget_allocations(
        db,
        event,
        BudgetUpdateRequest(
            total_budget=20000,
            user_approved_total_change=True,
            categories=[
                BudgetCategoryAllocationInput(name="Venue", planned_amount=17000),
                BudgetCategoryAllocationInput(
                    name="Emergency reserve", planned_amount=3000, is_emergency_reserve=True
                ),
            ],
        ),
    )
    assert approved.total_budget == 20000
    assert approved.emergency_reserve == 3000
