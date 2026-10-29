"use client";

import React, { useCallback, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  AlertTriangle,
  CheckCircle2,
  Loader2,
  Plus,
  Save,
  ShieldAlert,
  Sparkles,
  Trash2,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { apiClient } from "@/lib/api";
import { formatDateDisplay, formatINR } from "@/lib/formatting";
import type {
  BudgetCategoryAllocationInput,
  BudgetSummary,
} from "@/types/budget";
import type { EventSummaryCard } from "@/types/event";
import {
  BrickDivider,
  CloudSkyBanner,
  CoinIcon,
  EmptyQuestState,
  ErrorBanner,
  QuestionBlockBadge,
} from "@/components/ui/MarioMotifs";

const CHART_COLORS = [
  "#E8483F",
  "#279B52",
  "#FFC928",
  "#20304A",
  "#8EDBFA",
  "#F97316",
  "#8B5CF6",
];

export function BudgetClient() {
  const searchParams = useSearchParams();
  const initialEventIdParam = searchParams.get("eventId");

  const [events, setEvents] = useState<EventSummaryCard[]>([]);
  const [selectedEventId, setSelectedEventId] = useState<number | null>(
    initialEventIdParam ? Number(initialEventIdParam) : null
  );
  const [budget, setBudget] = useState<BudgetSummary | null>(null);
  const [editableCategories, setEditableCategories] = useState<
    BudgetCategoryAllocationInput[]
  >([]);
  const [editableTotalBudget, setEditableTotalBudget] = useState<number>(25000);
  const [userApprovedTotalChange, setUserApprovedTotalChange] =
    useState<boolean>(false);

  // Expense form state
  const [expCategory, setExpCategory] = useState("");
  const [expTitle, setExpTitle] = useState("");
  const [expAmount, setExpAmount] = useState("");
  const [expDate, setExpDate] = useState(
    () => new Date().toISOString().split("T")[0]
  );
  const [expNotes, setExpNotes] = useState("");

  const [loading, setLoading] = useState(true);
  const [savingAllocations, setSavingAllocations] = useState(false);
  const [addingExpense, setAddingExpense] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const loadBudgetForEvent = useCallback(async (evId: number) => {
    setLoading(true);
    setError(null);
    try {
      const b = await apiClient.getEventBudget(evId);
      setBudget(b);
      setEditableTotalBudget(b.total_budget);
      setUserApprovedTotalChange(false);
      setEditableCategories(
        b.categories.map((c) => ({
          name: c.name,
          planned_amount: c.planned_amount,
          is_emergency_reserve: c.is_emergency_reserve,
          notes: c.notes,
        }))
      );
      if (b.categories.length > 0) {
        setExpCategory(b.categories[0].name);
      }
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load event budget."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let mounted = true;
    apiClient
      .listEvents()
      .then((list) => {
        if (!mounted) return;
        setEvents(list);
        const paramId = initialEventIdParam ? Number(initialEventIdParam) : null;
        const targetId =
          paramId && list.some((e) => e.id === paramId)
            ? paramId
            : list[0]?.id ?? null;
        setSelectedEventId(targetId);
        if (targetId) {
          void loadBudgetForEvent(targetId);
        } else {
          setLoading(false);
        }
      })
      .catch((err) => {
        if (mounted) {
          setError(
            err instanceof Error ? err.message : "Failed to list events."
          );
          setLoading(false);
        }
      });
    return () => {
      mounted = false;
    };
  }, [initialEventIdParam, loadBudgetForEvent]);

  const handleSaveAllocations = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEventId || !budget) return;

    const totalChanged = editableTotalBudget !== budget.total_budget;
    if (totalChanged && !userApprovedTotalChange) {
      setError(
        "You changed the Total Budget. Please check the 'I approve changing my total event budget' box to confirm."
      );
      return;
    }

    setSavingAllocations(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const updated = await apiClient.updateEventBudget(selectedEventId, {
        total_budget: editableTotalBudget,
        user_approved_total_change: userApprovedTotalChange,
        categories: editableCategories,
      });
      setBudget(updated);
      setEditableTotalBudget(updated.total_budget);
      setUserApprovedTotalChange(false);
      setEditableCategories(
        updated.categories.map((c) => ({
          name: c.name,
          planned_amount: c.planned_amount,
          is_emergency_reserve: c.is_emergency_reserve,
          notes: c.notes,
        }))
      );
      setSuccessMsg(
        "Budget allocations validated and persisted deterministically by Python!"
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to update budget allocations."
      );
    } finally {
      setSavingAllocations(false);
    }
  };

  const handleAddExpense = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedEventId) return;
    const amt = Number(expAmount);
    if (!expTitle.trim() || !Number.isFinite(amt) || amt <= 0) {
      setError("Enter a valid expense title and positive integer INR amount.");
      return;
    }

    setAddingExpense(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const updated = await apiClient.addExpense(selectedEventId, {
        category_name: expCategory || "Miscellaneous",
        title: expTitle.trim(),
        amount: Math.round(amt),
        incurred_date: expDate,
        notes: expNotes.trim(),
      });
      setBudget(updated);
      setExpTitle("");
      setExpAmount("");
      setExpNotes("");
      setSuccessMsg("Expense recorded and budget balances recalculated!");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add expense.");
    } finally {
      setAddingExpense(false);
    }
  };

  const handleDeleteExpense = async (expenseId: number) => {
    if (!selectedEventId) return;
    setError(null);
    try {
      const updated = await apiClient.deleteExpense(selectedEventId, expenseId);
      setBudget(updated);
      setSuccessMsg("Expense removed.");
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to delete expense."
      );
    }
  };

  const applySuggestedSaving = (categoryName: string, suggestedPlanned: number) => {
    setEditableCategories((prev) =>
      prev.map((cat) =>
        cat.name === categoryName
          ? { ...cat, planned_amount: suggestedPlanned }
          : cat
      )
    );
    setSuccessMsg(
      `Applied suggested allocation (${formatINR(
        suggestedPlanned
      )}) to '${categoryName}' in editor below. Click 'Save Allocations' to persist.`
    );
  };

  const editorSum = editableCategories.reduce(
    (acc, c) => acc + (Number(c.planned_amount) || 0),
    0
  );

  return (
    <div className="space-y-6">
      <CloudSkyBanner
        badgeText="WORLD 3 • AUTHORITATIVE PYTHON BUDGET PLANNER"
        title="Event Budget & Expense Tracker (Integer INR)"
        subtitle="Manage category allocations, track actual expenditures, protect your Emergency Reserve, and visualize allocations with Recharts. All monetary values are validated in integer Indian Rupees (INR)."
      />

      {error && <ErrorBanner message={error} />}

      {successMsg && (
        <div
          role="status"
          className="rounded-xl border-2 border-mario-navy bg-emerald-50 p-4 text-xs font-bold text-mario-navy flex items-center gap-2 shadow-retro-sm"
        >
          <CheckCircle2 className="w-5 h-5 text-mario-green shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}

      {/* Event Selector */}
      <div className="rounded-2xl border-2 border-mario-navy bg-white p-4 shadow-retro-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <QuestionBlockBadge label="₹" />
          <div>
            <label
              htmlFor="budget-event-select"
              className="block text-sm font-extrabold text-mario-navy"
            >
              Select Event to Manage Budget
            </label>
            <p className="text-xs text-mario-muted">
              Sample prices and templates are illustrative estimates, not verified live market quotes.
            </p>
          </div>
        </div>
        <select
          id="budget-event-select"
          value={selectedEventId ?? ""}
          onChange={(e) => {
            const id = Number(e.target.value);
            setSelectedEventId(id);
            void loadBudgetForEvent(id);
          }}
          className="rounded-xl border-2 border-mario-navy bg-mario-bg px-4 py-2 text-sm font-bold text-mario-navy focus:outline-none focus:ring-2 focus:ring-mario-red"
        >
          {events.map((ev) => (
            <option key={ev.id} value={ev.id}>
              {ev.name} ({formatINR(ev.total_budget)})
            </option>
          ))}
        </select>
      </div>

      {!loading && !budget && (
        <EmptyQuestState
          title="No Event Available for Budgeting"
          description="Create an event in the Event Planner first to initialize its budget."
        />
      )}

      {budget && (
        <>
          {/* Overrun Warnings */}
          {budget.warnings.length > 0 && (
            <div
              role="alert"
              className="rounded-2xl border-2 border-mario-red bg-red-50 p-4 shadow-retro-sm space-y-1.5"
            >
              <div className="flex items-center gap-2 text-mario-red font-extrabold text-sm">
                <AlertTriangle className="w-5 h-5 shrink-0" />
                <span>Budget Alert & Overrun Detection</span>
              </div>
              <ul className="list-disc list-inside text-xs font-semibold text-mario-navy space-y-1">
                {budget.warnings.map((w, idx) => (
                  <li key={idx}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Top 5 Financial Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            <div className="rounded-2xl border-2 border-mario-navy bg-white p-4 shadow-retro">
              <p className="font-pixel text-[10px] text-mario-muted">
                APPROVED TOTAL BUDGET
              </p>
              <p className="mt-1 text-2xl font-extrabold text-mario-navy">
                {formatINR(budget.total_budget)}
              </p>
              <span className="mt-1 inline-block text-[11px] font-semibold text-mario-green">
                Authoritative INR Limit
              </span>
            </div>

            <div className="rounded-2xl border-2 border-mario-navy bg-white p-4 shadow-retro">
              <p className="font-pixel text-[10px] text-mario-muted">
                PLANNED SPENDING
              </p>
              <p
                className={`mt-1 text-2xl font-extrabold ${
                  budget.is_planned_over_budget
                    ? "text-mario-red"
                    : "text-mario-navy"
                }`}
              >
                {formatINR(budget.planned_spending)}
              </p>
              <span className="mt-1 inline-block text-[11px] text-mario-muted">
                Unallocated: {formatINR(budget.remaining_planned_budget)}
              </span>
            </div>

            <div className="rounded-2xl border-2 border-mario-navy bg-white p-4 shadow-retro">
              <p className="font-pixel text-[10px] text-mario-muted">
                ACTUAL SPENDING
              </p>
              <p
                className={`mt-1 text-2xl font-extrabold ${
                  budget.is_actual_over_budget
                    ? "text-mario-red"
                    : "text-mario-navy"
                }`}
              >
                {formatINR(budget.actual_spending)}
              </p>
              <span className="mt-1 inline-block text-[11px] text-mario-muted">
                {budget.expenses.length} recorded expense(s)
              </span>
            </div>

            <div className="rounded-2xl border-2 border-mario-navy bg-white p-4 shadow-retro">
              <p className="font-pixel text-[10px] text-mario-muted">
                REMAINING ACTUAL
              </p>
              <p
                className={`mt-1 text-2xl font-extrabold ${
                  budget.remaining_actual_budget < 0
                    ? "text-mario-red"
                    : "text-mario-green"
                }`}
              >
                {formatINR(budget.remaining_actual_budget)}
              </p>
              <span className="mt-1 inline-block text-[11px] text-mario-muted">
                {budget.overrun_amount > 0
                  ? `Overrun: ${formatINR(budget.overrun_amount)}`
                  : "Within approved total"}
              </span>
            </div>

            <div className="rounded-2xl border-2 border-mario-navy bg-amber-50 p-4 shadow-retro">
              <div className="flex items-center justify-between">
                <p className="font-pixel text-[10px] text-mario-navy">
                  EMERGENCY RESERVE
                </p>
                <CoinIcon className="w-5 h-5" />
              </div>
              <p className="mt-1 text-2xl font-extrabold text-mario-navy">
                {formatINR(budget.emergency_reserve)}
              </p>
              <span className="mt-1 inline-block text-[11px] font-bold text-amber-900">
                Protected Buffer
              </span>
            </div>
          </div>

          {/* Recharts Visualizations */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="rounded-2xl border-2 border-mario-navy bg-white p-5 shadow-retro">
              <h3 className="text-base font-extrabold text-mario-navy mb-1">
                Category Allocation Share (Illustrative INR)
              </h3>
              <p className="text-xs text-mario-muted mb-4">
                Proportional breakdown across event budget categories
              </p>
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={budget.categories}
                      dataKey="planned_amount"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={55}
                      outerRadius={95}
                      paddingAngle={2}
                    >
                      {budget.categories.map((entry, index) => (
                        <Cell
                          key={`cell-${entry.name}`}
                          fill={CHART_COLORS[index % CHART_COLORS.length]}
                          stroke="#20304A"
                          strokeWidth={1.5}
                        />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(val: number) => [formatINR(val), "Planned"]}
                    />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="rounded-2xl border-2 border-mario-navy bg-white p-5 shadow-retro">
              <h3 className="text-base font-extrabold text-mario-navy mb-1">
                Planned vs. Actual Spending by Category
              </h3>
              <p className="text-xs text-mario-muted mb-4">
                Compare approved category allocations against recorded expenses
              </p>
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart
                    data={budget.categories}
                    margin={{ top: 10, right: 20, left: 10, bottom: 25 }}
                  >
                    <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                    <XAxis
                      dataKey="name"
                      tick={{ fontSize: 11, fill: "#20304A" }}
                      interval={0}
                      angle={-15}
                      textAnchor="end"
                    />
                    <YAxis tick={{ fontSize: 11, fill: "#20304A" }} />
                    <Tooltip
                      formatter={(val: number) => formatINR(val)}
                    />
                    <Legend />
                    <Bar
                      dataKey="planned_amount"
                      name="Planned (INR)"
                      fill="#279B52"
                      radius={[4, 4, 0, 0]}
                    />
                    <Bar
                      dataKey="actual_spent"
                      name="Actual Spent (INR)"
                      fill="#E8483F"
                      radius={[4, 4, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          <BrickDivider />

          {/* Editable Category Allocations + Cost Reduction Suggestions */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <form
              onSubmit={handleSaveAllocations}
              className="lg:col-span-2 rounded-2xl border-2 border-mario-navy bg-white p-5 shadow-retro space-y-4"
            >
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <h3 className="text-lg font-extrabold text-mario-navy">
                    Edit Category Allocations
                  </h3>
                  <p className="text-xs text-mario-muted">
                    Adjust category amounts in integer INR. Total budget changes require explicit user approval.
                  </p>
                </div>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-extrabold border-2 border-mario-navy ${
                    editorSum > editableTotalBudget
                      ? "bg-red-100 text-mario-red"
                      : "bg-mario-gold text-mario-navy"
                  }`}
                >
                  Allocated Sum: {formatINR(editorSum)} /{" "}
                  {formatINR(editableTotalBudget)}
                </span>
              </div>

              {/* Total Budget Edit Row with Explicit Approval Guard */}
              <div className="rounded-xl border-2 border-mario-navy/70 bg-mario-bg p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <label
                    htmlFor="edit-total-budget"
                    className="block text-xs font-extrabold text-mario-navy"
                  >
                    Total Event Budget (INR)
                  </label>
                  <input
                    id="edit-total-budget"
                    type="number"
                    min={1000}
                    step={100}
                    value={editableTotalBudget}
                    onChange={(e) =>
                      setEditableTotalBudget(Number(e.target.value) || 0)
                    }
                    className="mt-1 rounded-lg border-2 border-mario-navy bg-white px-3 py-1.5 text-sm font-extrabold w-44"
                  />
                </div>

                {editableTotalBudget !== budget.total_budget && (
                  <label className="flex items-center gap-2 text-xs font-bold text-mario-navy bg-amber-100 px-3 py-2 rounded-lg border border-mario-navy cursor-pointer">
                    <input
                      type="checkbox"
                      checked={userApprovedTotalChange}
                      onChange={(e) =>
                        setUserApprovedTotalChange(e.target.checked)
                      }
                      className="w-4 h-4"
                    />
                    <span>
                      I approve changing my total budget from{" "}
                      {formatINR(budget.total_budget)} to{" "}
                      {formatINR(editableTotalBudget)}
                    </span>
                  </label>
                )}
              </div>

              <div className="space-y-2.5">
                {editableCategories.map((cat, idx) => (
                  <div
                    key={cat.name}
                    className={`rounded-xl border p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                      cat.is_emergency_reserve
                        ? "bg-amber-50 border-mario-navy"
                        : "bg-white border-slate-200"
                    }`}
                  >
                    <div className="min-w-0">
                      <p className="text-sm font-extrabold text-mario-navy">
                        {cat.name}{" "}
                        {cat.is_emergency_reserve && (
                          <span className="ml-1.5 px-2 py-0.5 rounded bg-mario-gold text-[10px] font-pixel">
                            RESERVE
                          </span>
                        )}
                      </p>
                      <p className="text-xs text-mario-muted truncate">
                        {cat.notes}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-xs font-bold text-mario-muted">
                        ₹
                      </span>
                      <input
                        type="number"
                        min={0}
                        step={100}
                        aria-label={`Planned allocation for ${cat.name}`}
                        value={cat.planned_amount}
                        onChange={(e) => {
                          const val = Math.max(0, Math.round(Number(e.target.value) || 0));
                          setEditableCategories((prev) =>
                            prev.map((item, i) =>
                              i === idx ? { ...item, planned_amount: val } : item
                            )
                          );
                        }}
                        className="w-32 rounded-lg border-2 border-mario-navy px-2.5 py-1.5 text-sm font-extrabold text-right"
                      />
                    </div>
                  </div>
                ))}
              </div>

              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  disabled={savingAllocations}
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl bg-mario-green text-white font-extrabold text-sm border-2 border-mario-navy shadow-retro-sm hover:bg-[#1f8244] disabled:opacity-50"
                >
                  {savingAllocations ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Save className="w-4 h-4" />
                  )}
                  <span>Save Allocations</span>
                </button>
              </div>
            </form>

            {/* Cost Reduction Suggestions */}
            <div className="rounded-2xl border-2 border-mario-navy bg-white p-5 shadow-retro space-y-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-mario-red" />
                <h3 className="text-base font-extrabold text-mario-navy">
                  Cost Reduction Suggestions
                </h3>
              </div>
              <p className="text-xs text-mario-muted">
                Deterministic savings ideas calculated while keeping your Emergency Reserve safe.
              </p>
              <div className="space-y-3">
                {budget.cost_reduction_suggestions.map((s, idx) => (
                  <div
                    key={idx}
                    className="rounded-xl border-2 border-mario-navy/80 bg-mario-bg p-3.5 space-y-2"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-extrabold text-xs text-mario-navy">
                        {s.category}
                      </span>
                      <span className="px-2 py-0.5 rounded bg-emerald-100 border border-mario-green text-[11px] font-extrabold text-mario-green">
                        Save {formatINR(s.potential_savings)}
                      </span>
                    </div>
                    <p className="text-xs text-mario-navy leading-relaxed">
                      {s.rationale}
                    </p>
                    <button
                      type="button"
                      onClick={() =>
                        applySuggestedSaving(s.category, s.suggested_planned)
                      }
                      className="w-full py-1.5 rounded-lg bg-white border-2 border-mario-navy text-xs font-bold text-mario-navy hover:bg-mario-gold transition-colors"
                    >
                      Preview {formatINR(s.suggested_planned)} in Editor
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Expense Tracker */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <form
              onSubmit={handleAddExpense}
              className="rounded-2xl border-2 border-mario-navy bg-white p-5 shadow-retro space-y-3.5"
            >
              <h3 className="text-base font-extrabold text-mario-navy flex items-center gap-2">
                <Plus className="w-4 h-4 text-mario-red" />
                <span>Record Actual Expense</span>
              </h3>

              <div>
                <label
                  htmlFor="exp-cat"
                  className="block text-xs font-bold text-mario-navy mb-1"
                >
                  Category
                </label>
                <select
                  id="exp-cat"
                  value={expCategory}
                  onChange={(e) => setExpCategory(e.target.value)}
                  className="w-full rounded-xl border-2 border-mario-navy px-3 py-2 text-xs font-bold bg-white"
                >
                  {budget.categories.map((c) => (
                    <option key={c.name} value={c.name}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label
                  htmlFor="exp-title"
                  className="block text-xs font-bold text-mario-navy mb-1"
                >
                  Expense Description *
                </label>
                <input
                  id="exp-title"
                  type="text"
                  required
                  value={expTitle}
                  onChange={(e) => setExpTitle(e.target.value)}
                  placeholder="e.g., Catering 25% Booking Advance"
                  className="w-full rounded-xl border-2 border-mario-navy px-3 py-2 text-xs font-medium"
                />
              </div>

              <div className="grid grid-cols-2 gap-2.5">
                <div>
                  <label
                    htmlFor="exp-amount"
                    className="block text-xs font-bold text-mario-navy mb-1"
                  >
                    Amount (INR) *
                  </label>
                  <input
                    id="exp-amount"
                    type="number"
                    required
                    min={1}
                    value={expAmount}
                    onChange={(e) => setExpAmount(e.target.value)}
                    placeholder="2500"
                    className="w-full rounded-xl border-2 border-mario-navy px-3 py-2 text-xs font-bold"
                  />
                </div>
                <div>
                  <label
                    htmlFor="exp-date"
                    className="block text-xs font-bold text-mario-navy mb-1"
                  >
                    Date *
                  </label>
                  <input
                    id="exp-date"
                    type="date"
                    required
                    value={expDate}
                    onChange={(e) => setExpDate(e.target.value)}
                    className="w-full rounded-xl border-2 border-mario-navy px-3 py-2 text-xs font-medium"
                  />
                </div>
              </div>

              <div>
                <label
                  htmlFor="exp-notes"
                  className="block text-xs font-bold text-mario-navy mb-1"
                >
                  Notes
                </label>
                <input
                  id="exp-notes"
                  type="text"
                  value={expNotes}
                  onChange={(e) => setExpNotes(e.target.value)}
                  placeholder="Optional receipt or payment method note"
                  className="w-full rounded-xl border-2 border-mario-navy px-3 py-2 text-xs font-medium"
                />
              </div>

              <button
                type="submit"
                disabled={addingExpense}
                className="w-full inline-flex items-center justify-center gap-2 py-2.5 rounded-xl bg-mario-red text-white font-extrabold text-xs border-2 border-mario-navy shadow-retro-sm hover:bg-[#d33b32]"
              >
                {addingExpense ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Plus className="w-4 h-4" />
                )}
                <span>Add Expense to Ledger</span>
              </button>
            </form>

            {/* Recorded Expenses List */}
            <div className="lg:col-span-2 rounded-2xl border-2 border-mario-navy bg-white p-5 shadow-retro space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-extrabold text-mario-navy">
                  Recorded Expenses Ledger ({budget.expenses.length})
                </h3>
                <span className="text-xs font-bold text-mario-muted">
                  Total Spent: {formatINR(budget.actual_spending)}
                </span>
              </div>

              {budget.expenses.length === 0 ? (
                <div className="rounded-xl border border-dashed border-mario-navy/40 bg-mario-bg p-6 text-center text-xs text-mario-muted">
                  No actual expenses recorded for this event yet.
                </div>
              ) : (
                <div className="space-y-2">
                  {budget.expenses.map((exp) => (
                    <div
                      key={exp.id}
                      className="rounded-xl border border-slate-200 bg-mario-bg p-3 flex items-center justify-between gap-3"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 rounded bg-white border border-mario-navy text-[10px] font-bold text-mario-navy">
                            {exp.category_name}
                          </span>
                          <span className="text-xs font-extrabold text-mario-navy">
                            {exp.title}
                          </span>
                        </div>
                        <p className="text-[11px] text-mario-muted mt-0.5">
                          {formatDateDisplay(exp.incurred_date)}
                          {exp.notes ? ` • ${exp.notes}` : ""}
                        </p>
                      </div>
                      <div className="flex items-center gap-3 shrink-0">
                        <span className="text-sm font-extrabold text-mario-navy">
                          {formatINR(exp.amount)}
                        </span>
                        <button
                          type="button"
                          onClick={() => handleDeleteExpense(exp.id)}
                          aria-label={`Delete expense ${exp.title}`}
                          className="p-1.5 rounded-lg text-mario-muted hover:text-mario-red transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div className="pt-2 border-t border-slate-200 flex items-center gap-2 text-[11px] text-mario-muted">
                <ShieldAlert className="w-4 h-4 text-mario-navy shrink-0" />
                <span>{budget.estimate_disclaimer}</span>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
