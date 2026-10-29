from typing import Any
from sqlalchemy.orm import Session

from app.database.models import BudgetCategoryModel, EventModel, ExpenseModel
from app.database.repository import BudgetRepository
from app.schemas.budget import (
    BudgetCategoryAllocationInput,
    BudgetCategoryResponse,
    BudgetSummaryResponse,
    BudgetUpdateRequest,
    CostReductionSuggestion,
    ExpenseCreate,
    ExpenseResponse,
)

# Exact deterministic allocation ratios per event type (sum to 1.00)
# For birthday ₹25,000:
# Venue: ₹5,000 (20%), Food and beverages: ₹8,000 (32%), Decoration: ₹3,000 (12%),
# Cake: ₹2,000 (8%), Entertainment: ₹2,000 (8%), Miscellaneous: ₹2,000 (8%),
# Emergency reserve: ₹3,000 (12%) -> Total ₹25,000.
EVENT_BUDGET_TEMPLATES: dict[str, list[tuple[str, float, bool, str]]] = {
    "birthday": [
        ("Venue", 0.20, False, "Hall rental, seating & basic power backup (illustrative estimate)"),
        ("Food and beverages", 0.32, False, "Catering buffet, welcome drinks & snacks (illustrative estimate)"),
        ("Decoration", 0.12, False, "Theme backdrop, balloons, lighting & table decor (illustrative estimate)"),
        ("Cake", 0.08, False, "Custom celebration cake & dessert table (illustrative estimate)"),
        ("Entertainment", 0.08, False, "Music/DJ, games host & photo booth props (illustrative estimate)"),
        ("Miscellaneous", 0.08, False, "Return gifts, invitations & photography (illustrative estimate)"),
        ("Emergency reserve", 0.12, True, "Protected contingency reserve for last-minute guests or price changes"),
    ],
    "wedding": [
        ("Venue", 0.24, False, "Marriage hall / lawn booking & generator backup (illustrative estimate)"),
        ("Food and beverages", 0.34, False, "Multi-course wedding feast, live counters & beverages (illustrative estimate)"),
        ("Decoration", 0.14, False, "Mandap/stage florals, entrance arch & ambient lighting (illustrative estimate)"),
        ("Photography and video", 0.08, False, "Candid photography & traditional coverage (illustrative estimate)"),
        ("Entertainment and rituals", 0.05, False, "Nadaswaram/DJ, sound system & ceremonial supplies (illustrative estimate)"),
        ("Miscellaneous", 0.05, False, "Hospitality kits, invitations & local transport (illustrative estimate)"),
        ("Emergency reserve", 0.10, True, "Protected contingency reserve for wedding day logistics"),
    ],
    "community": [
        ("Venue and permits", 0.20, False, "Community ground/hall booking, seating & local permits (illustrative estimate)"),
        ("Food and beverages", 0.32, False, "Refreshments, water stations & community meal (illustrative estimate)"),
        ("Stage, sound and AV", 0.16, False, "PA system, microphones, podium & lighting (illustrative estimate)"),
        ("Decoration and signage", 0.10, False, "Banners, directional signage & stage backdrop (illustrative estimate)"),
        ("Miscellaneous and logistics", 0.10, False, "Volunteer kits, sanitation, first-aid & waste management (illustrative estimate)"),
        ("Emergency reserve", 0.12, True, "Protected contingency reserve for safety & crowd buffer"),
    ],
}


class BudgetValidationError(ValueError):
    """Raised when a budget operation violates deterministic constraints."""


class BudgetService:
    @staticmethod
    def validate_positive_budget(total_budget: int) -> int:
        if not isinstance(total_budget, int) or isinstance(total_budget, bool) or total_budget <= 0:
            raise BudgetValidationError("Total budget must be a positive integer in INR.")
        if total_budget < 1000:
            raise BudgetValidationError("Total budget must be at least ₹1,000 INR.")
        return total_budget

    @staticmethod
    def calculate_default_allocations(
        event_type: str,
        total_budget: int,
    ) -> list[BudgetCategoryAllocationInput]:
        BudgetService.validate_positive_budget(total_budget)
        etype = event_type.strip().lower()
        template = EVENT_BUDGET_TEMPLATES.get(etype, EVENT_BUDGET_TEMPLATES["birthday"])

        allocations: list[BudgetCategoryAllocationInput] = []
        running_sum = 0
        for idx, (cat_name, weight, is_reserve, note) in enumerate(template):
            if idx < len(template) - 1:
                amount = int(round(total_budget * weight))
                running_sum += amount
            else:
                # Guarantee exact integer summation to total_budget
                amount = max(0, total_budget - running_sum)
            allocations.append(
                BudgetCategoryAllocationInput(
                    name=cat_name,
                    planned_amount=amount,
                    is_emergency_reserve=is_reserve,
                    notes=note,
                )
            )
        return allocations

    @staticmethod
    def initialize_event_budget(db: Session, event: EventModel) -> list[BudgetCategoryModel]:
        allocations = BudgetService.calculate_default_allocations(event.event_type, event.total_budget)
        models = [
            BudgetCategoryModel(
                event_id=event.id,
                name=item.name,
                planned_amount=item.planned_amount,
                is_emergency_reserve=item.is_emergency_reserve,
                notes=item.notes or "",
            )
            for item in allocations
        ]
        return BudgetRepository.replace_categories(db, event.id, models)

    @staticmethod
    def update_budget_allocations(
        db: Session,
        event: EventModel,
        update_req: BudgetUpdateRequest,
    ) -> BudgetSummaryResponse:
        # Never silently change the user's total budget
        if update_req.total_budget is not None and update_req.total_budget != event.total_budget:
            if not update_req.user_approved_total_change:
                raise BudgetValidationError(
                    "Cannot modify the event's total budget without explicit user approval "
                    "(user_approved_total_change=True)."
                )
            BudgetService.validate_positive_budget(update_req.total_budget)
            event.total_budget = update_req.total_budget

        if not update_req.categories:
            raise BudgetValidationError("At least one budget category is required.")

        seen_names: set[str] = set()
        models: list[BudgetCategoryModel] = []
        has_reserve = False

        for item in update_req.categories:
            if item.planned_amount < 0:
                raise BudgetValidationError(
                    f"Category '{item.name}' cannot have a negative allocation."
                )
            norm = item.name.strip().lower()
            if norm in seen_names:
                raise BudgetValidationError(f"Duplicate budget category '{item.name}'.")
            seen_names.add(norm)
            is_res = item.is_emergency_reserve or ("emergency" in norm or "reserve" in norm)
            if is_res:
                has_reserve = True
            models.append(
                BudgetCategoryModel(
                    event_id=event.id,
                    name=item.name.strip(),
                    planned_amount=int(item.planned_amount),
                    is_emergency_reserve=is_res,
                    notes=(item.notes or "").strip(),
                )
            )

        if not has_reserve:
            models.append(
                BudgetCategoryModel(
                    event_id=event.id,
                    name="Emergency reserve",
                    planned_amount=0,
                    is_emergency_reserve=True,
                    notes="Emergency reserve category preserved at ₹0; consider allocating 8–12%.",
                )
            )

        BudgetRepository.replace_categories(db, event.id, models)
        db.commit()
        db.refresh(event)
        return BudgetService.compute_budget_summary(event)

    @staticmethod
    def add_expense(
        db: Session,
        event: EventModel,
        expense_in: ExpenseCreate,
    ) -> BudgetSummaryResponse:
        if expense_in.amount <= 0:
            raise BudgetValidationError("Expense amount must be greater than zero.")
        expense_model = ExpenseModel(
            event_id=event.id,
            category_name=expense_in.category_name.strip(),
            title=expense_in.title.strip(),
            amount=int(expense_in.amount),
            incurred_date=expense_in.incurred_date or "",
            notes=(expense_in.notes or "").strip(),
        )
        BudgetRepository.add_expense(db, expense_model)
        db.refresh(event)
        return BudgetService.compute_budget_summary(event)

    @staticmethod
    def generate_cost_reduction_suggestions(
        total_budget: int,
        categories: list[BudgetCategoryResponse],
    ) -> list[CostReductionSuggestion]:
        suggestions: list[CostReductionSuggestion] = []
        for cat in categories:
            if cat.is_emergency_reserve or cat.planned_amount <= 0:
                continue
            cname = cat.name.lower()
            if "decor" in cname:
                cut = max(500, int(round(cat.planned_amount * 0.20)))
                suggestions.append(
                    CostReductionSuggestion(
                        category=cat.name,
                        current_planned=cat.planned_amount,
                        suggested_planned=max(0, cat.planned_amount - cut),
                        potential_savings=cut,
                        rationale=(
                            "Switch from imported cut flowers to seasonal local marigolds/jasmine, "
                            "reusable fabric drapes, and warm LED fairy lights (illustrative ~20% savings)."
                        ),
                    )
                )
            elif "venue" in cname:
                cut = max(500, int(round(cat.planned_amount * 0.15)))
                suggestions.append(
                    CostReductionSuggestion(
                        category=cat.name,
                        current_planned=cat.planned_amount,
                        suggested_planned=max(0, cat.planned_amount - cut),
                        potential_savings=cut,
                        rationale=(
                            "Book morning/afternoon slots or community banquet halls instead of peak-hour "
                            "premium lawn packages (illustrative ~15% savings)."
                        ),
                    )
                )
            elif "food" in cname or "cater" in cname:
                cut = max(500, int(round(cat.planned_amount * 0.12)))
                suggestions.append(
                    CostReductionSuggestion(
                        category=cat.name,
                        current_planned=cat.planned_amount,
                        suggested_planned=max(0, cat.planned_amount - cut),
                        potential_savings=cut,
                        rationale=(
                            "Curate a focused high-quality menu (2 starters + 2 mains) instead of oversized "
                            "multi-cuisine spreads to reduce food waste and per-plate cost (~12% savings)."
                        ),
                    )
                )
            elif "entertain" in cname or "misc" in cname:
                cut = max(300, int(round(cat.planned_amount * 0.15)))
                suggestions.append(
                    CostReductionSuggestion(
                        category=cat.name,
                        current_planned=cat.planned_amount,
                        suggested_planned=max(0, cat.planned_amount - cut),
                        potential_savings=cut,
                        rationale=(
                            "Use digital invitations, curated playlists with rented PA speakers, and DIY photo "
                            "booth props (~15% illustrative savings)."
                        ),
                    )
                )
        return suggestions[:4]

    @staticmethod
    def build_proposed_budget_reduction(
        event: EventModel,
        reduction_amount: int,
    ) -> dict[str, Any]:
        """
        Deterministically compute a proposed budget reduction while preserving the Emergency Reserve.
        Does NOT persist changes to SQLite.
        """
        current_total = event.total_budget
        safe_reduction = max(0, min(reduction_amount, current_total - 1000))
        proposed_total = current_total - safe_reduction

        existing_cats = event.budget_categories or []
        if not existing_cats:
            allocs = BudgetService.calculate_default_allocations(event.event_type, proposed_total)
            return {
                "current_total_budget": current_total,
                "proposed_total_budget": proposed_total,
                "proposed_categories": [a.model_dump() for a in allocs],
            }

        reserve_total = sum(c.planned_amount for c in existing_cats if c.is_emergency_reserve)
        non_reserve_total = sum(c.planned_amount for c in existing_cats if not c.is_emergency_reserve)
        target_non_reserve = max(0, proposed_total - reserve_total)

        proposed_cats: list[dict[str, Any]] = []
        running_sum = 0
        non_reserve_indices = [i for i, c in enumerate(existing_cats) if not c.is_emergency_reserve]

        for idx, cat in enumerate(existing_cats):
            if cat.is_emergency_reserve:
                amt = min(cat.planned_amount, proposed_total)
                running_sum += amt
                proposed_cats.append(
                    {
                        "name": cat.name,
                        "planned_amount": amt,
                        "is_emergency_reserve": True,
                        "notes": cat.notes or "Protected emergency reserve",
                    }
                )
            else:
                if non_reserve_total > 0:
                    ratio = cat.planned_amount / non_reserve_total
                    amt = int(round(target_non_reserve * ratio))
                else:
                    amt = 0
                running_sum += amt
                proposed_cats.append(
                    {
                        "name": cat.name,
                        "planned_amount": amt,
                        "is_emergency_reserve": False,
                        "notes": cat.notes or "",
                    }
                )

        # Adjust rounding difference on the last non-reserve category
        diff = proposed_total - running_sum
        if diff != 0 and non_reserve_indices:
            last_idx = non_reserve_indices[-1]
            proposed_cats[last_idx]["planned_amount"] = max(0, proposed_cats[last_idx]["planned_amount"] + diff)

        return {
            "current_total_budget": current_total,
            "proposed_total_budget": proposed_total,
            "proposed_categories": proposed_cats,
        }

    @staticmethod
    def compute_budget_summary(event: EventModel) -> BudgetSummaryResponse:
        total_budget = int(event.total_budget)
        categories_orm = list(event.budget_categories or [])
        expenses_orm = list(event.expenses or [])

        # Group actual expenses by category name (case-insensitive)
        spent_by_cat: dict[str, int] = {}
        known_cat_names = {c.name.strip().lower(): c.name for c in categories_orm}

        unmatched_spent = 0
        for exp in expenses_orm:
            key = exp.category_name.strip().lower()
            if key in known_cat_names:
                spent_by_cat[key] = spent_by_cat.get(key, 0) + int(exp.amount)
            else:
                unmatched_spent += int(exp.amount)

        cat_responses: list[BudgetCategoryResponse] = []
        planned_spending = 0
        emergency_reserve = 0
        warnings: list[str] = []

        for cat in categories_orm:
            key = cat.name.strip().lower()
            actual = spent_by_cat.get(key, 0)
            if "misc" in key and unmatched_spent > 0:
                actual += unmatched_spent
                unmatched_spent = 0

            planned = int(cat.planned_amount)
            planned_spending += planned
            if cat.is_emergency_reserve:
                emergency_reserve += planned

            rem_cat = planned - actual
            pct = round((planned / total_budget) * 100.0, 1) if total_budget > 0 else 0.0
            over_cat = actual > planned
            if over_cat:
                warnings.append(
                    f"Category '{cat.name}' actual spending (₹{actual:,}) exceeds its planned allocation (₹{planned:,}) by ₹{actual - planned:,}."
                )

            cat_responses.append(
                BudgetCategoryResponse(
                    id=cat.id,
                    name=cat.name,
                    planned_amount=planned,
                    actual_spent=actual,
                    remaining_in_category=rem_cat,
                    allocation_percent=pct,
                    is_emergency_reserve=bool(cat.is_emergency_reserve),
                    is_over_category_budget=over_cat,
                    notes=cat.notes or "",
                )
            )

        actual_spending = sum(int(e.amount) for e in expenses_orm)
        remaining_planned = total_budget - planned_spending
        remaining_actual = total_budget - actual_spending

        is_planned_over = planned_spending > total_budget
        is_actual_over = actual_spending > total_budget
        overrun_amount = max(0, planned_spending - total_budget, actual_spending - total_budget)

        if is_planned_over:
            warnings.insert(
                0,
                f"Planned category allocations (₹{planned_spending:,}) exceed total approved budget (₹{total_budget:,}) by ₹{planned_spending - total_budget:,}.",
            )
        if is_actual_over:
            warnings.insert(
                0,
                f"Actual recorded expenses (₹{actual_spending:,}) exceed total approved budget (₹{total_budget:,}) by ₹{actual_spending - total_budget:,}.",
            )
        if emergency_reserve == 0:
            warnings.append(
                "Emergency reserve is currently ₹0. Consider keeping 8–12% of your total budget as an emergency buffer."
            )
        elif emergency_reserve < int(total_budget * 0.05):
            warnings.append(
                f"Emergency reserve (₹{emergency_reserve:,}) is below 5% of total budget. Consider increasing your buffer."
            )

        expense_responses = [ExpenseResponse.model_validate(e) for e in expenses_orm]
        suggestions = BudgetService.generate_cost_reduction_suggestions(total_budget, cat_responses)

        return BudgetSummaryResponse(
            event_id=event.id,
            event_name=event.name,
            total_budget=total_budget,
            planned_spending=planned_spending,
            actual_spending=actual_spending,
            emergency_reserve=emergency_reserve,
            remaining_planned_budget=remaining_planned,
            remaining_actual_budget=remaining_actual,
            overrun_amount=overrun_amount,
            is_planned_over_budget=is_planned_over,
            is_actual_over_budget=is_actual_over,
            warnings=warnings,
            categories=cat_responses,
            expenses=expense_responses,
            cost_reduction_suggestions=suggestions,
        )
