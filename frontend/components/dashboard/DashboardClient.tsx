"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  ArrowRight,
  BookOpen,
  Bot,
  Calendar,
  CalendarPlus,
  CheckCircle2,
  Coins,
  MapPin,
  RefreshCw,
  Sparkles,
  Users,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import {
  formatDateDisplay,
  formatEventTypeLabel,
  formatINR,
} from "@/lib/formatting";
import type { DashboardData } from "@/types/event";
import type { TaskStatus } from "@/types/task";
import {
  BrickDivider,
  CloudSkyBanner,
  CoinIcon,
  EmptyQuestState,
  ErrorBanner,
  QuestionBlockBadge,
  StarMilestoneIcon,
} from "@/components/ui/MarioMotifs";
import { TaskQuestList } from "@/components/checklist/TaskQuestList";

export function DashboardClient() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.getDashboard();
      setData(res);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load dashboard metrics."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadDashboard();
  }, [loadDashboard]);

  const handleTaskStatusChange = async (taskId: number, status: TaskStatus) => {
    await apiClient.updateTask(taskId, { status });
    await loadDashboard();
  };

  if (loading && !data) {
    return (
      <div className="space-y-6" aria-busy="true">
        <div className="h-40 rounded-2xl border-2 border-mario-navy bg-mario-sky/40 animate-pulse" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((n) => (
            <div
              key={n}
              className="h-28 rounded-2xl border-2 border-mario-navy bg-white animate-pulse"
            />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <CloudSkyBanner
        badgeText="WORLD 1 • EVENTWISE AI COMMAND CENTER"
        title="Welcome to EventWise AI — Smart Event Planning Assistant"
        subtitle="Plan weddings, birthdays, and community events locally with custom Python RAG retrieval, Sentence Transformers embeddings, ChromaDB vector search, deterministic INR budgets, and local Ollama AI."
        rightSlot={
          <div className="flex flex-wrap items-center gap-2.5">
            <Link
              href="/planner"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-mario-red text-white font-bold text-sm border-2 border-mario-navy shadow-retro hover:bg-[#d33b32] transition-colors"
            >
              <CalendarPlus className="w-4 h-4" />
              <span>Create Event Plan</span>
            </Link>
            <Link
              href="/chat"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white text-mario-navy font-bold text-sm border-2 border-mario-navy shadow-retro hover:bg-mario-gold transition-colors"
            >
              <Bot className="w-4 h-4 text-mario-green" />
              <span>Ask AI Assistant</span>
            </Link>
          </div>
        }
      />

      {error && <ErrorBanner message={error} onRetry={loadDashboard} />}

      {data && (
        <>
          {/* Summary Metric Cards */}
          <section aria-label="Summary Metrics" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="rounded-2xl border-2 border-mario-navy bg-white p-5 shadow-retro flex items-start justify-between">
              <div>
                <p className="font-pixel text-[11px] text-mario-muted">TOTAL EVENTS</p>
                <p className="mt-1 text-3xl font-extrabold text-mario-navy">
                  {data.total_events}
                </p>
                <p className="mt-1 text-xs font-semibold text-mario-green">
                  {data.indexed_documents_count} RAG docs indexed
                </p>
              </div>
              <QuestionBlockBadge label="1" />
            </div>

            <div className="rounded-2xl border-2 border-mario-navy bg-white p-5 shadow-retro flex items-start justify-between">
              <div>
                <p className="font-pixel text-[11px] text-mario-muted">UPCOMING EVENTS</p>
                <p className="mt-1 text-3xl font-extrabold text-mario-navy">
                  {data.upcoming_events_count}
                </p>
                <p className="mt-1 text-xs font-semibold text-mario-muted">
                  Active event levels in progress
                </p>
              </div>
              <div className="w-9 h-9 rounded-lg bg-mario-sky border-2 border-mario-navy flex items-center justify-center">
                <Calendar className="w-5 h-5 text-mario-navy" />
              </div>
            </div>

            <div className="rounded-2xl border-2 border-mario-navy bg-white p-5 shadow-retro flex items-start justify-between">
              <div>
                <p className="font-pixel text-[11px] text-mario-muted">COMPLETED TASKS</p>
                <p className="mt-1 text-3xl font-extrabold text-mario-navy">
                  {data.completed_tasks}{" "}
                  <span className="text-base font-bold text-mario-muted">
                    / {data.total_tasks}
                  </span>
                </p>
                <p className="mt-1 text-xs font-semibold text-mario-green">
                  {data.overall_completion_percentage}% Quest Completion
                </p>
              </div>
              <div className="w-9 h-9 rounded-lg bg-mario-green border-2 border-mario-navy flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5 text-white" />
              </div>
            </div>

            <div className="rounded-2xl border-2 border-mario-navy bg-white p-5 shadow-retro flex items-start justify-between">
              <div>
                <p className="font-pixel text-[11px] text-mario-muted">REMAINING BUDGET</p>
                <p className="mt-1 text-2xl font-extrabold text-mario-navy">
                  {formatINR(data.remaining_budget_across_events)}
                </p>
                <p className="mt-1 text-xs font-semibold text-mario-muted">
                  Total Budget: {formatINR(data.total_budget_across_events)}
                </p>
              </div>
              <CoinIcon className="w-9 h-9" />
            </div>
          </section>

          {/* Quick Actions Bar */}
          <section aria-label="Quick Actions" className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            <Link
              href="/planner"
              className="group rounded-xl border-2 border-mario-navy bg-white p-4 shadow-retro-sm hover:bg-mario-gold/30 transition-all flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <span className="p-2 rounded-lg bg-mario-red text-white border border-mario-navy">
                  <Sparkles className="w-4 h-4" />
                </span>
                <div>
                  <p className="font-bold text-sm text-mario-navy">Create Event Plan</p>
                  <p className="text-xs text-mario-muted">AI + RAG generator</p>
                </div>
              </div>
              <ArrowRight className="w-4 h-4 text-mario-navy group-hover:translate-x-1 transition-transform" />
            </Link>

            <Link
              href="/budget"
              className="group rounded-xl border-2 border-mario-navy bg-white p-4 shadow-retro-sm hover:bg-mario-gold/30 transition-all flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <span className="p-2 rounded-lg bg-mario-gold text-mario-navy border border-mario-navy">
                  <Coins className="w-4 h-4" />
                </span>
                <div>
                  <p className="font-bold text-sm text-mario-navy">Budget Planner</p>
                  <p className="text-xs text-mario-muted">INR allocations & charts</p>
                </div>
              </div>
              <ArrowRight className="w-4 h-4 text-mario-navy group-hover:translate-x-1 transition-transform" />
            </Link>

            <Link
              href="/chat"
              className="group rounded-xl border-2 border-mario-navy bg-white p-4 shadow-retro-sm hover:bg-mario-gold/30 transition-all flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <span className="p-2 rounded-lg bg-mario-green text-white border border-mario-navy">
                  <Bot className="w-4 h-4" />
                </span>
                <div>
                  <p className="font-bold text-sm text-mario-navy">AI Planning Chat</p>
                  <p className="text-xs text-mario-muted">Follow-ups & proposals</p>
                </div>
              </div>
              <ArrowRight className="w-4 h-4 text-mario-navy group-hover:translate-x-1 transition-transform" />
            </Link>

            <Link
              href="/knowledge-base"
              className="group rounded-xl border-2 border-mario-navy bg-white p-4 shadow-retro-sm hover:bg-mario-gold/30 transition-all flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <span className="p-2 rounded-lg bg-mario-sky text-mario-navy border border-mario-navy">
                  <BookOpen className="w-4 h-4" />
                </span>
                <div>
                  <p className="font-bold text-sm text-mario-navy">Knowledge Base</p>
                  <p className="text-xs text-mario-muted">Upload & search RAG docs</p>
                </div>
              </div>
              <ArrowRight className="w-4 h-4 text-mario-navy group-hover:translate-x-1 transition-transform" />
            </Link>
          </section>

          <BrickDivider />

          {/* Upcoming Event Levels */}
          <section aria-labelledby="upcoming-events-heading">
            <div className="flex flex-wrap items-center justify-between gap-2 mb-4">
              <div className="flex items-center gap-2.5">
                <StarMilestoneIcon className="w-6 h-6" />
                <h2
                  id="upcoming-events-heading"
                  className="text-xl font-extrabold text-mario-navy"
                >
                  Upcoming Event Levels
                </h2>
              </div>
              <button
                type="button"
                onClick={loadDashboard}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white border-2 border-mario-navy text-xs font-bold hover:bg-mario-bg shadow-retro-sm"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Refresh</span>
              </button>
            </div>

            {data.upcoming_events.length === 0 ? (
              <EmptyQuestState
                title="No Event Quests Created Yet"
                description="Start your first wedding, birthday, or community event plan to generate a personalized RAG-backed budget and timeline."
                actionSlot={
                  <Link
                    href="/planner"
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-mario-red text-white font-bold text-sm border-2 border-mario-navy shadow-retro-sm"
                  >
                    <CalendarPlus className="w-4 h-4" />
                    <span>Launch Event Planner</span>
                  </Link>
                }
              />
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                {data.upcoming_events.map((ev) => (
                  <article
                    key={ev.id}
                    className="rounded-2xl border-2 border-mario-navy bg-white p-5 shadow-retro flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2 mb-3">
                        <span className="pipe-pill font-pixel text-[11px] px-2.5 py-1 rounded-md">
                          {ev.level_badge}
                        </span>
                        <span className="px-2.5 py-0.5 rounded-full bg-mario-gold/40 border border-mario-navy text-xs font-bold text-mario-navy">
                          {formatEventTypeLabel(ev.event_type)}
                        </span>
                      </div>

                      <h3 className="text-lg font-extrabold text-mario-navy line-clamp-1">
                        {ev.name}
                      </h3>
                      <p className="mt-1 text-xs text-mario-muted line-clamp-2">
                        {ev.summary || "Personalized event plan ready for review."}
                      </p>

                      <div className="mt-3 grid grid-cols-2 gap-2 text-xs bg-mario-bg p-3 rounded-xl border border-slate-200">
                        <div className="flex items-center gap-1.5 text-mario-navy font-semibold">
                          <MapPin className="w-3.5 h-3.5 text-mario-red shrink-0" />
                          <span className="truncate">{ev.location}</span>
                        </div>
                        <div className="flex items-center gap-1.5 text-mario-navy font-semibold">
                          <Calendar className="w-3.5 h-3.5 text-mario-green shrink-0" />
                          <span>{formatDateDisplay(ev.event_date)}</span>
                        </div>
                        <div className="flex items-center gap-1.5 text-mario-navy font-semibold">
                          <Users className="w-3.5 h-3.5 text-mario-navy shrink-0" />
                          <span>{ev.guest_count} Guests</span>
                        </div>
                        <div className="flex items-center gap-1.5 text-mario-navy font-bold">
                          <CoinIcon className="w-4 h-4 shrink-0" />
                          <span>{formatINR(ev.total_budget)}</span>
                        </div>
                      </div>

                      {/* Planning Progress Bar */}
                      <div className="mt-4">
                        <div className="flex items-center justify-between text-xs font-bold mb-1">
                          <span className="text-mario-navy">
                            Quest Progress ({ev.completed_tasks}/{ev.total_tasks} tasks)
                          </span>
                          <span className="text-mario-green">
                            {ev.completion_percentage}%
                          </span>
                        </div>
                        <div className="w-full h-3 rounded-full bg-slate-200 border border-mario-navy overflow-hidden">
                          <div
                            className="h-full bg-mario-green transition-all"
                            style={{
                              width: `${Math.min(100, Math.max(0, ev.completion_percentage))}%`,
                            }}
                          />
                        </div>
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-200 flex items-center justify-between gap-2">
                      <Link
                        href={`/events/${ev.id}`}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-mario-navy text-white text-xs font-bold hover:bg-mario-red transition-colors"
                      >
                        <span>View Plan</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                      <div className="flex items-center gap-1.5">
                        <Link
                          href={`/events/${ev.id}/timeline`}
                          className="px-2.5 py-1.5 rounded-lg bg-mario-bg border border-mario-navy text-xs font-bold text-mario-navy hover:bg-mario-gold"
                        >
                          Timeline
                        </Link>
                        <Link
                          href={`/budget?eventId=${ev.id}`}
                          className="px-2.5 py-1.5 rounded-lg bg-mario-bg border border-mario-navy text-xs font-bold text-mario-navy hover:bg-mario-gold"
                        >
                          Budget
                        </Link>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>

          {/* Two-column layout: Upcoming Task Quests & Recent Activity */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <section
              aria-labelledby="upcoming-quests-heading"
              className="lg:col-span-2 space-y-3"
            >
              <div className="flex items-center justify-between">
                <h2
                  id="upcoming-quests-heading"
                  className="text-lg font-extrabold text-mario-navy flex items-center gap-2"
                >
                  <QuestionBlockBadge label="?" />
                  <span>Active Planning Quests</span>
                </h2>
                <span className="text-xs font-semibold text-mario-muted">
                  Click status buttons to update progress
                </span>
              </div>
              <TaskQuestList
                tasks={data.upcoming_quests}
                onStatusChange={handleTaskStatusChange}
                compact
              />
            </section>

            <section
              aria-labelledby="recent-activity-heading"
              className="space-y-3"
            >
              <h2
                id="recent-activity-heading"
                className="text-lg font-extrabold text-mario-navy flex items-center gap-2"
              >
                <StarMilestoneIcon className="w-5 h-5" />
                <span>Recent Activity Log</span>
              </h2>
              <div className="rounded-2xl border-2 border-mario-navy bg-white p-4 shadow-retro space-y-3">
                {data.recent_activity.length === 0 ? (
                  <p className="text-xs text-mario-muted py-4 text-center">
                    No activity recorded yet.
                  </p>
                ) : (
                  data.recent_activity.map((act) => (
                    <div
                      key={act.id}
                      className="border-b border-slate-100 last:border-none pb-2.5 last:pb-0"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="px-2 py-0.5 rounded bg-mario-bg border border-mario-navy/30 font-pixel text-[9px] text-mario-navy">
                          {act.category}
                        </span>
                        <span className="text-[11px] text-mario-muted">
                          {formatDateDisplay(act.timestamp)}
                        </span>
                      </div>
                      <p className="mt-1 text-xs font-bold text-mario-navy">
                        {act.title}
                      </p>
                      <p className="text-[11px] text-mario-muted line-clamp-2">
                        {act.detail}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </section>
          </div>
        </>
      )}
    </div>
  );
}
