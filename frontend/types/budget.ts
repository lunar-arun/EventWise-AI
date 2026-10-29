export interface BudgetCategoryAllocationInput {
  name: string;
  planned_amount: number;
  is_emergency_reserve: boolean;
  notes?: string;
}

export interface BudgetUpdateRequest {
  total_budget?: number;
  user_approved_total_change: boolean;
  categories: BudgetCategoryAllocationInput[];
}

export interface BudgetCategoryItem {
  id?: number | null;
  name: string;
  planned_amount: number;
  actual_spent: number;
  remaining_in_category: number;
  allocation_percent: number;
  is_emergency_reserve: boolean;
  is_over_category_budget: boolean;
  notes: string;
}

export interface ExpenseCreateInput {
  category_name: string;
  title: string;
  amount: number;
  incurred_date?: string;
  notes?: string;
}

export interface ExpenseItem {
  id: number;
  event_id: number;
  category_name: string;
  title: string;
  amount: number;
  incurred_date: string;
  notes: string;
  created_at: string;
}

export interface CostReductionSuggestion {
  category: string;
  current_planned: number;
  suggested_planned: number;
  potential_savings: number;
  rationale: string;
}

export interface BudgetSummary {
  event_id: number;
  event_name: string;
  currency: string;
  monetary_unit: string;
  is_illustrative_estimate: boolean;
  estimate_disclaimer: string;
  total_budget: number;
  planned_spending: number;
  actual_spending: number;
  emergency_reserve: number;
  remaining_planned_budget: number;
  remaining_actual_budget: number;
  overrun_amount: number;
  is_planned_over_budget: boolean;
  is_actual_over_budget: boolean;
  warnings: string[];
  categories: BudgetCategoryItem[];
  expenses: ExpenseItem[];
  cost_reduction_suggestions: CostReductionSuggestion[];
}
