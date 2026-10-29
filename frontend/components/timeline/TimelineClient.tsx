"use client";

import React, { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  AlertTriangle,
  ArrowLeft,
  Calendar,
  CheckCircle2,
  Loader2,
  Plus,
} from "lucide-react";
import { apiClient } from "@/lib/api";
import { formatDateDisplay, formatEventTypeLabel } from "@/lib/formatting";
import type { TaskPriority, TaskStatus, TimelineSummary } from "@/types/task";
import {
  CloudSkyBanner,
  ErrorBanner,
  QuestionBlockBadge,
} from "@/components/ui/MarioMotifs";
import { TaskQuestList } from "@/components/checklist/TaskQuestList";

export function TimelineClient({ eventId }: { eventId: number }) {
  const [timeline, setTimeline] = useState<TimelineSummary | null>(null);
  const [statusFilter, setStatusFilter] = useState<"all" | TaskStatus>("all");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Add custom task form
  const [title, setTitle] = useState("");
  const [milestoneLabel, setMilestoneLabel] = useState("Custom Quest");
  const [dueDate, setDueDate] = useState(
    () => new Date().toISOString().split("T")[0]
  );
  const [priority, setPriority] = useState<TaskPriority>("medium");
  const [category, setCategory] = useState("Logistics");
  const [description, setDescription] = useState("");
  const [addingTask, setAddingTask] = useState(false);

  const loadTimeline = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.getEventTimeline(eventId);
      setTimeline(res);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load event timeline."
      );
    } finally {
      setLoading(false);
    }
  }, [eventId]);

  useEffect(() => {
    void loadTimeline();
  }, [loadTimeline]);

  const handleStatusChange = async (taskId: number, status: TaskStatus) => {
    await apiClient.updateTask(taskId, { status });
    await loadTimeline();
  };

  const handleDeleteTask = async (taskId: number) => {
    await apiClient.deleteTask(taskId);
    await loadTimeline();
  };

  const handleAddTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    setAddingTask(true);
    setError(null);
    try {
      await apiClient.createEventTask(eventId, {
        title: title.trim(),
        milestone_label: milestoneLabel.trim() || "Custom Quest",
        due_date: dueDate,
        priority,
        category: category.trim() || "General",
        description: description.trim(),
        status: "pending",
      });
      setTitle("");
      setDescription("");
      await loadTimeline();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to add custom quest task."
      );
    } finally {
      setAddingTask(false);
    }
  };

  const filteredTasks = (timeline?.tasks || []).filter((t) =>
    statusFilter === "all" ? true : t.status === statusFilter
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <Link
          href={`/events/${eventId}`}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-white border-2 border-mario-navy text-xs font-bold text-mario-navy shadow-retro-sm hover:bg-mario-gold"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Event Plan Details</span>
        </Link>
      </div>

      {error && <ErrorBanner message={error} onRetry={loadTimeline} />}

      {loading && !timeline && (
        <div className="h-40 rounded-2xl border-2 border-mario-navy bg-white animate-pulse" />
      )}

      {timeline && (
        <>
          <CloudSkyBanner
            badgeText={`QUEST TIMELINE • ${formatEventTypeLabel(
              timeline.event_type
            ).toUpperCase()}`}
            title={`Chronological Quest Timeline: ${timeline.event_name}`}
            subtitle={`Event Date: ${formatDateDisplay(
              timeline.event_date
            )} (${
              timeline.days_until_event >= 0
                ? `${timeline.days_until_event} day(s) remaining`
                : `${Math.abs(timeline.days_until_event)} day(s) ago`
            }). Mark tasks as Pending, In Progress, or Completed.`}
          />

          {timeline.schedule_notice && (
            <div
              role="status"
              className="rounded-xl border-2 border-amber-600 bg-amber-50 p-4 text-xs font-bold text-mario-navy flex items-start gap-2.5 shadow-retro-sm"
            >
              <AlertTriangle className="w-5 h-5 text-amber-700 shrink-0" />
              <span>{timeline.schedule_notice}</span>
            </div>
          )}

          {/* Progress Summary Bar */}
          <div className="rounded-2xl border-2 border-mario-navy bg-white p-5 shadow-retro space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <CheckCircle2 className="w-6 h-6 text-mario-green" />
                <div>
                  <h2 className="text-base font-extrabold text-mario-navy">
                    Overall Quest Completion: {timeline.completion_percentage}%
                  </h2>
                  <p className="text-xs text-mario-muted">
                    {timeline.completed_tasks} Completed •{" "}
                    {timeline.in_progress_tasks} In Progress •{" "}
                    {timeline.pending_tasks} Pending (Total {timeline.total_tasks})
                  </p>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-1.5">
                {(["all", "pending", "in_progress", "completed"] as const).map(
                  (st) => (
                    <button
                      key={st}
                      type="button"
                      onClick={() => setStatusFilter(st)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-bold border-2 ${
                        statusFilter === st
                          ? "bg-mario-navy text-white border-mario-navy"
                          : "bg-mario-bg text-mario-navy border-transparent hover:border-mario-navy"
                      }`}
                    >
                      {st === "all"
                        ? "All Quests"
                        : st === "in_progress"
                        ? "In Progress"
                        : st.charAt(0).toUpperCase() + st.slice(1)}
                    </button>
                  )
                )}
              </div>
            </div>

            <div className="w-full h-4 rounded-full bg-slate-200 border-2 border-mario-navy overflow-hidden">
              <div
                className="h-full bg-mario-green transition-all"
                style={{
                  width: `${Math.min(
                    100,
                    Math.max(0, timeline.completion_percentage)
                  )}%`,
                }}
              />
            </div>
          </div>

          {/* Quest List + Add Custom Task Form */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <TaskQuestList
                tasks={filteredTasks}
                onStatusChange={handleStatusChange}
                onDeleteTask={handleDeleteTask}
              />
            </div>

            <form
              onSubmit={handleAddTask}
              className="rounded-2xl border-2 border-mario-navy bg-white p-5 shadow-retro space-y-3.5 h-fit"
            >
              <div className="flex items-center gap-2">
                <QuestionBlockBadge label="+" />
                <h3 className="text-base font-extrabold text-mario-navy">
                  Add Custom Milestone Task
                </h3>
              </div>

              <div>
                <label
                  htmlFor="task-title"
                  className="block text-xs font-bold text-mario-navy mb-1"
                >
                  Task Title *
                </label>
                <input
                  id="task-title"
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g., Book return gift bags"
                  className="w-full rounded-xl border-2 border-mario-navy px-3 py-2 text-xs font-medium"
                />
              </div>

              <div className="grid grid-cols-2 gap-2.5">
                <div>
                  <label
                    htmlFor="task-milestone"
                    className="block text-xs font-bold text-mario-navy mb-1"
                  >
                    Milestone Label
                  </label>
                  <input
                    id="task-milestone"
                    type="text"
                    value={milestoneLabel}
                    onChange={(e) => setMilestoneLabel(e.target.value)}
                    className="w-full rounded-xl border-2 border-mario-navy px-3 py-2 text-xs font-medium"
                  />
                </div>
                <div>
                  <label
                    htmlFor="task-due"
                    className="block text-xs font-bold text-mario-navy mb-1"
                  >
                    Due Date *
                  </label>
                  <input
                    id="task-due"
                    type="date"
                    required
                    value={dueDate}
                    onChange={(e) => setDueDate(e.target.value)}
                    className="w-full rounded-xl border-2 border-mario-navy px-3 py-2 text-xs font-medium"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-2.5">
                <div>
                  <label
                    htmlFor="task-priority"
                    className="block text-xs font-bold text-mario-navy mb-1"
                  >
                    Priority
                  </label>
                  <select
                    id="task-priority"
                    value={priority}
                    onChange={(e) =>
                      setPriority(e.target.value as TaskPriority)
                    }
                    className="w-full rounded-xl border-2 border-mario-navy px-3 py-2 text-xs font-bold bg-white"
                  >
                    <option value="high">High (Boss Priority)</option>
                    <option value="medium">Medium (Standard)</option>
                    <option value="low">Low (Bonus)</option>
                  </select>
                </div>
                <div>
                  <label
                    htmlFor="task-category"
                    className="block text-xs font-bold text-mario-navy mb-1"
                  >
                    Category
                  </label>
                  <input
                    id="task-category"
                    type="text"
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full rounded-xl border-2 border-mario-navy px-3 py-2 text-xs font-medium"
                  />
                </div>
              </div>

              <div>
                <label
                  htmlFor="task-desc"
                  className="block text-xs font-bold text-mario-navy mb-1"
                >
                  Notes / Checklist Details
                </label>
                <textarea
                  id="task-desc"
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full rounded-xl border-2 border-mario-navy px-3 py-2 text-xs font-medium"
                />
              </div>

              <button
                type="submit"
                disabled={addingTask}
                className="w-full inline-flex items-center justify-center gap-2 py-2.5 rounded-xl bg-mario-red text-white font-extrabold text-xs border-2 border-mario-navy shadow-retro-sm hover:bg-[#d33b32]"
              >
                {addingTask ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Plus className="w-4 h-4" />
                )}
                <span>Add Task to Timeline</span>
              </button>
            </form>
          </div>
        </>
      )}
    </div>
  );
}
