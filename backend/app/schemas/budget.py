from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class BudgetCategoryAllocationInput(BaseModel):
    name: str = Field(..., min_length=2, max_length=120)
    planned_amount: int = Field(..., ge=0, description="Planned allocation in integer INR")
    is_emergency_reserve: bool = False
    notes: Optional[str] = Field(default="", max_length=500)

    @field_validator("name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Category name cannot be empty.")
        return cleaned


class BudgetUpdateRequest(BaseModel):
    total_budget: Optional[int] = Field(
        default=None,
        gt=0,
        le=1_000_000_000,
        description="Optional user-approved total budget in integer INR",
    )
    user_approved_total_change: bool = Field(
        default=False,
        description="Must be True if total_budget differs from the existing event total_budget",
    )
    categories: list[BudgetCategoryAllocationInput] = Field(..., min_length=1)


class BudgetCategoryResponse(BaseModel):
    id: Optional[int] = None
    name: str
    planned_amount: int
    actual_spent: int
    remaining_in_category: int
    allocation_percent: float
    is_emergency_reserve: bool
    is_over_category_budget: bool
    notes: str = ""


class ExpenseCreate(BaseModel):
    category_name: str = Field(..., min_length=2, max_length=120)
    title: str = Field(..., min_length=2, max_length=200)
    amount: int = Field(..., gt=0, le=1_000_000_000, description="Expense amount in integer INR")
    incurred_date: Optional[str] = Field(default=None, description="YYYY-MM-DD")
    notes: Optional[str] = Field(default="", max_length=500)

    @field_validator("incurred_date")
    @classmethod
    def validate_date_str(cls, v: Optional[str]) -> str:
        if not v:
            return date.today().isoformat()
        date.fromisoformat(v)
        return v


class ExpenseResponse(BaseModel):
    id: int
    event_id: int
    category_name: str
    title: str
    amount: int
    incurred_date: str
    notes: str
    created_at: datetime

    model_config = {"from_attributes": True}


class CostReductionSuggestion(BaseModel):
    category: str
    current_planned: int
    suggested_planned: int
    potential_savings: int
    rationale: str


class BudgetSummaryResponse(BaseModel):
    event_id: int
    event_name: str
    currency: str = "INR"
    monetary_unit: str = "integer_rupees"
    is_illustrative_estimate: bool = True
    estimate_disclaimer: str = (
        "All generated allocations and sample reference prices are illustrative estimates "
        "in integer INR, not verified live vendor quotes or market confirmations."
    )
    total_budget: int
    planned_spending: int
    actual_spending: int
    emergency_reserve: int
    remaining_planned_budget: int
    remaining_actual_budget: int
    overrun_amount: int
    is_planned_over_budget: bool
    is_actual_over_budget: bool
    warnings: list[str]
    categories: list[BudgetCategoryResponse]
    expenses: list[ExpenseResponse]
    cost_reduction_suggestions: list[CostReductionSuggestion]
