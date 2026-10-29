"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  Calendar,
  Coins,
  Edit3,
  Loader2,
  MapPin,
  RefreshCw,
  Sparkles,
  Trash2,
  Users,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import {
  formatDateDisplay,
  formatEventTypeLabel,
  formatINR,
} from "@/lib/formatting";
import type { EventDetail } from "@/types/event";
import type { TaskStatus } from "@/types/task";
import {
  BrickDivider,
  CloudSkyBanner,
  CoinIcon,
  ErrorBanner,
  QuestionBlockBadge,
  StarMilestoneIcon,
} from "@/components/ui/MarioMotifs";
import { SourceCitationsList } from "@/components/knowledge/SourceCitationsList";
import { TaskQuestList } from "@/components/checklist/TaskQuestList";
import { ChatClient } from "@/components/chat/ChatClient";

export default function EventDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const router = useRouter();
  const eventId = Number(params.id);

  const [event, setEvent] = useState<EventDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [regenerating, setRegenerating] = useState(false);
  const [editing, setEditing] = useState(false);
  const [savingEdit, setSavingEdit] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Edit preferences state
  const [editTheme, setEditTheme] = useState("");
  const [editDietary, setEditDietary] = useState("");
  const [editAdditional, setEditAdditional] = useState("");
  const [editGuests, setEditGuests] = useState(50);
  const [editDate, setEditDate] = useState("");
  const [editBudget, setEditBudget] = useState(25000);
  const [approveBudgetChange, setApproveBudgetChange] = useState(false);

  const loadEvent = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiClient.getEvent(eventId);
      setEvent(data);
      setEditTheme(data.preferred_theme);
      setEditDietary(data.dietary_requirements);
      setEditAdditional(data.additional_preferences);
      setEditGuests(data.guest_count);
      setEditDate(data.event_date);
      setEditBudget(data.total_budget);
      setApproveBudgetChange(false);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load event details."
      );
    } finally {
      setLoading(false);
    }
  }, [eventId]);

  useEffect(() => {
    void loadEvent();
  }, [loadEvent]);

  const handleRegeneratePlan = async () => {
    setRegenerating(true);
    setError(null);
    try {
      const updated = await apiClient.generateEventPlan(eventId);
      setEvent(updated);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to regenerate event plan."
      );
    } finally {
      setRegenerating(false);
    }
  };

  const handleSavePreferences = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!event) return;
    if (editBudget !== event.total_budget && !approveBudgetChange) {
      setError(
        "Please check the approval box to confirm changing your total budget."
      );
      return;
    }

    setSavingEdit(true);
    setError(null);
    try {
      const updated = await apiClient.updateEvent(eventId, {
        preferred_theme: editTheme,
        dietary_requirements: editDietary,
        additional_preferences: editAdditional,
        guest_count: editGuests,
        event_date: editDate,
        total_budget: editBudget,
        user_approved_budget_change: approveBudgetChange,
        regenerate_plan: true,
      });
      setEvent(updated);
      setEditing(false);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to update event."
      );
    } finally {
      setSavingEdit(false);
    }
  };

  const handleTaskStatusChange = async (taskId: number, status: TaskStatus) => {
    await apiClient.updateTask(taskId, { status });
    await loadEvent();
  };

  const handleDeleteEvent = async () => {
    await apiClient.deleteEvent(eventId);
    router.push("/");
  };

  if (loading && !event) {
    return (
      <div className="space-y-4">
        <div className="h-36 rounded-2xl border-2 border-mario-navy bg-white animate-pulse" />
        <div className="h-64 rounded-2xl border-2 border-mario-navy bg-white animate-pulse" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white border-2 border-mario-navy text-xs font-bold text-mario-navy shadow-retro-sm hover:bg-mario-gold"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Dashboard</span>
        </Link>

        {event && (
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => setEditing((prev) => !prev)}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white border-2 border-mario-navy text-xs font-bold text-mario-navy shadow-retro-sm hover:bg-mario-gold"
            >
              <Edit3 className="w-3.5 h-3.5" />
              <span>{editing ? "Close Editor" : "Edit Preferences"}</span>
            </button>

            <button
              type="button"
              disabled={regenerating}
              onClick={handleRegeneratePlan}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-mario-green text-white border-2 border-mario-navy text-xs font-bold shadow-retro-sm hover:bg-[#1f8244] disabled:opacity-50"
            >
              {regenerating ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <RefreshCw className="w-3.5 h-3.5" />
              )}
              <span>Regenerate AI Plan</span>
            </button>

            <button
              type="button"
              onClick={handleDeleteEvent}
              className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-red-50 border-2 border-mario-red text-xs font-bold text-mario-red hover:bg-mario-red hover:text-white transition-colors"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Delete Event</span>
            </button>
          </div>
        )}
      </div>

      {error && <ErrorBanner message={error} onRetry={loadEvent} />}

      {event && (
        <>
          <CloudSkyBanner
            badgeText={`${formatEventTypeLabel(
              event.event_type
            ).toUpperCase()} • MODE: ${event.generation_mode.toUpperCase()}`}
            title={event.name}
            subtitle={event.summary}
            rightSlot={
              <div className="flex flex-wrap gap-2">
                <Link
                  href={`/events/${event.id}/timeline`}
                  className="px-4 py-2.5 rounded-xl bg-mario-gold text-mario-navy font-extrabold text-xs border-2 border-mario-navy shadow-retro-sm"
                >
                  Open Quest Timeline ({event.tasks.length})
                </Link>
                <Link
                  href={`/budget?eventId=${event.id}`}
                  className="px-4 py-2.5 rounded-xl bg-white text-mario-navy font-extrabold text-xs border-2 border-mario-navy shadow-retro-sm"
                >
                  Manage Budget
                </Link>
              </div>
            }
          />

          {/* Event Metadata Strip */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="rounded-xl border-2 border-mario-navy bg-white p-3.5 shadow-retro-sm flex items-center gap-3">
              <MapPin className="w-5 h-5 text-mario-red shrink-0" />
              <div>
                <p className="text-[10px] font-pixel text-mario-muted">
                  LOCATION
                </p>
                <p className="text-sm font-extrabold text-mario-navy">
                  {event.location}
                </p>
              </div>
            </div>

            <div className="rounded-xl border-2 border-mario-navy bg-white p-3.5 shadow-retro-sm flex items-center gap-3">
              <Calendar className="w-5 h-5 text-mario-green shrink-0" />
              <div>
                <p className="text-[10px] font-pixel text-mario-muted">
                  EVENT DATE
                </p>
                <p className="text-sm font-extrabold text-mario-navy">
                  {formatDateDisplay(event.event_date)}
                </p>
              </div>
            </div>

            <div className="rounded-xl border-2 border-mario-navy bg-white p-3.5 shadow-retro-sm flex items-center gap-3">
              <Users className="w-5 h-5 text-mario-navy shrink-0" />
              <div>
                <p className="text-[10px] font-pixel text-mario-muted">
                  GUEST SCALE
                </p>
                <p className="text-sm font-extrabold text-mario-navy">
                  {event.guest_count} Guests
                </p>
              </div>
            </div>

            <div className="rounded-xl border-2 border-mario-navy bg-white p-3.5 shadow-retro-sm flex items-center gap-3">
              <CoinIcon className="w-6 h-6 shrink-0" />
              <div>
                <p className="text-[10px] font-pixel text-mario-muted">
                  APPROVED BUDGET
                </p>
                <p className="text-sm font-extrabold text-mario-navy">
                  {formatINR(event.total_budget)}
                </p>
              </div>
            </div>
          </div>

          {/* Preference Editor Panel */}
          {editing && (
            <form
              onSubmit={handleSavePreferences}
              className="rounded-2xl border-2 border-mario-navy bg-amber-50/70 p-5 shadow-retro space-y-4"
            >
              <h3 className="text-base font-extrabold text-mario-navy">
                Edit Event Preferences & Regenerate Recommendations
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-bold text-mario-navy mb-1">
                    Preferred Theme
                  </label>
                  <input
                    type="text"
                    value={editTheme}
                    onChange={(e) => setEditTheme(e.target.value)}
                    className="w-full rounded-xl border-2 border-mario-navy bg-white px-3 py-2 text-xs font-medium"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-mario-navy mb-1">
                    Dietary Requirements
                  </label>
                  <input
                    type="text"
                    value={editDietary}
                    onChange={(e) => setEditDietary(e.target.value)}
                    className="w-full rounded-xl border-2 border-mario-navy bg-white px-3 py-2 text-xs font-medium"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-mario-navy mb-1">
                    Guest Count
                  </label>
                  <input
                    type="number"
                    min={1}
                    value={editGuests}
                    onChange={(e) => setEditGuests(Number(e.target.value) || 1)}
                    className="w-full rounded-xl border-2 border-mario-navy bg-white px-3 py-2 text-xs font-bold"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-mario-navy mb-1">
                    Event Date
                  </label>
                  <input
                    type="date"
                    value={editDate}
                    onChange={(e) => setEditDate(e.target.value)}
                    className="w-full rounded-xl border-2 border-mario-navy bg-white px-3 py-2 text-xs font-medium"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-mario-navy mb-1">
                    Total Budget (INR)
                  </label>
                  <input
                    type="number"
                    min={1000}
                    step={100}
                    value={editBudget}
                    onChange={(e) =>
                      setEditBudget(Number(e.target.value) || 1000)
                    }
                    className="w-full rounded-xl border-2 border-mario-navy bg-white px-3 py-2 text-xs font-bold"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-mario-navy mb-1">
                    Additional Notes
                  </label>
                  <input
                    type="text"
                    value={editAdditional}
                    onChange={(e) => setEditAdditional(e.target.value)}
                    className="w-full rounded-xl border-2 border-mario-navy bg-white px-3 py-2 text-xs font-medium"
                  />
                </div>
              </div>

              {editBudget !== event.total_budget && (
                <label className="inline-flex items-center gap-2 text-xs font-bold text-mario-navy bg-white px-3 py-2 rounded-lg border-2 border-mario-navy cursor-pointer">
                  <input
                    type="checkbox"
                    checked={approveBudgetChange}
                    onChange={(e) => setApproveBudgetChange(e.target.checked)}
                    className="w-4 h-4"
                  />
                  <span>
                    I explicitly approve changing the total budget from{" "}
                    {formatINR(event.total_budget)} to {formatINR(editBudget)}
                  </span>
                </label>
              )}

              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setEditing(false)}
                  className="px-4 py-2 rounded-xl bg-white border-2 border-mario-navy text-xs font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={savingEdit}
                  className="inline-flex items-center gap-1.5 px-5 py-2 rounded-xl bg-mario-red text-white border-2 border-mario-navy text-xs font-extrabold shadow-retro-sm"
                >
                  {savingEdit && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>Save & Regenerate Plan</span>
                </button>
              </div>
            </form>
          )}

          {/* Theme Recommendations + AI Suggestions */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 rounded-2xl border-2 border-mario-navy bg-white p-5 shadow-retro space-y-4">
              <div className="flex items-center gap-2">
                <StarMilestoneIcon className="w-6 h-6" />
                <h2 className="text-lg font-extrabold text-mario-navy">
                  Theme & Concept Recommendations
                </h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {event.theme_recommendations.map((theme, idx) => (
                  <div
                    key={idx}
                    className="rounded-xl border-2 border-mario-navy/80 bg-mario-bg p-4 space-y-2"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="font-extrabold text-sm text-mario-navy">
                        {theme.title}
                      </h3>
                      <span className="px-2 py-0.5 rounded bg-mario-gold text-[10px] font-bold border border-mario-navy shrink-0">
                        {theme.estimated_tier}
                      </span>
                    </div>
                    <p className="text-xs font-bold text-mario-green">
                      {theme.tagline}
                    </p>
                    <p className="text-xs text-mario-navy leading-relaxed">
                      {theme.description}
                    </p>
                    <ul className="list-disc list-inside text-xs text-mario-navy space-y-1">
                      {theme.decor_highlights.map((d, i) => (
                        <li key={i}>{d}</li>
                      ))}
                    </ul>
                    <p className="text-[11px] font-semibold text-mario-muted pt-1 border-t border-slate-200">
                      🍽️ {theme.catering_notes}
                    </p>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-2xl border-2 border-mario-navy bg-white p-5 shadow-retro space-y-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-mario-red" />
                <h2 className="text-lg font-extrabold text-mario-navy">
                  AI Planning Suggestions
                </h2>
              </div>
              <p className="text-xs text-mario-muted">
                {event.illustrative_price_notice}
              </p>
              <ul className="space-y-2.5">
                {event.ai_suggestions.map((sug, i) => (
                  <li
                    key={i}
                    className="rounded-xl border border-slate-200 bg-mario-bg p-3 text-xs font-semibold text-mario-navy flex items-start gap-2.5"
                  >
                    <QuestionBlockBadge label={String(i + 1)} />
                    <span className="leading-relaxed">{sug}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* Budget Breakdown Summary */}
          <div className="rounded-2xl border-2 border-mario-navy bg-white p-5 shadow-retro space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <Coins className="w-5 h-5 text-mario-green" />
                <h2 className="text-lg font-extrabold text-mario-navy">
                  Deterministic Budget Breakdown (Total:{" "}
                  {formatINR(event.budget.total_budget)})
                </h2>
              </div>
              <Link
                href={`/budget?eventId=${event.id}`}
                className="px-3.5 py-1.5 rounded-lg bg-mario-gold border-2 border-mario-navy text-xs font-bold text-mario-navy shadow-retro-sm"
              >
                Edit Allocations & Expenses →
              </Link>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {event.budget.categories.map((cat) => (
                <div
                  key={cat.name}
                  className={`rounded-xl border p-3.5 ${
                    cat.is_emergency_reserve
                      ? "bg-amber-50 border-mario-navy"
                      : "bg-mario-bg border-slate-200"
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-extrabold text-mario-navy">
                      {cat.name}
                    </span>
                    <span className="text-[11px] font-bold text-mario-green">
                      {cat.allocation_percent}%
                    </span>
                  </div>
                  <p className="mt-1 text-lg font-extrabold text-mario-navy">
                    {formatINR(cat.planned_amount)}
                  </p>
                  <p className="text-[11px] text-mario-muted mt-0.5">
                    Actual Spent: {formatINR(cat.actual_spent)}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Interactive Timeline & Checklist */}
          <div className="rounded-2xl border-2 border-mario-navy bg-white p-5 shadow-retro space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-lg font-extrabold text-mario-navy">
                Planning Timeline & Task Checklist ({event.tasks.length})
              </h2>
              <Link
                href={`/events/${event.id}/timeline`}
                className="px-3.5 py-1.5 rounded-lg bg-mario-bg border-2 border-mario-navy text-xs font-bold text-mario-navy"
              >
                Open Full Timeline View →
              </Link>
            </div>
            <TaskQuestList
              tasks={event.tasks}
              onStatusChange={handleTaskStatusChange}
            />
          </div>

          {/* Knowledge Sources */}
          <SourceCitationsList
            citations={event.citations}
            missingEvidenceNote={event.missing_evidence_note}
          />

          <BrickDivider />

          {/* Embedded AI Chat for Modifying / Discussing this Event */}
          <section aria-labelledby="event-chat-heading" className="space-y-3">
            <h2
              id="event-chat-heading"
              className="text-xl font-extrabold text-mario-navy flex items-center gap-2"
            >
              <QuestionBlockBadge label="AI" />
              <span>Chat with EventWise AI to Refine This Plan</span>
            </h2>
            <ChatClient
              fixedEventId={event.id}
              onEventModified={loadEvent}
              embedded
            />
          </section>
        </>
      )}
    </div>
  );
}
